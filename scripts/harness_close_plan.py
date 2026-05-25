#!/usr/bin/env python3
"""Move a harness plan from active to completed."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = ROOT / "docs" / "harness" / "PLANS" / "active"
COMPLETED_DIR = ROOT / "docs" / "harness" / "PLANS" / "completed"
CURRENT_PLAN_PATH = ROOT / "docs" / "harness" / "STATE" / "current_plan.txt"


def normalize_filename(value: str) -> str:
    name = value.strip()
    if "/" in name or "\\" in name or name in {"", ".", ".."}:
        raise ValueError("Nombre de plan no permitido")
    if not name.endswith(".md"):
        name = f"{name}.md"
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.md", name):
        raise ValueError("Nombre de plan no permitido")
    if name == "README.md":
        raise ValueError("README.md no es un plan cerrable")
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description="Close an active harness plan.")
    parser.add_argument("plan", help="Plan filename in docs/harness/PLANS/active/")
    parser.add_argument(
        "--no-status-line",
        action="store_true",
        help="Do not append 'Estado: completado' before moving.",
    )
    args = parser.parse_args()

    try:
        filename = normalize_filename(args.plan)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    source = ACTIVE_DIR / filename
    destination = COMPLETED_DIR / filename
    if not source.exists():
        print(f"[FAIL] No existe en active: {source.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if destination.exists():
        print(f"[FAIL] Ya existe en completed: {destination.relative_to(ROOT)}", file=sys.stderr)
        return 1

    if not args.no_status_line:
        text = source.read_text(encoding="utf-8")
        if "Estado: completado" not in text:
            source.write_text(text.rstrip() + "\n\nEstado: completado\n", encoding="utf-8")

    COMPLETED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))
    if CURRENT_PLAN_PATH.exists() and CURRENT_PLAN_PATH.read_text(encoding="utf-8").strip() == filename:
        CURRENT_PLAN_PATH.write_text("", encoding="utf-8")
    print(destination.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
