# Expediente Search 1

# Objetivo

Añadir una búsqueda global de solo lectura dentro del expediente activo, orientada a localizar texto persistido en los módulos principales del expediente.

# Modulo

Expedientes / Detalle expediente / Informe V2 / Workbench pericial.

# Riesgo

Bajo-medio. Añade consultas de lectura y UI server-side en el detalle del expediente. No modifica datos, esquemas, PDFs, editor, autosave, CRM, facturación ni valoración hipotecaria.

# Archivos permitidos

`app/main.py`, `templates/detalle_expediente.html`, `templates/pericial_workbench.html`, `tests/smoke/test_pericial_workbench.py` y documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, OCR, indexadores externos, editor V2 salvo navegación de lectura, CRM, facturación, valoración hipotecaria y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.

# Diagnóstico

El expediente concentra información textual en tablas de informe, visita, estancias, patologías, documentos, fotografías, valoración y actuaciones/costes. No existe un índice unificado ni hace falta en esta fase: el volumen habitual permite consulta en memoria sobre filas filtradas por expediente.

# Implementación

- Añadir helpers de normalización, contexto y búsqueda segura por columnas existentes.
- Añadir `buscar_en_expediente_global()` como agregador de solo lectura.
- Conectar el detalle de expediente con parámetro GET `q`.
- Renderizar resultados agrupados por módulo, con contexto resaltado y enlace de navegación.
- Añadir ancla estable en la sección de documentación aportada del workbench pericial.
- Añadir smoke tests para Informe V2, estancias, fotografías, documentos, notas, valoración, costes, contexto, navegación, búsqueda vacía y no modificación de datos.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "expediente_search or informe_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos. No hay migraciones, cambios de esquema ni modificación de datos.

# Fuera de alcance

OCR, búsqueda en PDFs externos/binarios, indexadores externos, reemplazo global, cache persistente, cambios de autosave, cambios de CRM/facturación/valoración hipotecaria, modificación de PDFs o contenido.

# Aprobacion humana requerida

No requerida.

Estado: completado
