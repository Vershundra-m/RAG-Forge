import json
import os

from dotenv import load_dotenv

load_dotenv()

# --- Pipeline ---
VECTOR_STORE = os.getenv("VECTOR_STORE", "pinecone")  # "pinecone" | "local"
APP_NAME = os.getenv("APP_NAME", "RAG-Forge Assistant")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VERTEX_API_KEY = os.getenv("VERTEX_API_KEY")  # wired for future use

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "250"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "30"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "3"))

# --- Scraper ---
SCRAPE_URL = os.getenv("SCRAPE_URL", "")
# CSS selector strings applied in order; empty list = full-page text fallback
SCRAPE_SELECTORS: list[str] = json.loads(os.getenv("SCRAPE_SELECTORS", "[]"))

# --- Pinecone backend (VECTOR_STORE=pinecone) ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "twu-ai-chatbot")
PINECONE_EMBEDDING_MODEL = os.getenv("PINECONE_EMBEDDING_MODEL", "multilingual-e5-large")
# Note: the live Pinecone index is still named "twu-ai-chatbot".
# Rename it in the Pinecone console, then update PINECONE_INDEX_NAME here.

# --- Local backend (VECTOR_STORE=local) ---
LOCAL_STORE_PATH = os.getenv("LOCAL_STORE_PATH", "./data/chroma")
LOCAL_COLLECTION_NAME = os.getenv("LOCAL_COLLECTION_NAME", "rag-forge")

# --- UI (deployment-specific overrides) ---
HELP_URL = os.getenv("HELP_URL", "")
FOOTER_TEXT = os.getenv("FOOTER_TEXT", "")
# JSON array of [label, question] pairs; empty = no FAQ shortcuts shown
FAQ_ITEMS: list[list[str]] = json.loads(os.getenv("FAQ_ITEMS", "[]"))
