from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.connectors.whatsapp import parse_whatsapp
from app.connectors.email_imap import fetch_emails
from app.chunker import chunk
from app.embedder import embed
from app.vector_store import upsert
from app.database import get_connection, update_chunk_count
from app.ingestor import get_file_hash, already_ingested
from config import UPLOAD_FOLDER
from datetime import datetime, timezone
import os
import json

connectors_bp = Blueprint("connectors", __name__)


@connectors_bp.route("/connectors")
def connectors():
    """Render the connectors hub page."""
    return render_template("connectors.html")


# ── WhatsApp ──────────────────────────────────────────────────────────────────


@connectors_bp.route("/connectors/whatsapp", methods=["POST"])
def whatsapp_ingest():
    """
    Handle a WhatsApp exported .txt file upload.
    Parses the conversation, runs the full pipeline, saves to SQLite + Pinecone.
    """
    file = request.files.get("file")
    projet = request.form.get("projet", "general")
    lot_technique = request.form.get("lot_technique", "unknown")
    auteur = request.form.get("auteur", "unknown")
    criticite = request.form.get("criticite", "normale")

    # Validate file
    if not file or file.filename == "":
        flash("Aucun fichier sélectionné.")
        return redirect(url_for("connectors.connectors"))

    if not file.filename.lower().endswith(".txt"):
        flash("Format invalide. Exportez votre conversation WhatsApp en .txt")
        return redirect(url_for("connectors.connectors"))

    # Save the raw file to disk
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Deduplicate — if this exact file was already ingested, skip it
    file_hash = get_file_hash(filepath)
    if already_ingested(file_hash):
        flash("Ce fichier WhatsApp a déjà été ingéré.")
        return redirect(url_for("connectors.connectors"))

    # Parse the WhatsApp format into clean text
    text = parse_whatsapp(filepath)
    if not text.strip():
        flash("Aucun message lisible trouvé dans ce fichier.")
        return redirect(url_for("connectors.connectors"))

    # Metadata — used in Pinecone vectors and SQLite record
    meta = {
        "filename": file.filename,
        "file_type": "whatsapp",
        "projet": projet,
        "lot_technique": lot_technique,
        "auteur": auteur,
        "criticite": criticite,
        "type_document": "whatsapp",
        "source_type": "whatsapp",
    }

    # Run the pipeline: chunk → embed → upsert to Pinecone
    chunks = chunk(text)
    embeddings = embed(chunks)
    pinecone_ids = upsert(chunks, embeddings, meta)

    # Only save to SQLite after Pinecone succeeds — all or nothing
    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
           (filename, file_type, file_hash, projet, lot_technique, auteur,
            criticite, type_document, pinecone_ids, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            file.filename,
            "whatsapp",
            file_hash,
            projet,
            lot_technique,
            auteur,
            criticite,
            "whatsapp",
            json.dumps(pinecone_ids),
            "whatsapp",
        ),
    )
    conn.commit()
    conn.close()

    update_chunk_count(file_hash, len(chunks))

    flash(f"✅ WhatsApp ingéré avec succès — {len(chunks)} chunks indexés.")
    return redirect(url_for("connectors.connectors"))


# ── Email IMAP ────────────────────────────────────────────────────────────────


@connectors_bp.route("/connectors/email", methods=["POST"])
def email_ingest():
    """
    Handle IMAP email fetching.
    Connects to the email server, fetches recent emails, runs the full pipeline.
    Credentials are used only for this request and are never stored.
    """
    host = request.form.get("host", "").strip()
    port = int(request.form.get("port", 993))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    folder = request.form.get("folder", "INBOX").strip()
    max_emails = int(request.form.get("max_emails", 50))
    projet = request.form.get("projet", "general")
    lot_technique = request.form.get("lot_technique", "unknown")
    auteur = request.form.get("auteur", "")
    criticite = request.form.get("criticite", "normale")

    # Use the email address as auteur if not provided
    if not auteur:
        auteur = username

    # Validate required IMAP fields
    if not host or not username or not password:
        flash("Veuillez remplir tous les champs IMAP obligatoires.")
        return redirect(url_for("connectors.connectors"))

    # Fetch emails from the IMAP server
    try:
        text = fetch_emails(host, port, username, password, folder, max_emails)
    except Exception as e:
        flash(f"Erreur de connexion IMAP : {str(e)}")
        return redirect(url_for("connectors.connectors"))

    if not text.strip():
        flash("Aucun email lisible trouvé dans ce dossier.")
        return redirect(url_for("connectors.connectors"))

    # Generate a unique filename from the email account + timestamp
    # We save the fetched text to disk so deduplication works via MD5 hash
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"emails_{username}_{timestamp}.txt"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    file_hash = get_file_hash(filepath)

    meta = {
        "filename": filename,
        "file_type": "email",
        "projet": projet,
        "lot_technique": lot_technique,
        "auteur": auteur,
        "criticite": criticite,
        "type_document": "email",
        "source_type": "email",
    }

    # Run the pipeline: chunk → embed → upsert to Pinecone
    chunks = chunk(text)
    embeddings = embed(chunks)
    pinecone_ids = upsert(chunks, embeddings, meta)

    # Only save to SQLite after Pinecone succeeds
    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
           (filename, file_type, file_hash, projet, lot_technique, auteur,
            criticite, type_document, pinecone_ids, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            filename,
            "email",
            file_hash,
            projet,
            lot_technique,
            auteur,
            criticite,
            "email",
            json.dumps(pinecone_ids),
            "email",
        ),
    )
    conn.commit()
    conn.close()

    update_chunk_count(file_hash, len(chunks))

    flash(f"✅ {len(chunks)} chunks d'emails indexés avec succès.")
    return redirect(url_for("connectors.connectors"))
