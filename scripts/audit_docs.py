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
    "completado",
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
    "docs/facturacion.md",
    "docs/gastos.md",
    "docs/revision_probatoria.md",
    "docs/modelos_datos.md",
    "docs/ia_workflow.md",
    "docs/changelog.md",
}
NORMATIVE_DOCS = {
    "docs/SOURCE_OF_TRUTH.md",
    "docs/backend.md",
    "docs/modelos_datos.md",
    "docs/informes.md",
    "docs/ux.md",
    "docs/pwa.md",
    "docs/RESTORE.md",
    "docs/RECOVERY_CHECKLIST.md",
    "docs/facturacion.md",
    "docs/gastos.md",
}
HARNESS_REQUIRED_PATHS = {
    "docs/harness",
    "docs/harness/PROJECT_RULES.md",
    "docs/harness/PERMISSIONS.md",
    "docs/harness/CONTEXT_STRATEGY.md",
    "docs/harness/RISK_MAP.md",
    "docs/harness/CODEX_OPERATING_MANUAL.md",
    "docs/harness/GOLDEN_PRINCIPLES.md",
    "docs/harness/VALIDATION/minimal_checks.md",
    "docs/harness/METRICS.md",
    "docs/harness/MAINTENANCE",
    "docs/harness/MAINTENANCE/README.md",
    "docs/harness/MAINTENANCE/weekly_cleanup.md",
    "docs/harness/MAINTENANCE/monthly_review.md",
    "docs/harness/MAINTENANCE/dead_docs_policy.md",
    "docs/harness/BACKLOG",
    "docs/harness/BACKLOG/README.md",
    "docs/harness/BACKLOG/critical.md",
    "docs/harness/BACKLOG/high.md",
    "docs/harness/BACKLOG/medium.md",
    "docs/harness/BACKLOG/low.md",
    "docs/harness/BACKLOG/icebox.md",
    "docs/harness/STATE",
    "docs/harness/STATE/README.md",
    "docs/harness/STATE/current_focus.md",
    "docs/harness/STATE/current_plan.txt",
    "docs/harness/STATE/known_risks.md",
    "docs/harness/STATE/recent_changes.md",
    "docs/harness/STATE/active_constraints.md",
    "docs/harness/FAILURES",
    "docs/harness/FAILURES/README.md",
    "docs/harness/FAILURES/pwa_version_drift.md",
    "docs/harness/FAILURES/template_response_warning.md",
    "docs/harness/FAILURES/smoke_test_context_keyerror.md",
    "docs/harness/PATTERNS",
    "docs/harness/PATTERNS/README.md",
    "docs/harness/PATTERNS/safe_sqlite_migration.md",
    "docs/harness/PATTERNS/build_informe_context_extension.md",
    "docs/harness/PATTERNS/proposal_to_invoice_flow.md",
    "docs/harness/PATTERNS/mobile_partial_structure.md",
    "docs/harness/PATTERNS/backup_sandbox_pattern.md",
    "docs/harness/EPISODES",
    "docs/harness/EPISODES/README.md",
    "docs/harness/EPISODES/templates",
    "docs/harness/EPISODES/templates/EPISODE_TEMPLATE.md",
    "docs/harness/PLANS",
    "docs/harness/PLANS/active/README.md",
    "docs/harness/PLANS/completed/README.md",
    "docs/harness/PLANS/tech_debt_tracker.md",
    "docs/harness/AGENT_MAPS",
    "docs/harness/AGENT_MAPS/README.md",
    "docs/harness/AGENT_MAPS/route_map.md",
    "docs/harness/AGENT_MAPS/db_map.md",
    "docs/harness/AGENT_MAPS/critical_flows.md",
}
AGENTS_REQUIRED_LINKS = {
    "docs/harness/PROJECT_RULES.md",
    "docs/harness/PERMISSIONS.md",
    "docs/harness/CONTEXT_STRATEGY.md",
    "docs/harness/RISK_MAP.md",
    "docs/harness/CODEX_OPERATING_MANUAL.md",
    "docs/harness/GOLDEN_PRINCIPLES.md",
}
CRITICAL_PLAYBOOKS = {
    "docs/harness/PLAYBOOKS/facturacion.md",
    "docs/harness/PLAYBOOKS/propuestas.md",
    "docs/harness/PLAYBOOKS/emails.md",
    "docs/harness/PLAYBOOKS/informes.md",
    "docs/harness/PLAYBOOKS/base_datos.md",
    "docs/harness/PLAYBOOKS/jinja.md",
    "docs/harness/PLAYBOOKS/css_mobile.md",
    "docs/harness/PLAYBOOKS/deploy_acceso_remoto.md",
    "docs/harness/PLAYBOOKS/backups_restore.md",
    "docs/harness/PLAYBOOKS/secretos.md",
}
CRITICAL_GOALS = {
    "docs/harness/GOALS/activacion_comercial.md",
    "docs/harness/GOALS/estabilidad_operativa.md",
    "docs/harness/GOALS/facturacion_segura.md",
    "docs/harness/GOALS/informes_documentos.md",
    "docs/harness/GOALS/seguridad_backups.md",
    "docs/harness/GOALS/ux_movil.md",
    "docs/harness/GOALS/refactor_gradual.md",
}
CRITICAL_WORKFLOWS = {
    "docs/harness/WORKFLOWS/diff_approval.md",
    "docs/harness/WORKFLOWS/propuesta_a_factura_a_expediente.md",
}
CRITICAL_VALIDATION_DOCS = {
    "docs/harness/VALIDATION/minimal_checks.md",
    "docs/harness/VALIDATION/runner.md",
}
CRITICAL_TASK_PACKS = {
    "docs/harness/TASK_PACKS/README.md",
    "docs/harness/TASK_PACKS/bugfix.md",
    "docs/harness/TASK_PACKS/facturacion_change.md",
    "docs/harness/TASK_PACKS/informe_change.md",
    "docs/harness/TASK_PACKS/mobile_ui.md",
    "docs/harness/TASK_PACKS/safe_refactor.md",
    "docs/harness/TASK_PACKS/db_change.md",
    "docs/harness/TASK_PACKS/email_change.md",
    "docs/harness/TASK_PACKS/backup_restore_change.md",
}
TASK_PACK_SOURCE_LINKS = {
    "docs/harness/TASK_PACKS/bugfix.md": "docs/SOURCE_OF_TRUTH.md",
    "docs/harness/TASK_PACKS/facturacion_change.md": "docs/facturacion.md",
    "docs/harness/TASK_PACKS/informe_change.md": "docs/informes.md",
    "docs/harness/TASK_PACKS/mobile_ui.md": "docs/ux.md",
    "docs/harness/TASK_PACKS/safe_refactor.md": "docs/SOURCE_OF_TRUTH.md",
    "docs/harness/TASK_PACKS/db_change.md": "docs/modelos_datos.md",
    "docs/harness/TASK_PACKS/email_change.md": "docs/backend.md",
    "docs/harness/TASK_PACKS/backup_restore_change.md": "docs/RESTORE.md",
}
MAIN_MONOLITH_WARNING_LINES = 8000
ACTIVE_PLAN_CLOSED_PATTERNS = [
    re.compile(r"^estado:\s*(cerrado|completado|completed|validado)\s*$", re.MULTILINE),
    re.compile(r"\btarea cerrada\b"),
    re.compile(r"\bvalidaciones (pasan|pasaron)\b"),
    re.compile(r"\bvalidado y cerrado\b"),
]


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


