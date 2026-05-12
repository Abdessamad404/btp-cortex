from flask import Blueprint, render_template
from app.database import get_connection

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    conn = get_connection()
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunk_count = (
        conn.execute("SELECT SUM(chunk_count) FROM documents").fetchone()[0] or 0
    )
    proj_count = conn.execute(
        "SELECT COUNT(DISTINCT projet) FROM documents"
    ).fetchone()[0]
    conn.close()
    return render_template(
        "index.html",
        doc_count=doc_count,
        chunk_count=chunk_count,
        proj_count=proj_count,
    )
