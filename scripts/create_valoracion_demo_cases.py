#!/usr/bin/env python3
"""Crea casos demo ficticios de valoracion en una SQLite sandbox explicita."""

import argparse
import json
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SENSITIVE_DIRS = {
    (REPO_ROOT / "data").resolve(),
    (REPO_ROOT / "uploads").resolve(),
    (REPO_ROOT / "informes").resolve(),
    (REPO_ROOT / "fotos").resolve(),
    (REPO_ROOT / "backups").resolve(),
    (REPO_ROOT / "sistema_pericial").resolve(),
}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validar_db_sandbox(db_path: Path, append: bool, allow_project_db: bool) -> Path:
    destino = db_path.expanduser().resolve()
    for sensible in SENSITIVE_DIRS:
        if _is_relative_to(destino, sensible) and not allow_project_db:
            raise SystemExit(
                "Ruta rechazada por seguridad: "
                f"{destino}. Usa una ruta temporal o --allow-project-db "
                "tras crear backup local."
            )
    if destino.exists() and not append:
        raise SystemExit(
            f"La DB ya existe: {destino}. Usa --append o elige una ruta temporal nueva."
        )
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino


def configurar_entorno(db_path: Path) -> None:
    generated = db_path.parent / "generated"
    os.environ["APP_ENV"] = "test"
    os.environ["DB_PATH"] = str(db_path)
    os.environ.setdefault("UPLOAD_DIR", str(generated / "uploads"))
    os.environ.setdefault("INFORMES_DIR", str(generated / "informes"))
    os.environ.setdefault("FOTOS_DIR", str(generated / "fotos"))
    os.environ.setdefault("BACKUPS_DIR", str(generated / "backups"))
    os.environ.setdefault("EXPORTS_DIR", str(generated / "exports"))
    os.environ.setdefault("LOGS_DIR", str(generated / "logs"))
    os.environ.setdefault("STATIC_DIR", str(REPO_ROOT / "static"))
    os.environ.setdefault("TEMPLATES_DIR", str(REPO_ROOT / "templates"))
    os.environ.setdefault("SESSION_SECRET_KEY", "demo-valoracion-session-secret")
    os.environ.setdefault("SESSION_COOKIE_SECURE", "false")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Genera cinco casos ficticios de valoracion en una SQLite sandbox.",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Ruta de la SQLite sandbox a crear o completar.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Permite insertar en una DB sandbox existente.",
    )
    parser.add_argument(
        "--allow-project-db",
        action="store_true",
        help="Permite usar una DB dentro del proyecto tras backup local explicito.",
    )
    args = parser.parse_args()

    db_path = validar_db_sandbox(Path(args.db), args.append, args.allow_project_db)
    configurar_entorno(db_path)

    from app.database import get_connection, init_db
    from tests.fixtures.valoracion_demo_cases import crear_casos_demo_valoracion

    init_db()
    conn = get_connection()
    try:
        cur = conn.cursor()
        resultado = crear_casos_demo_valoracion(cur)
        conn.commit()
    finally:
        conn.close()

    print(json.dumps({"db": str(db_path), **resultado}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
