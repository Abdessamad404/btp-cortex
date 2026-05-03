from flask import Flask
from config import FLASK_SECRET_KEY, UPLOAD_FOLDER, DB_PATH
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY

    # Ensure required folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    return app
