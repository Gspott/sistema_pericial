# Pericial Risky Statements 1

# Objetivo

Extender `PERICIAL-CONSISTENCY-CHECKER-1` con una revision informativa de
afirmaciones pericialmente sensibles en capitulos del Informe V2.

Debe detectar patrones de riesgo sin afirmar que el texto sea incorrecto, y
sin bloquear guardado, edicion ni exportacion.

# Modulo

Informes / Informe V2 / revision de coherencia pericial.

# Riesgo

Critico por proximidad a informes, mitigado con alcance acotado:

- Sin tocar PDF/DOCX.
- Sin tocar `build_informe_context()`.
- Sin migraciones ni cambios de esquema.
- Sin IA externa.
- Sin cambios en CRM/prospeccion.
- Solo heuristicas informativas y conservadoras.

# Archivos permitidos

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan harness

# Archivos prohibidos

- `templates/informes/imprimir.html`
- `app/services/informe.py`
- Generacion PDF/DOCX.
- Datos reales, uploads, informes generados, fotos, backups y DB real.
- CRM/prospeccion.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Lectura realizada:

- `docs/harness/PROJECT_RULES.md`
- `docs/harness/PERMISSIONS.md`
- `docs/harness/CONTEXT_STRATEGY.md`
- `docs/harness/RISK_MAP.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/GOLDEN_PRINCIPLES.md`
- `docs/harness/PLAYBOOKS/informes.md`
- `docs/harness/TASK_PACKS/informe_change.md`
- `docs/informes.md`
- `docs/revision_probatoria.md`

Diagnostico:

- La revision de coherencia ya centraliza incidencias en
  `analizar_consistencia_expediente()`.
- El punto mas seguro es reutilizar esa respuesta, anadiendo
  `riesgos_periciales` y manteniendo las incidencias tambien dentro de
  `advertencias`.
- El HTML actual ya renderiza "Revision de coherencia"; se puede anadir una
  subseccion "Afirmaciones a revisar" sin tocar flujos de guardado/exportacion.

# Validaciones

- `python3 scripts/audit_docs.py`: OK antes de editar, con warnings
  preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 8 passed.
- Pendiente de cierre:
  - `python3 scripts/audit_docs.py`
  - `python3 -m compileall app`
  - `git diff --check`
  - `bash scripts/finish_harness_task.sh`

# Rollback

Revertir cambios en:

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan/episodio si la tarea no cierra.

# Fuera de alcance

- No modificar PDF.
- No modificar generacion DOCX.
- No modificar esquema DB.
- No usar IA externa.
- No emitir criterio juridico ni validar si una afirmacion es correcta.
- No tocar CRM/prospeccion.

# Aprobacion humana requerida

No requerida: cambio pequeno, reversible, informativo y validado sobre DB
temporal de tests.

Estado: completado
