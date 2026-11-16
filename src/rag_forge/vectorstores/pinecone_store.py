import time

import pinecone
from pinecone import ServerlessSpec

from rag_forge import config
from rag_forge.vectorstores.base import BaseVectorStore


class PineconeStore(BaseVectorStore):
    def __init__(self):
        self.pc = pinecone.Pinecone(api_key=config.PINECONE_API_KEY)
        self.index_name = config.PINECONE_INDEX_NAME
        self.embedding_model = config.PINECONE_EMBEDDING_MODEL
        self._handle = None

    def setup(self) -> None:
        """Connect to an existing Pinecone index."""
        if self.index_name not in self.pc.list_indexes().names():
            raise RuntimeError(
                f"Pinecone index '{self.index_name}' does not exist. "
                "Run: uv run rag-forge --rebuild"
            )
        self._handle = self.pc.Index(self.index_name)
        print(f"Connected to Pinecone index '{self.index_name}'")

    def _create_index(self) -> None:
        """Create a fresh index, deleting any existing one."""
        if self.index_name in self.pc.list_indexes().names():
            self.pc.delete_index(self.index_name)
            time.sleep(5)
        self.pc.create_index(
            name=self.index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not self.pc.describe_index(self.index_name).status["ready"]:
            time.sleep(1)
        self._handle = self.pc.Index(self.index_name)
        print(f"Created Pinecone index '{self.index_name}'")

    def index(self, chunks: list[str]) -> None:
        """Embed and upload chunks in batches with rate limiting."""
        if self._handle is None:
            raise RuntimeError("Call setup() or _create_index() before index().")

        # Step 1: Embed chunks in batches
        print(f"  Embedding {len(chunks)} chunks in batches...")
        embed_batch_size = 96
        embeddings = []

        for i in range(0, len(chunks), embed_batch_size):
            batch = chunks[i : i + embed_batch_size]

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    result = self.pc.inference.embed(
                        model=self.embedding_model,
                        inputs=batch,
                        parameters={"input_type": "passage"},
                    )
                    embeddings.extend([e.values for e in result])
                    break
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait_time = 30 * (attempt + 1)
                        print(f"    Rate limit hit. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

            print(f"    Embedded {min(i + embed_batch_size, len(chunks))}/{len(chunks)} chunks")
            time.sleep(2)

        # Step 2: Upload vectors in batches
        print(f"  Uploading to Pinecone...")
        upsert_batch_size = 100
        vectors = [
            {"id": f"chunk_{i:05d}", "values": emb, "metadata": {"text": chunk}}
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        for i in range(0, len(vectors), upsert_batch_size):
            self._handle.upsert(vectors=vectors[i : i + upsert_batch_size])
            print(f"    Uploaded {min(i + upsert_batch_size, len(vectors))}/{len(vectors)} vectors")

        print(f"Indexed {len(chunks)} chunks to Pinecone")

    def query(self, text: str, top_k: int = config.TOP_K_RESULTS) -> list[dict]:
        if self._handle is None:
            raise RuntimeError("Call setup() before query().")
        embedding = self.pc.inference.embed(
            model=self.embedding_model,
            inputs=[text],
            parameters={"input_type": "query"},
        )
        results = self._handle.query(
            vector=embedding[0].values, top_k=top_k, include_metadata=True
        )
        return [{"text": m["metadata"]["text"], "score": m["score"]} for m in results["matches"]]

    def clear(self) -> None:
        self._create_index()
