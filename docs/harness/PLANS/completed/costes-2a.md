# Costes 2A

# Objetivo

Implementar COSTES-2A: workbench escritorio SSR/manual para buscar, crear,
editar y validar partidas de costes con descomposicion.

# Modulo

Costes de reparacion.

# Riesgo

Medio-alto por crear rutas nuevas y registrar router. No cambia esquema,
facturacion, patologias, informes ni datos reales.

# Archivos permitidos

- `app/routers/costes.py`
- `app/main.py` solo para importar/incluir el router nuevo solicitado.
- `templates/costes/listado.html`
- `templates/costes/form.html`
- `templates/costes/detalle.html`
- `tests/smoke/test_costes_workbench.py`
- este plan y episodio harness.

# Archivos prohibidos

- DB real, backups, uploads, informes, fotos, logs y secretos.
- Patologias, expedientes, inspecciones, valoraciones, CRM, emails,
  facturacion e informes.
- Navegacion global salvo que el patron real lo exija; en esta fase no se
  modifica drawer.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

Playbooks: `docs/harness/PLAYBOOKS/base_datos.md` y
`docs/harness/PLAYBOOKS/jinja.md`.

Nota: `include_router()` se limita a un router nuevo, aislado y solicitado por
la fase COSTES-2A. No activa routers legacy.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `pytest tests/smoke/test_costes_workbench.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir router, templates, test, import/include en `app/main.py` y docs
harness de esta fase. Descartar DB temporal de pytest.

# Fuera de alcance

- OCR.
- Importador BC3/FIEBDC.
- Conexion con patologias, expedientes, inspecciones, informes o facturacion.
- Edicion de fuentes/capturas.
- Navegacion global.

# Aprobacion humana requerida

No requerida: el usuario pidio explicitamente crear y registrar el router nuevo.
Requerida en fases futuras si se conecta con patologias/informes o se toca DB
real.

Estado: completado
