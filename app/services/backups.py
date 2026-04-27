from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.config import (
    BACKUPS_DIR,
    BASE_DIR,
    DB_PATH,
    FOTOS_DIR,
    INFORMES_DIR,
    LOGS_DIR,
    UPLOAD_DIR,
)

BACKUPS_PATH = Path(BACKUPS_DIR).resolve()


def _backup_path(nombre_archivo: str) -> Path | None:
    if not nombre_archivo.endswith(".zip"):
        return None
    if Path(nombre_archivo).name != nombre_archivo:
        return None
    ruta = (BACKUPS_PATH / nombre_archivo).resolve()
    if BACKUPS_PATH not in ruta.parents and ruta != BACKUPS_PATH:
        return None
    return ruta


def _arcname(ruta: Path) -> str:
    try:
        return ruta.resolve().relative_to(Path(BASE_DIR).resolve()).as_posix()
    except ValueError:
        return ruta.name


def _agregar_archivo(zip_file: ZipFile, ruta: Path):
    if ruta.exists() and ruta.is_file():
        zip_file.write(ruta, _arcname(ruta))


def _agregar_directorio(zip_file: ZipFile, ruta: Path):
    if not ruta.exists() or not ruta.is_dir():
        return

    for archivo in ruta.rglob("*"):
        if not archivo.is_file():
            continue
        partes = set(archivo.parts)
        if {".git", ".venv", "__pycache__", "backups"} & partes:
            continue
        zip_file.write(archivo, _arcname(archivo))


def crear_backup_zip(owner_user_id=None) -> Path:
    BACKUPS_PATH.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_backup = BACKUPS_PATH / f"backup_sistema_pericial_{timestamp}.zip"

    with ZipFile(ruta_backup, "w", ZIP_DEFLATED) as zip_file:
        _agregar_archivo(zip_file, Path(DB_PATH))
        _agregar_directorio(zip_file, Path(UPLOAD_DIR))
        _agregar_directorio(zip_file, Path(INFORMES_DIR))
        _agregar_directorio(zip_file, Path(FOTOS_DIR))
        _agregar_directorio(zip_file, Path(LOGS_DIR))
        _agregar_archivo(zip_file, Path(BASE_DIR) / ".env.example")

    return ruta_backup


def listar_backups() -> list:
    BACKUPS_PATH.mkdir(parents=True, exist_ok=True)
    backups = []
    for ruta in sorted(BACKUPS_PATH.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True):
        stat = ruta.stat()
        backups.append(
            {
                "nombre": ruta.name,
                "tamano": stat.st_size,
                "fecha": datetime.fromtimestamp(stat.st_mtime),
            }
        )
    return backups


def obtener_backup(nombre_archivo: str) -> Path | None:
    ruta = _backup_path(nombre_archivo)
    if ruta and ruta.exists() and ruta.is_file():
        return ruta
    return None


def borrar_backup(nombre_archivo: str) -> bool:
    ruta = obtener_backup(nombre_archivo)
    if not ruta:
        return False
    ruta.unlink()
    return True
