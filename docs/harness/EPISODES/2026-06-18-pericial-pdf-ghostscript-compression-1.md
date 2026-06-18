# Episode: Pericial Pdf Ghostscript Compression 1

## Fecha

2026-06-18

## Tarea

PERICIAL-PDF-GHOSTSCRIPT-COMPRESSION-1

## Plan asociado

pericial-pdf-ghostscript-compression-1.md

## Task Pack usado

`informe_change`

## Objetivo

Mejorar la compresion opcional de PDFs externos fusionados en Informe V2 usando
Ghostscript cuando este disponible, sin convertirlo en dependencia obligatoria.

## Archivos modificados

- `app/services/pdf_annex_optimizer.py`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/completed/pericial-pdf-ghostscript-compression-1.md`
- `docs/harness/METRICS.md`
- `docs/harness/EPISODES/2026-06-18-pericial-pdf-ghostscript-compression-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`: OK con warnings preexistentes.
- `python3 -m compileall app`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`:
  OK, 55 passed.
- `git diff --check`: OK.
- `bash scripts/finish_harness_task.sh --smoke-scope app`: OK, alcance elevado
  automaticamente a full, 244 passed.

## Resultado

`app/services/pdf_annex_optimizer.py` tiene ahora configuracion explicita:

- `email`: Ghostscript `/ebook`, timeout 120 segundos.
- `judicial`: Ghostscript `/screen`, timeout 120 segundos.

El servicio detecta `gs` con `shutil.which("gs")`, construye el comando como
lista de argumentos, ejecuta sin `shell=True`, escribe siempre en temporal,
descarta salidas parciales o mas grandes, y conserva el PDF original si no hay
reduccion.

El resultado de `optimizar_pdf_externo()` incluye `mensaje` ademas de ruta,
metodo, tamanos y porcentaje de reduccion.

## Warnings

Ghostscript no esta instalado en este entorno (`which gs` no devuelve ruta). La
validacion con Ghostscript real sobre 019-26 queda pendiente tras instalacion
manual opcional:

```bash
brew install ghostscript
```

Sin Ghostscript, el sistema mantiene fallback seguro con `pypdf` o conserva el
original si no hay reduccion.

## Rollback

Revertir cambios en `app/services/pdf_annex_optimizer.py` y tests asociados. No
hay migraciones ni datos persistentes nuevos.

## Memoria actualizada

Plan cerrado en
`docs/harness/PLANS/completed/pericial-pdf-ghostscript-compression-1.md`.
Metricas actualizadas por el cierre harness.

## Decisiones humanas

No requeridas. No se instala Ghostscript automaticamente.

## Proximos pasos

Instalar Ghostscript manualmente si se quiere medir 019-26 y comparar
`master`, `email` y `judicial` en peso y legibilidad visual de Anexo A/F.
