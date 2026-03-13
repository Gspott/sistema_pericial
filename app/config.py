from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = str(BASE_DIR / "pericial.db")
UPLOAD_DIR = str(BASE_DIR / "uploads")
TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")
INFORMES_DIR = str(BASE_DIR / "informes")
