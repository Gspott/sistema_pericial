#!/usr/bin/env python3
"""Resuelve el scope minimo de smoke a partir de paths modificados."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass


SCOPE_ORDER = {
    "docs": 0,
    "app": 1,
    "valoracion": 2,
    "full": 3,
}


@dataclass(frozen=True)
class ScopeDecision:
    requested_scope: str
    required_scope: str
    effective_scope: str
    unsafe_override: bool
    reasons: tuple[str, ...]
    files: tuple[str, ...]


def _git_changed_files() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            files.append(path)
    return files


def _is_docs_only_path(path: str) -> bool:
    return (
        path.startswith("docs/")
        or path in {"AGENTS.md", "agents.md", "README.md"}
    )


def _is_valoracion_path(path: str) -> bool:
    return (
        path.startswith("templates/valoracion")
        or path.startswith("tests/smoke/test_valoracion")
        or path.startswith("tests/fixtures/valoracion")
        or path == "app/services/informe.py"
        or path == "scripts/create_valoracion_demo_cases.py"
    )


def _is_static_path(path: str) -> bool:
    return path.startswith("static/")


def _is_critical_path(path: str) -> bool:
    critical_exact = {
        "app/database.py",
        "app/services/backups.py",
        "app/services/exportaciones.py",
        "app/services/email_sender.py",
    }
    critical_prefixes = (
        "templates/informes/",
        "templates/propuestas/",
        "app/routers/",
    )
    critical_fragments = (
        "backup",
        "restore",
        "upload",
        "uploads",
        "auth",
        "login",
        "password",
        "session",
        "pdf",
        "docx",
    )
    lower_path = path.lower()
    return (
        path in critical_exact
        or any(path.startswith(prefix) for prefix in critical_prefixes)
        or any(fragment in lower_path for fragment in critical_fragments)
    )


def required_scope_for_files(files: list[str]) -> tuple[str, list[str]]:
    if not files:
        return "docs", ["sin cambios detectados"]

    reasons: list[str] = []
    required = "docs"

    if all(_is_docs_only_path(path) for path in files):
        return "docs", ["solo paths documentales"]

    for path in files:
        if _is_critical_path(path):
            required = "full"
            reasons.append(f"{path}: path critico")
            continue
        if _is_valoracion_path(path) and SCOPE_ORDER[required] < SCOPE_ORDER["valoracion"]:
            required = "valoracion"
            reasons.append(f"{path}: valoracion")
            continue
        if _is_static_path(path) and SCOPE_ORDER[required] < SCOPE_ORDER["app"]:
            required = "app"
            reasons.append(f"{path}: static/app")
            continue
        if path.startswith("app/") or path.startswith("templates/") or path.startswith("tests/"):
            if SCOPE_ORDER[required] < SCOPE_ORDER["app"]:
                required = "app"
            reasons.append(f"{path}: app/templates/tests")
            continue
        if not _is_docs_only_path(path) and SCOPE_ORDER[required] < SCOPE_ORDER["app"]:
            required = "app"
            reasons.append(f"{path}: path no documental")

    if not reasons:
        reasons.append("solo paths documentales")
    return required, reasons


def resolve_scope(
    requested_scope: str,
    files: list[str],
    allow_unsafe_scope: bool = False,
) -> ScopeDecision:
    required_scope, reasons = required_scope_for_files(files)
    requested_rank = SCOPE_ORDER[requested_scope]
    required_rank = SCOPE_ORDER[required_scope]
    unsafe = requested_rank < required_rank and allow_unsafe_scope
    effective = (
        requested_scope
        if requested_rank >= required_rank or allow_unsafe_scope
        else required_scope
    )
    return ScopeDecision(
        requested_scope=requested_scope,
        required_scope=required_scope,
        effective_scope=effective,
        unsafe_override=unsafe,
        reasons=tuple(reasons),
        files=tuple(files),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requested-scope", required=True, choices=sorted(SCOPE_ORDER))
    parser.add_argument("--allow-unsafe-scope", action="store_true")
    parser.add_argument(
        "--format",
        choices=("shell", "text"),
        default="text",
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    files = args.files or _git_changed_files()
    decision = resolve_scope(
        args.requested_scope,
        files,
        allow_unsafe_scope=args.allow_unsafe_scope,
    )

    if args.format == "shell":
        print(f"REQUESTED_SCOPE={decision.requested_scope}")
        print(f"REQUIRED_SCOPE={decision.required_scope}")
        print(f"EFFECTIVE_SCOPE={decision.effective_scope}")
        print(f"UNSAFE_OVERRIDE={'1' if decision.unsafe_override else '0'}")
        return 0

    print(f"[INFO] requested_scope={decision.requested_scope}")
    print(f"[INFO] required_scope={decision.required_scope}")
    print(f"[INFO] effective_scope={decision.effective_scope}")
    for reason in decision.reasons:
        print(f"[INFO] scope_reason={reason}")
    if SCOPE_ORDER[decision.requested_scope] < SCOPE_ORDER[decision.required_scope]:
        if decision.unsafe_override:
            print("[WARN] requested scope is below required scope; unsafe override enabled")
        else:
            print(
                "[AUTO-UPGRADE] "
                f"requested_scope={decision.requested_scope} insufficient; "
                f"using scope={decision.effective_scope}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
