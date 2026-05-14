from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.ingestor import ingest
from app.chunker import chunk
from app.embedder import embed
from app.vector_store import upsert
from config import UPLOAD_FOLDER
from app.database import get_connection, update_chunk_count
import os
import json

upload_bp = Blueprint("upload", __name__)

# File types accepted on the manual upload page
ALLOWED = {".pdf", ".docx", ".txt", ".eml", ".csv", ".xlsx"}


@upload_bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        projet = request.form.get("projet", "general")
        lot_technique = request.form.get("lot_technique", "unknown")
        auteur = request.form.get("auteur", "unknown")
        criticite = request.form.get("criticite", "normale")
        type_document = request.form.get("type_document", None)

        # Validate file presence
        if not file or file.filename == "":
            flash("Aucun fichier sélectionné.")
            return redirect(url_for("upload.upload"))

        # Validate file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED:
            flash(f"Type de fichier non supporté : {ext}")
            return redirect(url_for("upload.upload"))

        # Save file to disk before processing
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Deduplicate + extract text
        result = ingest(
            filepath,
            projet=projet,
            lot_technique=lot_technique,
            auteur=auteur,
            criticite=criticite,
            type_document=type_document,
        )

        if result["status"] == "duplicate":
            flash("Ce fichier a déjà été ingéré.")
            return redirect(url_for("upload.upload"))

        # Chunk → embed → upsert to Pinecone
        chunks = chunk(result["text"])
        embeddings = embed(chunks)
        pinecone_ids = upsert(chunks, embeddings, result["meta"])

        # Only commit to SQLite after Pinecone succeeds — prevents ghost records
        meta = result["meta"]
        conn = get_connection()
        conn.execute(
            """INSERT INTO documents
               (filename, file_type, file_hash, projet, lot_technique, auteur,
                criticite, type_document, pinecone_ids, source_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                meta["filename"],
                meta["file_type"],
                result["file_hash"],
                meta["projet"],
                meta["lot_technique"],
                meta["auteur"],
                meta["criticite"],
                meta["type_document"],
                json.dumps(pinecone_ids),
                "upload",  # source_type for manual uploads
            ),
        )
        conn.commit()
        conn.close()

        update_chunk_count(result["file_hash"], len(chunks))

        flash(f"✅ {file.filename} ingéré avec succès — {len(chunks)} chunks indexés.")
        return redirect(url_for("upload.upload"))

    return render_template("upload.html")
