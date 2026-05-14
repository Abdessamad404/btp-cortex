import sqlite3
import os
from config import DB_PATH


def get_connection():
    """Open a SQLite connection with Row factory and foreign key enforcement."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # required for ON DELETE CASCADE to work
    return conn


def init_db():
    """Create all tables if they don't already exist."""
    os.makedirs("data", exist_ok=True)
    conn = get_connection()

    # ── Documents ─────────────────────────────────────────────────────────────
    # source_type tracks where the document came from: 'upload', 'whatsapp', 'email'
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
            pinecone_ids  TEXT,
            source_type   TEXT DEFAULT 'upload',
            uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status        TEXT DEFAULT 'pending'
        )
    """)

    # ── Conversations ─────────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT DEFAULT 'Nouvelle conversation',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Messages ──────────────────────────────────────────────────────────────
    # ON DELETE CASCADE: deleting a conversation auto-deletes its messages
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

    # ── Email schedules ───────────────────────────────────────────────────────
    # Stores recurring IMAP polling configurations.
    # Each row = one email account polled automatically every interval_hours.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_schedules (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            host           TEXT NOT NULL,
            port           INTEGER DEFAULT 993,
            username       TEXT NOT NULL,
            password       TEXT NOT NULL,
            folder         TEXT DEFAULT 'INBOX',
            max_emails     INTEGER DEFAULT 50,
            projet         TEXT DEFAULT 'general',
            lot_technique  TEXT DEFAULT 'unknown',
            criticite      TEXT DEFAULT 'normale',
            interval_hours INTEGER DEFAULT 6,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def update_chunk_count(file_hash: str, count: int):
    """Mark a document as processed and store how many chunks were created."""
    conn = get_connection()
    conn.execute(
        "UPDATE documents SET chunk_count = ?, status = 'processed' WHERE file_hash = ?",
        (count, file_hash),
    )
    conn.commit()
    conn.close()
