# Pericial Photo Boards 2

# Objetivo

Evolucionar las laminas fotograficas del Informe V2 hacia una herramienta
editorial: pies editables, observaciones, layouts canonicos V2, ordenacion de
fotografias y render PDF mas claro.

# Modulo

- Informe V2 / editor.
- Generacion PDF del informe pericial.
- Persistencia SQLite de laminas fotograficas.

# Riesgo

- Medio: toca persistencia, rutas del editor y render PDF.
- Mitigacion: migraciones idempotentes, compatibilidad con layouts V1
  (`dos_fotos`, `cuatro_fotos`) y smoke tests sobre CRUD/render/paginacion.

# Archivos permitidos

- app/database.py
- app/main.py
- templates/informe_v2_editor.html
- templates/informes/v2_pdf.html
- tests/smoke/test_pericial_workbench.py
- docs/harness/METRICS.md
- docs/harness/EPISODES/
- docs/harness/PLANS/

# Archivos prohibidos

- CRM/prospeccion.
- DOCX.
- PDFs originales y fotografias originales.
- Datos reales, uploads, bases SQLite, backups e informes generados.
- Anexo B por patologias y Anexo C por estancias, salvo insertar el bloque de
  laminas ya existente sin alterar su flujo.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

- docs/harness/PLAYBOOKS/informes.md
- docs/informes.md
- docs/modelos_datos.md

# Validaciones

- python3 scripts/audit_docs.py
- python3 -m compileall app
- .venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q
- git diff --check
- bash scripts/finish_harness_task.sh --smoke-scope app

# Rollback

Revertir la columna `observacion`, helpers/rutas de edicion, cambios de UI y
render PDF. Las fotografias originales no se modifican.

# Fuera de alcance

- Drag-and-drop.
- Referencias cruzadas reales o numeracion final `Figura D.1.1`.
- Exportacion independiente de laminas.
- Cambios en DOCX/CRM.

# Aprobacion humana requerida

No prevista. Se limita a ampliacion idempotente minima de tabla existente.

Estado: completado
