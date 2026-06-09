import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in client.models.list(config={'page_size': 50}):
    if "embed" in m.name.lower():
        print(f"Model Name: {m.name}")
        print(f"Supported Actions: {m.supported_actions}")

