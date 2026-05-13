import sqlite3
import os
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # enforce cascade deletes
    return conn


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            filename      TEXT NOT NULL,
            file_type     TEXT NOT NULL,
            file_hash     TEXT UNIQUE NOT NULL,
            projet        TEXT,
            lot_technique TEXT,
            auteur        TEXT,
            criticite     TEXT,
            type_document TEXT,
            chunk_count   INTEGER DEFAULT 0,
            uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status        TEXT DEFAULT 'pending'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT DEFAULT 'Nouvelle conversation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()


def update_chunk_count(file_hash: str, count: int):
    """Update chunk_count for a document after chunking is done."""
    conn = get_connection()
    conn.execute(
        "UPDATE documents SET chunk_count = ?, status = 'processed' WHERE file_hash = ?",
        (count, file_hash),
    )
    conn.commit()
    conn.close()
