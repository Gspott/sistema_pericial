# Valoracion Docx Editable Modern

# Objetivo

Adaptar el DOCX editable moderno para valoracion inmobiliaria usando
`build_informe_context()`, sin tocar DOCX legacy, calculo, homogeneizacion,
DB ni migraciones.

# Modulo

Informes / DOCX editable moderno / smoke tests.

# Riesgo

Critico por afectar salida documental, acotado a rama `es_valoracion` y smoke
con SQLite temporal.

# Archivos permitidos

- `app/services/informe.py`
- `tests/smoke/test_informe_context.py`
- `docs/harness/PLANS/active/valoracion-docx-editable-modern.md`
- `docs/harness/METRICS.md` por cierre automatico

# Archivos prohibidos

- DOCX legacy salvo compatibilidad estricta
- DB real, datos reales, secretos, uploads, fotos reales, informes generados y backups
- Calculo/homogeneizacion
- Migraciones o cambios de esquema
- Routers legacy
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/informe_change.md`.

Playbook: `docs/harness/PLAYBOOKS/informes.md`.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_informe_context.py -q`
- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh`
- `python3 -m compileall app`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en generacion DOCX editable moderna y smoke DOCX.

# Fuera de alcance

- Adaptar DOCX legacy.
- Crear calculo u homogeneizacion.
- Mover campos entre tablas.
- Generar documentos reales.

# Aprobacion humana requerida

No adicional: el usuario ha autorizado esta fase funcional acotada. Parar si
aparece cambio de esquema, calculo, rediseño mayor o fallo de validacion.

Estado: completado
