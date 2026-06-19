# Pericial Pdf V2 Bookmarks Fix 1

# Objetivo

Corregir los bookmarks/outlines del PDF V2 para que apunten a las páginas finales visibles del índice ya validado mediante `indice_paginas`.

# Modulo

Informes / PDF V2 / Navegación interna / Bookmarks.

# Riesgo

Bajo-medio. Cambio acotado al postproceso de bookmarks PDF V2. No modifica contenido, textos, datos, orden documental, paginación calculada, PDFs externos ni editor.

# Archivos permitidos

`app/main.py`, `tests/smoke/test_pericial_workbench.py` y documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, editor V2, buscador/reemplazo, CRM, costes, facturación y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico

Tras `PERICIAL-PDF-V2-NAVIGATION-3-FIX-2`, los enlaces del índice impreso usan `indice_paginas` como fuente fiable, pero los bookmarks seguían resolviendo páginas mediante extracción de texto. En PDFs reales, esa detección podía llevar múltiples capítulos y anexos a la página del índice.

# Implementación

- Añadir resolvedor de página para bookmarks con prioridad: `indice_paginas`, destino registrado, extracción de texto y fallback.
- Usar ese resolvedor para portada, índice, capítulos, conclusiones, anexos técnicos, documentación aportada, relación documental y documentos aportados.
- Añadir bookmarks explícitos de Portada e Índice bajo el nodo Informe.
- Mantener la normalización de enlaces internos existente sin cambiar índice impreso ni contenido.
- Añadir smoke estructural con pypdf que valida jerarquía y páginas concretas de bookmarks.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`
- `bash scripts/finish_harness_task.sh --smoke-scope app`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos. No hay migraciones, cambios de esquema ni modificación de datos.

# Fuera de alcance

No modificar índice impreso, enlaces internos ya corregidos, contenido técnico, orden documental, paginación, PDFs externos, editor, buscador/reemplazo ni datos.

# Aprobacion humana requerida

No requerida.

Estado: completado
