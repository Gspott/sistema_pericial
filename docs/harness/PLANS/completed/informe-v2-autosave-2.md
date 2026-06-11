# Informe V2 Autosave 2

# Objetivo

Mejorar la fiabilidad percibida y real del autosave del Editor V2, evitando un estado inicial engañoso y protegiendo el guardado manual frente a contenido autosalvado más reciente.

# Modulo

Pericial / Informe V2 / editor estructurado.

# Riesgo

Bajo-medio. Cambia el flujo de guardado manual del editor V2 para detectar conflictos por `updated_at`, sin cambiar esquema ni generación de informes.

# Archivos permitidos

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/informe-v2-autosave-2.md`
- episodio harness asociado

# Archivos prohibidos

- PDF/DOCX.
- Workbench pericial.
- Costes, patologías, visitas, fotos, CRM, emails, facturación y valoraciones.
- Base de datos real, uploads, informes generados y backups.

# Playbook aplicable

Task Pack sugerido: `app_change`.

- `docs/harness/PLAYBOOKS/informes.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Retirar la comparación `updated_at_*` del guardado manual, devolver el estado inicial visual anterior y eliminar los tests añadidos. No hay cambios de esquema que revertir.

# Fuera de alcance

- No rediseñar el editor.
- No tocar PDF/DOCX.
- No cambiar estructura de `informe_v2_capitulos`.
- No implementar resolución avanzada de conflictos.

# Aprobacion humana requerida

No requerida para el alcance actual. Sí sería necesaria para cambiar esquema o tocar datos reales.

Estado: completado
