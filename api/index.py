from backend.main import app

# Vercel looks for the 'app' or 'application' variable in api/index.py
# to serve as the FastAPI entrypoint.
application = app
