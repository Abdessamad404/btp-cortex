from flask import Blueprint, request, render_template, jsonify
from app.rag import ask

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

    if not question:
        return jsonify({"error": "Question vide."}), 400

    result = ask(question, projet=projet)
    return jsonify(result)
