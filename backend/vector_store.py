import faiss
import numpy as np
from typing import List, Dict, Any
import json
import os
import time
from google import genai

class VectorStoreManager:
    def __init__(self, api_key: str = None, model_name: str = "gemini-embedding-2", index_path: str = "index.faiss", chunks_path: str = "chunks.json", meta_path: str = "meta.json"):
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model_name = model_name
        self.dimension = 3072 # gemini-embedding-2 default dimension
        
        temp_dir = "/tmp" if os.getenv("VERCEL") == "1" else "."
        self.index_path = os.path.join(temp_dir, index_path)
        self.chunks_path = os.path.join(temp_dir, chunks_path)
        self.meta_path = os.path.join(temp_dir, meta_path)
        
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

    def _embed_with_retry(self, texts: List[str], max_retries: int = 5):
        """Call the Gemini embedding API with automatic retry + exponential backoff on 429 errors."""
        for attempt in range(max_retries):
            try:
                res = self.client.models.embed_content(
                    model=self.model_name,
                    contents=texts
                )
                return res
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = min(2 ** attempt * 5, 60)  # 5s, 10s, 20s, 40s, 60s
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise  # Re-raise non-rate-limit errors immediately
        raise Exception("Gemini embedding API rate limit exceeded after maximum retries. Please wait a few minutes and try again.")

    def add_chunks(self, chunks: List[Dict[str, Any]], repo_name: str = "Local Files"):
        if not chunks:
            return
        self.repo_name = repo_name
        
        # Use smaller batches + delay to stay within free-tier rate limits
        batch_size = 20
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            batch_num = i // batch_size + 1
            texts = [c["text"] for c in batch]
            
            print(f"Embedding batch {batch_num}/{total_batches} ({len(texts)} chunks)...")
            res = self._embed_with_retry(texts)
            embeddings = np.array([e.values for e in res.embeddings]).astype('float32')
            
            self.index.add(embeddings)
            self.chunks.extend(batch)
            
            # Throttle between batches to avoid hitting rate limits
            if i + batch_size < len(chunks):
                time.sleep(2)
            
        self.save()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []
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
