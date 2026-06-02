# Valoracion Qa 1 Consolidacion

# Objetivo

Consolidar y auditar Workbench de Valoracion y Biblioteca de Testigos sin
anadir funcionalidades nuevas, detectando inconsistencias UX, duplicidades,
riesgos legacy y huecos de smoke.

# Modulo

Valoracion inmobiliaria / Workbench SSR / Biblioteca de Testigos / harness.

# Riesgo

Bajo-medio. Auditoria y correcciones defensivas pequenas; no se toca DB,
calculos ni informes.

# Archivos permitidos

- `app/main.py`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB real, datos reales, backups, uploads reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes HTML/PDF/DOCX salvo documentacion menor.
- Calculos, homogeneizacion y ponderacion.
- Refactor masivo o SPA/JS nuevo.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios de `app/main.py`, smoke y documentacion de esta fase. No
requiere restaurar DB ni uploads.

# Fuera de alcance

- Nuevas features.
- Cambios de esquema o migraciones.
- Cambios de calculo.
- Cambios de informes.
- Cambios de mobile-first salvo correccion de rotura detectada.

# Aprobacion humana requerida

No prevista salvo deteccion de necesidad de DB real, esquema, datos reales,
informes o refactor mayor.

# Hallazgos

- Workbench: el filtro/diagnostico de advertencias no incluia
  `advertencias_tecnicas`, por lo que UX-VAL-8 podia mostrar avisos en la fila
  pero no hacerlos entrar en `filtro=advertencias`.
- Workbench: carga de fotos defensiva podia asumir IDs numericos; se refuerza
  para ignorar IDs no numericos aunque el contexto normal sea seguro.
- Biblioteca: rutas desktop, alta rapida, duplicados, vinculacion y fotos
  mantienen separacion entre testigo maestro y datos por expediente. No se
  detecto necesidad de cambio funcional.
- Legacy: `comparables_valoracion` y flujos antiguos siguen como fallback; no se
  toca.

# Correcciones aplicadas

- `workbench_comparable_advertencias()` suma ahora advertencias de calculo,
  homogeneizacion y tecnicas.
- `cargar_fotos_workbench_testigos()` ignora IDs vacios/no numericos antes de
  consultar fotos.
- Smoke del workbench comprueba que `filtro=advertencias` incluye avisos
  tecnicos.

Estado: completado
