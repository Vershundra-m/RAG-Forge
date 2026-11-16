# RAG-Forge Configuration

All configuration is loaded from environment variables via a `.env` file
in the repo root. Copy the relevant example from `examples/` to get started.

## Pipeline settings

- `VECTOR_STORE` — which backend to use
  - `pinecone` (default) — Pinecone serverless; requires `PINECONE_API_KEY`
  - `local` — ChromaDB on disk; no cloud credentials needed
- `APP_NAME` — display name shown in the Streamlit UI (default: `RAG-Forge Assistant`)
- `GEMINI_API_KEY` — required for answer generation in both backends
- `VERTEX_API_KEY` — optional; wired for future Vertex AI LLM path

## Chunking settings

- `CHUNK_SIZE` — maximum chunk size in tokens (default: `250`)
- `CHUNK_OVERLAP` — token overlap between adjacent chunks (default: `30`)
- `TOP_K_RESULTS` — number of chunks retrieved per query (default: `3`)

## Scraper settings

- `SCRAPE_URL` — URL to scrape when running `python main.py --rebuild`
- `SCRAPE_SELECTORS` — JSON array of CSS selector strings controlling which
  page sections are extracted, in order
  - Empty array (default): extracts all page text as fallback
  - Example for a typical CMS layout:
    `["main", "div.sidebar", "[data-aria-accordion]", "div.jump-scroll", "div.feature"]`

## Pinecone backend settings

Only used when `VECTOR_STORE=pinecone`.

- `PINECONE_API_KEY` — Pinecone API key
- `PINECONE_INDEX_NAME` — name of the Pinecone index (default: `twu-ai-chatbot`)
  - Note: the live index is still named `twu-ai-chatbot`. To rename it, delete
    and recreate in the Pinecone console, update this value, and run `--rebuild`.
- `PINECONE_EMBEDDING_MODEL` — Pinecone Inference model for embeddings
  (default: `multilingual-e5-large`, dimension 1024)

## Local backend settings

Only used when `VECTOR_STORE=local`.

- `LOCAL_STORE_PATH` — filesystem path for ChromaDB persistence
  (default: `./data/chroma`)
- `LOCAL_COLLECTION_NAME` — ChromaDB collection name (default: `rag-forge`)
- Embeddings use sentence-transformers `all-MiniLM-L6-v2` via ChromaDB's
  default embedding function. The model (~90 MB) downloads automatically on
  first use and is cached locally.

## UI settings (deployment-specific)

All optional. Omit to use the generic defaults.

- `HELP_URL` — URL for the Help link in the header; omit to hide the link
- `FOOTER_TEXT` — caption shown below the chat area; omit to hide
- `FAQ_ITEMS` — JSON array of `[label, question]` pairs for FAQ shortcut
  buttons; omit or set to `[]` to hide the FAQ row
  - Example:
    `[["Deadlines","What are the deadlines?"],["Costs","What does it cost?"]]`
