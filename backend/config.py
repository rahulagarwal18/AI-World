import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GITHUB_REPO_URL: str = os.getenv("GITHUB_REPO_URL", "https://github.com/rahulagarwal18/AI-World.git")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "rahulagarwal18")
    GDRIVE_FOLDER_ID: str = os.getenv("GDRIVE_FOLDER_ID", "16JoYjvINixhs1TRgZLplF9mdIMXl-eP0")
    
    WORKSPACE_DIR: Path = BASE_DIR / "workspace"
    MAX_GROQ_RETRIES: int = 5
    MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

Config.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
