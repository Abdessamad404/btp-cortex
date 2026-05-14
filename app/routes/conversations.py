from flask import Blueprint, jsonify, request
from app.database import get_connection

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.route("/api/conversations", methods=["POST"])
def create_conversation():
    """Create a new conversation row and return its id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO conversations (title) VALUES (?)", ("Nouvelle conversation",)
    )
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": conversation_id})


@conversations_bp.route("/api/conversations", methods=["GET"])
def list_conversations():
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
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@conversations_bp.route("/api/conversations/<int:conversation_id>", methods=["PATCH"])
def update_title(conversation_id):
    title = request.get_json().get("title", "").strip()
    if not title:
        return jsonify({"error": "Titre vide."}), 400
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


@conversations_bp.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    conn = get_connection()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})
