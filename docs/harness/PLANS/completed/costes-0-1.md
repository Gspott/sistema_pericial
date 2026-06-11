# Costes 0 1

# Objetivo

Implementar COSTES-0 y COSTES-1: inspeccion de patrones reales, documento de
diseno minimo y esquema SQLite inicial para base propia de costes de reparacion
inspirada en BC3/FIEBDC.

# Modulo

Base de datos / harness / smoke tests.

# Riesgo

Critico por cambio de esquema, mitigado con tablas nuevas, migracion
idempotente y validacion sobre DB temporal.

# Archivos permitidos

- `app/database.py`
- `tests/smoke/test_costes_db.py`
- `docs/harness/costes_0_1.md`
- este plan activo

# Archivos prohibidos

- DB real y cualquier SQLite versionado/no versionado.
- Backups, uploads, informes, fotos y logs.
- Patologias, expedientes, inspecciones, valoraciones, CRM, emails,
  facturacion, routers y navegacion global.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

Playbook: `docs/harness/PLAYBOOKS/base_datos.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `pytest tests/smoke/test_costes_db.py -q`
- `python3 -m compileall app`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir diff de `app/database.py`, test y documento. Descartar DB temporal de
pytest. No aplica restauracion de DB real porque no se toca.

# Fuera de alcance

- OCR.
- Importador BC3/FIEBDC.
- Conexion con patologias.
- Workbench escritorio.
- Rutas, templates o navegacion.
- Facturacion, CRM, emails, expedientes, inspecciones y valoraciones.

# Aprobacion humana requerida

No requerida para esta implementacion porque solo crea tablas nuevas
idempotentes y tests sandbox. Requerida en fases futuras si se conectan costes
con patologias/informes o se toca DB real.

Estado: completado
