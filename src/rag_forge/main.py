import argparse
import sys
import os

import google.generativeai as genai
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_forge import config
from rag_forge.scrapers import SCRAPER_REGISTRY
from rag_forge.vectorstores import get_store


def chunk_text(text: str) -> list[str]:
    tokenizer = tiktoken.get_encoding("cl100k_base")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=lambda x: len(tokenizer.encode(x)),
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def generate_answer(query: str, chunks: list[dict]) -> str:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    context = "\n\n---\n\n".join([c["text"] for c in chunks])
    prompt = f"""Answer based on the context below. If unsure, say "I don't know."

CONTEXT: {context}
QUESTION: {query}
ANSWER:"""
    return model.generate_content(prompt).text


def main():
    parser = argparse.ArgumentParser(description="RAG-Forge pipeline runner")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Scrape source and rebuild the vector index from scratch",
    )
    parser.add_argument(
        "--query", type=str, default=None, help="Run a test query against the current index"
    )
    args = parser.parse_args()

    print(f"RAG-Forge — backend: {config.VECTOR_STORE}")
    print("=" * 40)

    db = get_store()

    if args.rebuild:
        if not config.SCRAPE_URL:
            print("ERROR: SCRAPE_URL must be set in .env to rebuild the index.", file=sys.stderr)
            sys.exit(1)

        scraper_type = os.getenv("SCRAPER_TYPE", "web_page")
        print(f"Using scraper: {scraper_type}")

        if scraper_type not in SCRAPER_REGISTRY:
            print(f"ERROR: Unknown scraper '{scraper_type}'. Available: {list(SCRAPER_REGISTRY.keys())}", file=sys.stderr)
            sys.exit(1)

        scraper_class = SCRAPER_REGISTRY[scraper_type]

        scraper_config = {
            "base_url": config.SCRAPE_URL,
            "url": config.SCRAPE_URL,
            "content_selectors": config.SCRAPE_SELECTORS,
        }

        scraper = scraper_class(scraper_config)

        print(f"Scraping {config.SCRAPE_URL}...")

        if hasattr(scraper, "scrape"):
            text = scraper.scrape()
        else:
            text = scraper.fetch()

        print(f"Cleaned {len(text)} characters")

        chunks = chunk_text(text)
        print(f"Created {len(chunks)} chunks")

        if config.VECTOR_STORE == "pinecone":
            db._create_index()
        else:
            db.setup()
        db.index(chunks)
    else:
        db.setup()

    if args.query:
        print(f"\nQuery: {args.query}")
        retrieved = db.query(args.query)
        if retrieved:
            print(f"Best score: {retrieved[0]['score']:.3f}")
            answer = generate_answer(args.query, retrieved)
            print(f"Answer: {answer}")
        else:
            print("No results returned.")

    print("\nDone.")


if __name__ == "__main__":
    main()