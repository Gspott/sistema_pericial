# Pericial Pdf V2 Navigation 2

# Objetivo

Añadir marcadores PDF nativos (Outline/Bookmarks) al PDF V2 final para mejorar
la navegación lateral en visores compatibles, sin modificar contenido,
paginación, datos ni PDFs externos.

# Modulo

Informes / PDF V2 / navegación post-proceso.

# Riesgo

Crítico por intervenir el PDF final. El cambio se limita a metadatos de
navegación (`/Outlines`) tras render, fusión y paginación; debe degradar sin
romper generación si el visor o `pypdf` no soportan bookmarks.

# Archivos permitidos

- `app/main.py` en helpers de PDF V2 y endpoint de generación.
- `tests/smoke/test_pericial_workbench.py`.
- Documentación harness de esta tarea.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- PDFs externos fusionados.
- Plantilla visual del índice salvo si una prueba demuestra necesidad.
- Editor V2, CRM, costes, valoración hipotecaria y módulos ajenos.

# Playbook aplicable

Task Pack: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.
- `git diff --check`.

# Rollback

Revertir helper de bookmarks, llamada en endpoint, tests y documentación
harness de esta tarea.

# Fuera de alcance

- Cambiar índice visual.
- Cambiar contenido, orden documental, datos, PDFs externos o paginación.
- Añadir navegación a figuras/fichas individuales.

# Aprobacion humana requerida

Si la implementación exige modificar el motor PDF, cambiar paginación,
alterar PDFs externos o tocar contenido/datos persistidos.

Estado: completado
