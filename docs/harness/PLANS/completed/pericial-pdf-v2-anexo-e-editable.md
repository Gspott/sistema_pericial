# Pericial Pdf V2 Anexo E Editable

# Objetivo

Convertir el Anexo E del PDF Pericial V2 en un capitulo editable persistido en
`informe_v2_capitulos`, manteniendolo fuera del cuerpo principal y dentro de
anexos.

# Modulo

Informes / PDF V2 / Editor V2.

# Riesgo

Critico por tocar salida de informe y editor estructurado. Alcance limitado a
la lista de capitulos V2, precarga, render del PDF V2 y smoke tests.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- PDF clasico y `templates/informes/imprimir.html`
- Workbench salvo lectura
- Patologias, costes, visitas, fotos y captura movil
- Nuevas tablas o migraciones

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Clave editable

- `anexo_e_partida_4`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir cambios acotados en contexto/editor, plantilla PDF V2 y tests.

# Fuera de alcance

- Modificar PDF clasico.
- Modificar Workbench.
- Modificar patologias, costes, visitas, fotos o captura movil.
- Crear tablas.
- Sobrescribir contenido manual existente.

# Aprobacion humana requerida

No prevista si se mantiene este alcance. Cualquier cambio de persistencia fuera
de `informe_v2_capitulos`, PDF clasico o datos de negocio requiere revision.

Estado: completado
