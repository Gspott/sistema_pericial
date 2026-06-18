# Pericial Quality Dashboard 1

# Objetivo

Crear una V1 del Dashboard de Calidad del Informe, agregando los resultados
existentes de coherencia, riesgo tecnico y revision juridica.

No debe crear reglas nuevas: solo calcula puntuaciones, estado, nivel y totales
desde `analizar_consistencia_expediente(expediente_id)`.

# Modulo

Informes / Informe V2 / revision de coherencia y calidad.

# Riesgo

Critico por proximidad a informes, mitigado con alcance acotado:

- Sin PDF/DOCX.
- Sin cambios de esquema DB.
- Sin CRM/prospeccion.
- Sin IA externa.
- Sin bloqueo de guardado, edicion ni exportacion.
- Agregacion determinista sobre incidencias ya existentes.

# Archivos permitidos

- `app/services/pericial_consistency.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan harness

# Archivos prohibidos

- `app/services/informe.py`
- `templates/informes/imprimir.html`
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

- `pericial_consistency.py` ya devuelve `errores`,
  `advertencias_coherencia`, `riesgos_periciales` y `revision_juridica`.
- El punto de extension minimo es calcular `dashboard_calidad` justo antes del
  `return`, reutilizando esas listas.
- La UI del editor ya muestra "Revision de coherencia"; se anade cabecera
  "CALIDAD DEL INFORME" dentro del mismo bloque, sin cambiar flujos.

# Validaciones

- `python3 scripts/audit_docs.py`: OK antes de editar, con warnings
  preexistentes.
- `python3 -m compileall app/services/pericial_consistency.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`:
  OK, 16 passed.
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

- No anadir nuevas reglas de validacion.
- No impedir exportacion.
- No exportar con advertencias.
- No checklist previa a emision.
- No historico ni evolucion entre autosaves.
- No tocar PDF/DOCX, CRM, DB ni datos reales.

# Aprobacion humana requerida

No requerida. Cambio pequeno, reversible, informativo y validado con DB
temporal de tests.

Estado: completado
