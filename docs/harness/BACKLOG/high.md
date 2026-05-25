# High Backlog

Usar esta prioridad para problemas que no son emergencia inmediata, pero condicionan cambios seguros en modulos criticos.

## Monolito app/main.py

- Impacto: eleva riesgo de cambios cruzados y dificulta mantenimiento.
- Modulos: backend, expedientes, visitas, informes, auth.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: `python3 -m compileall app`, `pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea refactors grandes sin plan.
- Dependencias: ampliar smoke tests antes de extracciones por flujo.

## Decidir Destino De Carpeta Anidada `sistema_pericial/`

- Impacto: reduce riesgo de tocar copia equivocada, datos sensibles o entorno local anidado.
- Modulos: seguridad, workspace, datos locales.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md` con aprobacion humana.
- Validaciones minimas: auditoria solo lectura; no leer DB ni datos generados; `git status --short`.
- Bloqueo/no bloqueo: Bloquea limpiezas o reorganizaciones del workspace.
- Dependencias: decision humana sobre conservar, mover, archivar o eliminar tras backup verificado.

## Mapa `app/main.py` Vs Routers No Incluidos

- Impacto: evita borrar codigo que podria ser extraccion parcial y prepara refactor gradual seguro.
- Modulos: expedientes, visitas, estancias, patologias, informes.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: mapa de rutas, `python3 -m compileall app`, `pytest tests/smoke -q`.
- Bloqueo/no bloqueo: No bloquea cambios quirurgicos; bloquea limpieza de routers no incluidos.
- Dependencias: smoke tests por flujo y aprobacion antes de incluir o eliminar rutas.

## Crear Mapa Ruta A Ruta `app/main.py` Vs Routers Legacy

- Impacto: permite decidir que rutas pueden extraerse y cuales son obsoletas.
- Modulos: expedientes, visitas, estancias, patologias.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: auditoria solo lectura, `python3 scripts/audit_docs.py`.
- Bloqueo/no bloqueo: Bloquea cualquier `include_router()` de routers legacy.
- Dependencias: `docs/harness/AGENT_MAPS/main_vs_routers_map.md`.

## Smoke Ownership Expedientes/Visitas Antes De Extraccion

- Impacto: evita regresiones de seguridad al mover rutas desde `app/main.py`.
- Modulos: expedientes, visitas, auth, DB.
- Riesgo: Alto.
- Task Pack recomendado: `docs/harness/TASK_PACKS/bugfix.md`.
- Validaciones minimas: `python3 -m pytest tests/smoke -q`, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: Bloquea extraccion de rutas con `owner_user_id`.
- Dependencias: fixtures temporales y usuarios demo, sin DB real.