def check_harness_contract(errors: list[str]) -> None:
    required_paths = (
        HARNESS_REQUIRED_PATHS
        | CRITICAL_PLAYBOOKS
        | CRITICAL_GOALS
        | CRITICAL_WORKFLOWS
        | CRITICAL_VALIDATION_DOCS
        | CRITICAL_TASK_PACKS
    )
    for rel in sorted(required_paths):
        if not (ROOT / rel).exists():
            errors.append(f"Ruta harness requerida inexistente: {rel}")


def check_normative_docs(errors: list[str]) -> None:
    for rel in sorted(NORMATIVE_DOCS):
        if not (ROOT / rel).exists():
            errors.append(f"Documento normativo requerido inexistente: {rel}")


def check_task_pack_source_links(errors: list[str]) -> None:
    for pack_rel, source_rel in sorted(TASK_PACK_SOURCE_LINKS.items()):
        pack = ROOT / pack_rel
        if not pack.exists():
            continue
        text = pack.read_text(encoding="utf-8")
        if source_rel not in text and Path(source_rel).name not in text:
            errors.append(f"Task Pack sin enlace a fuente normativa {source_rel}: {pack_rel}")


def check_agents_harness_links(errors: list[str]) -> None:
    agents = ROOT / "AGENTS.md"
    if not agents.exists():
        errors.append("Falta AGENTS.md")
        return
    text = agents.read_text(encoding="utf-8")
    for rel in sorted(AGENTS_REQUIRED_LINKS):
        if rel not in text:
            errors.append(f"AGENTS.md no enlaza harness requerido: {rel}")


