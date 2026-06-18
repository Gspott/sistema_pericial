# Pericial Pdf Pagination Visible Hotfix 2

# Objetivo

Garantizar que la numeracion `Página X de Y` sea visible en el PDF final V2 ya
fusionado, incluidos anexos externos escaneados, rotados o con fondos oscuros.

# Modulo

Informe V2 / segunda pasada de paginacion PDF final.

# Riesgo

Medio-alto. La paginacion se aplica al PDF completo despues de render, fusion de
Anexo A, fusion de Anexo F, optimizacion opcional y antes de responder al
cliente. Debe degradar sin romper si un PDF externo no admite overlay.

# Archivos permitidos

- `app/services/pdf_pagination.py`
- `app/main.py`
- `requirements.txt`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-pagination-visible-hotfix-2.md`
- Episodio harness de cierre

# Archivos prohibidos

- DOCX
- CRM
- Esquema de base de datos
- PDFs, informes o uploads reales
- Contenido tecnico del informe

# Playbook aplicable

Task Pack sugerido: `informe_change`.

# Diagnostico

La implementacion anterior anadia un stream manual de texto con pypdf. El texto
podia ser extraible pero no suficientemente robusto visualmente sobre anexos
escaneados, fondos oscuros, paginas rotadas o PDFs con recursos complejos.

La causa raiz probable es que el stream manual no garantizaba una capa visible
por encima del contenido ni una caja de contraste. En un PDF escaneado oscuro,
el texto podia quedar invisible aunque existiera en el contenido del PDF.

# Alcance

- Añadir `reportlab` como dependencia controlada.
- Generar un overlay PDF por pagina con ReportLab.
- Dibujar caja blanca pequeña y texto negro centrado.
- Fusionar el overlay por encima con pypdf `merge_page`.
- Mantener normalizacion de rotacion antes de calcular dimensiones.
- Guardar en modo debug:
  - `final_antes_paginacion.pdf`
  - `final_despues_paginacion.pdf`
  - `overlay_test_page_1.pdf`
- Registrar en logs tamaño antes/despues, paginas, duracion y carpeta debug.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir `app/services/pdf_pagination.py`, la llamada debug del endpoint,
`requirements.txt` y los smoke tests añadidos. No hay migraciones ni datos
persistentes nuevos.

# Fuera de alcance

- Optimizar peso de Anexo A.
- Cambiar contenido tecnico.
- Leer/generar expediente real `019-26` sin autorizacion explicita.
- Recalcular indice dinamico.

# Aprobacion humana requerida

Solo para validar con DB/uploads reales del expediente `019-26`.

Estado: completado
