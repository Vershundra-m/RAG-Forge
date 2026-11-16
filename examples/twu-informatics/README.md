# TWU Informatics — RAG-Forge Deployment

This is the original deployment of RAG-Forge: a Q&A assistant for the
Texas Woman's University Informatics Graduate Program page.

## Setup

Copy `.env.example` to the repo root as `.env` and fill in your API keys:

```bash
cp examples/twu-informatics/.env.example .env
```

## Rebuild the index

```bash
uv run rag-forge --rebuild
```

This scrapes the TWU Informatics page, chunks the content, and uploads it
to Pinecone. The CSS selectors in `SCRAPE_SELECTORS` target the specific
content sections used by TWU's CMS (main content, sidebar, accordions,
jump-scroll sections, and feature boxes).

## Run the assistant

```bash
uv run streamlit run src/rag_forge/app.py
```

The live deployment is at https://twuchatbot.streamlit.app (URL predates
the RAG-Forge rename; update in Streamlit Cloud settings when convenient).

## Notes

- The Pinecone index is still named `twu-ai-chatbot`. To rename it: delete
  and recreate in the Pinecone console, update `PINECONE_INDEX_NAME` in
  `.env`, and run `--rebuild`.
- The TWU-specific CSS selectors are in `SCRAPE_SELECTORS`. If TWU updates
  their CMS layout, update those selectors and rebuild.