def check_tests_contract(errors: list[str]) -> None:
    if not (ROOT / "pytest.ini").exists():
        errors.append("Falta pytest.ini para smoke tests")
    if not (ROOT / "tests" / "smoke").is_dir():
        errors.append("Falta tests/smoke/")

    runner = ROOT / "scripts" / "validate_harness.sh"
    if not runner.exists():
        errors.append("Falta scripts/validate_harness.sh")
        return
    runner_text = runner.read_text(encoding="utf-8")
    if "tests/smoke" not in runner_text:
        errors.append("validate_harness.sh no referencia tests/smoke")


def check_pwa_version_drift(warnings: list[str]) -> None:
    pwa_path = ROOT / "static" / "pwa.js"
    sw_path = ROOT / "static" / "sw.js"
    if not pwa_path.exists() or not sw_path.exists():
        warnings.append("No se puede comprobar drift PWA: falta static/pwa.js o static/sw.js")
        return

    pwa_text = pwa_path.read_text(encoding="utf-8")
    sw_text = sw_path.read_text(encoding="utf-8")
    pwa_match = re.search(r"/sw\.js\?v=(\d+)", pwa_text)
    cache_match = re.search(r"CACHE_NAME\s*=\s*[\"'][^\"']*v(\d+)[\"']", sw_text)

    if not pwa_match or not cache_match:
        warnings.append("No se puede comprobar drift PWA: version de registro o cache no reconocida")
        return

    pwa_version = pwa_match.group(1)
    cache_version = cache_match.group(1)
    if pwa_version != cache_version:
        warnings.append(
            "Drift PWA: static/pwa.js registra service worker "
            f"v={pwa_version}, pero static/sw.js usa cache v{cache_version}"
        )


def check_monolith_size(warnings: list[str]) -> None:
    main_path = ROOT / "app" / "main.py"
    if not main_path.exists():
        return
    line_count = len(main_path.read_text(encoding="utf-8").splitlines())
    if line_count > MAIN_MONOLITH_WARNING_LINES:
        warnings.append(
            f"Monolito estructural: app/main.py tiene {line_count} lineas "
            f"(umbral informativo {MAIN_MONOLITH_WARNING_LINES})"
        )


def check_active_plan_drift(warnings: list[str]) -> None:
    active_dir = ROOT / "docs" / "harness" / "PLANS" / "active"
    if not active_dir.exists():
        return

    for path in sorted(active_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8").lower()
        if any(pattern.search(text) for pattern in ACTIVE_PLAN_CLOSED_PATTERNS):
            warnings.append(
                "Plan activo parece cerrado/completado/validado: "
                f"{relative(path)}"
            )


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
    warnings: list[str] = []
    files = markdown_files()

    check_empty(files, errors)
    check_titles(files, errors)
    check_agents_sync(errors)
    check_duplicate_decision_ids(files, errors)
    check_markdown_links(files, errors)
    check_decision_metadata(files, errors)
    check_adr_required_fields(errors)
    check_thematic_contracts(errors)
    check_harness_contract(errors)
    check_normative_docs(errors)
    check_task_pack_source_links(errors)
    check_agents_harness_links(errors)
    check_tests_contract(errors)
    check_adr_readme(errors)
    check_known_drifts(files, errors)
    check_pwa_version_drift(warnings)
    check_monolith_size(warnings)
    check_active_plan_drift(warnings)

    print("Auditoria documental")
    print(f"- Markdown revisados: {len(files)}")

    if warnings:
        print("- Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("- Estado: ERROR")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("- Estado: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
