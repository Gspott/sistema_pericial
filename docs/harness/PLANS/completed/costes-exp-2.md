# Costes Exp 2

# Objetivo

Implementar COSTES-EXP-2: el anexo económico opcional del informe debe usar actuaciones de reparación como fuente principal cuando existan partidas, manteniendo fallback a `patologia_costes`.

# Modulo

Informes / costes / expedientes / Jinja / DOCX editable.

# Riesgo

Alto por tocar informes. Cambio limitado al anexo opcional con flag explícito; sin flag el informe debe mantenerse igual.

# Archivos permitidos

- `app/services/informe.py`
- `app/main.py`
- `templates/informes/imprimir.html`
- `templates/detalle_expediente.html`
- `templates/actuaciones_reparacion.html`
- `tests/smoke/test_patologia_costes.py`
- `tests/smoke/test_actuaciones_reparacion.py`
- `docs/harness/PLANS/active/costes-exp-2.md`
- `docs/harness/EPISODES/2026-06-05-costes-exp-2.md`
- `docs/harness/METRICS.md` si cambia al cierre

# Archivos prohibidos

- Facturación, CRM, emails y valoración.
- Datos reales SQLite, uploads, informes generados, backups, fotos y logs.
- Eliminación o modificación destructiva de `patologia_costes`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

- `docs/harness/PLAYBOOKS/informes.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_actuaciones_reparacion.py tests/smoke/test_patologia_costes.py tests/smoke/test_informe_context.py tests/smoke/test_flow_expediente_informe.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay borrado de datos ni migración nueva.

# Fuera de alcance

- Generar factura, presupuesto comercial o propuesta.
- Eliminar anexo por patologías.
- Cambiar lógica de patologías o biblioteca de costes.
- Añadir IVA, gastos generales o beneficio industrial.

# Aprobacion humana requerida

Si se quisiera cambiar el informe sin flag, modificar conclusiones técnicas o alterar facturación/presupuestos comerciales.

# Decisión

Las actuaciones de reparación son la fuente principal del anexo económico. Si no hay actuaciones con partidas, se mantiene el fallback de COSTES-4C basado en costes vinculados a patologías.

Estado: completado
