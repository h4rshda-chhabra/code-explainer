"""FastAPI backend for CodeSense AI — Codebase Explainer."""

# NOTE: All routes now require authentication and DB session

import os
import logging
from fastapi import Depends, Request, Response, Cookie, HTTPException
from fastapi.responses import JSONResponse

import shutil
import tempfile
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
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
from sqlalchemy.orm import Session
from .vector_store import VectorStoreManager

# Local imports for DB, auth, and middleware
from .database import get_db, engine, Base
from .models_orm import Repository, Conversation, Message, Report, Analytics
from .auth import get_current_user
from .models_orm import User
from .middleware import RequestIDMiddleware, ErrorHandlingMiddleware

load_dotenv()

# Logging configuration (structured JSON)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","message":%(message)s}',
)
logger = logging.getLogger("codesense")

# Environment variable validation (fail fast)
required_env = ["DATABASE_URL", "GROQ_API_KEY", "GITHUB_TOKEN"]
missing = [var for var in required_env if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Conditional DB schema creation – only for local development
if os.getenv("ENV", "development").lower() == "development":
    Base.metadata.create_all(bind=engine)

# Initialize FastAPI with middleware
app = FastAPI(title="CodeSense AI — Codebase Explainer", middleware=[])
app.add_middleware(RequestIDMiddleware)
app.add_middleware(ErrorHandlingMiddleware)

# Determine allowed origins
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")] if allowed_origins_str else []

if os.getenv("ENV", "development").lower() == "development" or not allowed_origins:
    # Fallback to wildcard for local dev if no specific origins are set, but credentials won't work with "*"
    # Usually in dev we want local ports
    allowed_origins.extend(["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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
def upload_files(request: UploadRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Index code from local file paths or directories and record repository metadata."""
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

        # ---- Repository metadata handling ----
        # Compute simple stats
        file_set = {c["metadata"]["source"] for c in all_chunks}
        file_count = len(file_set)
        chunk_count = len(all_chunks)
        # For this sprint we treat each chunk as one embedding
        embedding_count = chunk_count
        # Update or create repository entry
        repo = db.query(Repository).filter(Repository.name == repo_name, Repository.owner_id == user.get("user_id")).first()
        if not repo:
            repo = Repository(name=repo_name, owner_id=user.get("user_id"))
            db.add(repo)
        repo.last_indexed_at = datetime.utcnow()
        repo.file_count = file_count
        repo.chunk_count = chunk_count
        repo.embedding_count = embedding_count
        repo.indexing_status = "idle"
        db.commit()
        # --------------------------------------

        return UploadResponse(
            message="Successfully indexed codebase.",
            files_indexed=file_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.post("/upload-github", response_model=UploadResponse)
def upload_github(request: GithubUploadRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Clone a public GitHub repo, index its code, and record repository metadata."""
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

        # ---- Repository metadata handling for GitHub repo ----
        repo_name = request.github_url
        file_set = {c["metadata"]["source"] for c in all_chunks}
        file_count = len(file_set)
        chunk_count = len(all_chunks)
        embedding_count = chunk_count
        repo = db.query(Repository).filter(Repository.name == repo_name, Repository.owner_id == user.get("user_id")).first()
        if not repo:
            repo = Repository(name=repo_name, owner_id=user.get("user_id"))
            db.add(repo)
        repo.last_indexed_at = datetime.utcnow()
        repo.file_count = file_count
        repo.chunk_count = chunk_count
        repo.embedding_count = embedding_count
        repo.indexing_status = "idle"
        db.commit()
        # ---------------------------------------------------

        return UploadResponse(
            message=f"Successfully cloned and indexed {request.github_url}.",
            files_indexed=file_count,
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
def upload_local(files: List[UploadFile] = File(...), paths: List[str] = Form(...), db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Upload local files via browser, index them, and record repository metadata."""
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

        # ---- Repository metadata handling for local upload ----
        file_set = {c["metadata"]["source"] for c in all_chunks}
        file_count = len(file_set)
        chunk_count = len(all_chunks)
        embedding_count = chunk_count
        repo = db.query(Repository).filter(Repository.name == repo_name, Repository.owner_id == user.get("user_id")).first()
        if not repo:
            repo = Repository(name=repo_name, owner_id=user.get("user_id"))
            db.add(repo)
        repo.last_indexed_at = datetime.utcnow()
        repo.file_count = file_count
        repo.chunk_count = chunk_count
        repo.embedding_count = embedding_count
        repo.indexing_status = "idle"
        db.commit()
        # ----------------------------------------------------

        return UploadResponse(
            message="Successfully indexed uploaded local files.",
            files_indexed=file_count,
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


@app.get("/repositories", response_model=List[dict])
def list_repositories(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Return repositories owned by the current user with statistics."""
    repos = db.query(Repository).filter(Repository.owner_id == user.get("user_id")).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "branch": r.branch,
            "file_count": r.file_count,
            "chunk_count": r.chunk_count,
            "embedding_count": r.embedding_count,
            "size_bytes": r.size_bytes,
            "last_indexed_at": r.last_indexed_at,
            "indexing_status": r.status,
        }
        for r in repos
    ]

@app.put("/repositories/{repo_id}/reindex")
def reindex_repository(repo_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Trigger a re‑index of the repository (placeholder implementation)."""
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.owner_id == user.get("user_id")).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    # For now we just set status to "reindex_requested"
    repo.indexing_status = "reindex_requested"
    db.commit()
    return {"message": f"Re‑index requested for repository {repo.name}."}

@app.delete("/repositories/{repo_id}")
def delete_repository(repo_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Delete a repository and cascade delete related data."""
    repo = db.query(Repository).filter(Repository.id == repo_id, Repository.owner_id == user.get("user_id")).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    db.delete(repo)
    db.commit()
    return {"message": f"Repository {repo.name} deleted."}

# Preserve original index-status endpoint for compatibility
@app.get("/index-status")
def get_index_status(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Return the currently indexed repo name and file list for the user's repository (if any)."""
    if not vector_store.chunks:
        return {"repo_name": None, "files": []}
    # Find repository matching current vector_store.repo_name and owned by user
    repo = db.query(Repository).filter(Repository.name == vector_store.repo_name, Repository.owner_id == user.get("user_id")).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found in database.")
    unique_files = sorted({chunk["metadata"]["source"] for chunk in vector_store.chunks})
    return {"repo_name": repo.name, "files": unique_files}
