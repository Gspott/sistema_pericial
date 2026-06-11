# Pericial Pdf V2 3

# Objetivo

Evolucionar exclusivamente el Anexo B del PDF Pericial V2 para que el
reportaje fotografico se agrupe por tipologia de dano mediante reglas
deterministas y reutilizando datos existentes.

# Modulo

Informes / PDF V2 / Anexo B.

# Riesgo

Critico, por tocar salida de informe. Alcance limitado a contexto y plantilla
del PDF V2; sin modificar PDF clasico, anexos A/C/D, editor, Workbench,
patologias, fotos almacenadas ni captura movil.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- PDF clasico y `templates/informes/imprimir.html`
- Editor V2 y Workbench salvo lectura
- Patologias, costes, captura movil y persistencia
- Bases SQLite, uploads, informes generados, backups, logs y secretos

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Datos reutilizados

- Patologia, elemento, estancia/zona y pies de foto ya presentes en
  `build_informe_context()`.
- Relaciones foto-patologia y foto-estancia ya existentes.
- Fotografias de visita/estancia/patologia sin tocar almacenamiento.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir los cambios acotados en contexto/plantilla/test de PDF V2.

# Fuera de alcance

- Cambiar anexos A, C o D.
- Cambiar cuerpo principal del PDF V2.
- Cambiar PDF clasico.
- Modificar editor V2, Workbench, patologias, costes o captura movil.
- Crear clasificacion manual, IA, tablas, migraciones o almacenamiento nuevo.

# Aprobacion humana requerida

No prevista si se mantiene el alcance anterior. Cualquier cambio de criterio
pericial persistido, almacenamiento de fotos o PDF clasico requiere revision.

Estado: completado
