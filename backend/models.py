"""Pydantic models for API request/response schemas."""

from typing import List, Optional

from pydantic import BaseModel


class UploadRequest(BaseModel):
    """Request to index local file paths or directories."""
    files: List[str]
    allowed_extensions: Optional[List[str]] = None


class GithubUploadRequest(BaseModel):
    """Request to clone and index a GitHub repository."""
    github_url: str


class UploadResponse(BaseModel):
    """Response after indexing files."""
    message: str
    files_indexed: int


class QueryRequest(BaseModel):
    """Request to ask a question about the indexed codebase."""
    question: str
    top_k: Optional[int] = 3
    conversation_id: Optional[int] = None


class QueryResponse(BaseModel):
    """Response containing the AI-generated answer and context."""
    answer: str
    context_chunks: List[str]
