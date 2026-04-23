# AI-Powered DevOps Codebase Assistant (RAG)

An AI-powered tool that explains source code and DevOps configuration files using Retrieval-Augmented Generation (RAG). It splits files into chunks, indexes them in a FAISS vector store, and uses an LLM to answer questions based only on the retrieved context.

## Features
- **File Ingestion**: Supports `.py`, `.js`, `.sh`, `.yml`, `.yaml`, and `Dockerfile`.
- **Vector Storage**: Uses FAISS (`IndexFlatL2`) for efficient similarity search.
- **RAG Workflow**: Converts user questions to embeddings, retrieves relevant chunks, and generates context-aware answers.
- **Strict Prompting**: Prevents hallucinations by instructing the LLM to only use provided context.

## Tech Stack
- **Language**: Python 3.x
- **Framework**: FastAPI
- **Vector DB**: FAISS
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **LLM**: OpenAI (abstracted for easy switching)

## How it Works
1. **RAG (Retrieval-Augmented Generation)**: Instead of relying solely on the LLM's training data, we provide it with relevant "context" retrieved from our own codebase index.
2. **FAISS**: A library for efficient similarity search and clustering of dense vectors. We use it to map code chunks to a high-dimensional space and find the closest matches to a user's question.

## Getting Started

### Prerequisites
- Python 3.9+
- Gemini API Key (get from Google AI Studio)

### Installation
1. Clone the repository and navigate to the root directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project
1. Set your Gemini API key:
   ```bash
   $env:GEMINI_API_KEY="your_key_here"  # Windows PowerShell
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn backend.main:app --reload
   ```

### API Endpoints
- **POST `/upload`**: Ingest and index files.
  - Body: `{"files": ["path/to/folder", "path/to/file.py"]}`
- **POST `/ask`**: Query the codebase.
  - Body: `{"question": "How does the ingestion logic work?"}`
- **GET `/health`**: Check system status.

## Project Structure
```
backend/
 ├── main.py          # FastAPI app
 ├── ingest.py        # file reading & chunking
 ├── vector_store.py  # FAISS index creation & search
 ├── qa.py            # prompt construction & LLM call
 ├── models.py        # request/response schemas
 └── utils.py         # helper functions
requirements.txt
README.md
```
