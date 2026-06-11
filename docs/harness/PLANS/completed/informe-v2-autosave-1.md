# Informe V2 Autosave 1

# Objetivo

Añadir autosalvado por campo al editor estructurado de Informe Pericial V2 para evitar pérdida de texto al cerrar o recargar la página sin pulsar el guardado manual.

# Modulo

Módulo pericial / editor Informe V2 (`/expedientes/{expediente_id}/informe-v2-editor`).

# Riesgo

Bajo-medio. Toca persistencia existente de `informe_v2_capitulos`, pero reutiliza el mismo upsert del guardado manual y limita la ruta nueva a una lista blanca de claves de capítulos V2.

# Archivos permitidos

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/informe-v2-autosave-1.md`
- episodio harness asociado

# Archivos prohibidos

- Generación PDF/DOCX clásica o V2 salvo lectura.
- Módulos de costes, OCR, parser IVE, actuaciones, patologías, CRM, emails, facturación y valoraciones.
- Base de datos real, uploads, informes generados y backups.

# Playbook aplicable

Task Pack sugerido: `app_change`.

- `docs/harness/PLAYBOOKS/informes.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir los cambios de la ruta `/informes-v2/{expediente_id}/autosave`, retirar el JavaScript/estado visual del template y eliminar los tests añadidos. El guardado manual queda independiente.

# Fuera de alcance

- No se modifican PDF/DOCX.
- No se añaden tablas, campos ni migraciones.
- No se toca ningún módulo económico, OCR, patologías, actuaciones ni valoración.
- No se introduce IA ni servicios externos.

# Aprobacion humana requerida

No requerida para el alcance previsto. Sí sería requerida si apareciera necesidad de tocar datos reales o cambiar el esquema.

Estado: completado
