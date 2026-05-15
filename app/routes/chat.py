from flask import Blueprint, request, render_template, jsonify
from app.rag import ask
from app.database import get_connection
import time

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat")
def chat():
    """Serve the chat page."""
    return render_template("chat.html")


@chat_bp.route("/api/chat", methods=["POST"])
def api_chat():
    """
    API endpoint called by JavaScript (not the browser directly).
    Receives JSON, returns JSON.
    """
    data = request.get_json()
    question = data.get("question", "").strip()
    projet = data.get("projet", None)
    conversation_id = data.get("conversation_id", None)

    if not question:
        return jsonify({"error": "Question vide."}), 400

    last_error = None
    for attempt in range(3):
        try:
            result = ask(question, projet=projet)
            break
        except Exception as e:
            last_error = e
            time.sleep(1)
    else:
        return jsonify({"answer": "Le service est temporairement indisponible. Réessayez dans quelques secondes.", "sources": []}), 200

    # Save messages to DB if a conversation is active
    if conversation_id:
        conn = get_connection()
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, "user", question),
        )
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, "assistant", result["answer"]),
        )
        conn.commit()
        conn.close()

    return jsonify(result)
