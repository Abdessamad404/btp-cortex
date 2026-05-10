import fitz  # pymupdf
from docx import Document
import os


def extract_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()


def extract_docx(filepath):
    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()


def extract_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        return extract_pdf(filepath)
    elif ext == ".docx":
        return extract_docx(filepath)
    elif ext == ".txt":
        return extract_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
