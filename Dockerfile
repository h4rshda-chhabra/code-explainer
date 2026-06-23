# ── Build Stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System dependencies for psycopg2, faiss-cpu, and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install CPU-only PyTorch first (smaller, faster) before other deps
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install remaining Python dependencies (layer cache)
COPY backend/requirements.txt .
RUN grep -v "^torch" requirements.txt | pip install --no-cache-dir -r /dev/stdin

# Copy the full project
COPY . .

# Expose port (Render injects $PORT at runtime)
EXPOSE 8000

# Run the FastAPI app
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
