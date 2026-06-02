# Valoracion Workbench Ux Val 6

# Objetivo

Integrar progresivamente el workbench de valoracion en la UX normal del
sistema, como accion secundaria y sin sustituir la valoracion clasica.

# Modulo

Valoracion inmobiliaria / navegacion SSR.

# Riesgo

Bajo: enlaces contextuales y smokes, sin cambios de esquema, calculo ni
informes.

# Archivos permitidos

- `templates/detalle_expediente.html`
- `templates/valoracion_expediente_testigos.html`
- `tests/smoke/test_valoracion_expediente_form.py`
- `tests/smoke/test_valoracion_testigos_reutilizables_form.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB reales, backups, uploads, informes generados, secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy, patologias e inspecciones salvo lectura.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los enlaces en templates, smokes y documentacion de la fase.

# Fuera de alcance

- Redirects automaticos al workbench.
- Sustituir formularios/cards mobile-first.
- Cambiar logica de creacion/edicion de valoracion.
- Tocar informes, calculo o esquema.

# Aprobacion humana requerida

Si el cambio exigiera modificar rutas publicas existentes o navegacion global
critica.

Estado: completado
