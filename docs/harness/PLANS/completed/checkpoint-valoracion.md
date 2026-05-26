# Checkpoint Valoracion

# Objetivo

Preparar un checkpoint seguro del trabajo acumulado de valoracion inmobiliaria
y harness antes de commit.

Alcance:
- revisar `git status`;
- agrupar cambios por bloques logicos;
- detectar archivos accidentales;
- ejecutar validacion full una vez;
- documentar punto estable.

# Modulo

Harness / valoracion inmobiliaria.

# Riesgo

Medio. El checkpoint no introduce cambios funcionales, pero el diff acumulado
incluye app, templates, scripts, tests y documentacion.

Durante la validacion se detecto un bug minimo del wrapper
`scripts/finish_harness_task.sh`: con `set -u`, Bash puede tratar el array
vacio `VALIDATE_ARGS[@]` como variable no ligada al invocar el validador sin
argumentos. Se corrige solo el wrapper para mantener operativo el cierre full.

# Archivos permitidos

Solo documentacion de harness para registrar el checkpoint y cierre del plan.
Correccion minima del wrapper `scripts/finish_harness_task.sh` si bloquea el
cierre de validacion.

# Archivos prohibidos

DB real, datos reales, uploads, informes generados, backups, secretos, routers
legacy, carpeta anidada `sistema_pericial/`, cambios funcionales o refactors.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash -n scripts/finish_harness_task.sh`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir solo la documentacion de checkpoint si fuese necesario. No hay cambios
funcionales en esta fase.

# Fuera de alcance

Commits reales, borrados, limpieza destructiva, cambios funcionales, DB real.

# Aprobacion humana requerida

Solo para ejecutar los commits o borrar/descartar cualquier archivo.

# Resultado de auditoria previa

`git status --short` muestra un diff amplio acumulado de fases previas de
valoracion/harness. No se detectan candidatos accidentales en:

- `data/`
- `uploads/`
- `informes/`
- `backups/`
- `logs/`
- `sistema_pericial/`
- `.env`
- `*.db`
- `*.sqlite`
- `*.pdf`
- `*.docx`
- imagenes generadas
- `__pycache__` / `*.pyc`

# Agrupacion propuesta para commits

1. Harness lifecycle y scopes:
   `AGENTS.md`, `scripts/start_harness_task.sh`,
   `scripts/finish_harness_task.sh`, `scripts/validate_harness.sh`,
   `scripts/harness_close_plan.py`, `scripts/harness_scope_resolver.py`,
   `docs/harness/TASK_PACKS/`, `docs/harness/VALIDATION/`,
   `docs/harness/CODEX_OPERATING_MANUAL.md`,
   `docs/harness/EXECUTION_POLICY.md`, `docs/harness/METRICS.md`,
   planes/episodios harness y `tests/smoke/test_harness_scope_resolver.py`.

2. Modelo/contexto de valoracion:
   `app/database.py`, `app/services/informe.py`, `docs/modelos_datos.md`,
   `docs/informes.md`, patterns/goals de valoracion y smokes de contexto,
   DB defensiva, fallback y completitud.

3. UX y formularios de valoracion:
   `app/main.py`, templates `valoracion_*`, `templates/nueva_visita.html`,
   `templates/detalle_expediente.html`, `templates/resumen_registro.html`,
   `templates/partials/_drawer_nav.html`, `static/mobile.css`, smokes de
   formularios, visita limpia, testigos y ajustes.

4. Casos demo y QA:
   `scripts/create_valoracion_demo_cases.py`, `tests/fixtures/`,
   `tests/smoke/test_valoracion_demo_cases.py`, episodios de demo/import/QA y
   documentacion asociada.

5. Checkpoint:
   este plan/episodio de checkpoint, si se quiere dejar como commit separado o
   incluido en harness lifecycle.

Estado: completado
