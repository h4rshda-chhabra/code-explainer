import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .utils import get_allowed_files
class FileProcessor:
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Reads a file and splits it into chunks with metadata."""
        chunks = []
        try:
            # Try utf-8 first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Fallback to latin-1 for legacy or binary-ish files
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            if not content.strip():
                return []

            # Use LangChain semantic text splitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            
            split_texts = text_splitter.split_text(content)
            
            # Retain original index tracking locally
            current_idx = 0
            for chunk_text in split_texts:
                start_idx = content.find(chunk_text, current_idx)
                if start_idx == -1:
                    start_idx = current_idx
                current_idx = start_idx + len(chunk_text) - self.chunk_overlap
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": file_path,
                        "start_char": start_idx
                    }
                })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
        return chunks

    def process_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        from .utils import get_allowed_files
        all_chunks = []
        files = list(set(get_allowed_files(directory_path)))
        
        print(f"Index engine starting: found {len(files)} potential code/config files.")
        
        for i, file in enumerate(files):
            new_chunks = self.process_file(file)
            if new_chunks:
                print(f"[{i+1}/{len(files)}] Indexed {os.path.basename(file)}")
                all_chunks.extend(new_chunks)
            else:
                print(f"[{i+1}/{len(files)}] Skipped/Empty {os.path.basename(file)}")
            
        return all_chunks
