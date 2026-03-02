import requests
import json
import os

BASE_URL = "http://127.0.0.1:8002"

def test_flow():
    # 1. Health Check
    print("Checking health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Health: {resp.json()}")
    except Exception as e:
        print(f"Failed to connect to server. Is it running? {e}")
        return

    # 2. Upload (Indexing self)
    print("\nIndexing backend directory...")
    backend_path = os.path.join(os.getcwd(), "backend")
    upload_data = {"files": [backend_path]}
    resp = requests.post(f"{BASE_URL}/upload", json=upload_data)
    print(f"Upload Response: {resp.json()}")

    # 3. Ask
    print("\nAsking a question...")
    query_data = {"question": "What files are supported for ingestion?", "top_k": 3}
    resp = requests.post(f"{BASE_URL}/ask", json=query_data)
    result = resp.json()
    print(f"Answer: {result['answer']}")
    print("\nContext Chunks used:")
    for i, chunk in enumerate(result['context_chunks']):
        print(f"[{i+1}] {chunk[:100]}...")

if __name__ == "__main__":
    test_flow()
