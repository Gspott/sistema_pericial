# Pericial Docs A 1

# Objetivo

Permitir gestionar desde el Workbench pericial documentos PDF aportados al
expediente para que aparezcan ordenados en el Anexo A del PDF Pericial V2 con
nombre pericial editable y orden manual.

# Modulo

Informes / PDF Pericial V2 / Workbench pericial / esquema SQLite idempotente.

# Riesgo

Crítico por tocar esquema e informe, mitigado por tabla nueva idempotente,
subida limitada a PDF, ownership del expediente y presentación sin incrustar
documentos completos.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `templates/pericial_workbench.html`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-docs-a-1.md`

# Archivos prohibidos

- PDF clásico y plantillas legacy.
- Editor V2 salvo enlaces si fueran imprescindibles.
- Patologías, costes, fotos, visitas y captura móvil.
- Datos reales, uploads reales ajenos a pruebas, informes generados y backups.

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

Revertir cambios en esquema idempotente, helpers/rutas del Workbench,
template del Workbench, Anexo A del PDF V2 y smoke tests asociados.

# Fuera de alcance

- Incrustar PDFs completos en el informe.
- Recalcular o modificar costes/importes.
- Cambiar patologías, fotos, visitas o captura móvil.
- Cambiar PDF clásico.
- Crear clasificación IA o extracción de contenido documental.

# Aprobacion humana requerida

No prevista si el cambio se limita a tabla nueva y gestión documental del
Anexo A con archivos PDF.

Estado: completado
