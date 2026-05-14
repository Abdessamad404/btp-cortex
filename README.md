# BâtiMind 🧠
> The brain behind BTP data — AI system for centralizing, structuring, and querying construction documents.

---

## What is this project?

BâtiMind is a **RAG (Retrieval-Augmented Generation)** application built for the construction industry (BTP = Bâtiment et Travaux Publics).

It allows you to:
- **Upload** construction documents (PDFs, Word files, emails, spreadsheets)
- **Ask questions** in natural language about those documents
- **Get answers with citations** — the AI tells you which document the answer came from
- **Browse a registry** of all indexed documents

Instead of searching manually through hundreds of pages, you ask a question and get a precise, sourced answer in seconds.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11+ | Best AI/NLP ecosystem |
| Orchestration | LangChain | Glues all AI components together |
| Embeddings | sentence-transformers (`multilingual-MiniLM-L12-v2`) | Free, local, supports FR/AR/EN |
| Vector DB | Pinecone (free serverless) | Production-grade semantic search |
| Relational DB | SQLite | Metadata & provenance tracking, zero setup |
| LLM | `gpt-oss-20b` via NVIDIA NIM | Free API, high-quality answers |
| Web Framework | Flask + Jinja2 | Full-stack web app with complete control |
| Frontend | Bootstrap 5 + vanilla JS | Clean UI, no frontend framework needed |

---

## Project Structure

```
batimind/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── database.py           # SQLite connection and schema
│   ├── routes/
│   │   ├── upload.py         # POST /upload — file ingestion
│   │   ├── chat.py           # POST /api/chat — RAG query endpoint
│   │   └── documents.py      # GET /documents — registry browser
│   ├── services/
│   │   ├── extractor.py      # Text extraction (PDF, DOCX, email, CSV...)
│   │   ├── chunker.py        # Text splitting logic
│   │   ├── embedder.py       # sentence-transformers wrapper
│   │   ├── pinecone_db.py    # Pinecone client (upsert + query)
│   │   ├── sqlite_db.py      # SQLite metadata store
│   │   └── rag.py            # Full RAG pipeline
│   ├── templates/
│   │   ├── base.html         # Layout with navbar
│   │   ├── index.html        # Landing page
│   │   ├── upload.html       # Document upload UI
│   │   ├── chat.html         # Chat interface
│   │   └── documents.html    # Document registry
│   └── static/
│       ├── css/style.css
│       └── js/chat.js        # Async chat (fetch API)
├── scripts/
│   └── ingest_knowledge.py   # One-time loader for external knowledge (DTU, normes, CSTB)
├── data/
│   ├── uploads/              # Uploaded raw files (gitignored)
│   ├── knowledge/            # External regulatory sources (gitignored)
│   └── btp.db                # SQLite database (gitignored)
├── config.py                 # All settings in one place
├── run.py                    # Flask entry point
├── requirements.txt
└── .env                      # API keys — NEVER push this
```

---

## How It Works (RAG Pipeline)

```
User uploads a document
        ↓
Text extraction (PyMuPDF / python-docx / OCR)
        ↓
Text splitting into overlapping chunks (~500 tokens)
        ↓
Each chunk → embedding vector (384 dimensions)
        ↓
Vectors stored in Pinecone  +  metadata stored in SQLite
        ↓
User asks a question
        ↓
Question → embedding → top-5 similar chunks retrieved from Pinecone
        ↓
Chunks injected into LLM prompt as context
        ↓
LLM answers using only the retrieved context + cites source files
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Abdessamad404/btp-cortex.git
cd btp-cortex
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

```
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX=btp-docs
NVIDIA_API_KEY=your_nvidia_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=openai/gpt-oss-20b
EMBED_MODEL=paraphrase-multilingual-MiniLM-L12-v2
FLASK_SECRET_KEY=pick_any_random_string
```

**Where to get the keys (both free):**
- **Pinecone** → [pinecone.io](https://pinecone.io) — create a free serverless index named `btp-docs`, dimension `384`, metric `cosine`
- **NVIDIA NIM** → [build.nvidia.com](https://build.nvidia.com) — sign up and generate an API key

### 5. Run the app

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Features

### Upload documents (`/upload`)
Supports: `.pdf`, `.docx`, `.txt`, `.eml`, `.csv`, `.xlsx`

- Scanned PDFs are handled with OCR (Tesseract)
- Deduplication: the same file is never indexed twice
- Each document is tagged with project, technical lot, author, and criticality

### Chat with your documents (`/chat`)
- Ask questions in French, Arabic, or English
- Answers are grounded — the LLM only uses your documents, never invents
- Sources are cited in every response

### Document registry (`/documents`)
- Browse all indexed documents
- See metadata: project, file type, number of chunks, ingestion date

---

## External Knowledge Base

In addition to uploaded documents, the system supports loading regulatory references (DTU standards, NF/EN/ISO norms, CSTB guides) as a one-time batch:

```bash
# Place PDF files in data/knowledge/ then run:
python scripts/ingest_knowledge.py
```

These are tagged as `projet: base-reglementaire` and are always searchable alongside your project documents.

---

## Roadmap

Phase | Status | Description
---|---|---
Phase 1 | Done | Project setup, accounts, skeleton
Phase 2 | Done | Document ingestion pipeline
Phase 3 | Done | Chunking, embedding, vector storage
Phase 4 | In progress | RAG query engine
Phase 5 | Planned | Flask web interface
Phase 6 | Planned | Testing, demo, polish

**Future integrations (out of scope for prototype):** WhatsApp connector, BIM file support, ERP/CRM integration, GED synchronization.

---

## Supported File Types

| Format | Method |
|---|---|
| `.pdf` | PyMuPDF (text) or Tesseract OCR (scanned) |
| `.docx` | python-docx |
| `.txt` | UTF-8 read |
| `.eml` | Python `email` library (headers + body) |
| `.csv` | pandas (stringified rows) |
| `.xlsx` | pandas + openpyxl |

---

## Cost

**$0** — all tools used are on free tiers:
- Pinecone: free serverless (up to 2M vectors)
- NVIDIA NIM: free API credits
- sentence-transformers: runs locally
- SQLite: built into Python
- Flask: open source

---

*Built by [Abdessamad](https://github.com/Abdessamad404) as a BTP AI prototype.*
