# Valoracion Quick Wins Qa Visual

# Objetivo

Aplicar quick wins del QA visual de valoracion sin cambiar modelo ni calculo:
formatos con unidades, ocultacion de campos vacios, filtros server-side,
accion destructiva diferenciada y miniaturas de testigo.

# Modulo

Valoracion inmobiliaria, biblioteca de testigos, seleccion por expediente,
informe HTML/PDF y smokes.

# Riesgo

Alto por tocar valoracion e informe, pero sin esquema, migracion, calculo ni
outputs reales.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/valoracion_testigos.html`
- `templates/valoracion_expediente_testigos.html`
- `templates/informes/imprimir.html`
- `tests/smoke/test_valoracion_*.py`
- `docs/ux.md`
- `docs/informes.md`
- harness backlog/episode/plan

# Archivos prohibidos

- DB real, datos reales, uploads reales, informes reales, backups y secretos.
- Routers legacy.
- Carpeta anidada `sistema_pericial/`.
- Cambios de esquema, scraping/OCR, calculo definitivo o APIs de negocio
  paralelas.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.

# Cambios ejecutados

- Comparables y testigos vinculados muestran importes, superficies, valores
  unitarios y coeficientes con formato profesional.
- Informe imprimible oculta campos vacios tipo `-` en secciones de valoracion y
  comparables.
- Biblioteca de testigos incorpora filtros server-side por tipologia, municipio,
  validacion y reutilizable.
- Seleccion de testigos por expediente incorpora busqueda/filtros server-side.
- `Quitar del expediente` queda diferenciado como accion destructiva/secundaria.
- Cards de biblioteca muestran miniatura si existe foto manual del testigo.

# Validaciones

- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_informe_context.py tests/smoke/test_valoracion_testigos_reutilizables_form.py -q`
- `.venv/bin/python -m pytest tests/smoke -q`
- QA visual sandbox con Playwright local sobre DB temporal.
- Pendientes al cierre: `python3 scripts/audit_docs.py`,
  `bash scripts/finish_harness_task.sh`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir diff. No hay migracion ni cambio de esquema. Descartar temporales en
`/private/tmp/valoracion-qw-visual.*`.

# Fuera de alcance

- Compactar comparables como tabla/resumen de mercado responsive.
- Scraping/OCR/descarga remota.
- Calculo definitivo o metodo de coste.
- Migracion de legacy.

# Aprobacion humana requerida

No requerida para estos quick wins. Requerida para calculo final, scraping/OCR,
migraciones reales o rediseno mayor del informe.

Estado: completado
