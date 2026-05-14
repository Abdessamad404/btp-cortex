import os
import json
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

# Module-level singleton — one scheduler instance shared across the whole app.
# daemon=True means the scheduler thread dies automatically when Flask stops.
scheduler = BackgroundScheduler(daemon=True)


def _make_poll_job(app, schedule_id: int):
    """
    Build and return the polling function for a given schedule.

    We use a closure (a function that captures variables from its outer scope)
    so each job knows which schedule_id it belongs to.

    The function re-fetches the schedule config from DB on every run —
    this avoids stale data if the schedule is edited in the future.
    """

    def poll():
        # APScheduler runs jobs in background threads.
        # Flask's database helpers (get_connection, etc.) require an app context
        # to know which database file to use. We push one manually here.
        with app.app_context():
            from app.database import get_connection, update_chunk_count
            from app.connectors.email_imap import fetch_emails
            from app.chunker import chunk
            from app.embedder import embed
            from app.vector_store import upsert
            from app.ingestor import get_file_hash, already_ingested
            from config import UPLOAD_FOLDER

            # Re-read config from DB (fresh, not stale closure)
            conn = get_connection()
            row = conn.execute(
                "SELECT * FROM email_schedules WHERE id = ?", (schedule_id,)
            ).fetchone()
            conn.close()

            if not row:
                # Schedule was deleted between runs — nothing to do
                return

            # Connect to IMAP and fetch emails
            try:
                text = fetch_emails(
                    row["host"],
                    row["port"],
                    row["username"],
                    row["password"],
                    row["folder"],
                    row["max_emails"],
                )
            except Exception as e:
                print(f"[scheduler] IMAP error for schedule {schedule_id}: {e}")
                return

            if not text.strip():
                print(f"[scheduler] No new emails for schedule {schedule_id}")
                return

            # Save text to disk so MD5 deduplication works the same as manual ingest
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"emails_{row['username']}_auto_{timestamp}.txt"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

            # Skip if these exact emails were already indexed
            file_hash = get_file_hash(filepath)
            if already_ingested(file_hash):
                print(f"[scheduler] No new content since last run for schedule {schedule_id}")
                return

            meta = {
                "filename": filename,
                "file_type": "email",
                "projet": row["projet"],
                "lot_technique": row["lot_technique"],
                "auteur": row["username"],
                "criticite": row["criticite"],
                "type_document": "email",
                "source_type": "email",
            }

            # Full pipeline — all or nothing
            chunks = chunk(text)
            embeddings = embed(chunks)
            pinecone_ids = upsert(chunks, embeddings, meta)

            conn = get_connection()
            conn.execute(
                """INSERT INTO documents
                   (filename, file_type, file_hash, projet, lot_technique, auteur,
                    criticite, type_document, pinecone_ids, source_type)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    filename, "email", file_hash, row["projet"], row["lot_technique"],
                    row["username"], row["criticite"], "email",
                    json.dumps(pinecone_ids), "email",
                ),
            )
            conn.commit()
            conn.close()

            update_chunk_count(file_hash, len(chunks))
            print(f"[scheduler] Indexed {len(chunks)} chunks for schedule {schedule_id}")

    return poll


def init_scheduler(app):
    """
    Start the APScheduler background scheduler and reload any saved schedules.

    Called once from create_app() in app/__init__.py.
    On startup, we re-register all schedules that were saved before the server
    restarted — otherwise they would be lost on every Flask restart.
    """
    # Guard against double-start (Werkzeug reloader launches two processes)
    if scheduler.running:
        return

    from app.database import get_connection

    # Re-register all existing schedules from DB
    with app.app_context():
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, interval_hours FROM email_schedules"
        ).fetchall()
        conn.close()

    for row in rows:
        scheduler.add_job(
            _make_poll_job(app, row["id"]),
            trigger="interval",
            hours=row["interval_hours"],
            id=f"email_poll_{row['id']}",
            replace_existing=True,
        )
        print(f"[scheduler] Restored job for schedule {row['id']} (every {row['interval_hours']}h)")

    scheduler.start()
    print(f"[scheduler] Started — {len(rows)} job(s) loaded")
