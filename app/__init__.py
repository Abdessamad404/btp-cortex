from flask import Flask
from config import FLASK_SECRET_KEY, UPLOAD_FOLDER, DB_PATH
import os
from app.database import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Ensure required folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Initialize the database
    init_db()

    # Register blueprints
    from app.routes.upload import upload_bp
    from app.routes.chat import chat_bp
    from app.routes.documents import docs_bp
    from app.routes.home import home_bp
    from app.routes.conversations import conversations_bp
    from app.routes.connectors import connectors_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(connectors_bp)

    # Start the background email polling scheduler.
    # Only runs in the main process — not in the Werkzeug reloader watcher process,
    # which would cause the scheduler (and its jobs) to start twice in debug mode.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
