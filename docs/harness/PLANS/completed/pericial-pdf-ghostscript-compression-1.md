# Pericial Pdf Ghostscript Compression 1

# Objetivo

Mejorar la compresion opcional de PDFs externos fusionados en Informe V2 usando
Ghostscript cuando este disponible, manteniendo fallback seguro sin dependencia
obligatoria.

# Modulo

Servicio `app/services/pdf_annex_optimizer.py` y smoke tests del pipeline PDF V2.

# Riesgo

Bajo. La mejora queda aislada en el optimizador de anexos externos; `master`,
`informe_anexos` y el perfil por defecto mantienen comportamiento historico.

# Archivos permitidos

- `app/services/pdf_annex_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-ghostscript-compression-1.md`
- Documentacion harness generada al cierre.

# Archivos prohibidos

- PDFs originales subidos.
- DOCX.
- CRM/prospeccion.
- Esquema de base de datos.
- Instalacion automatica de Ghostscript o cambios en requirements.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Diagnostico:

- El caso 019-26 queda dominado por PDFs externos fusionados y genera 247
  paginas con 45.591.599 bytes en `master`, `email` y `judicial`.
- `pypdf.compress_content_streams()` no recompone imagenes internas de escaneos.
- Ghostscript no esta instalado localmente (`which gs` no devuelve ruta).
- Se integrara como dependencia opcional con perfiles `email=/ebook` y
  `judicial=/screen`, timeout y fallback.

Instalacion opcional macOS:

```bash
brew install ghostscript
```

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en `pdf_annex_optimizer.py` y tests añadidos. No hay
migraciones ni datos persistentes.

# Fuera de alcance

- Instalar Ghostscript.
- Recompresion visual validada del expediente 019-26 con `gs` real.
- Cambiar contenido tecnico, DOCX o PDFs originales.

# Aprobacion humana requerida

No prevista.

Estado: completado
