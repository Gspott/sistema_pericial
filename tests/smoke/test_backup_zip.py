from pathlib import Path
from zipfile import ZipFile


def test_backup_zip_uses_sandbox_paths(isolated_import):
    isolated_import("app.main")

    from app import config
    from app.services.backups import crear_backup_zip

    backup_path = crear_backup_zip()

    assert backup_path.exists()
    assert backup_path.suffix == ".zip"
    assert Path(config.BACKUPS_DIR) in backup_path.parents
    assert "generated/backups" in backup_path.as_posix()
    assert "sistema_pericial/backups" not in backup_path.as_posix()

    with ZipFile(backup_path) as zip_file:
        names = set(zip_file.namelist())

    assert "pericial_test.db" in names
    assert ".env" not in names
    assert ".env.example" in names

