import os
from typing import List, Dict

class FileProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str) -> List[Dict[str, str]]:
        """Reads a file and splits it into chunks with metadata."""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple fixed-size chunking
            for i in range(0, len(content), self.chunk_size - self.chunk_overlap):
                chunk_text = content[i : i + self.chunk_size]
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": file_path,
                        "start_char": i
                    }
                })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        return chunks

    def process_directory(self, directory_path: str) -> List[Dict[str, str]]:
        from .utils import get_allowed_files
        all_chunks = []
        files = get_allowed_files(directory_path)
        
        for file in files:
            all_chunks.extend(self.process_file(file))
            
        return all_chunks
