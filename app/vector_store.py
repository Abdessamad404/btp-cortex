from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX
import uuid

# Connect to Pinecone once when the file is imported — reused on every call
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def upsert(chunks: list[str], embeddings: list[list[float]], metadata: dict):
    """
    Store chunks and their vectors in Pinecone.
    Each chunk gets its own vector entry with a unique ID and shared metadata.
    """
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append(
            {
                "id": str(uuid.uuid4()),  # unique ID for each vector
                "values": embedding,  # the 384-number vector
                "metadata": {
                    **metadata,
                    "text": chunk,
                },  # BTP fields + the chunk text itself
            }
        )
    index.upsert(vectors=vectors)


def search(embedding: list[float], top_k: int = 5, filter: dict = None) -> list[dict]:
    """
    Find the top_k most similar chunks to a query embedding.
    Optionally filter by metadata fields (e.g. projet, lot_technique).
    Returns a list of metadata dicts — one per matching chunk.
    """
    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,  # return metadata alongside the vectors
        filter=filter,  # e.g. {"projet": "Résidence Oran"}
    )
    # Extract just the metadata from each match — that's all the RAG engine needs
    return [match.metadata for match in results.matches]
