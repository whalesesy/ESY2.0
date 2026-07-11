import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# API Keys and Endpoints
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Determine AI Provider
if GROQ_API_KEY:
    AI_PROVIDER = "groq"
elif GEMINI_API_KEY:
    AI_PROVIDER = "gemini"
elif OPENAI_API_KEY or OPENAI_API_BASE:
    AI_PROVIDER = "openai"
else:
    AI_PROVIDER = "offline"

# Speech Configurations
WAKE_WORDS = ["esy", "jarvis"]
VOICE_RATE = int(os.getenv("VOICE_RATE", 185))
VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", 1.0))
VOICE_GENDER = os.getenv("VOICE_GENDER", "male")  # male or female

# Paths
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)
HISTORY_FILE = MEMORY_DIR / "history.json"

