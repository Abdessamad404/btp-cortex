from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, current_app
from app.connectors.whatsapp import parse_whatsapp
from app.connectors.email_imap import fetch_emails
from app.connectors.photo import analyze_photo
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


# ── Photos de chantier ────────────────────────────────────────────────────────


@connectors_bp.route("/connectors/photo", methods=["POST"])
def photo_ingest():
    """
    Handle a construction site photo upload.
    Sends the image to the NIM vision model (Llama 3.2 Vision) which returns
    a detailed French text description of what it sees.
    That description then goes through the full pipeline: chunk → embed → Pinecone → SQLite.
    """
    file = request.files.get("file")
    projet = request.form.get("projet", "general")
    lot_technique = request.form.get("lot_technique", "unknown")
    criticite = request.form.get("criticite", "normale")
    # Optional context hint from the user — helps the model focus its analysis
    description = request.form.get("description", "")

    # Validate file presence
    if not file or file.filename == "":
        flash("Aucune image sélectionnée.")
        return redirect(url_for("connectors.connectors"))

    # Only accept JPG and PNG — common formats for phone photos on site
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed_extensions:
        flash("Format invalide. Utilisez JPG ou PNG.")
        return redirect(url_for("connectors.connectors"))

    # Save the image to disk
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Deduplicate — same image uploaded twice should not be indexed twice
    file_hash = get_file_hash(filepath)
    if already_ingested(file_hash):
        flash("Cette photo a déjà été ingérée.")
        return redirect(url_for("connectors.connectors"))

    # Send the image to the vision model — get back a text description
    try:
        text = analyze_photo(filepath, description)
    except Exception as e:
        flash(f"Erreur d'analyse de l'image : {str(e)}")
        return redirect(url_for("connectors.connectors"))

    if not text.strip():
        flash("Le modèle n'a pas pu analyser cette image.")
        return redirect(url_for("connectors.connectors"))

    meta = {
        "filename": file.filename,
        "file_type": "photo",
        "projet": projet,
        "lot_technique": lot_technique,
        "auteur": "vision-model",
        "criticite": criticite,
        "type_document": "photo",
        "source_type": "photo",
    }

    # Pipeline: chunk → embed → upsert to Pinecone (all or nothing)
    chunks = chunk(text)
    embeddings = embed(chunks)
    pinecone_ids = upsert(chunks, embeddings, meta)

    # Only write to SQLite after Pinecone confirms success
    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
           (filename, file_type, file_hash, projet, lot_technique, auteur,
            criticite, type_document, pinecone_ids, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            file.filename,
            "photo",
            file_hash,
            projet,
            lot_technique,
            "vision-model",
            criticite,
            "photo",
            json.dumps(pinecone_ids),
            "photo",
        ),
    )
    conn.commit()
    conn.close()

    update_chunk_count(file_hash, len(chunks))

    flash(f"✅ Photo analysée et indexée — {len(chunks)} chunks.")
    return redirect(url_for("connectors.connectors"))


# ── Photo ingest — JSON API (used by the multi-upload JS) ────────────────────


@connectors_bp.route("/api/connectors/photo", methods=["POST"])
def photo_ingest_api():
    """
    JSON version of photo_ingest — called by the frontend JS for each photo
    in the batch upload. Returns {"ok": true, "chunks": N} or {"ok": false, "error": "..."}.

    Why a separate route?
    The HTML form route uses flash() + redirect() which is designed for full page reloads.
    AJAX (fetch) calls need a JSON response instead — the JS reads it to update the progress bar.
    """
    file = request.files.get("file")
    projet = request.form.get("projet", "general")
    lot_technique = request.form.get("lot_technique", "unknown")
    criticite = request.form.get("criticite", "normale")
    description = request.form.get("description", "")

    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "Aucune image."})

    allowed_extensions = {".jpg", ".jpeg", ".png"}
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in allowed_extensions:
        return jsonify({"ok": False, "error": "Format invalide."})

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    file_hash = get_file_hash(filepath)
    if already_ingested(file_hash):
        return jsonify({"ok": False, "error": "Déjà ingérée."})

    try:
        text = analyze_photo(filepath, description)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

    if not text.strip():
        return jsonify({"ok": False, "error": "Analyse vide."})

    meta = {
        "filename": file.filename,
        "file_type": "photo",
        "projet": projet,
        "lot_technique": lot_technique,
        "auteur": "vision-model",
        "criticite": criticite,
        "type_document": "photo",
        "source_type": "photo",
    }

    chunks_list = chunk(text)
    embeddings = embed(chunks_list)
    pinecone_ids = upsert(chunks_list, embeddings, meta)

    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
           (filename, file_type, file_hash, projet, lot_technique, auteur,
            criticite, type_document, pinecone_ids, source_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            file.filename, "photo", file_hash, projet, lot_technique,
            "vision-model", criticite, "photo", json.dumps(pinecone_ids), "photo",
        ),
    )
    conn.commit()
    conn.close()

    update_chunk_count(file_hash, len(chunks_list))
    return jsonify({"ok": True, "chunks": len(chunks_list)})


# ── Email schedule (polling automatique) ─────────────────────────────────────


@connectors_bp.route("/connectors/email/schedule", methods=["POST"])
def email_schedule_create():
    """
    Save a new email polling schedule to SQLite and register it with APScheduler.
    From this moment the scheduler will poll that inbox every interval_hours hours,
    run the full pipeline, and index any new emails automatically.
    """
    from app.scheduler import scheduler, _make_poll_job

    host = request.form.get("host", "").strip()
    port = int(request.form.get("port", 993))
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    folder = request.form.get("folder", "INBOX").strip()
    max_emails = int(request.form.get("max_emails", 50))
    projet = request.form.get("projet", "general")
    lot_technique = request.form.get("lot_technique", "unknown")
    criticite = request.form.get("criticite", "normale")
    interval_hours = int(request.form.get("interval_hours", 6))

    if not host or not username or not password:
        flash("Veuillez remplir tous les champs IMAP obligatoires.")
        return redirect(url_for("connectors.connectors"))

    # Persist the schedule config to SQLite
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO email_schedules
           (host, port, username, password, folder, max_emails,
            projet, lot_technique, criticite, interval_hours)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (host, port, username, password, folder, max_emails,
         projet, lot_technique, criticite, interval_hours),
    )
    schedule_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Register the job with the live scheduler — takes effect immediately
    app = current_app._get_current_object()
    scheduler.add_job(
        _make_poll_job(app, schedule_id),
        trigger="interval",
        hours=interval_hours,
        id=f"email_poll_{schedule_id}",
        replace_existing=True,
    )

    flash(f"✅ Polling configuré — vérification toutes les {interval_hours}h.")
    return redirect(url_for("connectors.connectors"))


@connectors_bp.route("/api/email-schedules", methods=["GET"])
def email_schedules_list():
    """Return all saved email schedules as JSON. Passwords are excluded."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, host, username, folder, max_emails,
                  projet, lot_technique, criticite, interval_hours, created_at
           FROM email_schedules
           ORDER BY created_at DESC"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@connectors_bp.route("/api/email-schedules/<int:schedule_id>", methods=["DELETE"])
def email_schedule_delete(schedule_id):
    """Remove a schedule from SQLite and cancel its APScheduler job."""
    from app.scheduler import scheduler

    # Cancel the running job first
    job_id = f"email_poll_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Then delete from DB
    conn = get_connection()
    conn.execute("DELETE FROM email_schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})
