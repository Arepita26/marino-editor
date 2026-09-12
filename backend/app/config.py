import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
TEMP_DIR = Path(os.getenv("TEMP_DIR", "/tmp/marino_processing"))

# Ensure temp directory exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Intro video path (check mp4 then mov)
INTRO_VIDEO_PATH = ASSETS_DIR / "intro_marino.mp4"
if not INTRO_VIDEO_PATH.exists():
    INTRO_VIDEO_PATH = ASSETS_DIR / "intro_marino.mov"

# Video Processing Parameters
INTRO_DURATION_SECONDS = float(os.getenv("INTRO_DURATION", "4.13"))
CROSSFADE_DURATION_SECONDS = float(os.getenv("CROSSFADE_DURATION", "0.3"))
CROSSFADE_OFFSET_SECONDS = float(os.getenv("CROSSFADE_OFFSET", "3.83"))  # 4.13 - 0.3 = 3.83

# Output video specs: 1080x1920 vertical, 30fps constant
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FPS = 30

# File limits
# User requested 500 MB limit
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(500 * 1024 * 1024)))  # 500 MB
MAX_FILE_SIZE_MB = 500

# Cleanup configurations
FILE_EXPIRATION_SECONDS = int(os.getenv("FILE_EXPIRATION_SECONDS", "1800"))  # 30 minutes
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300"))  # Every 5 minutes

# Allowed video extensions and mime types
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".3gp"}
ALLOWED_MIME_PREFIXES = ("video/", "application/octet-stream")

# CORS Allowed Origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "https://*.vercel.app",
    "https://*.hf.space",
]
# If specific frontend origin passed via environment
if os.getenv("FRONTEND_URL"):
    CORS_ORIGINS.append(os.getenv("FRONTEND_URL"))
