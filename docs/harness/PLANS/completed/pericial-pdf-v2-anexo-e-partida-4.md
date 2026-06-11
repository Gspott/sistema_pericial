# Pericial Pdf V2 Anexo E Partida 4

# Objetivo

Añadir al PDF Pericial V2 un Anexo E con el analisis de ejecucion de la
partida nº 4 del presupuesto de reparacion de cubierta, usando el texto
aportado por el usuario y reutilizando datos economicos estructurados si existe
una cuarta partida.

# Modulo

Informes / PDF V2 / Anexos.

# Riesgo

Critico por tocar salida de informe. Alcance limitado a PDF V2; sin modificar
PDF clasico, editor V2, Workbench, patologias, fotografias almacenadas,
captura movil ni persistencia.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- `templates/informes/imprimir.html`
- Editor V2 y Workbench salvo lectura
- Patologias, costes, captura movil y almacenamiento
- Bases SQLite, uploads, informes generados, backups, logs y secretos

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Datos reutilizados

- Anexo economico ya construido para PDF V2.
- Cuarta partida estructurada si existe en las actuaciones economicas.
- Texto literal aportado por el usuario para el Anexo E.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir cambios acotados en contexto, plantilla y test del PDF V2.

# Fuera de alcance

- Modificar anexos A, B, C o D.
- Modificar cuerpo principal del PDF V2.
- Modificar PDF clasico, editor V2, Workbench, patologias, costes o fotos.
- Parsear documentos aportados, crear IA o crear clasificacion manual.

# Aprobacion humana requerida

No prevista si se mantiene este alcance. Cualquier cambio en persistencia,
criterios periciales guardados o PDF clasico requiere revision humana.

Estado: completado
