# Valoracion Casos Demo

# Objetivo

Crear casos ficticios completos de valoracion inmobiliaria para QA funcional de
UX, testigos reutilizables, ajustes, contexto informe, HTML/PDF, DOCX,
completitud y calculo preparatorio.

# Modulo

Valoracion inmobiliaria / QA funcional / datos demo sandbox.

# Riesgo

Alto por generar datos de prueba estructurados, mitigado porque solo se usan
DBs temporales/sandbox, datos ficticios, sin uploads ni DB real.

# Archivos permitidos

- `tests/fixtures/`
- `tests/smoke/`
- `scripts/create_valoracion_demo_cases.py`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, backups, uploads, fotos reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- Esquema y migraciones.
- Cambios de calculo productivo.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/demo_data.md`.
Task Pack no encontrado; se aplica alcance sandbox equivalente con reglas de
datos demo y DB temporal.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Eliminar fixture, smoke, script y documentacion de la fase. Descartar cualquier
SQLite temporal generada fuera del repo. No hay datos reales implicados.

# Fuera de alcance

- Poblar DB real.
- Usar inmuebles o datos de mercado reales.
- Crear uploads/fotos/informes reales.
- QA visual con screenshots.
- Implementar calculo profesional final.

# Aprobacion humana requerida

Necesaria si se quisiera poblar DB real, leer datos reales, usar uploads,
generar informes reales persistidos o tocar routers legacy. No aplica en esta
fase.

Estado: Active

Estado: completado
