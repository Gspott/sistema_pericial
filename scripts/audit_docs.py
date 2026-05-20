#!/usr/bin/env python3
"""Auditoria documental no invasiva para Sistema Pericial."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROL = "rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca"
OBSOLETE_SW_VERSION = "/sw.js?v=" + "4"
ALLOWED_STATES = {
    "Proposed",
    "Active",
    "Experimental",
    "Deprecated",
    "Replaced",
    "Legacy",
    "Pending validation",
}
ALLOWED_CATEGORIES = {
    "UX",
    "PWA",
    "Datos",
    "Informes",
    "Revisión probatoria",
    "Backend",
    "Operaciones",
    "IA workflow",
    "Documentación",
}
ADR_REQUIRED_FIELDS = [
    "Decision ID",
    "Estado",
    "Categoria",
    "Categoría",
    "Fecha/periodo",
    "Fuente normativa",
]
THEMATIC_DOCS = {
    "docs/ux.md",
    "docs/pwa.md",
    "docs/informes.md",
    "docs/backend.md",
    "docs/revision_probatoria.md",
    "docs/modelos_datos.md",
    "docs/ia_workflow.md",
    "docs/changelog.md",
}


def markdown_files() -> list[Path]:
    files = [ROOT / "AGENTS.md", ROOT / "agents.md"]
    files.extend(sorted((ROOT / "docs").rglob("*.md")))
    return [path for path in files if path.exists()]


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def check_empty(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if not path.read_text(encoding="utf-8").strip():
            errors.append(f"Documento vacio: {relative(path)}")


def check_titles(files: list[Path], errors: list[str]) -> None:
    for path in files:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"^#\s+\S+", text, flags=re.MULTILINE):
            errors.append(f"Documento sin titulo principal '#': {relative(path)}")


def check_agents_sync(errors: list[str]) -> None:
    agents = ROOT / "AGENTS.md"
    alias = ROOT / "agents.md"
    if not agents.exists() and not alias.exists():
        errors.append("Falta AGENTS.md o agents.md")


def check_duplicate_decision_ids(files: list[Path], errors: list[str]) -> None:
    ids: dict[str, list[str]] = {}
    for path in files:
        rel = relative(path)
        if rel == "docs/changelog.md" or rel.startswith("docs/adr/"):
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"Decision ID:\s*([A-Z]+-\d{3})", text):
            ids.setdefault(match.group(1), []).append(f"{rel}:{text[:match.start()].count(chr(10)) + 1}")
    for decision_id, locations in sorted(ids.items()):
        if len(locations) > 1:
            errors.append(f"Decision ID duplicado fuera de ADR/changelog: {decision_id} -> {', '.join(locations)}")


def check_markdown_links(files: list[Path], errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]+)?\)")
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            target_raw = match.group(1)
            if "://" in target_raw:
                continue
            target = Path(target_raw)
            resolved = (ROOT / target if target_raw.startswith("docs/") or target_raw in {"AGENTS.md", "agents.md"} else path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"Referencia fuera del repo en {relative(path)}: {target_raw}")
                continue
            if not resolved.exists():
                errors.append(f"Referencia rota en {relative(path)}: {target_raw}")


def check_decision_metadata(files: list[Path], errors: list[str]) -> None:
    for path in files:
        text = path.read_text(encoding="utf-8")
        rel = relative(path)

        for match in re.finditer(r"^Estado:[ \t]*(.+)$", text, flags=re.MULTILINE):
            state = match.group(1).strip()
            if "|" in state or state.startswith("<"):
                continue
            if state not in ALLOWED_STATES:
                line = text[: match.start()].count("\n") + 1
                errors.append(f"Estado de decision no permitido en {rel}:{line}: {state}")

        for match in re.finditer(r"^Categor[ií]a:[ \t]*(.+)$", text, flags=re.MULTILINE):
            category = match.group(1).strip()
            if "|" in category or category.startswith("<"):
                continue
            if category not in ALLOWED_CATEGORIES:
                line = text[: match.start()].count("\n") + 1
                errors.append(f"Categoria de decision no permitida en {rel}:{line}: {category}")


def check_adr_required_fields(errors: list[str]) -> None:
    adr_dir = ROOT / "docs" / "adr"
    if not adr_dir.exists():
        errors.append("Falta docs/adr/")
        return

    for path in sorted(adr_dir.glob("ADR-*.md")):
        text = path.read_text(encoding="utf-8")
        for field in ["Decision ID", "Estado", "Fecha/periodo", "Fuente normativa"]:
            if not re.search(rf"^{re.escape(field)}:\s*\S+", text, flags=re.MULTILINE):
                errors.append(f"ADR sin campo obligatorio {field}: {relative(path)}")
        if not re.search(r"^Categor[ií]a:\s*\S+", text, flags=re.MULTILINE):
            errors.append(f"ADR sin campo obligatorio Categoria/Categoría: {relative(path)}")


def check_thematic_contracts(errors: list[str]) -> None:
    for rel in sorted(THEMATIC_DOCS):
        path = ROOT / rel
        if not path.exists():
            errors.append(f"Documento tematico inexistente: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if "## Dependencias" not in text:
            errors.append(f"Documento tematico sin ## Dependencias: {rel}")
        if "Puede impactar:" not in text:
            errors.append(f"Documento tematico sin Puede impactar: {rel}")


def check_adr_readme(errors: list[str]) -> None:
    adr_dir = ROOT / "docs" / "adr"
    readme = adr_dir / "README.md"
    if not readme.exists():
        errors.append("Falta docs/adr/README.md")
        return
    readme_text = readme.read_text(encoding="utf-8")
    for path in sorted(adr_dir.glob("ADR-*.md")):
        if path.name not in readme_text:
            errors.append(f"ADR no referenciada en docs/adr/README.md: {path.name}")


def check_known_drifts(files: list[Path], errors: list[str]) -> None:
    no_api_unqualified = re.compile(r"\b[Nn]o crear APIs(?! de negocio paralelas)")
    canonical_compact = re.sub(r"[\s`]", "", CANONICAL_ROL)
    for path in files:
        rel = relative(path)
        text = path.read_text(encoding="utf-8")
        if OBSOLETE_SW_VERSION in text:
            errors.append(f"Version PWA hardcodeada obsoleta en {rel}")
        for line_number, line in enumerate(text.splitlines(), start=1):
            line_compact = re.sub(r"[\s`]", "", line)
            if "rol_final=" in line_compact and canonical_compact not in line_compact:
                errors.append(f"Formula alternativa de rol_final en {rel}:{line_number}")
        for match in no_api_unqualified.finditer(text):
            errors.append(f"Regla API sin matiz de negocio paralelas en {rel}:{text[:match.start()].count(chr(10)) + 1}")
        if "node --check static/app_shell.js" in text:
            errors.append(f"Validacion JS limitada a static/app_shell.js en {rel}")


def main() -> int:
    errors: list[str] = []
    files = markdown_files()

    check_empty(files, errors)
    check_titles(files, errors)
    check_agents_sync(errors)
    check_duplicate_decision_ids(files, errors)
    check_markdown_links(files, errors)
    check_decision_metadata(files, errors)
    check_adr_required_fields(errors)
    check_thematic_contracts(errors)
    check_adr_readme(errors)
    check_known_drifts(files, errors)

    print("Auditoria documental")
    print(f"- Markdown revisados: {len(files)}")

    if errors:
        print("- Estado: ERROR")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("- Estado: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
