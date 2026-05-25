#!/usr/bin/env python3
"""Create a lightweight harness episode package."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EPISODES_DIR = ROOT / "docs" / "harness" / "EPISODES"
TEMPLATE_PATH = EPISODES_DIR / "templates" / "EPISODE_TEMPLATE.md"


def normalize_slug(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9._-]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        raise ValueError("El slug no puede quedar vacio")
    if slug in {".", ".."} or "/" in slug or "\\" in slug:
        raise ValueError("Slug no permitido")
    return slug[:-3] if slug.endswith(".md") else slug


def normalize_plan(value: str | None) -> str:
    if not value:
        return ""
    plan = value.strip()
    if "/" in plan or "\\" in plan or plan in {".", ".."}:
        raise ValueError("Plan no permitido")
    return plan if plan.endswith(".md") else f"{plan}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a harness episode.")
    parser.add_argument("slug", help="Episode slug")
    parser.add_argument("--plan", default="", help="Associated plan filename")
    args = parser.parse_args()

    try:
        slug = normalize_slug(args.slug)
        plan = normalize_plan(args.plan)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    destination = EPISODES_DIR / f"{date.today().isoformat()}-{slug}.md"
    if destination.exists():
        print(f"[FAIL] Ya existe: {destination.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not TEMPLATE_PATH.exists():
        print(f"[FAIL] Falta plantilla: {TEMPLATE_PATH.relative_to(ROOT)}", file=sys.stderr)
        return 1

    title = slug.replace("-", " ").replace("_", " ").title()
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    content = content.replace("# Episode", f"# Episode: {title}", 1)
    content = content.replace("## Fecha\n\n", f"## Fecha\n\n{date.today().isoformat()}\n\n", 1)
    if plan:
        content = content.replace("## Plan asociado\n\n", f"## Plan asociado\n\n{plan}\n\n", 1)

    destination.write_text(content, encoding="utf-8")
    print(destination.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
