# Pericial Pdf Cleanup 1

# Objetivo

Mejorar la calidad editorial del PDF Pericial V2 eliminando vocabulario interno
del sistema y presentando solo contenido de informe.

# Modulo

Informes / PDF Pericial V2.

# Riesgo

Medio-alto por tocar salida PDF V2, mitigado porque no se modifica el PDF
clasico, la persistencia, el Workbench ni el Editor V2.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-cleanup-1.md`
- `docs/harness/EPISODES/*pericial-pdf-cleanup-1*.md`

# Archivos prohibidos

- `templates/informes/imprimir.html`
- `app/services/informe.py` salvo necesidad estricta.
- `app/database.py`
- Bases SQLite reales, informes generados, uploads y fotos.
- Modulos de patologias, costes, visitas, actuaciones, facturacion, CRM, emails y valoraciones.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir cambios de contexto/plantilla/tests. El PDF clasico queda intacto.

# Fuera de alcance

- Cambiar estructura del informe.
- Cambiar persistencia o capitulos guardados.
- Modificar Workbench o Editor V2.
- Anexos nuevos.
- IA o servicios externos.

# Aprobacion humana requerida

No prevista si el cambio queda acotado a presentacion PDF V2.

Estado: completado
