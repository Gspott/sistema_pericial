import importlib
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_ENV_FILE = REPO_ROOT / ".env"


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            sys.modules.pop(name, None)


def _configure_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    generated_dir = tmp_path / "generated"

    paths = {
        "DB_PATH": data_dir / "pericial_test.db",
        "UPLOAD_DIR": generated_dir / "uploads",
        "INFORMES_DIR": generated_dir / "informes",
        "FOTOS_DIR": generated_dir / "fotos",
        "BACKUPS_DIR": generated_dir / "backups",
        "EXPORTS_DIR": generated_dir / "exports",
        "LOGS_DIR": generated_dir / "logs",
        "STATIC_DIR": REPO_ROOT / "static",
        "TEMPLATES_DIR": REPO_ROOT / "templates",
    }
    for key, value in paths.items():
        monkeypatch.setenv(key, str(value))

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_PORT", "8000")
    monkeypatch.setenv("BASE_URL", "http://testserver")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-session-secret")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "false")

    for key in (
        "DUCKDNS_DOMAIN",
        "DUCKDNS_TOKEN",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_HOST",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
        "OPENAI_API_KEY",
    ):
        monkeypatch.setenv(key, "")


@contextmanager
def _block_real_env_file():
    original_exists = Path.exists

    def exists_without_real_env(self):
        if self == REAL_ENV_FILE:
            return False
        return original_exists(self)

    with patch.object(Path, "exists", exists_without_real_env):
        yield


@pytest.fixture
def isolated_import(monkeypatch, tmp_path):
    def importer(module_name: str):
        _configure_test_env(monkeypatch, tmp_path)
        _purge_app_modules()
        with _block_real_env_file():
            return importlib.import_module(module_name)

    return importer

