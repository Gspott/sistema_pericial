# Pericial Editor 1

# Objetivo

Implementar un editor SSR de escritorio para informe pericial V2, con capitulos
estructurados, precarga desde borradores PERICIAL-WB-2 y persistencia minima de
textos editados.

# Modulo

Pericial / expedientes / base de datos / editor SSR.

# Riesgo

Alto por crear tabla nueva e integrar rutas de expediente, mitigado con tabla
idempotente, sin tocar PDF/DOCX, sin modificar patologias/costes/fotos y con
tests en DB temporal.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `templates/pericial_workbench.html`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-editor-1.md`
- `docs/harness/EPISODES/*pericial-editor-1*.md`

# Archivos prohibidos

- Bases SQLite reales.
- Informes generados reales, uploads y fotos.
- `templates/informes/imprimir.html`.
- `app/services/informe.py`.
- Modulos de facturacion, CRM, emails, costes, patologias, visitas y valoracion.

# Playbook aplicable

Task Pack sugerido: `db_change`.

Playbooks: `base_datos.md` e `informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir la tabla idempotente, rutas/helpers, plantilla nueva, enlace y tests.
No hay migracion destructiva ni modificaciones de PDF.

# Fuera de alcance

- Exportacion PDF V2.
- Cambiar generacion PDF actual.
- Crear nuevas entidades fuera de capitulos V2.
- Editar patologias, visitas, fotos, costes o actuaciones.
- Usar IA, LLM o servicios externos.

# Aprobacion humana requerida

No prevista si la tabla es idempotente, no destructiva y se valida sobre DB
temporal.

Estado: completado
