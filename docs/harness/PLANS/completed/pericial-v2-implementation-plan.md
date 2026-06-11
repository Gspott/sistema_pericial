# Pericial V2 Implementation Plan

# Objetivo

Generar un plan tecnico detallado de implementacion por fases para un primer Workbench pericial V2 de escritorio operativo, sin implementar nada.

# Modulo

Dominio pericial / Workbench escritorio / plan tecnico.

# Riesgo

Bajo mientras se mantenga documental. Riesgo alto si se pasa a implementacion tocando informes, DB o mobile-first sin fases separadas.

# Archivos permitidos

- `docs/harness/DOMAIN/pericial/PERICIAL_IMPLEMENTATION_PLAN_V2.md`
- `docs/harness/PLANS/active/pericial-v2-implementation-plan.md`
- `docs/harness/PLANS/completed/pericial-v2-implementation-plan.md`
- `docs/harness/EPISODES/2026-06-06-pericial-v2-implementation-plan.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Codigo Python.
- Base de datos.
- Migraciones.
- Rutas reales.
- Formularios.
- Plantillas PDF/HTML.
- Modelos nuevos.
- Uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/doc_change.md`.

Referencias:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_DATA_V2.md`
- `docs/ux.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar el documento de plan tecnico y revertir plan/episodio. No hay cambios de codigo ni datos.

# Fuera de alcance

- Implementar Workbench.
- Crear rutas.
- Crear plantillas.
- Crear migraciones.
- Modificar DB.
- Modificar informe PDF/DOCX.
- Cambiar formularios.

# Aprobacion humana requerida

Requerida para ejecutar cualquier fase de implementacion real posterior.

Estado: completado
