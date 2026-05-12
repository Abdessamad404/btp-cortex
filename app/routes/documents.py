from flask import Blueprint, render_template
from app.database import get_connection

docs_bp = Blueprint("documents", __name__)


@docs_bp.route("/documents")
def documents():
    """Show all ingested documents in a table."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
    conn.close()
    return render_template("documents.html", documents=rows)
