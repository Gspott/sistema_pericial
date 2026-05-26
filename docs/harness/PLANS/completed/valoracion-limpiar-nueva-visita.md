# Valoracion Limpiar Nueva Visita

# Objetivo

Limpiar `templates/nueva_visita.html` para `tipo_informe='valoracion'`,
dejando solo bloques propios de visita fisica y evitando campos generales que
ya viven en `valoracion_expediente`, testigos, ajustes o resultados.

# Modulo

UX mobile-first / Jinja / visitas / valoracion inmobiliaria.

# Riesgo

Bajo-medio: template compartido por varios tipos de informe. Mitigado con smoke
de render para valoracion y patologias, y cambio backend minimo para no vaciar
legacy oculto.

# Archivos permitidos

- `templates/nueva_visita.html`
- `app/main.py`
- `tests/smoke/test_valoracion_nueva_visita_ux.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/visita_especifica_por_tipo_informe.md`
- `docs/harness/EPISODES/2026-05-26-valoracion-limpiar-nueva-visita.md`

# Archivos prohibidos

DB real, uploads, informes reales, backups, secretos, routers legacy y carpeta
anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/jinja.md`.

# Cambios

- Valoracion oculta climatologia y campos generales legacy de valoracion.
- Valoracion mantiene exterior, reforma observada, datos esenciales y acceso a
  estancias.
- Se añade bloque portal/contadores reutilizando `visita_fotos` con categoria
  `portal_contadores`.
- No se crea esquema para observaciones textuales de portal/contadores.
- `guardar_visita()` solo actualiza `valoracion_visita` legacy si el form trae
  campos `valoracion__*`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_nueva_visita_ux.py -q`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir los cambios de template, helper de POST y smoke; no hay migracion ni
datos que restaurar.

# Fuera de alcance

Persistencia textual de portal/contadores, cambio de esquema, migracion de datos
legacy, subida de fotos reales, calculo, PDF/DOCX y routers legacy.

# Aprobacion humana requerida

No requerida: no hay cambio de esquema ni DB real.

Estado: completado
