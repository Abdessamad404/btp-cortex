from sentence_transformers import SentenceTransformer
from config import EMBED_MODEL

model = SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    return model.encode(texts, show_progress_bar=False).tolist()
