# Pericial Pdf Design 2

# Objetivo

Implementar tres mejoras finales del PDF Pericial V2: Anexo D horizontal, PEM
total destacado como presupuesto de ejecucion material y nuevo Anexo F editable
para justificacion de mediciones.

# Modulo

Informes / PDF V2 / anexos editables.

# Riesgo

Critico por tocar salida de informe y editor estructurado. Alcance limitado a
capitulos V2, contexto de anexos, plantilla PDF V2 y smoke tests.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- PDF clasico y `templates/informes/imprimir.html`
- Workbench
- Patologias, costes, visitas, fotografias y datos persistidos existentes
- Nuevas tablas o migraciones

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir cambios acotados en contexto, plantilla PDF V2 y tests.

# Fuera de alcance

- Recalcular importes o mediciones.
- Modificar PDF clasico, Workbench, patologias, costes, visitas o fotos.
- Introducir IA.
- Persistir datos fuera de `informe_v2_capitulos`.

# Aprobacion humana requerida

No prevista si se mantiene este alcance y no se toca persistencia distinta de la
tabla existente `informe_v2_capitulos`.

Estado: completado
