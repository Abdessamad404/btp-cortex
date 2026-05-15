# BâtiMind 🧠
> The brain behind BTP data — AI assistant for centralizing and querying construction documents.

<!-- **Live demo → [batimind.onrender.com](https://batimind.onrender.com)** -->

---

## What is it?

BâtiMind is a **RAG (Retrieval-Augmented Generation)** application built for the construction industry. Upload your project documents, ask questions in natural language, and get precise answers with source citations — in French, Arabic, or English.

No more searching manually through hundreds of pages.

---

<!-- ## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| LLM | `openai/gpt-oss-20b` via NVIDIA NIM |
| Embeddings | `nvidia/nv-embedqa-e5-v5` via NVIDIA NIM |
| Vision AI | `meta/llama-3.2-11b-vision-instruct` |
| Vector DB | Pinecone (serverless) |
| Orchestration | LangChain |
| Backend | Flask + SQLite |
| Frontend | Tailwind CSS + Lucide Icons |
| Deployment | Render.com + Gunicorn |

--- -->

## Features

- **Document upload** — PDF, Word, Excel, CSV, emails. Deduplicated, tagged with BTP metadata (project, lot, criticality).
- **RAG chat** — grounded answers with source citations. The LLM never invents.
- **Connectors** — import emails via IMAP, analyze field photos with Vision AI, parse WhatsApp exports.
- **Document registry** — browse, filter, and delete indexed documents.
- **Conversation history** — persistent chat sessions stored in SQLite.

---

## Technical Highlights

- Full RAG pipeline built from scratch — every step understood and hand-wired.
- Lazy loading architecture keeps startup RAM under Render's 512 MB free-tier limit.
- APScheduler runs background email polling inside the Flask process with proper reloader guards.
- Multimodal — text documents and field photos through the same ingestion pipeline.
- Zero infrastructure cost — entirely on free tiers.

---

*Built by [Abdessamad](https://github.com/Abdessamad404)*
