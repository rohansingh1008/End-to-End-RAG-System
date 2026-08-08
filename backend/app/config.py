import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
BASE_TEMP_DIR = Path("./temp_sessions")
BASE_TEMP_DIR.mkdir(exist_ok=True)