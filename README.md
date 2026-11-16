# RAG-Forge

RAG-Forge is a general-purpose, multi-backend Retrieval-Augmented Generation (RAG) pipeline framework. It ingests content from a configurable data source, chunks and embeds that content into a pluggable vector store, and retrieves relevant context to ground LLM-generated responses. The chatbot interface for the TWU Informatics Graduate Program is the first consumer of the pipeline — one application built on top of RAG-Forge, not the system itself.

**Note:** RAG-Forge was migrated from a prior capstone GitHub repository (TWU_Chatbot) 

## Architecture

The pipeline runs in five stages. Each stage is backed by a swappable component.

- **Ingestion** — `src/rag_forge/scrapers/web_page.py` (`WebPageScraper`)
  - Fetches HTML from a configurable URL (`SCRAPE_URL`)
  - Strips scripts, styles, and head elements
  - Extracts content by CSS selector list (`SCRAPE_SELECTORS`); falls back to full-page text if empty
  - Returns clean plaintext

- **Chunking** — `src/rag_forge/main.py` (`chunk_text`)
  - Splits plaintext using `RecursiveCharacterTextSplitter` (LangChain)
  - Token counting via `tiktoken` (cl100k_base)
  - Chunk size and overlap configurable via `CHUNK_SIZE` / `CHUNK_OVERLAP`

- **Embedding and storage** — `src/rag_forge/vectorstores/`
  - Interface defined in `vectorstores/base.py` (`BaseVectorStore`)
  - Two implementations available; selected via `VECTOR_STORE` env var:
    - `pinecone` — Pinecone serverless with Pinecone Inference embeddings
    - `local` — ChromaDB on disk with sentence-transformers embeddings (no cloud credentials needed)

- **Retrieval** — `BaseVectorStore.query()`
  - Embeds the query and performs cosine similarity search
  - Returns top-k chunks with scores (`TOP_K_RESULTS`)

- **Generation** — `src/rag_forge/app.py` / `src/rag_forge/main.py`
  - Constructs a grounded prompt from retrieved context
  - Calls Gemini 2.5 Flash-Lite via `google-generativeai`

### Pluggable backend points

- **Data source** — any URL, set via `SCRAPE_URL`; selectors via `SCRAPE_SELECTORS`
- **Vector backend** — implement `BaseVectorStore` in `src/rag_forge/vectorstores/` and register in `vectorstores/__init__.py`
- **Scraper** — implement `BaseScraper` in `src/rag_forge/scrapers/` for non-web sources
- **LLM** — Gemini currently; `VERTEX_API_KEY` is present in config for Vertex AI as a future alternative

## Consumers

RAG-Forge is designed to support multiple front-end consumers. The chatbot is the first.

- **TWU Informatics Chatbot** — `src/rag_forge/app.py`
  - Streamlit web interface for Q&A against the TWU Informatics Graduate Program page
  - Session-limited to 10 questions; supports configurable FAQ shortcuts and chat history
  - Deployment config: `examples/twu-informatics/`
  - Live deployment: https://twuchatbot.streamlit.app *(URL predates the RAG-Forge rename)*

## Pipeline runner

The `rag-forge` console script (installed by `uv sync`) runs the pipeline CLI.

```bash
# Rebuild the index from scratch (scrape → chunk → embed → store)
uv run rag-forge --rebuild

# Run a test query against the current index
uv run rag-forge --query "What are the application deadlines?"
```

## Setup

```bash
uv sync

# Copy the example config for your deployment
cp examples/twu-informatics/.env.example .env
# Edit .env and fill in your API keys

# Build the index
uv run rag-forge --rebuild

# Launch the Streamlit UI
uv run streamlit run src/rag_forge/app.py
```

## Configuration

See `docs/configuration.md` for the full reference.

Key env vars:

- `VECTOR_STORE` — `pinecone` (default) or `local`
- `SCRAPE_URL` — page to ingest when running `--rebuild`
- `APP_NAME` — display name in the UI
- `GEMINI_API_KEY` — required for answer generation

## Repository layout

```
src/rag_forge/              installable package
  scrapers/
    base.py                 BaseScraper ABC
    web_page.py             generic web-page scraper (CSS-selector configurable)
  vectorstores/
    base.py                 BaseVectorStore ABC
    pinecone_store.py       Pinecone backend
    local_store.py          ChromaDB backend (local, no cloud dependencies)
  config.py                 environment-driven configuration
  main.py                   pipeline runner (registered as rag-forge console script)
  app.py                    Streamlit UI (generic, deployment-configured)
examples/
  twu-informatics/          deployment config for the TWU Informatics chatbot
docs/
  configuration.md          full configuration reference
pyproject.toml              project metadata and dependencies
uv.lock                     locked dependency tree
```
