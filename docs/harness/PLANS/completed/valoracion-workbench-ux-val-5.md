# Valoracion Workbench Ux Val 5

# Objetivo

Mejorar la trazabilidad tecnica de los ajustes de homogeneizacion dentro del
workbench SSR de valoracion inmobiliaria, sin cambiar calculos persistidos ni
convertir la vista en editor inline.

# Modulo

Valoracion inmobiliaria / workbench SSR.

# Riesgo

Bajo-medio: solo presentacion SSR y smokes. No cambia esquema, persistencia ni
calculo de valoracion.

# Archivos permitidos

- `app/main.py`
- `templates/valoracion_workbench.html`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB reales, backups, uploads, informes generados, secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy y modulos de patologias/inspecciones salvo lectura.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir cambios en helper de presentacion del workbench, template y smokes.

# Fuera de alcance

- Edicion inline de ajustes.
- Recalculo automatico desde el panel.
- Batch edit, scoring, outliers, IA.
- Adopcion automatica de valor final.

# Aprobacion humana requerida

Si aparece necesidad de cambiar esquema, migrar datos o modificar calculos.

Estado: completado
