from fastapi import FastAPI, HTTPException
from .models import UploadRequest, UploadResponse, QueryRequest, QueryResponse
from .ingest import FileProcessor
from .vector_store import VectorStoreManager
from .qa import QAEngine, OpenAIProvider, MockProvider
import os

app = FastAPI(title="AI-Powered DevOps Codebase Explainer")

# Initialize components
file_processor = FileProcessor()
vector_store = VectorStoreManager()

# Use OpenAI if API key exists, otherwise Mock
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    llm_provider = OpenAIProvider(api_key=api_key)
else:
    llm_provider = MockProvider()

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
        vector_store.add_chunks(all_chunks)
        
        return UploadResponse(
            message="Successfully indexed codebase.",
            files_indexed=len(set(c["metadata"]["source"] for c in all_chunks))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        results = vector_store.search(request.question, top_k=request.top_k)
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
