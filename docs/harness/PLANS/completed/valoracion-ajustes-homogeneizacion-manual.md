# Valoracion Ajustes Homogeneizacion Manual

# Objetivo

Crear formulario minimo para ajustes/homogeneizacion manual por testigo
vinculado a expediente de valoracion, persistiendo coeficientes y justificacion
sin implementar calculo final de valoracion.

# Modulo

Valoracion inmobiliaria / testigos vinculados / ajustes manuales.

# Riesgo

Alto por persistencia economica preparatoria y rutas nuevas en `app/main.py`;
mitigado porque no cambia esquema, no migra datos, no toca DB real y limita el
calculo a coeficiente por testigo.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/valoracion_expediente_testigos.html`
- `templates/valoracion_testigo_ajustes.html`
- `tests/smoke/`
- `docs/modelos_datos.md`
- `docs/informes.md`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- DB real, datos reales, backups, uploads, fotos reales, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- Esquema salvo correccion defensiva imprescindible.
- Calculo final del expediente, promedio/ponderacion global y metodo de coste.
- Modificacion del testigo base al editar ajustes.
- Eliminacion de legacy.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir helpers/rutas de ajustes en `app/main.py`, revertir exposicion extra
de ajustes en `app/services/informe.py`, eliminar template y smoke nuevos,
revertir cambios documentales. No hay migracion ni datos reales.

# Fuera de alcance

- Cambiar esquema.
- Calcular valor final del expediente.
- Calcular promedio/ponderacion de testigos.
- Implementar metodo de coste.
- Gestionar fotos.
- Modificar `testigos_valoracion` desde el formulario de ajustes.

# Aprobacion humana requerida

Necesaria si aparece cambio de esquema no trivial, migracion, DB real, fotos,
calculo final, metodo de coste, outputs PDF/DOCX o routers legacy. No aplica en
esta fase.

Estado: Active

Estado: completado
