import fitz  # pymupdf
from docx import Document
import pandas as pd
import email as email_lib
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


def extract_eml(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        msg = email_lib.message_from_file(f)
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    date = msg.get("Date", "")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    return f"Subject: {subject}\nFrom: {sender}\nDate: {date}\n\n{body}".strip()


def extract_csv(filepath):
    df = pd.read_csv(filepath) # DataFrame
    return df.to_string(index=False) 


def extract_xlsx(filepath):
    df = pd.read_excel(filepath)
    return df.to_string(index=False)


def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    handlers = {
        ".pdf": extract_pdf,
        ".docx": extract_docx,
        ".txt": extract_txt,
        ".eml": extract_eml,
        ".csv": extract_csv,
        ".xlsx": extract_xlsx,
    }
    if ext not in handlers:
        raise ValueError(f"Unsupported file type: {ext}")
    return handlers[ext](filepath)
