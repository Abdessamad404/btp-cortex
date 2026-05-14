from config import CHUNK_SIZE, CHUNK_OVERLAP

_splitter = None


def _get_splitter():
    global _splitter
    if _splitter is None:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", " ", ""],
        )
    return _splitter


def chunk(text: str) -> list[str]:
    return _get_splitter().split_text(text)
