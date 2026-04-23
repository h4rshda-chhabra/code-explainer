FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (git for cloning, libgomp1 for faiss)
RUN apt-get update && apt-get install -y git libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV GIT_PYTHON_REFRESH=quiet
COPY . .

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-10000}"]