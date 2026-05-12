from flask import Blueprint, render_template
from app.database import get_connection

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    conn = get_connection()
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    chunk_count = conn.execute("SELECT SUM(status) FROM documents").fetchone()[0] or 0
    question_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0] or 0
    conn.close()
    return render_template(
        "index.html", doc_count=doc_count, chunk_count=chunk_count, question_count=question_count
    )
