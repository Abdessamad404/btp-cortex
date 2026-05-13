from flask import Blueprint, jsonify
from app.database import get_connection

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/api/conversations", methods=["POST"])
def create_conversation():
    """Create a new conversation row and return its id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO conversations (title) VALUES (?)",
        ("Nouvelle conversation",),
    )
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": conversation_id})


@conversations_bp.route("/api/conversations", methods=["GET"])
def list_conversations():
    """Return all conversations, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@conversations_bp.route(
    "/api/conversations/<int:conversation_id>/messages", methods=["GET"]
)
def get_messages(conversation_id):
    """Return all messages for a specific conversation, oldest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@conversations_bp.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages (cascade)."""
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


@conversations_bp.route("/api/conversations", methods=["DELETE"])
def delete_all_conversations():
    """Delete all conversations and their messages (cascade)."""
    conn = get_connection()
    conn.execute("DELETE FROM conversations")
    conn.commit()
    conn.close()
    return jsonify({"status": "all deleted"})
