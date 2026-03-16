from typing import List, Dict

class FileProcessor:
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str) -> List[Dict[str, str]]:
        """Reads a file and splits it into chunks with metadata."""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            # Fallback if the user hasn't pip installed it yet
            print("Warning: langchain-text-splitters not found. Falling back to simple chunker.")
            return self._legacy_process_file(file_path)

        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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

    def _legacy_process_file(self, file_path: str) -> List[Dict[str, str]]:
        """Legacy naive chunking system for fallback."""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
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
