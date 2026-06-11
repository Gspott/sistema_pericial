# Pericial Workbench V2

# Objetivo

Definir documentalmente el futuro Workbench V2 de escritorio para redaccion y analisis de informes periciales complejos, usando `019-26` como caso piloto.

La tarea es exclusivamente documental y de analisis UX. No implementa funcionalidades, no disena tablas, no crea modelos y no modifica codigo, DB, rutas ni plantillas PDF.

# Modulo

Dominio pericial / UX escritorio / informes V2.

# Riesgo

Bajo mientras se mantenga en documentacion. Riesgo diferido si se implementa como formulario gigante o si sustituye flujos mobile-first existentes.

# Archivos permitidos

- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`
- `docs/harness/PLANS/active/pericial-workbench-v2.md`
- `docs/harness/PLANS/completed/pericial-workbench-v2.md`
- `docs/harness/EPISODES/2026-06-06-pericial-workbench-v2.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Codigo Python.
- Base de datos.
- Migraciones.
- Rutas.
- Plantillas PDF/HTML.
- Formularios.
- Modelos nuevos.
- Uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/doc_change.md`.

Documentos de referencia obligatorios:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`

Documentos/pantallas consultados:

- `docs/ux.md`
- `templates/detalle_expediente.html`
- `templates/actuaciones_reparacion.html`
- `templates/presupuesto_reparacion.html`
- `templates/informes/imprimir.html`
- `templates/valoracion_workbench.html`

# Validaciones

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md` y revertir plan/episodio. No hay cambios de codigo ni datos.

# Fuera de alcance

- Implementar Workbench.
- Crear rutas.
- Modificar formularios.
- Disenar DB.
- Crear modelos.
- Cambiar informe PDF/DOCX.
- Crear wireframes visuales definitivos.

# Aprobacion humana requerida

Requerida para cualquier fase posterior de implementacion o cambios de UI real.

Estado: completado
