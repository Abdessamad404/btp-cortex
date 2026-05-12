from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.ingestor import ingest
from app.chunker import chunk
from app.embedder import embed
from app.vector_store import upsert
from config import UPLOAD_FOLDER
from app.database import update_chunk_count
import os

upload_bp = Blueprint("upload", __name__)

# File types we accept
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

        # Validate file
        if not file or file.filename == "":
            flash("Aucun fichier sélectionné.")
            return redirect(url_for("upload.upload"))

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED:
            flash(f"Type de fichier non supporté : {ext}")
            return redirect(url_for("upload.upload"))

        # Save file to disk
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # Run the full ingestion pipeline
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

        # Chunk → embed → store in Pinecone
        chunks = chunk(result["text"])
        embeddings = embed(chunks)
        upsert(chunks, embeddings, result["meta"])

        # Update chunk count in SQLite
        update_chunk_count(result["file_hash"], len(chunks))

        flash(f"✅ {file.filename} ingéré avec succès — {len(chunks)} chunks indexés.")
        return redirect(url_for("upload.upload"))

    return render_template("upload.html")
