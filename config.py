import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openrouter")
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    SCREENSHOT_DIR = BASE_DIR / "temp_screenshots"

Config.SCREENSHOT_DIR.mkdir(exist_ok=True)
