# Pericial Wb 1

# Objetivo

Implementar el primer Workbench pericial SSR de escritorio, solo lectura/diagnostico, para expedientes de patologias.

# Modulo

Modulo pericial / expedientes / patologias / escritorio.

# Riesgo

Medio. Se toca `app/main.py` y `templates/detalle_expediente.html`, pero sin modificar DB, migraciones, PDF, captura mobile, costes ni patologias. La ruta nueva debe ser secundaria y reversible.

# Archivos permitidos

- `app/main.py`
- `templates/detalle_expediente.html`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-wb-1.md`
- `docs/harness/PLANS/completed/pericial-wb-1.md`
- `docs/harness/EPISODES/2026-06-06-pericial-wb-1.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Base de datos.
- Migraciones.
- Nuevas tablas o campos.
- Plantillas PDF/DOCX.
- Logica de captura de patologias.
- Logica de costes.
- Datos reales, uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.

Referencias:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_DATA_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_IMPLEMENTATION_PLAN_V2.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `python3 -m pytest` si esta disponible.
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar ruta/helper de Workbench en `app/main.py`, eliminar enlace en `templates/detalle_expediente.html`, eliminar `templates/pericial_workbench.html` y el test smoke asociado.

# Fuera de alcance

- Persistir datos V2.
- Editar metodologia/limitaciones desde el Workbench.
- Crear nuevas entidades.
- Cambiar informe PDF/DOCX.
- Sustituir detalle de expediente.
- Cambiar flujos mobile-first.

# Aprobacion humana requerida

No requerida para esta implementacion acotada. Requerida para fases posteriores con DB, informes o edicion persistente.

Estado: completado
