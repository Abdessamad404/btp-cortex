from config import NVIDIA_API_KEY, NVIDIA_BASE_URL, EMBED_MODEL

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    return _client


def embed(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    response = _get_client().embeddings.create(
        input=texts,
        model=EMBED_MODEL,
        encoding_format="float",
        extra_body={"input_type": input_type, "truncate": "NONE"},
    )
    return [item.embedding for item in response.data]
