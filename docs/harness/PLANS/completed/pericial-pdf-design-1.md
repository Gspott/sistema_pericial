# Pericial Pdf Design 1

# Objetivo

Mejorar la maquetacion editorial del PDF Pericial V2 en anexos B, C y D sin
modificar contenido tecnico, datos ni estructura funcional.

# Modulo

Informes / PDF V2 / presentacion.

# Riesgo

Critico por tocar salida de informe. Alcance limitado a plantilla PDF V2 y, si
es imprescindible, campos de presentacion derivados para formato visual.

# Archivos permitidos

- `templates/informes/v2_pdf.html`
- `app/main.py` solo para formato derivado de presentacion
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- PDF clasico y `templates/informes/imprimir.html`
- Workbench y Editor V2
- Patologias, costes, visitas, fotos y datos persistidos

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir ajustes de presentacion en plantilla/contexto y tests.

# Fuera de alcance

- Cambiar contenido tecnico.
- Cambiar PDF clasico, Workbench o Editor V2.
- Modificar patologias, costes, fotografias almacenadas o datos persistidos.

# Aprobacion humana requerida

No prevista si se mantiene el alcance visual y no se toca persistencia.

Estado: completado
