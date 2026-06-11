# Costes Ive 1E Diagnostico

# Objetivo

Implementar COSTES-IVE-1E diagnóstico: seguir el ciclo de vida de `MOOA12a` desde texto OCR hasta parser, JSON, contexto GET y template de revisión.

# Modulo

Costes / capturas / parser IVE / revisión manual.

# Riesgo

Bajo. Diagnóstico con test de integración; no toca OCR ni módulos de negocio.

# Archivos permitidos

- `tests/smoke/test_costes_capturas.py`
- `docs/harness/PLANS/active/costes-ive-1e-diagnostico.md`
- `docs/harness/EPISODES/2026-06-06-costes-ive-1e-diagnostico.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- OCR.
- Parser salvo bug real.
- Informes, actuaciones, patologías, facturación, CRM, emails y valoraciones.
- Datos reales, uploads, informes generados, backups, fotos y logs.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/app_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py tests/smoke/test_costes_bc3.py tests/smoke/test_patologia_costes.py tests/smoke/test_actuaciones_reparacion.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir test y documentos harness. No hay cambios de datos.

# Fuera de alcance

- Cambiar OCR.
- Cambiar parser si no se reproduce bug real.
- Leer datos reales.

# Aprobacion humana requerida

Si se quisiera inspeccionar la captura real o datos SQLite reales.

# Diagnóstico

Con OCR exacto:

`MOOA12a h Peón ordinario construcción 21.08€ 0.500 10.54€`
`% % Costes directos complementarios 10.54€ 0.020 021€`

el ciclo completo conserva `MOOA12a`:

- parser: `datos_parseados.descompuestos` contiene `MOOA12a` y `%`.
- JSON guardado: `datos_extraidos_json.datos_parseados.descompuestos` contiene ambos.
- contexto GET: `descompuestos_sugeridos` contiene ambos.
- HTML: aparecen `MOOA12a`, `Peón ordinario construcción` y `Costes directos complementarios`.

No se reproduce desaparición con ese texto exacto. Causa probable en uso real: captura no reextraída, JSON antiguo o texto OCR real diferente.

Estado: completado
