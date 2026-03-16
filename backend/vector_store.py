import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import os
class VectorStoreManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "index.faiss", chunks_path: str = "chunks.json", meta_path: str = "meta.json"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.meta_path = meta_path
        self.repo_name = "None"
        self.load()
    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            if os.path.exists(self.meta_path):
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    self.repo_name = json.load(f).get("repo_name", "None")
            print(f"Loaded existing index with {len(self.chunks)} chunks from {self.repo_name}.")
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.chunks = []
            self.repo_name = "None"
            print("Initialized new empty index.")
    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump({"repo_name": self.repo_name}, f)
    def add_chunks(self, chunks: List[Dict[str, Any]], repo_name: str = "Local Files"):
        if not chunks:
            return
        self.repo_name = repo_name
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts)
        # Convert to float32 for FAISS
        embeddings = np.array(embeddings).astype('float32')
        
        self.index.add(embeddings)
        self.chunks.extend(chunks)
        self.save()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.chunks):
                results.append(self.chunks[idx])
                
        return results

    def clear(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.repo_name = "None"
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.chunks_path):
            os.remove(self.chunks_path)
        if os.path.exists(self.meta_path):
            os.remove(self.meta_path)
