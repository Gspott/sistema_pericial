# Valoracion Testigos Reutilizables Form

# Objetivo

Crear formulario minimo de testigos reutilizables y seleccion/vinculacion por
expediente de valoracion, guardando snapshot historico y sin implementar
homogeneizacion ni calculo.

# Modulo

Valoracion inmobiliaria / testigos reutilizables / expedientes.

# Riesgo

Alto por tocar `app/main.py`, detalle de expediente y smoke de flujo; mitigado
con cambios server-side pequenos, sin esquema nuevo, sin migracion y sin tocar
PDF/DOCX ni calculo.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/valoracion_testigos.html`
- `templates/valoracion_testigo_form.html`
- `templates/valoracion_expediente_testigos.html`
- `templates/detalle_expediente.html`
- `tests/smoke/`
- `docs/modelos_datos.md`
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
- Calculo, homogeneizacion y resultados finales.
- Gestion/subida de fotos de testigos.
- Eliminacion de `comparables_valoracion`.

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

Revertir rutas/helpers de testigos en `app/main.py`, revertir exposicion extra
de orden/incluido/notas en `app/services/informe.py`, eliminar templates y
smoke nuevos, quitar CTA del detalle y revertir docs. No hay migracion ni datos
reales implicados.

# Fuera de alcance

- Crear o modificar esquema.
- Migrar `comparables_valoracion`.
- Homogeneizar testigos o calcular valor final.
- Gestionar fotos reales de testigos.
- Borrar testigos base.

# Aprobacion humana requerida

Necesaria si aparece cambio de esquema no trivial, migracion, DB real, fotos,
calculo/homogeneizacion, outputs PDF/DOCX o routers legacy. No aplica en esta
fase.

Estado: Active

Estado: completado
