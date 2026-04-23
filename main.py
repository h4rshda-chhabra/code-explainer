from backend.main import app

# This file serves as the entrypoint for platforms like Vercel or Render
# that look for a 'main.py' or 'app' instance in the root directory.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
