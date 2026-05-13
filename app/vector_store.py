from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX
import uuid

# Connect to Pinecone once when the file is imported — reused on every call
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


def upsert(
    chunks: list[str], embeddings: list[list[float]], metadata: dict
) -> list[str]:
    """
    Store chunks and their vectors in Pinecone.
    Returns the list of vector IDs generated.
    """
    vectors = []
    ids = []
    for chunk, embedding in zip(chunks, embeddings):
        vector_id = str(uuid.uuid4())  # unique ID for each vector
        ids.append(vector_id)
        vectors.append(
            {
                "id": vector_id,
                "values": embedding,  # the 384-number vector
                "metadata": {
                    **metadata,
                    "text": chunk,
                },  # BTP fields + the chunk text itself
            }
        )
    index.upsert(vectors=vectors)
    return ids


def delete_vectors(ids: list[str]):
    """Delete vectors from Pinecone by their IDs."""
    index.delete(ids=ids)


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
