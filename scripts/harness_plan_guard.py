#!/usr/bin/env python3
"""Validate harness plan artifacts before they become historical records."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = (
    "Objetivo",
    "Modulo",
    "Riesgo",
    "Validaciones",
    "Rollback",
    "Fuera de alcance",
    "Aprobacion humana requerida",
)
SUSPICIOUS_COMPLETED_SUFFIXES = (
    "-duplicate-plan.md",
    "-duplicate.md",
    "-revalidation.md",
)


@dataclass(frozen=True)
class PlanQuality:
    path: Path
    template_shaped: bool
    empty_sections: tuple[str, ...]
    missing_sections: tuple[str, ...]

    @property
    def is_empty_template(self) -> bool:
        return self.template_shaped and bool(self.empty_sections)


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _section_body(text: str, heading: str) -> str | None:
    marker = f"# {heading}"
    start = text.find(marker)
    if start < 0:
        return None
    body_start = start + len(marker)
    next_heading = text.find("\n# ", body_start)
    body = text[body_start : next_heading if next_heading >= 0 else len(text)]
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped == "Estado: completado":
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def analyze_plan(path: Path) -> PlanQuality:
    text = path.read_text(encoding="utf-8")
    missing = []
    empty = []
    for section in REQUIRED_SECTIONS:
        body = _section_body(text, section)
        if body is None:
            missing.append(section)
        elif not body:
            empty.append(section)
    return PlanQuality(
        path=path,
        template_shaped=not missing,
        empty_sections=tuple(empty),
        missing_sections=tuple(missing),
    )


def validate_plan_for_close(path: Path) -> list[str]:
    quality = analyze_plan(path)
    if not quality.template_shaped:
        return []
    if not quality.empty_sections:
        return []
    sections = ", ".join(quality.empty_sections)
    return [
        (
            f"Plan sin contenido real: {relative(path)}. "
            f"Completa estas secciones antes de cerrar: {sections}."
        )
    ]


def audit_completed_plan_quality(completed_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not completed_dir.exists():
        return errors, warnings

    for path in sorted(completed_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        quality = analyze_plan(path)
        if not quality.is_empty_template:
            continue
        sections = ", ".join(quality.empty_sections)
        message = (
            f"Plan completado sin contenido real: {relative(path)} "
            f"(secciones vacias: {sections})"
        )
        if path.name.endswith(SUSPICIOUS_COMPLETED_SUFFIXES):
            errors.append(message)
        else:
            warnings.append(message)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate harness plan quality.")
    parser.add_argument("plan", help="Plan path to validate.")
    args = parser.parse_args()

    path = Path(args.plan)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        print(f"[FAIL] Plan no encontrado: {relative(path)}", file=sys.stderr)
        return 1

    errors = validate_plan_for_close(path)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print(f"[OK] Plan con contenido suficiente: {relative(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
