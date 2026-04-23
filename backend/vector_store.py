import faiss
import numpy as np
from typing import List, Dict, Any
import json
import os
from google import genai

class VectorStoreManager:
    def __init__(self, api_key: str = None, model_name: str = "text-embedding-004", index_path: str = "index.faiss", chunks_path: str = "chunks.json", meta_path: str = "meta.json"):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model_name = model_name
        self.dimension = 768 # Gemini text-embedding-004 dimension
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.meta_path = meta_path
        self.repo_name = "None"
        self.load()

    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            try:
                self.index = faiss.read_index(self.index_path)
                # Verify dimension compatibility
                if self.index.d != self.dimension:
                    print(f"Index dimension mismatch ({self.index.d} vs {self.dimension}). Clearing index.")
                    self.clear()
                    return
                    
                with open(self.chunks_path, 'r', encoding='utf-8') as f:
                    self.chunks = json.load(f)
                if os.path.exists(self.meta_path):
                    with open(self.meta_path, 'r', encoding='utf-8') as f:
                        self.repo_name = json.load(f).get("repo_name", "None")
                print(f"Loaded existing index with {len(self.chunks)} chunks from {self.repo_name}.")
            except Exception as e:
                print(f"Error loading index: {e}. Starting fresh.")
                self.clear()
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
        
        # Batch processing embeddings via Gemini API
        batch_size = 90 # Gemini API limit is around 100 for batch embedding
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [c["text"] for c in batch]
            
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=texts
            )
            embeddings = np.array([e.values for e in res.embeddings]).astype('float32')
            
            self.index.add(embeddings)
            self.chunks.extend(batch)
            
        self.save()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        res = self.client.models.embed_content(
            model=self.model_name,
            contents=query
        )
        query_embedding = np.array([res.embeddings[0].values]).astype('float32')
        
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
