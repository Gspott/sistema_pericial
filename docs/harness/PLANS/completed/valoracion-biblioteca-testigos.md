# Valoracion Biblioteca Testigos

# Objetivo

Evolucionar `/valoracion/testigos` hacia una biblioteca reutilizable de
testigos/comparables para valoracion inmobiliaria, con mejoras visuales,
busqueda, detalle, fotos manuales y documentacion de captura futura desde
enlaces/capturas.

# Modulo

Valoracion inmobiliaria: testigos reutilizables, seleccion por expediente,
templates Jinja y smokes.

# Riesgo

Medio. Toca rutas server-side existentes de valoracion y anade subida manual de
fotos de testigo. No cambia esquema, no migra datos, no toca calculo ni outputs
PDF/DOCX.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_testigos.html`
- `templates/valoracion_testigo_detalle.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/modelos_datos.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/2026-05-26-valoracion-biblioteca-testigos.md`

# Archivos prohibidos

- DB real, datos reales, uploads reales, informes generados reales, backups y
  secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- PDF/DOCX moderno, salvo que una validacion lo exigiera; no fue necesario.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.

- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Cambios ejecutados

- Anadidos helpers de formato para moneda, precio unitario, superficie y
  booleanos.
- `/valoracion/testigos` muestra busqueda y cards con importes/superficies
  formateados, fuente, estado, validacion y acciones.
- Anadido detalle `GET /valoracion/testigos/{testigo_id}` con datos completos,
  fotos y usos en expedientes del mismo propietario.
- Anadida subida manual `POST /valoracion/testigos/{testigo_id}/fotos` usando
  `testigos_valoracion_fotos` y uploads contextuales existentes.
- Documentado que URL/capturas/OCR/scraping quedan para fase futura separada.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_valoracion_testigos_reutilizables_form.py -q`
- Pendientes al cierre: `python3 scripts/audit_docs.py`,
  `python3 -m compileall app`, `.venv/bin/python -m pytest tests/smoke -q`,
  `bash scripts/finish_harness_task.sh`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir cambios en los archivos listados. La fase no requiere migracion ni
reversion de esquema.

# Fuera de alcance

- Scraping de portales inmobiliarios.
- OCR o IA para leer capturas.
- Descarga automatica de imagenes desde URLs externas.
- Calculo final, homogeneizacion automatica o metodo de coste.
- Migracion de `comparables_valoracion`.

# Aprobacion humana requerida

Solo para implementar automatizaciones de captura/OCR/scraping o modificar
reglas de calculo/valoracion.

Estado: completado
