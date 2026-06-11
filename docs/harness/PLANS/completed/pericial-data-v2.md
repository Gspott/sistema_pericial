# Pericial Data V2

# Objetivo

Definir documentalmente la informacion nueva realmente imprescindible para soportar `INFORME_SCHEMA_V2` y `PERICIAL_WORKBENCH_V2`, usando `019-26` como caso piloto.

La tarea es exclusivamente documental y de analisis de modelo conceptual. No disena tablas, columnas, relaciones, migraciones, modelos ni pantallas.

# Modulo

Dominio pericial / modelo conceptual V2 / informes.

# Riesgo

Bajo mientras se limite a documentacion. Riesgo diferido alto si se traduce a DB sin contencion, porque anadir datos permanentes aumenta carga de captura, mantenimiento y compatibilidad.

# Archivos permitidos

- `docs/harness/DOMAIN/pericial/PERICIAL_DATA_V2.md`
- `docs/harness/PLANS/active/pericial-data-v2.md`
- `docs/harness/PLANS/completed/pericial-data-v2.md`
- `docs/harness/EPISODES/2026-06-06-pericial-data-v2.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Codigo Python.
- Base de datos.
- Migraciones.
- Rutas.
- Formularios.
- Plantillas PDF/HTML.
- Modelos nuevos.
- Uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/doc_change.md`.

Documentos de referencia obligatorios:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`
- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar `docs/harness/DOMAIN/pericial/PERICIAL_DATA_V2.md` y revertir plan/episodio. No hay cambios de codigo ni datos.

# Fuera de alcance

- Disenar tablas.
- Disenar migraciones.
- Crear modelos.
- Implementar Workbench.
- Modificar informes.
- Modificar formularios.
- Crear nuevas rutas.

# Aprobacion humana requerida

Requerida para cualquier fase posterior que convierta estos datos conceptuales en esquema, UI o informe real.

Estado: completado
