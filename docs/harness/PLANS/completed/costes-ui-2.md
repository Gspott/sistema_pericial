# Costes Ui 2

# Objetivo

Mejorar productividad desktop en biblioteca de costes: editar descompuestos
existentes, mantener partidas corregibles y convertir las tablas de
descompuestos en formato horizontal tipo hoja de calculo.

# Modulo

Costes de reparacion / workbench / capturas.

# Riesgo

Medio por tocar router y templates de costes, mitigado sin cambios de esquema,
sin OCR/parser/BC3 y con smoke especifico de costes.

# Archivos permitidos

- `app/routers/costes.py`
- `templates/costes/detalle.html`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_workbench.py`
- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ui-2.md`
- `docs/harness/EPISODES/*costes-ui-2*.md`

# Archivos prohibidos

- OCR/parser IVE.
- BC3.
- Patologias, actuaciones, informes, facturacion, CRM, emails y valoraciones.
- Bases SQLite reales, uploads y capturas reales.

# Playbook aplicable

Task Pack sugerido: `app_change`.

Playbook: `docs/harness/PLAYBOOKS/jinja.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir router/template/tests de costes. No hay migracion ni cambio de datos.

# Fuera de alcance

- OCR.
- Parser IVE.
- Importador BC3.
- Vinculacion con patologias/actuaciones.
- Informes o PDF.

# Aprobacion humana requerida

No prevista si se mantiene el alcance UI/rutas de costes existente.

Estado: completado
