#!/usr/bin/env python3
"""Create a new active harness plan from the task envelope template."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = ROOT / "docs" / "harness" / "PLANS" / "active"
TEMPLATE_PATH = ROOT / "docs" / "harness" / "templates" / "TASK_ENVELOPE.md"
CURRENT_PLAN_PATH = ROOT / "docs" / "harness" / "STATE" / "current_plan.txt"


def normalize_slug(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9._-]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        raise ValueError("El slug no puede quedar vacio")
    if slug in {".", ".."} or "/" in slug or "\\" in slug:
        raise ValueError("Slug no permitido")
    return slug[:-3] if slug.endswith(".md") else slug


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an active harness plan.")
    parser.add_argument("slug", help="Plan slug, for example smoke-tests-emails")
    parser.add_argument("task_pack", nargs="?", help="Optional Task Pack name")
    args = parser.parse_args()

    try:
        slug = normalize_slug(args.slug)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    destination = ACTIVE_DIR / f"{slug}.md"
    if destination.exists():
        print(f"[FAIL] Ya existe: {destination.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"[FAIL] Falta plantilla: {TEMPLATE_PATH.relative_to(ROOT)}", file=sys.stderr)
        return 1

    title = slug.replace("-", " ").replace("_", " ").title()
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    content = f"# {title}\n\n{content}"
    if args.task_pack:
        content = content.replace(
            "# Playbook aplicable\n\n",
            f"# Playbook aplicable\n\nTask Pack sugerido: `{args.task_pack}`.\n\n",
        )

    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    CURRENT_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_PLAN_PATH.write_text(destination.name + "\n", encoding="utf-8")
    print(destination.relative_to(ROOT))
    print(f"Current active plan: {destination.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
