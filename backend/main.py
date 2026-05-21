from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from typing import List
import shutil
import tempfile
from fastapi.middleware.cors import CORSMiddleware
from .models import UploadRequest, UploadResponse, QueryRequest, QueryResponse, GithubUploadRequest
from .ingest import FileProcessor
from .vector_store import VectorStoreManager
from .qa import QAEngine
from .github_ingest import GitHubIngestor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI-Powered DevOps Codebase Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
file_processor = FileProcessor()
vector_store = VectorStoreManager()
github_ingestor = GitHubIngestor()

# Use Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
qa_engine = QAEngine(api_key=api_key)

@app.post("/upload", response_model=UploadResponse)
def upload_files(request: UploadRequest):
    try:
        all_chunks = []
        for path in request.files:
            if os.path.isdir(path):
                chunks = file_processor.process_directory(path, allowed_extensions=request.allowed_extensions)
            else:
                chunks = file_processor.process_file(path)
            all_chunks.extend(chunks)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid DevOps/Code files found in the provided paths.")

        vector_store.clear()
        repo_name = os.path.basename(os.path.normpath(request.files[0])) if len(request.files) == 1 else "Multiple Local Folders"
        vector_store.add_chunks(all_chunks, repo_name=repo_name)

        return UploadResponse(
            message="Successfully indexed codebase.",
            files_indexed=len(set(c["metadata"]["source"] for c in all_chunks))
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/upload-github", response_model=UploadResponse)
def upload_github(request: GithubUploadRequest):
    temp_dir = None
    try:
        repo_url = request.github_url
        if not repo_url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")

        try:
            temp_dir = github_ingestor.clone_repo(repo_url)
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

        all_chunks = file_processor.process_directory(temp_dir)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No readable code files found in the repository.")

        vector_store.clear()
        vector_store.add_chunks(all_chunks, repo_name=repo_url)

        return UploadResponse(
            message=f"Successfully cloned and indexed {repo_url}.",
            files_indexed=len(set(c["metadata"]["source"] for c in all_chunks))
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

@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    try:
        # Force top_k to 8 to guarantee maximum AI context on complex ML pipelines
        results = vector_store.search(request.question, top_k=8)
        context_chunks = [r["text"] for r in results]
        
        answer = qa_engine.answer_question(request.question, context_chunks)
        
        return QueryResponse(
            answer=answer,
            context_chunks=context_chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clear")
def clear_index():
    try:
        vector_store.clear()
        return {"message": "Successfully unindexed codebase."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok", "indexed_chunks": len(vector_store.chunks)}

@app.get("/index-status")
def get_index_status():
    try:
        if not vector_store.chunks:
            return {"repo_name": "None", "files": []}
            
        # Extract unique file paths from the metadata
        unique_files = list(set(chunk["metadata"]["source"] for chunk in vector_store.chunks))
        unique_files.sort()
        
        return {
            "repo_name": vector_store.repo_name,
            "files": unique_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-local", response_model=UploadResponse)
def upload_local(files: List[UploadFile] = File(...), paths: List[str] = Form(...)):
    temp_dir = tempfile.mkdtemp(prefix="codesense_local_")
    try:
        if len(files) != len(paths):
            raise HTTPException(status_code=400, detail="Mismatched files and paths.")

        for file, rel_path in zip(files, paths):
            # rel_path contains the full webkitRelativePath e.g., "MyRepo/src/main.py"
            # Ensure safe path extraction to prevent traversal attacks
            safe_path = os.path.normpath(rel_path).lstrip(os.sep)
            full_path = os.path.join(temp_dir, safe_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        # Now use the existing file_processor on the temp_dir
        all_chunks = file_processor.process_directory(temp_dir)

        if not all_chunks:
            raise HTTPException(status_code=400, detail="No valid code files found in the upload.")

        vector_store.clear()
        repo_name = paths[0].split("/")[0] if paths else "Local Upload"
        vector_store.add_chunks(all_chunks, repo_name=repo_name)

        return UploadResponse(
            message="Successfully indexed uploaded local files.",
            files_indexed=len(set(c["metadata"]["source"] for c in all_chunks))
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        github_ingestor.cleanup_dir(temp_dir)
