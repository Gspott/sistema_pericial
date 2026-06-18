# Pericial Pdf Generation Hang Hotfix 1

# Objetivo

Diagnosticar y corregir el bloqueo percibido en la generación PDF V2 con anexos
en expedientes reales grandes, especialmente `019-26`, sin modificar el
contenido técnico del informe ni los PDFs originales aportados.

La tarea añade observabilidad controlada del pipeline, una vía de diagnóstico
JSON sin renderizar el PDF completo, un bypass interno de paginación para aislar
la segunda pasada y una respuesta defensiva mediante fichero temporal para PDFs
grandes.

# Modulo

Informe V2 / generación PDF con anexos externos.

# Riesgo

Medio. El endpoint `/generar-informe-v2-pdf/{expediente_id}` es crítico para la
emisión de informes. El cambio debe preservar el comportamiento normal y limitar
los nuevos flags a diagnóstico interno, siempre tras el control de ownership ya
existente.

# Archivos permitidos

- `app/main.py`
- `app/services/pdf_annex_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-generation-hang-hotfix-1.md`
- Episodio harness de cierre

# Archivos prohibidos

- DOCX
- CRM
- Esquema de base de datos
- PDFs/documentos/fotografías originales subidos
- Datos reales, backups, logs o uploads salvo lectura diagnóstica autorizada

# Playbook aplicable

Task Pack sugerido: `informe_change`.

# Diagnostico

- El perfil `solo_informe` evita la fusión de anexos y genera correctamente.
- Los perfiles `master`, `email` y `judicial` ejecutan render principal, fusión
  de anexos externos y paginación final.
- En el caso real `019-26`, el PDF final validado anteriormente tiene 247
  páginas y 45.591.599 bytes; el tamaño restante está dominado por anexos PDF
  externos, no por las imágenes del cuerpo del informe.
- El bloqueo observado se produce después del render principal, en una fase con
  poca visibilidad previa: fusión/optimización/paginación/respuesta.

# Alcance

- Instrumentación por logger activable con `debug_pdf_pipeline=log`.
- Diagnóstico JSON con `debug_pdf_pipeline=1` sin generar PDF.
- Bypass interno `debug_sin_paginacion=1` para aislar la paginación final.
- Confirmación de timeout/fallback de Ghostscript en perfil `email`.
- Uso de `FileResponse` temporal para PDFs generados grandes.

# Fuera de alcance tecnico

- Nueva compresión de anexos externos.
- Cambios en contenido técnico.
- Cambios en DOCX.
- Cambios en esquema de datos.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir los cambios de `app/main.py`, `app/services/pdf_annex_optimizer.py` y
los smoke tests asociados. Los flags de diagnóstico no crean ni modifican datos.

# Fuera de alcance

- Optimización adicional de PDFs escaneados.
- Instalación obligatoria de Ghostscript.
- Regeneración o modificación de PDFs originales.
- Cambios en PDF/DOCX distintos del pipeline PDF V2.

# Aprobacion humana requerida

No prevista para el hotfix: no se toca DB, datos reales, CRM ni DOCX.

Estado: completado

## Ampliacion paginacion final

Fecha: 2026-06-18.

Objetivo adicional: diagnosticar y corregir por que `Página X de Y` podia no
aparecer en el PDF completo con anexos externos.

Diagnostico:

- La llamada a `paginar_pdf_final_bytes()` se hace despues del render principal
  y despues de `fusionar_pdf_informe_v2_con_anexos_integrados()`.
- El endpoint reasigna `pdf_bytes` con el resultado paginado antes de construir
  la respuesta, por lo que no se detecta devolucion del buffer anterior.
- El punto fragil estaba en la escritura manual del overlay: se posicionaba con
  `mediabox` y no normalizaba paginas con `/Rotate`. En PDFs externos rotados,
  escaneados o con area visible basada en `cropbox`, la numeracion podia quedar
  fuera de la zona visible o en orientacion no esperada.
- La excepcion de paginacion se degradaba devolviendo el PDF original, pero sin
  warning, lo que dificultaba diagnosticar fallos reales.

Cambios:

- `app/services/pdf_pagination.py` normaliza rotacion con
  `transfer_rotation_to_content()` antes de anadir el pie.
- La posicion se calcula sobre `cropbox` cuando existe.
- `paginar_pdf_final_bytes()` acepta `debug=True`, registra duracion/tamanos en
  modo debug y registra warning si falla.
- El endpoint PDF V2 pasa `debug=True` a paginacion cuando
  `debug_pdf_pipeline=log`.
- Se añadieron smoke tests para todos los perfiles, pagina rotada,
  `FileResponse`, bytes paginados y fallo controlado.

Validaciones de la ampliacion:

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 63 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: smoke full OK,
  252 passed; el cierre automatico fallo solo porque ya existia este plan en
  completed y la ampliacion se consolida manualmente aqui.

Validacion 019-26:

No ejecutada en esta ampliacion porque el harness prohibe leer DB/uploads reales
sin autorizacion explicita. Queda preparado el diagnostico con
`debug_pdf_pipeline=log` y comparacion con `debug_sin_paginacion=1`.
