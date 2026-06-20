# Autosave Patologias Visitas 1

# Objetivo

Extender `AUTOSAVE-STANDARD-1` a la primera subfase del rollout en formularios de visita con riesgo de perdida de informacion en campo, reutilizando `static/js/autosave.js` y el componente visual estandar.

# Modulo

Visitas y observaciones de visita de valoracion.

# Riesgo

Medio. Son formularios de campo y mobile-first. Se limita el primer bloque a fichas de visita existentes y observaciones de portal/contadores para mantener el diff reversible. No se migran datos ni se modifica esquema.

# Archivos permitidos

- `app/main.py`
- `templates/nueva_visita.html`
- `templates/editar_visita.html`
- `static/mobile.css`
- `tests/smoke/test_valoracion_nueva_visita_ux.py`
- episodio harness asociado.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos, logs y secretos.
- Migraciones de esquema.
- Reimplementacion o duplicado de `static/js/autosave.js`.
- Cambios funcionales en facturacion, CRM, costes o propuestas.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

- `docs/harness/PATTERNS/autosave_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PLAYBOOKS/jinja.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- smoke de visitas/autosave
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Retirar los atributos `data-autosave-*`, los includes del componente, los endpoints `/autosave` de visita/observaciones y los tests añadidos. El guardado manual queda intacto.

# Fuera de alcance

- Autosave de registros de patologias interiores/exteriores.
- Autosave de mapas/cuadrantes de patologias.
- Autosave de estancias.
- CRM, costes, propuestas y otros formularios largos.
- Migrar `visitas` para anadir `updated_at`.

# Aprobacion humana requerida

Solo si se decide modificar esquema, tocar datos reales o ampliar la subfase a otros modulos en el mismo diff.

Estado: completado
