# BâtiMind 🧠
> The brain behind BTP data — AI assistant for centralizing, structuring, and querying construction documents.

---

## What is this project?

BâtiMind is a **RAG (Retrieval-Augmented Generation)** application built for the construction industry (BTP = Bâtiment et Travaux Publics).

It allows you to:
- **Upload** construction documents (PDFs, Word files, emails, spreadsheets)
- **Ask questions** in natural language about those documents
- **Get answers with citations** — the AI tells you which document the answer came from
- **Connect external sources** — import emails, WhatsApp messages, and field photos directly
- **Browse a registry** of all indexed documents

Instead of searching manually through hundreds of pages, you ask a question and get a precise, sourced answer in seconds.

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| Language | Python 3.11+ | Best AI/NLP ecosystem |
| Orchestration | LangChain | Text splitting and pipeline glue |
| Embeddings | NVIDIA NIM (`nvidia/nv-embedqa-e5-v5`) | Free API, 1024-dim, no local model needed |
| Vision AI | NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`) | Field photo analysis |
| Vector DB | Pinecone (free serverless) | Production-grade semantic search |
| Relational DB | SQLite | Metadata & provenance tracking, zero setup |
| LLM | `openai/gpt-oss-20b` via NVIDIA NIM | Free API, high-quality answers |
| Web Framework | Flask + Jinja2 | Full-stack web app with complete control |
| Frontend | Tailwind CSS (CDN) + Lucide Icons | Dark-themed UI, no build step |
| Scheduler | APScheduler | Background email polling jobs |
| Deployment | Render.com + Gunicorn | Free tier hosting |

---

## Project Structure

```
batimind/
├── app/
│   ├── __init__.py           # Flask app factory + scheduler init
│   ├── database.py           # SQLite schema and connection
│   ├── embedder.py           # NVIDIA NIM embeddings wrapper
│   ├── chunker.py            # Text splitting (LangChain)
│   ├── extractors.py         # Text extraction (PDF, DOCX, email, CSV...)
│   ├── ingestor.py           # Deduplication + extraction orchestration
│   ├── rag.py                # Full RAG pipeline
│   ├── vector_store.py       # Pinecone client (upsert + query)
│   ├── scheduler.py          # APScheduler background jobs
│   ├── connectors/
│   │   ├── email_imap.py     # IMAP email fetcher
│   │   ├── photo.py          # Vision AI photo analyzer
│   │   └── whatsapp.py       # WhatsApp message parser
│   ├── routes/
│   │   ├── upload.py         # POST /upload — file ingestion
│   │   ├── chat.py           # POST /api/chat — RAG query endpoint
│   │   ├── documents.py      # GET /documents — registry browser
│   │   ├── conversations.py  # Conversation history API
│   │   ├── connectors.py     # Connectors UI + API
│   │   └── home.py           # Landing page
│   ├── templates/
│   │   ├── base.html         # Sidebar layout + conversation list
│   │   ├── index.html        # Landing page
│   │   ├── upload.html       # Document upload UI
│   │   ├── chat.html         # Chat interface
│   │   ├── documents.html    # Document registry
│   │   └── connectors.html   # Connectors (Email, WhatsApp, Photos)
│   └── static/
│       └── favicon.svg
├── config.py                 # All settings in one place
├── run.py                    # Flask entry point
├── render.yaml               # Render.com deployment config
├── requirements.txt
└── .env                      # API keys — NEVER push this
```

---

## How It Works (RAG Pipeline)

```
User uploads a document
        ↓
Text extraction (PyMuPDF / python-docx / pandas / email)
        ↓
Text splitting into overlapping chunks (~500 tokens)
        ↓
Each chunk → embedding vector via NVIDIA NIM (1024 dimensions)
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

## Technical Highlights

- **Full RAG pipeline built from scratch** — no black-box wrappers. Every step from text extraction to vector retrieval is hand-wired and understood.
- **Zero-cost production stack** — entirely on free tiers (Pinecone, NVIDIA NIM, Render). Proves you don't need a budget to ship real AI.
- **Multimodal** — handles text documents, structured spreadsheets, emails, and field photos through a Vision LLM.
- **Background job scheduling** — APScheduler runs email polling in a background thread inside the Flask process, with proper guards for the Werkzeug reloader.
- **Lazy loading architecture** — all heavy dependencies (Pinecone, LangChain, file parsers) are initialized only on first use, keeping startup RAM well under Render's 512 MB free-tier limit.
- **Multilingual** — answers questions in French, Arabic, and English using the same pipeline.

---

## Features

### Upload documents (`/upload`)
Supports: `.pdf`, `.docx`, `.txt`, `.eml`, `.csv`, `.xlsx`

- Deduplication: the same file is never indexed twice
- Each document is tagged with project, technical lot, author, and criticality
- Loading spinner while processing

### Chat with your documents (`/chat`)
- Ask questions in French, Arabic, or English
- Answers are grounded — the LLM only uses your documents, never invents
- Sources are cited in every response
- Conversation history persisted in SQLite

### Document registry (`/documents`)
- Browse all indexed documents
- See metadata: project, file type, number of chunks, ingestion date
- Delete documents and remove their vectors from Pinecone

### Connectors (`/connectors`) — Beta
- **Email**: Connect an IMAP mailbox and schedule automatic polling (every N hours)
- **Photos**: Upload field photos and get AI-generated analysis via Vision LLM
- **WhatsApp**: Import exported WhatsApp chat files

---

## Supported File Types

| Format | Method |
|---|---|
| `.pdf` | PyMuPDF |
| `.docx` | python-docx |
| `.txt` | UTF-8 read |
| `.eml` | Python `email` library (headers + body) |
| `.csv` | pandas |
| `.xlsx` | pandas + openpyxl |

---

## Deployment

The app is deployed on [Render.com](https://render.com) free tier using Gunicorn:

```
gunicorn run:app --workers 1 --bind 0.0.0.0:$PORT --timeout 120
```

`--workers 1` is required for SQLite + APScheduler compatibility.

---

## Cost

**$0** — all tools used are on free tiers:
- Pinecone: free serverless (up to 2M vectors)
- NVIDIA NIM: free API credits (LLM + embeddings + vision)
- SQLite: built into Python
- Flask: open source
- Render.com: free web service tier

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 1 | ✅ Done | Project setup, accounts, skeleton |
| Phase 2 | ✅ Done | Document ingestion pipeline |
| Phase 3 | ✅ Done | Chunking, embedding, vector storage |
| Phase 4 | ✅ Done | RAG query engine |
| Phase 5 | ✅ Done | Flask web application |
| Phase 6 | 🔄 In progress | Connectors, deployment, polish |

---

*Built by [Abdessamad](https://github.com/Abdessamad404) — BTP AI prototype.*
