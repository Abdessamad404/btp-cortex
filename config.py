import os
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "btp-docs")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5
UPLOAD_FOLDER = "data/uploads"
DB_PATH = "data/btp.db"
