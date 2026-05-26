# Valoracion Modelo Helpers Fallback

# Objetivo

Crear una capa unica de lectura para valoracion inmobiliaria que priorice el
modelo nuevo y degrade a legacy sin tocar formularios, templates ni calculo.

# Modulo

Informes / valoracion inmobiliaria / datos.

# Riesgo

Alto por afectar `build_informe_context()`, mitigado con cambios pequenos,
sin esquema nuevo y con smokes de legacy, modelo nuevo, precedencia y no
valoracion.

# Archivos permitidos

- `app/services/informe.py`
- `tests/smoke/`
- `docs/modelos_datos.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, backups, uploads, fotos reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- Formularios y templates.
- Calculo/homogeneizacion.
- Cambios de esquema salvo correccion defensiva minima exigida por smoke.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir helpers y llamada desde `build_informe_context()`, eliminar el smoke
nuevo y revertir docs de la fase. No hay datos reales ni migraciones.

# Fuera de alcance

- Formularios de alta/edicion del modelo nuevo.
- Migracion desde `valoracion_visita` o `comparables_valoracion`.
- Cambios en HTML/PDF/DOCX.
- Calculo final, homogeneizacion o formateo monetario avanzado.

# Aprobacion humana requerida

Necesaria si aparece cambio de esquema no trivial, migracion de datos, DB real,
formularios publicos, outputs modernos o calculo/homogeneizacion. No aplica en
esta fase.

Estado: completado
