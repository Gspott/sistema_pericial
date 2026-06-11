# Field Map V2 Fase 2

# Objetivo

Crear el mapa documental entre datos existentes del sistema y capitulos definidos en `INFORME_SCHEMA_V2`, usando el expediente `019-26` como caso piloto.

La tarea es exclusivamente documental y de analisis. No modifica codigo, base de datos, formularios, rutas, plantillas PDF, migraciones ni modelos.

# Modulo

Informes periciales / dominio pericial / harness documental.

# Riesgo

Bajo mientras se limite a documentacion. Riesgo diferido si una fase posterior implementa V2 sin preservar compatibilidad con V1, PDF/DOCX y contexto compartido.

# Archivos permitidos

- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`
- `docs/harness/PLANS/active/field-map-v2-fase-2.md`
- `docs/harness/PLANS/completed/field-map-v2-fase-2.md`
- `docs/harness/EPISODES/2026-06-06-field-map-v2-fase-2.md`
- `docs/harness/METRICS.md` si el cierre del harness lo actualiza.

# Archivos prohibidos

- Codigo Python.
- Plantillas HTML/PDF/DOCX.
- Formularios.
- Rutas.
- Migraciones.
- Modelos nuevos.
- Bases SQLite, uploads, informes generados, fotos, backups o logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/doc_change.md`.

Documentos de referencia:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`
- `docs/informes.md`
- `docs/revision_probatoria.md`
- `docs/modelos_datos.md`
- `docs/harness/PLAYBOOKS/informes.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Eliminar `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md` y revertir plan/episodio. No hay cambios de codigo ni datos.

# Fuera de alcance

- Disenar nuevas entidades.
- Disenar nuevas pantallas.
- Implementar capitulos V2.
- Cambiar informes actuales.
- Crear migraciones.
- Modificar formularios.

# Aprobacion humana requerida

Requerida para cualquier fase posterior que pase de analisis a implementacion o toque DB, rutas, formularios o plantillas.

Estado: completado
