# Objetivo

Crear packs operativos reutilizables para que Codex pueda abordar tareas reales sin prompts largos, eligiendo el pack adecuado segun tipo de cambio.

# Modulo

Harness operativo, seleccion de tareas, task envelopes y auditoria documental.

# Riesgo

Bajo. Cambios documentales y auditoria de existencia. No se toca logica de aplicacion ni datos reales.

# Archivos permitidos

- `docs/harness/TASK_PACKS/*`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `scripts/audit_docs.py` si el cambio es simple y seguro.
- Este plan activo.

# Archivos prohibidos

- `app/`, `templates/`, `static/`.
- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs`, `exports/`.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/templates/TASK_ENVELOPE.md`

# Validaciones

```bash
python3 scripts/audit_docs.py
bash scripts/validate_harness.sh
git diff --check
git status --short
```

# Rollback

Revertir `docs/harness/TASK_PACKS/`, cambios del manual, auditoria documental, drift docs y este plan.

# Fuera de alcance

- Logica de negocio.
- Datos reales.
- Refactors.
- Cambios funcionales.

# Aprobacion humana requerida

No prevista mientras el cambio sea solo documental/auditoria de estructura.

