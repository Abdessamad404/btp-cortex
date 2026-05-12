from flask import Flask
from config import FLASK_SECRET_KEY, UPLOAD_FOLDER, DB_PATH
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Ensure required folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Initialize the database
    from app.database import init_db

    init_db()

    # Register blueprints
    from app.routes.upload import upload_bp
    from app.routes.chat import chat_bp
    from app.routes.documents import docs_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(docs_bp)

    return app
