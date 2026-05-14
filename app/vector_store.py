from config import PINECONE_API_KEY, PINECONE_INDEX
import uuid

_index = None


def _get_index():
    global _index
    if _index is None:
        from pinecone import Pinecone
        _index = Pinecone(api_key=PINECONE_API_KEY).Index(PINECONE_INDEX)
    return _index


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
        vector_id = str(uuid.uuid4())
        ids.append(vector_id)
        vectors.append(
            {
                "id": vector_id,
                "values": embedding,
                "metadata": {**metadata, "text": chunk},
            }
        )
    _get_index().upsert(vectors=vectors)
    return ids


def delete_vectors(ids: list[str]):
    """Delete vectors from Pinecone by their IDs."""
    _get_index().delete(ids=ids)


def search(embedding: list[float], top_k: int = 5, filter: dict = None) -> list[dict]:
    """
    Find the top_k most similar chunks to a query embedding.
    Optionally filter by metadata fields (e.g. projet, lot_technique).
    Returns a list of metadata dicts — one per matching chunk.
    """
    results = _get_index().query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter,
    )
    return [match.metadata for match in results.matches]
