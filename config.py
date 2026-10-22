"""Central configuration – every value comes from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _id_set(name: str) -> set:
    out = set()
    for part in os.getenv(name, "").replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            out.add(int(part))
    return out


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = _id_set("ADMIN_IDS")
ALLOWED_USERS = _id_set("ALLOWED_USERS")

API_BASE_URL = os.getenv("API_BASE_URL", "").strip().rstrip("/")
MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 49)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

MAX_PLAYLIST_ITEMS = max(1, _int("MAX_PLAYLIST_ITEMS", 25))
MAX_PLAYLIST_SCAN = 500
MAX_CONCURRENT_JOBS = max(1, _int("MAX_CONCURRENT_JOBS", 2))
COOLDOWN_SECONDS = max(0, _int("COOLDOWN_SECONDS", 5))
DAILY_LIMIT = max(0, _int("DAILY_LIMIT", 0))
MAX_VIDEO_MINUTES = max(0, _int("MAX_VIDEO_MINUTES", 0))

_cookies = os.getenv("COOKIES_FILE", "").strip()
COOKIES_FILE = str(Path(_cookies).expanduser()) if _cookies else ""
YTDLP_JS_RUNTIME = os.getenv("YTDLP_JS_RUNTIME", "").strip()

DATA_DIR = BASE_DIR / "data"
TEMP_DIR = BASE_DIR / "work"
DB_PATH = DATA_DIR / "bot.db"

PENDING_TTL = 30 * 60  # seconds a link card stays clickable
