from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env simple sin dependencias extra
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

APP_ENV = os.getenv("APP_ENV", "dev")

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "data" / "pericial.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))
INFORMES_DIR = os.getenv("INFORMES_DIR", str(BASE_DIR / "informes"))
FOTOS_DIR = os.getenv("FOTOS_DIR", str(BASE_DIR / "fotos"))

TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CLOUDFLARED_BIN = os.getenv("CLOUDFLARED_BIN", "/opt/homebrew/bin/cloudflared")


def ensure_directories() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(INFORMES_DIR).mkdir(parents=True, exist_ok=True)
    Path(FOTOS_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATIC_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
