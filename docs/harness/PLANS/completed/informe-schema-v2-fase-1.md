# Informe Schema V2 Fase 1

# Objetivo

Definir documentalmente `INFORME_SCHEMA_V2` como fuente de verdad futura del modulo pericial, usando el expediente real `019-26` como caso piloto.

La tarea es exclusivamente documental y de analisis: no modifica codigo, rutas, base de datos, migraciones ni plantillas PDF.

# Modulo

Informes periciales / dominio pericial / harness documental.

# Riesgo

Bajo si se mantiene como documentacion. Riesgo alto diferido si se implementa sin versionado, porque informes PDF/DOCX y contexto compartido son modulos criticos.

# Archivos permitidos

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/harness/PLANS/active/informe-schema-v2-fase-1.md`
- `docs/harness/PLANS/completed/informe-schema-v2-fase-1.md`
- `docs/harness/EPISODES/2026-06-06-informe-schema-v2-fase-1.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Codigo Python.
- Plantillas HTML/PDF/DOCX.
- Rutas.
- Migraciones o inicializacion de base de datos.
- Bases SQLite, uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/doc_change.md`.

Playbooks/documentos leidos:

- `docs/harness/PROJECT_RULES.md`
- `docs/harness/PERMISSIONS.md`
- `docs/harness/CONTEXT_STRATEGY.md`
- `docs/harness/RISK_MAP.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/GOLDEN_PRINCIPLES.md`
- `docs/harness/PLAYBOOKS/informes.md`
- `docs/informes.md`
- `docs/revision_probatoria.md`
- `docs/modelos_datos.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md` y revertir este plan/episodio. No hay cambios de datos ni codigo.

# Fuera de alcance

- Implementar `INFORME_SCHEMA_V2`.
- Modificar `build_informe_context()`.
- Modificar `templates/informes/imprimir.html`.
- Cambiar generacion PDF/DOCX.
- Crear campos, tablas o migraciones.
- Leer o modificar informes generados o fotografias reales.

# Aprobacion humana requerida

Requerida para cualquier fase posterior de implementacion que toque informes, DB, rutas o plantillas. No requerida para esta definicion documental.

Estado: completado
