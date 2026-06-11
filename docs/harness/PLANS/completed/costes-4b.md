# Costes 4B

# Objetivo

Crear vista de presupuesto de reparación por expediente a partir de `patologia_costes`, agregando subtotales por patología y total PEM, sin modificar informes ni generar exportaciones.

# Modulo

- Ruta SSR de expediente.
- Plantilla de presupuesto de reparación.
- Enlace local desde detalle de expediente.
- Tests smoke de presupuesto/costes/patologías.

# Riesgo

Bajo-medio. Agregación de solo lectura sobre datos ya vinculados. No hay cambios de esquema, no se modifican costes base, informes, facturación ni lógica de patologías.

# Archivos permitidos

- `app/main.py`
- `templates/detalle_expediente.html`
- `templates/presupuesto_reparacion.html`
- `tests/smoke/test_patologia_costes.py`
- `docs/harness/PLANS/active/costes-4b.md`
- episodio harness COSTES-4B

# Archivos prohibidos

- Generación de informes.
- Facturación, CRM, emails y valoraciones.
- Costes base.
- Datos reales, backups, uploads reales, logs y secretos.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- smoke costes + patologías + presupuesto
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay cambios de esquema en esta fase.

# Fuera de alcance

- PDF, DOCX, informe o anexo económico.
- Factura/presupuesto comercial.
- Edición desde la vista de presupuesto.
- Patologías exteriores.

# Aprobacion humana requerida

Para introducir exportación, informe, facturación o afectar datos reales.

Estado: completado
