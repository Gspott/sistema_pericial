# Valoracion Task Pack

# Objetivo

Crear un task pack especifico para cambios de valoracion inmobiliaria que
reduzca prompts futuros y consolide reglas de seguridad, modelo nuevo,
fallback legacy, testigos reutilizables, snapshots, ajustes, demo cases,
smokes y QA visual.

# Modulo

Harness, documentacion operativa y valoracion inmobiliaria.

# Riesgo

Bajo. Cambio documental del harness. No toca app, templates, DB, datos ni
uploads.

# Archivos permitidos

- `docs/harness/TASK_PACKS/valoracion_change.md`
- `docs/harness/TASK_PACKS/README.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `AGENTS.md`
- `agents.md` si requiere sincronizacion

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- DB real, datos reales, uploads, informes, backups y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/docs_change.md`.

Nota: `docs_change.md` no existe como task pack canonico; la fase crea el pack
especifico `docs/harness/TASK_PACKS/valoracion_change.md` y actualiza indices
para usarlo en fases futuras.

# Cambios ejecutados

- Creado `docs/harness/TASK_PACKS/valoracion_change.md`.
- Actualizado `docs/harness/TASK_PACKS/README.md` para priorizarlo en tareas de
  valoracion.
- Actualizado `docs/harness/CODEX_OPERATING_MANUAL.md` para recomendarlo.
- Actualizado `AGENTS.md` en la matriz rapida de lectura.

# Validaciones

- Pendientes al cierre: `python3 scripts/audit_docs.py`,
  `bash scripts/finish_harness_task.sh`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir los cambios documentales listados. No hay migracion ni artefactos
externos.

# Fuera de alcance

- Cambios funcionales de valoracion.
- Cambios de esquema o migraciones.
- Scraping, OCR, calculo definitivo o outputs.

# Aprobacion humana requerida

No requerida para esta fase documental.

Estado: completado
