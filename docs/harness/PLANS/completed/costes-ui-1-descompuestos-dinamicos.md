# Costes Ui 1 Descompuestos Dinamicos

# Objetivo

Implementar COSTES-UI-1: permitir añadir y eliminar filas de descompuestos en la revisión manual de capturas de costes.

# Modulo

Costes / capturas / revisión manual.

# Riesgo

Bajo. Cambio acotado al formulario de revisión y al filtrado de filas vacías; no toca OCR ni parser.

# Archivos permitidos

- `app/routers/costes.py`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ui-1-descompuestos-dinamicos.md`
- `docs/harness/EPISODES/2026-06-06-costes-ui-1-descompuestos-dinamicos.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR y parser IVE.
- Importador BC3.
- Informes, actuaciones, patologías, facturación, CRM, emails y valoraciones.
- Datos reales, uploads, informes generados, backups, fotos y logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay migración ni cambios de esquema.

# Fuera de alcance

- Mejorar OCR.
- Cambiar parser IVE o parser genérico.
- Cambiar importación BC3.
- Validar automáticamente partidas.
- Tocar informes, patologías, actuaciones o facturación.

# Aprobacion humana requerida

Si se quisiera tocar OCR/parser, datos reales o módulos fuera de costes.

# Decisión

El formulario mantiene nombres de campos tipo lista (`descomp_codigo`, `descomp_tipo`, etc.) y usa JavaScript mínimo para añadir/quitar filas. El backend ignora filas sin código, unidad, resumen ni valores económicos aunque conserven `tipo=material`.

Estado: completado
