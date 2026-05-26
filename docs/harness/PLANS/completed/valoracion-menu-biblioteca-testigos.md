# Valoracion Menu Biblioteca Testigos

# Objetivo

Anadir "Biblioteca de testigos" al drawer izquierdo justo debajo de
"Biblioteca de patologias", apuntando a `/valoracion/testigos` y reutilizando
el patron de estado activo existente.

# Modulo

Navegacion/drawer y valoracion inmobiliaria.

# Riesgo

Bajo. Cambio acotado de navegacion y smoke; no toca DB, formularios ni logica de
valoracion.

# Archivos permitidos

- `templates/partials/_drawer_nav.html`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/2026-05-26-valoracion-menu-biblioteca-testigos.md`

# Archivos prohibidos

- DB real, datos reales, uploads reales, informes reales, backups y secretos.
- Formularios de valoracion.
- Routers legacy.
- Carpeta anidada `sistema_pericial/`.
- Refactor de navegacion.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.

# Cambios ejecutados

- Enlace anadido debajo de "Biblioteca de patologias".
- Estado activo: `path.startswith('/valoracion/testigos')`.
- Smoke comprueba presencia y orden del enlace.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_valoracion_testigos_reutilizables_form.py -q`
- Pendientes al cierre: `python3 scripts/audit_docs.py`,
  `bash scripts/finish_harness_task.sh`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir cambios documentales, el smoke y la linea de `templates/partials/_drawer_nav.html`.

# Fuera de alcance

- Cambios de DB.
- Cambios en formularios.
- Scraping/OCR.
- Refactor de navegacion.

# Aprobacion humana requerida

No requerida para esta fase acotada.

Estado: completado
