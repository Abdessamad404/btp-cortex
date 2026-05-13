from flask import Blueprint, render_template, jsonify
from app.database import get_connection
from app.vector_store import delete_vectors
from config import UPLOAD_FOLDER
import json
import os

docs_bp = Blueprint("documents", __name__)


@docs_bp.route("/documents")
def documents():
    """Show all ingested documents in a table."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    return render_template("documents.html", documents=rows)


@docs_bp.route("/api/documents/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete a document from Pinecone, disk, and SQLite — all or nothing."""
    conn = get_connection()
    row = conn.execute(
        "SELECT filename, pinecone_ids FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Document introuvable."}), 404

    filename = row["filename"]
    pinecone_ids = json.loads(row["pinecone_ids"]) if row["pinecone_ids"] else []
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Step 1 — delete from Pinecone
    try:
        if pinecone_ids:
            delete_vectors(pinecone_ids)
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Échec suppression Pinecone : {str(e)}"}), 500

    # Step 2 — delete file from disk
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Échec suppression fichier : {str(e)}"}), 500

    # Step 3 — delete from SQLite (only if both above succeeded)
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "deleted"})
