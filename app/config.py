import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"


def load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _resolve_project_path(path_value: str | None, fallback: Path) -> str:
    if not path_value or "TU_USUARIO" in path_value:
        return str(fallback)

    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return str(candidate.resolve())


load_env_file()

default_db_path = BASE_DIR / "data" / "pericial.db"
default_upload_dir = BASE_DIR / "uploads"
default_informes_dir = BASE_DIR / "informes"
default_fotos_dir = BASE_DIR / "fotos"
default_static_dir = BASE_DIR / "static"
default_templates_dir = BASE_DIR / "templates"
default_logs_dir = BASE_DIR / "logs"

APP_ENV = os.getenv("APP_ENV", "dev")

APP_HOST = os.getenv("APP_HOST", os.getenv("HOST", "0.0.0.0"))
APP_PORT = int(os.getenv("APP_PORT", os.getenv("PORT", "8000")))
BASE_URL = os.getenv("BASE_URL", f"http://127.0.0.1:{APP_PORT}")

DB_PATH = _resolve_project_path(os.getenv("DB_PATH"), default_db_path)
UPLOAD_DIR = _resolve_project_path(os.getenv("UPLOAD_DIR"), default_upload_dir)
INFORMES_DIR = _resolve_project_path(os.getenv("INFORMES_DIR"), default_informes_dir)
FOTOS_DIR = _resolve_project_path(os.getenv("FOTOS_DIR"), default_fotos_dir)
STATIC_DIR = _resolve_project_path(os.getenv("STATIC_DIR"), default_static_dir)
TEMPLATES_DIR = _resolve_project_path(
    os.getenv("TEMPLATES_DIR"),
    default_templates_dir,
)
LOGS_DIR = _resolve_project_path(os.getenv("LOGS_DIR"), default_logs_dir)

HOST = APP_HOST
PORT = APP_PORT

DUCKDNS_DOMAIN = os.getenv("DUCKDNS_DOMAIN", "").strip()
DUCKDNS_TOKEN = os.getenv("DUCKDNS_TOKEN", "").strip()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CLOUDFLARED_BIN = os.getenv("CLOUDFLARED_BIN", "/opt/homebrew/bin/cloudflared")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", secrets.token_urlsafe(32))


def ensure_directories() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(INFORMES_DIR).mkdir(parents=True, exist_ok=True)
    Path(FOTOS_DIR).mkdir(parents=True, exist_ok=True)
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATIC_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
