from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env si existe en la raíz del proyecto
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value

# Valores por defecto seguros, relativos al proyecto
default_db_path = str(BASE_DIR / "data" / "pericial.db")
default_upload_dir = str(BASE_DIR / "uploads")
default_informes_dir = str(BASE_DIR / "informes")
default_fotos_dir = str(BASE_DIR / "fotos")

APP_ENV = os.getenv("APP_ENV", "dev")

DB_PATH = os.getenv("DB_PATH", default_db_path)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", default_upload_dir)
INFORMES_DIR = os.getenv("INFORMES_DIR", default_informes_dir)
FOTOS_DIR = os.getenv("FOTOS_DIR", default_fotos_dir)

TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CLOUDFLARED_BIN = os.getenv("CLOUDFLARED_BIN", "/opt/homebrew/bin/cloudflared")


def _sanitize_path(path_value: str, fallback: str) -> str:
    if not path_value or "TU_USUARIO" in path_value:
        return fallback
    return path_value


DB_PATH = _sanitize_path(DB_PATH, default_db_path)
UPLOAD_DIR = _sanitize_path(UPLOAD_DIR, default_upload_dir)
INFORMES_DIR = _sanitize_path(INFORMES_DIR, default_informes_dir)
FOTOS_DIR = _sanitize_path(FOTOS_DIR, default_fotos_dir)


def ensure_directories() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(INFORMES_DIR).mkdir(parents=True, exist_ok=True)
    Path(FOTOS_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATIC_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
