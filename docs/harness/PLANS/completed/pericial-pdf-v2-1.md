# Pericial Pdf V2 1

# Objetivo

Implementar la primera exportacion PDF independiente del modelo pericial V2,
consumiendo exclusivamente capitulos guardados en `informe_v2_capitulos`.

# Modulo

Informes / pericial V2 / exportacion PDF.

# Riesgo

Alto por tocar flujo de informes y PDF, mitigado con rutas y plantilla separadas,
sin modificar `build_informe_context`, sin sustituir el PDF clasico y sin tocar
patologias, visitas, costes, actuaciones ni fotografias.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/informes/v2_pdf.html`
- `templates/informe_v2_editor.html`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-v2-1.md`
- `docs/harness/EPISODES/*pericial-pdf-v2-1*.md`

# Archivos prohibidos

- Bases SQLite reales.
- Informes generados reales, uploads y fotos.
- `templates/informes/imprimir.html`
- Modulos de facturacion, CRM, emails, costes, patologias, visitas y valoracion.
- Cambios en la logica del informe clasico.

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

Revertir rutas/helpers V2, plantilla V2, enlaces y tests. El PDF clasico no se
modifica.

# Fuera de alcance

- Sustituir el informe clasico.
- PDF/DOCX V2 completo con anexos redisenados.
- Regenerar borradores o reconstruir texto desde patologias.
- Editar capitulos desde la exportacion.

# Aprobacion humana requerida

No prevista si la exportacion permanece paralela y consume solo capitulos
guardados.

Estado: completado
