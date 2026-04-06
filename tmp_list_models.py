import os
from google.genai import Client
from dotenv import load_dotenv

load_dotenv()
client = Client(api_key=os.environ.get("GEMINI_API_KEY"))
for m in client.models.list():
    print(m.name)
