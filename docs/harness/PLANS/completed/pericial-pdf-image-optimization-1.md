# Pericial Pdf Image Optimization 1

# Objetivo

Reducir el peso de PDFs V2 mediante optimizacion temporal de imagenes por
perfil de exportacion, sin modificar fotografias originales ni contenido tecnico.

# Modulo

Informe V2. Perfiles PDF, contexto de imagenes del PDF y servicio nuevo
`app/services/pdf_image_optimizer.py`.

# Riesgo

Bajo-medio. La ruta historica `master`/sin perfil debe conservarse. La
optimizacion solo debe activarse para perfiles preparados y trabajar sobre
copias temporales.

# Archivos permitidos

- `app/main.py`
- `app/services/pdf_image_optimizer.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-image-optimization-1.md`
- Documentacion harness generada al cierre.

# Archivos prohibidos

- DOCX.
- CRM/prospeccion.
- Esquema de base de datos y migraciones.
- Fotografias originales, uploads reales, backups, informes generados y logs.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Playbook revisado: `docs/harness/PLAYBOOKS/informes.md`.

Diagnostico:

- El PDF V2 inserta imagenes mediante `foto.url` en `templates/informes/v2_pdf.html`.
- Las figuras se construyen desde `app/services/informe.py` y los anexos
  derivados se preparan en `app/main.py`.
- El punto minimo de intervencion es el contexto PDF ya construido, antes de
  llamar a `generar_informe_v2_pdf_bytes`.
- `solo_informe` no fusiona anexos externos; `email` y `judicial` pueden activar
  optimizacion sin cambiar el contenido del informe.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir servicio nuevo, cambios de perfiles/endpoint/UI y tests. No hay
migraciones ni datos persistentes que revertir.

# Fuera de alcance

- Compresion de PDFs externos fusionados como anexos A/F.
- Cambios en DOCX.
- Persistencia de imagenes optimizadas o metricas en base de datos.
- Garantizar un tamano final exacto de PDF.
- Validacion manual con expediente real o lote de 20-30 fotos.

# Aprobacion humana requerida

No prevista. Requerida si se decide modificar originales, esquema de base de
datos, DOCX o datos reales.

Estado: completado
