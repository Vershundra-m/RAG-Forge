import chromadb

from rag_forge import config
from rag_forge.vectorstores.base import BaseVectorStore


class LocalStore(BaseVectorStore):
    """ChromaDB-backed vector store with no cloud dependencies.

    Embeddings use ChromaDB's default function (sentence-transformers/all-MiniLM-L6-v2).
    The model is downloaded automatically on first use (~90 MB).

    Persistence location: config.LOCAL_STORE_PATH (default: ./data/chroma)
    """

    def __init__(self):
        self.path = config.LOCAL_STORE_PATH
        self.collection_name = config.LOCAL_COLLECTION_NAME
        self.client = None
        self.collection = None

    def setup(self) -> None:
        self.client = chromadb.PersistentClient(path=self.path)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
        print(f"Connected to local store at '{self.path}' (collection: {self.collection_name})")

    def index(self, chunks: list[str]) -> None:
        if self.collection is None:
            raise RuntimeError("Call setup() before index().")
        ids = [f"chunk_{i:03d}" for i in range(len(chunks))]
        self.collection.upsert(documents=chunks, ids=ids)
        print(f"Indexed {len(chunks)} chunks to local store")

    def query(self, text: str, top_k: int = config.TOP_K_RESULTS) -> list[dict]:
        if self.collection is None:
            raise RuntimeError("Call setup() before query().")
        results = self.collection.query(query_texts=[text], n_results=top_k)
        return [
            {"text": doc, "score": 1.0 - dist}
            for doc, dist in zip(results["documents"][0], results["distances"][0], strict=False)
        ]

    def clear(self) -> None:
        if self.client is None:
            raise RuntimeError("Call setup() before clear().")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
        print(f"Cleared local store collection '{self.collection_name}'")
