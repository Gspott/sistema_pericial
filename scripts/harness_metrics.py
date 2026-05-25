#!/usr/bin/env python3
"""Generate mechanical harness metrics without reading real data."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "docs" / "harness" / "METRICS.md"
GENERATED_HEADING = "## Métricas generadas"
MAIN_MONOLITH_WARNING_LINES = 8000


def count_markdown_files(path: Path, exclude_readme: bool = True) -> int:
    if not path.exists():
        return 0
    return sum(
        1
        for item in path.glob("*.md")
        if item.is_file() and not (exclude_readme and item.name == "README.md")
    )


def count_smoke_tests() -> int:
    smoke_dir = ROOT / "tests" / "smoke"
    if not smoke_dir.exists():
        return 0

    total = 0
    for path in sorted(smoke_dir.glob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                total += test_case_count(node)
    return total


def test_case_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    count = 1
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        is_parametrize = (
            isinstance(func, ast.Attribute)
            and func.attr == "parametrize"
        )
        if not is_parametrize or len(decorator.args) < 2:
            continue
        values = decorator.args[1]
        if isinstance(values, (ast.List, ast.Tuple)):
            count *= max(1, len(values.elts))
    return count


def pwa_warning() -> str:
    pwa_path = ROOT / "static" / "pwa.js"
    sw_path = ROOT / "static" / "sw.js"
    if not pwa_path.exists() or not sw_path.exists():
        return "WARNING: no se puede comprobar PWA"

    pwa_text = pwa_path.read_text(encoding="utf-8")
    sw_text = sw_path.read_text(encoding="utf-8")
    pwa_match = re.search(r"/sw\.js\?v=(\d+)", pwa_text)
    cache_match = re.search(r"CACHE_NAME\s*=\s*[\"'][^\"']*v(\d+)[\"']", sw_text)
    if not pwa_match or not cache_match:
        return "WARNING: version PWA no reconocida"
    if pwa_match.group(1) != cache_match.group(1):
        return f"WARNING: drift PWA v={pwa_match.group(1)} vs v{cache_match.group(1)}"
    return "OK"


def main_warning() -> str:
    main_path = ROOT / "app" / "main.py"
    if not main_path.exists():
        return "OK"
    line_count = len(main_path.read_text(encoding="utf-8").splitlines())
    if line_count > MAIN_MONOLITH_WARNING_LINES:
        return f"WARNING: app/main.py tiene {line_count} lineas"
    return "OK"


def generated_section() -> str:
    active_dir = ROOT / "docs" / "harness" / "PLANS" / "active"
    completed_dir = ROOT / "docs" / "harness" / "PLANS" / "completed"
    failures_dir = ROOT / "docs" / "harness" / "FAILURES"
    patterns_dir = ROOT / "docs" / "harness" / "PATTERNS"
    task_packs_dir = ROOT / "docs" / "harness" / "TASK_PACKS"
    episodes_dir = ROOT / "docs" / "harness" / "EPISODES"

    rows = [
        ("Smoke tests", str(count_smoke_tests())),
        ("Planes activos", str(count_markdown_files(active_dir))),
        ("Planes completados", str(count_markdown_files(completed_dir))),
        ("Failures documentados", str(count_markdown_files(failures_dir))),
        ("Patterns reutilizables", str(count_markdown_files(patterns_dir))),
        ("Task Packs", str(count_markdown_files(task_packs_dir))),
        ("Episodios", str(count_markdown_files(episodes_dir))),
        ("Warning monolito", main_warning()),
        ("Warning PWA", pwa_warning()),
    ]
    table = ["| Metrica | Valor |", "|---|---|"]
    table.extend(f"| {name} | {value} |" for name, value in rows)
    return GENERATED_HEADING + "\n\n" + "\n".join(table) + "\n"


def update_metrics() -> None:
    if METRICS_PATH.exists():
        text = METRICS_PATH.read_text(encoding="utf-8")
    else:
        text = "# Harness Metrics\n\n"

    section = generated_section()
    if GENERATED_HEADING in text:
        prefix = text.split(GENERATED_HEADING, 1)[0].rstrip()
        text = prefix + "\n\n" + section
    else:
        text = text.rstrip() + "\n\n" + section

    METRICS_PATH.write_text(text, encoding="utf-8")
    print(METRICS_PATH.relative_to(ROOT))


if __name__ == "__main__":
    update_metrics()
