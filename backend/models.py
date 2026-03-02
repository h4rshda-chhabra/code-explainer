from pydantic import BaseModel
from typing import List, Optional

class UploadRequest(BaseModel):
    files: List[str]  # List of file paths or directory

class UploadResponse(BaseModel):
    message: str
    files_indexed: int

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    context_chunks: List[str]
