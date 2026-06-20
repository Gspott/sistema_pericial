# Timezone Standard Implementation 1

# Objetivo

Implementar un primer estandar transversal de zona horaria para evitar que
timestamps UTC de SQLite (`CURRENT_TIMESTAMP`) se muestren con desfase respecto
a Europe/Madrid.

Primer corte: utilidad central, filtro Jinja, visualizacion de timestamps
crudos en pantallas criticas y sustitucion acotada de `datetime.now()`/`date.today()`
en puntos no fiscales de CRM, dashboard e informes.

# Modulo

Backend/Jinja/servicios compartidos. Impacta visualizacion de registros, emails,
dashboard, CRM e informes. No cambia esquema ni migra datos.

# Riesgo

Medio-alto por alcance transversal. Se limita a helpers, formato de salida y
timestamps no fiscales. No se modifican numeracion, emision, anulaciones,
backups reales, autenticacion ni DB real.

# Archivos permitidos

- `app/utils/timezone.py`
- `app/main.py`
- `app/routers/dashboard.py`
- `app/routers/crm.py`
- `app/services/crm_scheduled.py`
- `app/services/informe.py`
- Templates con timestamps crudos seleccionados
- `tests/smoke/`
- Este plan y episodio harness

# Archivos prohibidos

- Bases SQLite reales
- Backups, uploads, informes generados, fotos, logs y secretos
- Cambios de esquema o migraciones de datos historicos
- Emision/numeracion/rectificativas/anulaciones de facturacion
- Autenticacion, deploy, service worker

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

Documentos consultados: auditoria transversal completada, `PROJECT_RULES`,
`PERMISSIONS`, `RISK_MAP`, `SOURCE_OF_TRUTH`, `backend.md`, `informes.md` y
`VALIDATION/minimal_checks`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- Smoke especifico de timezone
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`
- `git status --short`

# Rollback

Revertir helper, imports, filtros, templates y tests de timezone. No hay datos
ni migraciones que revertir.

# Fuera de alcance

- Migrar masivamente timestamps historicos.
- Cambiar defaults `CURRENT_TIMESTAMP` en schema existente.
- Cambiar comportamiento fiscal de facturas/propuestas.
- Enviar emails reales.
- Cambiar frontend PWA/service worker.

# Aprobacion humana requerida

Requerida antes de tocar facturacion fiscal, backups reales, autenticacion,
DB real, migraciones historicas o envios externos reales.

Estado: completado
