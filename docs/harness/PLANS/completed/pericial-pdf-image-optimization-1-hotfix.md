# Pericial Pdf Image Optimization 1 Hotfix

# Objetivo

Diagnosticar y corregir que los perfiles PDF optimizados puedan producir el
mismo peso que `master`, verificando que el HTML final usa rutas temporales
optimizadas.

# Modulo

Informe V2. Perfil PDF, servicio `app/services/pdf_image_optimizer.py`,
endpoint `/generar-informe-v2-pdf/{expediente_id}` y smoke tests.

# Riesgo

Bajo. Hotfix acotado a configuracion de perfiles, guardado JPEG optimizado y
tests de regresion sobre el HTML renderizado. No toca originales ni DOCX.

# Archivos permitidos

- `app/main.py`
- `app/services/pdf_image_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-image-optimization-1-hotfix.md`
- Documentacion harness generada al cierre.

# Archivos prohibidos

- DOCX.
- CRM/prospeccion.
- Esquema de base de datos y migraciones.
- Fotografias originales, uploads reales, backups e informes generados.
- Refactors amplios del pipeline PDF.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Diagnostico:

- El contexto PDF se construye en `preparar_contexto_pdf_informe_v2`.
- Las fotografias se renderizan en `templates/informes/v2_pdf.html` desde
  `anexos.fotografias_grupos[*].fotos[*].url` y
  `anexos.fichas_danos[*].fotos[*].url`.
- La sustitucion por temporales ocurre antes de `generar_informe_v2_pdf_bytes`.
- La fusion de anexos PDF externos ocurre despues del render y no queda cubierta
  por la optimizacion de imagenes.
- Las imagenes subidas ya se normalizan a 1600 px, JPEG quality 80, progressive
  y sin metadatos; por tanto `email` con 1600 px podia quedar equivalente a
  master en imagenes ya procesadas.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir los cambios de configuracion del perfil email, el ajuste de guardado
JPEG progresivo y los tests añadidos.

# Fuera de alcance

- Optimizacion de PDFs externos fusionados como Anexo A/F.
- Comparativa manual con expediente real.
- Nuevas funcionalidades o UI adicional.

# Aprobacion humana requerida

No prevista.

Estado: completado
