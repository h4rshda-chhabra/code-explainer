"""Vector Store — FAISS index with Gemini embeddings for semantic code search."""

import json
import os
import time
from typing import Any, Dict, List

import faiss
import numpy as np
from google import genai


EMBEDDING_DIMENSION = 3072  # gemini-embedding-2 default dimension
BATCH_SIZE = 20
BATCH_DELAY_SECONDS = 2


class VectorStoreManager:
    """Manages a FAISS vector index backed by Gemini embeddings."""

    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gemini-embedding-2",
        index_path: str = "index.faiss",
        chunks_path: str = "chunks.json",
        meta_path: str = "meta.json",
    ):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model_name = model_name
        self.dimension = EMBEDDING_DIMENSION

        # Use /tmp on Vercel (ephemeral filesystem), current dir otherwise
        base_dir = "/tmp" if os.getenv("VERCEL") == "1" else "."
        self.index_path = os.path.join(base_dir, index_path)
        self.chunks_path = os.path.join(base_dir, chunks_path)
        self.meta_path = os.path.join(base_dir, meta_path)

        self.repo_name = "None"
        self.load()

    # ── Persistence ────────────────────────────────────────────────────

    def load(self):
        """Load an existing FAISS index and chunk data from disk."""
        if not (os.path.exists(self.index_path) and os.path.exists(self.chunks_path)):
            self._init_empty()
            return

        try:
            self.index = faiss.read_index(self.index_path)

            if self.index.d != self.dimension:
                print(f"Index dimension mismatch ({self.index.d} vs {self.dimension}). Clearing index.")
                self.clear()
                return

            with open(self.chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.repo_name = json.load(f).get("repo_name", "None")

            print(f"Loaded existing index with {len(self.chunks)} chunks from {self.repo_name}.")
        except Exception as e:
            print(f"Error loading index: {e}. Starting fresh.")
            self.clear()

    def save(self):
        """Persist the FAISS index, chunks, and metadata to disk."""
        faiss.write_index(self.index, self.index_path)

        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({"repo_name": self.repo_name}, f)

    def clear(self):
        """Remove all indexed data and delete persisted files."""
        self._init_empty()
        for path in (self.index_path, self.chunks_path, self.meta_path):
            if os.path.exists(path):
                os.remove(path)

    def _init_empty(self):
        """Initialize an empty FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.repo_name = "None"
        print("Initialized new empty index.")

    # ── Embedding ──────────────────────────────────────────────────────

    def _embed_with_retry(self, texts: List[str], max_retries: int = 5) -> Any:
        """Call the Gemini embedding API with exponential backoff on 429 errors."""
        for attempt in range(max_retries):
            try:
                return self.client.models.embed_content(
                    model=self.model_name,
                    contents=texts,
                )
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    wait = min(2 ** attempt * 5, 60)
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise

        raise Exception("Gemini embedding API rate limit exceeded after maximum retries.")

    # ── Indexing & Search ──────────────────────────────────────────────

    def add_chunks(self, chunks: List[Dict[str, Any]], repo_name: str = "Local Files"):
        """Embed and add code chunks to the FAISS index in batches."""
        if not chunks:
            return

        self.repo_name = repo_name
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            texts = [c["text"] for c in batch]

            print(f"Embedding batch {batch_num}/{total_batches} ({len(texts)} chunks)...")
            res = self._embed_with_retry(texts)
            embeddings = np.array([e.values for e in res.embeddings]).astype("float32")

            self.index.add(embeddings)
            self.chunks.extend(batch)

            # Throttle between batches to stay within free-tier rate limits
            if i + BATCH_SIZE < len(chunks):
                time.sleep(BATCH_DELAY_SECONDS)

        self.save()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search the index for chunks most relevant to the query."""
        if not self.chunks:
            return []

        res = self.client.models.embed_content(
            model=self.model_name,
            contents=query,
        )
        query_embedding = np.array([res.embeddings[0].values]).astype("float32")
        _, indices = self.index.search(query_embedding, top_k)

        return [
            self.chunks[idx]
            for idx in indices[0]
            if idx != -1 and idx < len(self.chunks)
        ]
