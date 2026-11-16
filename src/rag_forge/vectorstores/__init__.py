from rag_forge import config
from rag_forge.vectorstores.base import BaseVectorStore


def get_store() -> BaseVectorStore:
    backend = config.VECTOR_STORE
    if backend == "pinecone":
        from rag_forge.vectorstores.pinecone_store import PineconeStore

        return PineconeStore()
    if backend == "local":
        from rag_forge.vectorstores.local_store import LocalStore

        return LocalStore()
    raise ValueError(f"Unknown VECTOR_STORE backend: {backend!r}. Must be 'pinecone' or 'local'.")
