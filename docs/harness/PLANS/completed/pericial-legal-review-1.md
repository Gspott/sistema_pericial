# Pericial Legal Review 1

# Objetivo

Anadir una V1 informativa de revision juridica y riesgo procesal en Informe V2,
reutilizando el motor de coherencia existente.

La revision debe detectar expresiones potencialmente impugnables o
excesivamente categoricas, aportar sugerencias prudentes y no bloquear guardado,
edicion ni exportacion.

# Modulo

Informes / Informe V2 / revision de coherencia y calidad pericial.

# Riesgo

Critico por proximidad a informes, mitigado con alcance acotado:

- Sin PDF/DOCX.
- Sin cambios en `app/services/informe.py`.
- Sin cambios de esquema DB.
- Sin IA externa ni dependencias nuevas.
- Sin CRM/prospeccion.
- Heuristicas informativas, conservadoras y reversibles.

# Archivos permitidos

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan harness

# Archivos prohibidos

- `templates/informes/imprimir.html`
- `app/services/informe.py`
- CRM/prospeccion.
- DB real, uploads, backups, fotos e informes generados.
- Migraciones.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Lectura realizada:

- `AGENTS.md`
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

Diagnostico:

- `PERICIAL-CONSISTENCY-CHECKER-1` y `PERICIAL-RISKY-STATEMENTS-1` ya
  centralizan el analisis en `app/services/pericial_consistency.py`.
- El punto de extension mas pequeno es una nueva funcion de deteccion paralela
  a `detectar_afirmaciones_riesgo()`.
- La UI ya muestra "Revision de coherencia"; se anade una tercera seccion
  "Redaccion potencialmente impugnable" sin tocar flujos de guardado ni
  exportacion.

# Validaciones

- `python3 scripts/audit_docs.py`: OK antes de editar, con warnings
  preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 12 passed.
- Pendiente final:
  - `python3 scripts/audit_docs.py`
  - `python3 -m compileall app`
  - `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`
  - `git diff --check`
  - `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en:

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan/episodio si la tarea no cierra.

# Fuera de alcance

- No dar asesoramiento juridico.
- No validar si una afirmacion es correcta.
- No bloquear guardado, edicion ni exportacion.
- No tocar PDF/DOCX.
- No tocar CRM/prospeccion.
- No modificar DB ni datos reales.

# Aprobacion humana requerida

No requerida. Cambio pequeno, reversible, informativo y validado con DB
temporal de tests.

Estado: completado
