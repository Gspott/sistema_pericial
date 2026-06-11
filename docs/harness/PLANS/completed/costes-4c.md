# Costes 4C

# Objetivo

Permitir incluir opcionalmente un anexo económico de reparación en el informe pericial, basado en costes vinculados a patologías y desactivado por defecto.

# Modulo

- `build_informe_context`.
- Plantilla HTML/PDF moderna `informes/imprimir.html`.
- Endpoints de informe HTML/PDF/DOCX editable con flag por generación.
- Detalle de expediente como punto de activación UI.
- Tests smoke de informes y costes.

# Riesgo

Bajo-medio. Primera integración de costes en informe, mitigada por flag explícito, ausencia de costes = sin anexo, y comportamiento por defecto sin cambios.

# Archivos permitidos

- `app/main.py`
- `app/services/informe.py`
- `templates/detalle_expediente.html`
- `templates/informes/imprimir.html`
- `tests/smoke/test_patologia_costes.py`
- `docs/harness/PLANS/active/costes-4c.md`
- episodio harness COSTES-4C

# Archivos prohibidos

- Facturación, CRM, emails y valoraciones.
- Costes base.
- Presupuesto comercial/factura.
- Datos reales, backups, uploads reales, logs y secretos.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- smoke informes + costes
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir archivos listados. No hay cambios de esquema.

# Fuera de alcance

- IVA, beneficio industrial y gastos generales.
- Presupuesto comercial o factura.
- Activación automática del anexo.
- Costes de patologías exteriores.

# Aprobacion humana requerida

Para convertir el anexo en presupuesto comercial, añadir impuestos/márgenes o conectar con facturación.

Estado: completado
