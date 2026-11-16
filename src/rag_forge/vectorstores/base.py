from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    @abstractmethod
    def setup(self) -> None:
        """Connect to or initialize the store. Must be called before index() or query()."""

    @abstractmethod
    def index(self, chunks: list[str]) -> None:
        """Embed and store text chunks. Idempotent — re-indexing the same IDs overwrites."""

    @abstractmethod
    def query(self, text: str, top_k: int) -> list[dict]:
        """Return top-k relevant chunks as [{'text': str, 'score': float}, ...]."""

    @abstractmethod
    def clear(self) -> None:
        """Delete all indexed data and reset the store to empty."""
