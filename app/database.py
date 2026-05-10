import sqlite3
import os
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
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
            uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status        TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()
