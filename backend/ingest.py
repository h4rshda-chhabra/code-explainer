"""File Processor — Reads and chunks code files for vector embedding."""

import os
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .utils import get_allowed_files


class FileProcessor:
    """Reads code files and splits them into overlapping chunks with metadata."""

    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read a single file and split it into chunks with source metadata."""
        chunks = []
        try:
            content = self._read_file(file_path)
            if not content or not content.strip():
                return []

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            split_texts = splitter.split_text(content)

            current_idx = 0
            for chunk_text in split_texts:
                start_idx = content.find(chunk_text, current_idx)
                if start_idx == -1:
                    start_idx = current_idx
                current_idx = start_idx + len(chunk_text) - self.chunk_overlap

                chunks.append({
                    "text": chunk_text,
                    "metadata": {"source": file_path, "start_char": start_idx},
                })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return chunks

    def process_directory(
        self, directory_path: str, allowed_extensions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Process all allowed files in a directory tree."""
        all_chunks = []
        files = sorted(set(get_allowed_files(directory_path, allowed_extensions)))

        print(f"Index engine starting: found {len(files)} potential code/config files.")

        for i, file in enumerate(files, 1):
            new_chunks = self.process_file(file)
            basename = os.path.basename(file)
            if new_chunks:
                print(f"[{i}/{len(files)}] Indexed {basename}")
                all_chunks.extend(new_chunks)
            else:
                print(f"[{i}/{len(files)}] Skipped/Empty {basename}")

        return all_chunks

    @staticmethod
    def _read_file(file_path: str) -> str:
        """Read file content with UTF-8 fallback to Latin-1."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
