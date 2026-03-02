import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

class VectorStoreManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = [] # Store original text and metadata

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return
            
        texts = [c["text"] for c in chunks]
        embeddings = self.model.encode(texts)
        
        # Convert to float32 for FAISS
        embeddings = np.array(embeddings).astype('float32')
        
        self.index.add(embeddings)
        self.chunks.extend(chunks)

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
