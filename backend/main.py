"""FastAPI backend for CodeSense AI — Codebase Explainer."""

import os
import shutil
import tempfile
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .github_ingest import GitHubIngestor
from .ingest import FileProcessor
from .models import (
    GithubUploadRequest,
    QueryRequest,
    QueryResponse,
    UploadRequest,
    UploadResponse,
)
from .qa import QAEngine
from .vector_store import VectorStoreManager

load_dotenv()

# ── App Setup ──────────────────────────────────────────────────────────

app = FastAPI(title="CodeSense AI — Codebase Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Component Initialization ──────────────────────────────────────────

file_processor = FileProcessor()
vector_store = VectorStoreManager()
github_ingestor = GitHubIngestor()

# Groq for LLM (Q&A), Gemini still used for embeddings in vector_store
qa_engine = QAEngine(api_key=os.getenv("GROQ_API_KEY"))

# ── Endpoints ─────────────────────────────────────────────────────────


@app.post("/upload", response_model=UploadResponse)
def upload_files(request: UploadRequest):
    """Index code from local file paths or directories."""
    try:
        all_chunks = []
        for path in request.files:
            if os.path.isdir(path):
                chunks = file_processor.process_directory(path, allowed_extensions=request.allowed_extensions)
            else:
                chunks = file_processor.process_file(path)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid code files found in the provided paths.")

        vector_store.clear()
        repo_name = (
            os.path.basename(os.path.normpath(request.files[0]))
            if len(request.files) == 1
            else "Multiple Local Folders"
        )
        vector_store.add_chunks(all_chunks, repo_name=repo_name)

        return UploadResponse(
            message="Successfully indexed codebase.",
            files_indexed=len({c["metadata"]["source"] for c in all_chunks}),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.post("/upload-github", response_model=UploadResponse)
def upload_github(request: GithubUploadRequest):
    """Clone a public GitHub repo and index its code."""
    temp_dir = None
    try:
        if not request.github_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")

        try:
            temp_dir = github_ingestor.clone_repo(request.github_url)
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

        all_chunks = file_processor.process_directory(temp_dir)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No readable code files found in the repository.")

        vector_store.clear()
        vector_store.add_chunks(all_chunks, repo_name=request.github_url)

        return UploadResponse(
            message=f"Successfully cloned and indexed {request.github_url}.",
            files_indexed=len({c["metadata"]["source"] for c in all_chunks}),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_dir:
            github_ingestor.cleanup_dir(temp_dir)


@app.post("/upload-local", response_model=UploadResponse)
def upload_local(files: List[UploadFile] = File(...), paths: List[str] = Form(...)):
    """Upload local files via browser and index them."""
    temp_dir = tempfile.mkdtemp(prefix="codesense_local_")
    try:
        if len(files) != len(paths):
            raise HTTPException(status_code=400, detail="Mismatched files and paths.")

        for file, rel_path in zip(files, paths):
            safe_path = os.path.normpath(rel_path).lstrip(os.sep)
            full_path = os.path.join(temp_dir, safe_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        all_chunks = file_processor.process_directory(temp_dir)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid code files found in the upload.")

        vector_store.clear()
        repo_name = paths[0].split("/")[0] if paths else "Local Upload"
        vector_store.add_chunks(all_chunks, repo_name=repo_name)

        return UploadResponse(
            message="Successfully indexed uploaded local files.",
            files_indexed=len({c["metadata"]["source"] for c in all_chunks}),
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        github_ingestor.cleanup_dir(temp_dir)


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """Answer a question about the indexed codebase using RAG."""
    try:
        results = vector_store.search(request.question, top_k=8)
        context_chunks = [r["text"] for r in results]
        answer = qa_engine.answer_question(request.question, context_chunks)

        return QueryResponse(answer=answer, context_chunks=context_chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
def clear_index():
    """Remove all indexed data."""
    try:
        vector_store.clear()
        return {"message": "Successfully unindexed codebase."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "indexed_chunks": len(vector_store.chunks)}


@app.get("/index-status")
def get_index_status():
    """Return the currently indexed repo name and file list."""
    try:
        if not vector_store.chunks:
            return {"repo_name": "None", "files": []}

        unique_files = sorted({chunk["metadata"]["source"] for chunk in vector_store.chunks})

        return {"repo_name": vector_store.repo_name, "files": unique_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
