# Costes 4A

# Objetivo

Vincular partidas de costes a patologías interiores de forma controlada, copiando snapshot de unidad/precio, calculando subtotal por medición y manteniendo informes sin cambios.

# Modulo

- Base de datos: tabla `patologia_costes`.
- Edición de patología interior (`/editar-registro/{id}`).
- Rutas aisladas de costes de patología.
- Tests smoke de costes/patologías.

# Riesgo

Medio. Primer contacto entre módulo de costes y patologías. Mitigación: tabla nueva idempotente, rutas aisladas, snapshot de precio/unidad, sin tocar informes, sin presupuesto global y sin modificar partidas base.

# Archivos permitidos

- `app/database.py`
- `app/main.py` solo bloque aislado de costes de patología y contexto de edición.
- `templates/editar_registro.html` solo sección “Coste de subsanación”.
- `tests/smoke/test_patologia_costes.py`
- `docs/harness/PLANS/active/costes-4a.md`
- episodio harness COSTES-4A

# Archivos prohibidos

- Informes.
- Facturación, CRM, emails y valoraciones.
- Lógica funcional existente de patologías fuera del bloque aislado de costes.
- Datos reales, backups, uploads reales, logs y secretos.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- smoke costes + patologías/informe relevantes
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los archivos listados. La tabla nueva es aditiva e idempotente; no se borran ni renombran tablas existentes.

# Fuera de alcance

- Informes.
- Presupuesto global por expediente.
- Facturación.
- Patologías exteriores.
- Cambios en partidas base al editar medición de patología.

# Aprobacion humana requerida

Para conectar con informes/facturación, tocar datos reales o ampliar a presupuesto global.

Estado: completado
