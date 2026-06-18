# Pericial Pdf Email Broken Images Hotfix 1

# Objetivo

Corregir los enlaces rotos de fotografias en PDFs V2 generados con perfiles
optimizados `email` y `judicial`, manteniendo las imagenes originales intactas y
limpiando los temporales al finalizar el pipeline.

# Modulo

Informe V2 / optimizacion de imagenes para PDF / render Playwright.

# Riesgo

Medio. El cambio afecta a las rutas de imagen que consume la plantilla PDF V2.
Debe conservar el comportamiento de `master`, no modificar uploads y no limpiar
temporales antes de que Chromium renderice el HTML.

# Archivos permitidos

- `app/services/pdf_image_optimizer.py`
- `app/main.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-email-broken-images-hotfix-1.md`
- Episodio harness de cierre

# Archivos prohibidos

- DOCX
- CRM
- Esquema de base de datos
- Fotografias originales, uploads reales, informes generados reales
- Contenido tecnico del informe

# Playbook aplicable

Task Pack sugerido: `informe_change`.

# Diagnostico

La plantilla PDF V2 usa el campo `url` de cada fotografia. El campo sustituido
era correcto, pero `PERICIAL-PDF-IMAGE-OPTIMIZATION-1` lo reemplazaba por
`file://...` apuntando al temporal optimizado.

El render usa Playwright con `page.set_content(html)`. En ese contexto, las
rutas `file://` quedan fuera del origen HTTP de la aplicacion y pueden aparecer
como imagen rota. La solucion mas robusta sin nuevas dependencias es servir las
imagenes temporales por una ruta HTTP interna de FastAPI mientras dura el render.

# Alcance

- Crear URLs temporales `/pdf-temp-images/{token}/{archivo}` para imagenes
  optimizadas.
- Registrar el directorio temporal en `app.state` antes del render y retirarlo
  en el `finally`, antes de borrar la carpeta.
- Mantener fallback a `/uploads/...` si una imagen no se puede optimizar.
- Registrar diagnostico con ruta original, ruta optimizada, campo usado y
  existencia en disco.
- Validar que `master` conserva rutas originales.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir los cambios en `app/services/pdf_image_optimizer.py`, la ruta temporal
en `app/main.py` y los smoke tests asociados. No hay migraciones ni cambios en
uploads.

# Fuera de alcance

- Optimizar Anexo A.
- Cambiar compresion Ghostscript.
- Validar expediente real `019-26` sin autorizacion explicita.
- Cambiar plantillas PDF o contenido tecnico.

# Aprobacion humana requerida

Solo para leer/generar con datos reales del expediente `019-26`. Los tests usan
datos sinteticos.

Estado: completado
