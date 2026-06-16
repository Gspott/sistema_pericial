from pathlib import Path

from scripts.harness_plan_guard import (
    audit_completed_plan_quality,
    validate_plan_for_close,
)


PLAN_TEMPLATE = """# Plan Demo

# Objetivo
{objetivo}

# Modulo
{modulo}

# Riesgo
{riesgo}

# Archivos permitidos

# Archivos prohibidos

# Playbook aplicable

# Validaciones
{validaciones}

# Rollback
{rollback}

# Fuera de alcance
{fuera}

# Aprobacion humana requerida
{aprobacion}
"""


def _write_plan(path: Path, **values) -> Path:
    defaults = {
        "objetivo": "",
        "modulo": "",
        "riesgo": "",
        "validaciones": "",
        "rollback": "",
        "fuera": "",
        "aprobacion": "",
    }
    defaults.update(values)
    path.write_text(PLAN_TEMPLATE.format(**defaults), encoding="utf-8")
    return path


def test_plan_guard_rechaza_plantilla_vacia(tmp_path):
    plan = _write_plan(tmp_path / "empty.md")

    errors = validate_plan_for_close(plan)

    assert errors
    assert "Plan sin contenido real" in errors[0]
    assert "Objetivo" in errors[0]


def test_plan_guard_acepta_plan_con_contenido(tmp_path):
    plan = _write_plan(
        tmp_path / "valid.md",
        objetivo="Probar guard de planes.",
        modulo="Harness.",
        riesgo="Medio.",
        validaciones="- pytest tests/smoke/test_harness_plan_guard.py",
        rollback="Revertir cambios del guard.",
        fuera="- Codigo funcional.",
        aprobacion="No requerida.",
    )

    assert validate_plan_for_close(plan) == []


def test_audit_completed_error_en_revalidation_vacia(tmp_path):
    completed = tmp_path / "completed"
    completed.mkdir()
    _write_plan(completed / "demo-revalidation.md")
    _write_plan(
        completed / "demo-valid.md",
        objetivo="Plan util.",
        modulo="Harness.",
        riesgo="Medio.",
        validaciones="- audit_docs",
        rollback="Revertir.",
        fuera="- App.",
        aprobacion="No requerida.",
    )

    errors, warnings = audit_completed_plan_quality(completed)

    assert len(errors) == 1
    assert "demo-revalidation.md" in errors[0]
    assert warnings == []
