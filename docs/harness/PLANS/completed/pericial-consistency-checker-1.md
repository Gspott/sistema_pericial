# Pericial Consistency Checker 1

# Objetivo

Crear una V1 informativa del motor de revision de coherencia pericial para
expedientes de informe real, sin modificar PDF/DOCX ni datos existentes.

La funcion publica nueva es
`analizar_consistencia_expediente(expediente_id: int) -> dict`.

# Modulo

Informes / Informe V2 / revision pericial previa a emision.

# Riesgo

Critico por proximidad a informes, mitigado con alcance acotado:

- Solo lectura sobre SQLite.
- Sin migraciones.
- Sin tocar generacion PDF/DOCX.
- Sin bloqueo de guardado, exportacion ni emision manual.
- Heuristicas V1 defensivas y trazables.

# Archivos permitidos

- `app/services/pericial_consistency.py`
- Integracion minima en `app/main.py`
- Bloque informativo en `templates/informe_v2_editor.html`
- Smoke tests en `tests/smoke/`
- Este plan harness

# Archivos prohibidos

- Informes reales generados.
- Fotos, uploads y backups reales.
- Bases SQLite reales.
- Generacion PDF/DOCX.
- Routers legacy no incluidos.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Playbooks y fuentes revisados:

- `docs/harness/PROJECT_RULES.md`
- `docs/harness/PERMISSIONS.md`
- `docs/harness/CONTEXT_STRATEGY.md`
- `docs/harness/RISK_MAP.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/GOLDEN_PRINCIPLES.md`
- `docs/harness/PLAYBOOKS/informes.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/harness/EXECUTION_POLICY.md`
- `docs/backend.md`
- `docs/informes.md`
- `docs/revision_probatoria.md`
- `docs/ux.md`

Diagnostico:

- Informe V2 mantiene capitulos en `informe_v2_capitulos`.
- Fotos proceden de `visita_fotos`, `estancia_fotos`,
  `registro_patologia_fotos` y `registro_patologia_exterior_fotos`.
- Documentos aportados proceden de `expediente_documentos`.
- El punto de integracion menos invasivo es el editor de Informe V2, en el
  panel de contexto, como bloque no imprimible y no bloqueante.
- El endpoint interno seguro es una ruta en `app/main.py` con
  `get_owned_expediente`, sin activar routers legacy ni crear API de negocio
  paralela.

# Validaciones

- `python3 scripts/audit_docs.py` antes de editar: OK con warnings
  preexistentes de planes completados vacios y tamano de `app/main.py`.
- `python3 -m compileall app/services/pericial_consistency.py app/main.py`: OK.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`: OK,
  5 passed.
- Pendiente de cierre: `bash scripts/finish_harness_task.sh`.

# Rollback

Revertir cambios en:

- `app/services/pericial_consistency.py`
- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_consistency.py`
- Este plan y episodio asociado si el cierre no procede.

# Fuera de alcance

- No modificar PDF/DOCX.
- No cambiar `build_informe_context()`.
- No bloquear generacion manual, guardado ni exportacion.
- No introducir IA externa.
- No implementar Legal Review ni Risky Statements salvo heuristica basica de
  conclusion sin soporte minimo.
- No cambiar esquema de base de datos.
- No tocar datos reales, uploads, backups, fotos ni informes generados.

# Aprobacion humana requerida

No requerida para el diff aplicado: cambio pequeno, reversible, de solo lectura
y validado en DB temporal.

Estado: completado
