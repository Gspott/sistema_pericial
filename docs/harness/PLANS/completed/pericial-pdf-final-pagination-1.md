# Pericial Pdf Final Pagination 1

# Objetivo

Añadir paginación global y continua al PDF final del Informe V2 mediante una
segunda pasada posterior a la fusión de anexos.

# Modulo

Informe V2. Endpoint `/generar-informe-v2-pdf/{expediente_id}` y servicio nuevo
`app/services/pdf_pagination.py`.

# Riesgo

Bajo-medio. La paginación se aplica al PDF final en memoria antes de devolver la
respuesta. Si el PDF no puede leerse, el servicio devuelve los bytes originales
para no romper la exportación.

# Archivos permitidos

- `app/main.py`
- `app/services/pdf_pagination.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-final-pagination-1.md`
- Documentación harness generada al cierre.

# Archivos prohibidos

- PDFs originales subidos.
- DOCX.
- CRM/prospección.
- Esquema de base de datos.
- Contenido técnico del informe.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Diagnóstico:

- El PDF principal se genera en `generar_informe_v2_pdf_bytes`.
- Anexos A/F y PDFs externos se integran después en
  `fusionar_pdf_informe_v2_con_anexos_integrados`.
- La paginación debe aplicarse inmediatamente después de esa fusión y antes de
  `StreamingResponse`.
- Se usa `pypdf` para leer/escribir y añadir un stream de texto por página con
  tamaño tomado de `page.mediabox`. `reportlab` no está disponible en el
  entorno y no se añade dependencia nueva.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir el servicio nuevo, la llamada final desde el endpoint y los tests
añadidos. No hay migraciones ni datos persistentes.

# Fuera de alcance

- Índice dinámico recalculado con `numero_pagina_final`.
- Guardar PDFs paginados en disco.
- Cambios en DOCX.

Validación real 019-26:

- `master`: 247 páginas. Numeración verificada en página 1, Anexo A página 13,
  página intermedia 124, Anexo F página 242 y página final 247.
- `email`: 247 páginas. Numeración verificada en los mismos puntos.
- `judicial`: 247 páginas. Numeración verificada en los mismos puntos.
- Los tres perfiles generaron 45.591.599 bytes en esta validación; el peso está
  dominado por anexos externos que el fallback actual no reduce.

# Aprobacion humana requerida

No prevista.

Estado: completado
