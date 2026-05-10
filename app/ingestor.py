import hashlib
import os
from datetime import datetime
from app.extractors import extract_text
from app.database import get_connection
from config import UPLOAD_FOLDER


def get_file_hash(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def already_ingested(file_hash):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM documents WHERE file_hash = ?", (file_hash,)
    ).fetchone()
    conn.close()
    return row is not None


def ingest(
    filepath,
    projet="general",
    lot_technique="unknown",
    auteur="unknown",
    criticite="normale",
    type_document=None,
):

    # Step 1 — deduplicate
    file_hash = get_file_hash(filepath)
    if already_ingested(file_hash):
        return {"status": "duplicate", "message": "File already ingested."}

    # Step 2 — extract text
    text = extract_text(filepath)

    # Step 3 — save metadata to SQLite
    filename = os.path.basename(filepath)
    file_type = os.path.splitext(filename)[1].lower().replace(".", "")
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO documents
          (filename, file_type, file_hash, projet, lot_technique, auteur, criticite, type_document)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            filename,
            file_type,
            file_hash,
            projet,
            lot_technique,
            auteur,
            criticite,
            type_document or file_type,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "text": text,
        "meta": {
            "filename": filename,
            "file_type": file_type,
            "projet": projet,
            "lot_technique": lot_technique,
            "auteur": auteur,
            "criticite": criticite,
            "type_document": type_document or file_type,
            "ingested_at": datetime.utcnow().isoformat(),
        },
    }
