"""Vector Store — FAISS index with local sentence-transformers embeddings."""

import json
import os
from typing import Any, Dict, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 64


class VectorStoreManager:
    """Manages a FAISS vector index backed by local sentence-transformers embeddings."""

    def __init__(
        self,
        index_path: str = "index.faiss",
        chunks_path: str = "chunks.json",
        meta_path: str = "meta.json",
    ):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.dimension = EMBEDDING_DIMENSION

        base_dir = "/tmp" if os.getenv("VERCEL") == "1" else "."
        self.index_path = os.path.join(base_dir, index_path)
        self.chunks_path = os.path.join(base_dir, chunks_path)
        self.meta_path = os.path.join(base_dir, meta_path)

        self.repo_name = "None"
        self.load()

    # ── Persistence ────────────────────────────────────────────────────

    def load(self):
        if not (os.path.exists(self.index_path) and os.path.exists(self.chunks_path)):
            self._init_empty()
            return
        try:
            self.index = faiss.read_index(self.index_path)
            if self.index.d != self.dimension:
                print(f"Index dimension mismatch ({self.index.d} vs {self.dimension}). Clearing.")
                self.clear()
                return
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.repo_name = json.load(f).get("repo_name", "None")
            print(f"Loaded index with {len(self.chunks)} chunks from {self.repo_name}.")
        except Exception as e:
            print(f"Error loading index: {e}. Starting fresh.")
            self.clear()

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({"repo_name": self.repo_name}, f)

    def clear(self):
        self._init_empty()
        for path in (self.index_path, self.chunks_path, self.meta_path):
            if os.path.exists(path):
                os.remove(path)

    def _init_empty(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.repo_name = "None"

    # ── Indexing & Search ──────────────────────────────────────────────

    def add_chunks(self, chunks: List[Dict[str, Any]], repo_name: str = "Local Files"):
        if not chunks:
            return
        self.repo_name = repo_name
        texts = [c["text"] for c in chunks]

        print(f"Embedding {len(texts)} chunks locally...")
        embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
        ).astype("float32")

        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self.save()
        print(f"Done. Index now has {len(self.chunks)} chunks.")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []
        query_vec = self.model.encode([query], convert_to_numpy=True).astype("float32")
        _, indices = self.index.search(query_vec, top_k)
        return [
            self.chunks[idx]
            for idx in indices[0]
            if idx != -1 and idx < len(self.chunks)
        ]
