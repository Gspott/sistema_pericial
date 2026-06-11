# Pericial Pdf Design 3

# Objetivo

Ajustar exclusivamente el formato económico del Anexo D del PDF Pericial V2:
mediciones a 2 decimales, importes en formato español con símbolo euro,
negrita en importes/PEM/subtotales, alineación numérica a la derecha y
márgenes laterales reducidos solo para el Anexo D horizontal.

# Modulo

Informes / PDF Pericial V2.

# Riesgo

Crítico por tratarse de salida documental, mitigado por alcance de presentación:
no se modifica contexto económico, persistencia, costes ni cálculos.

# Archivos permitidos

- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-design-3.md`

# Archivos prohibidos

- PDF clásico y plantillas legacy.
- Workbench.
- Editor V2.
- Modelos, migraciones o tablas.
- Costes, importes, mediciones persistidas.
- Fotos, uploads, informes generados, bases de datos reales.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

- `docs/harness/PLAYBOOKS/informes.md`
- `docs/informes.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir los cambios en `templates/informes/v2_pdf.html` y las aserciones
añadidas/ajustadas en `tests/smoke/test_pericial_workbench.py`.

# Fuera de alcance

- Recalcular importes o mediciones.
- Cambiar datos de actuaciones económicas.
- Cambiar Anexos A, B, C, E o F.
- Cambiar PDF clásico, Workbench o Editor V2.

# Aprobacion humana requerida

No prevista mientras el cambio se limite a presentación del Anexo D.

Estado: completado
