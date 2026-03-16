from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import UploadRequest, UploadResponse, QueryRequest, QueryResponse, GithubUploadRequest
from .ingest import FileProcessor
from .vector_store import VectorStoreManager
from .qa import QAEngine, GeminiProvider
from .github_ingest import GitHubIngestor
import os

app = FastAPI(title="AI-Powered DevOps Codebase Explainer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In a production environment, change this to ["http://localhost:5173"] or your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
file_processor = FileProcessor()
vector_store = VectorStoreManager()
github_ingestor = GitHubIngestor()

# Use Gemini API Key
api_key = "AIzaSyATloysJHz3kiUfwov6uR7ssUCm3SBjgb0"
llm_provider = GeminiProvider(api_key=api_key)

qa_engine = QAEngine(llm_provider)

@app.post("/upload", response_model=UploadResponse)
async def upload_files(request: UploadRequest):
    try:
        all_chunks = []
        for path in request.files:
            if os.path.isdir(path):
                chunks = file_processor.process_directory(path)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-github", response_model=UploadResponse)
async def upload_github(request: GithubUploadRequest):
    try:
        repo_url = request.github_url
        if not repo_url.startswith("http"):
             raise HTTPException(status_code=400, detail="Invalid GitHub URL provided.")
             
        # Clone repo to temp dir
        temp_dir = github_ingestor.clone_repo(repo_url)
        
        # Process the cloned directory
        all_chunks = file_processor.process_directory(temp_dir)
        
        if not all_chunks:
            # Clean up empty clones
            github_ingestor.cleanup_dir(temp_dir)
            raise HTTPException(status_code=400, detail="No readable code files found in the repository.")
            
        vector_store.clear()
        vector_store.add_chunks(all_chunks, repo_name=repo_url)
        
        # Clean up immediately after reading to save PC space
        github_ingestor.cleanup_dir(temp_dir)
        
        return UploadResponse(
            message=f"Successfully cloned and indexed {repo_url}.",
            files_indexed=len(set(c["metadata"]["source"] for c in all_chunks))
        )
    except Exception as e:
        # Return 400 Bad Request for user-facing errors like invalid repositories
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
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

@app.get("/health")
async def health_check():
    return {"status": "ok", "indexed_chunks": len(vector_store.chunks)}

@app.get("/index-status")
async def get_index_status():
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

@app.get("/browse")
async def browse_local():
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Create a hidden native window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True) # Bring to front over the browser
        
        # Ask for directory
        folder_path = filedialog.askdirectory(parent=root, title="Select Project Folder to Index")
        root.destroy()
        
        if not folder_path:
            return {"path": ""}
            
        # Convert path to standard format
        folder_path = os.path.normpath(folder_path)
        return {"path": folder_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
