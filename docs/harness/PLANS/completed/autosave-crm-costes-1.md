# Autosave Crm Costes 1

# Objetivo

Extender `AUTOSAVE-STANDARD-1` a formularios largos y persistidos de CRM y
Costes, reutilizando la infraestructura comun existente y manteniendo guardado
manual como fallback.

El paquete debe ser pequeno, reversible y no mezclar propuestas, facturacion ni
flujos estructurales.

# Modulo

Inventario afectado:

- CRM Workbench: `templates/crm/prospeccion.html`.
  - Entra: notas internas del lead seleccionado, persistidas en `leads.notas`.
  - No entra: alta rapida, filtros, envio inmediato, programacion de email,
    cambio de estado, llamadas y creacion automatica de tareas.
- Costes: `templates/costes/detalle.html`.
  - Entra: formulario de edicion de partida existente en `costes_conceptos`,
    con foco en `descripcion` y campos principales ya persistidos.
  - No entra: alta de nueva partida, capturas/OCR, importacion BC3,
    validacion, descompuestos, borrados ni acciones estructurales.

Pantallas revisadas y fuera de fase:

- `templates/costes/captura_form.html`: alta con upload, sin entidad editable
  previa.
- `templates/costes/captura_revision.html`: mezcla revision, creacion de
  partida y OCR; requiere separacion textual/estructural si se aborda.
- `templates/costes/bc3_*`: importacion estructural.
- `templates/crm/prospeccion_agenda.html`: confirma/envia programados, accion
  irreversible o semiestructural.

# Riesgo

Medio. CRM y Costes son workbenches con texto editable y sesiones largas, pero
ambos tienen `updated_at` real. El riesgo se contiene usando endpoints
especificos, proteccion de concurrencia y manteniendo el submit manual.

# Archivos permitidos

- `app/routers/crm.py`
- `app/routers/costes.py`
- `templates/crm/prospeccion.html`
- `templates/costes/detalle.html`
- `tests/smoke/test_autosave_crm_costes.py`
- `docs/harness/PLANS/active/autosave-crm-costes-1.md`
- Episodio harness correspondiente.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos y logs.
- Migraciones o cambios de esquema.
- Propuestas, facturacion, mapa patologia estructural y refactors generales.
- Reimplementacion o duplicado de `static/js/autosave.js`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- Smoke especifico de CRM/Costes.
- Smokes existentes de CRM y Costes proporcionales.
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Retirar atributos `data-autosave-*`, hidden `updated_at`, includes del
componente visual y scripts comunes de las dos plantillas; retirar endpoints
especificos y smoke nuevo. Los guardados manuales quedan intactos.

# Fuera de alcance

- Propuestas.
- Facturacion.
- Capturas/OCR, importaciones BC3 y uploads.
- Descompuestos y validacion de partidas.
- Alta rapida sin entidad persistida previa.
- Migraciones de datos historicos.
- Cambios visuales no necesarios.

# Aprobacion humana requerida

No prevista si se mantiene el alcance. Si aparece necesidad de migracion,
uploads, OCR, envio automatico, facturacion, propuestas o cambios estructurales
de costes, abrir plan independiente y solicitar decision humana.

Estado: completado
