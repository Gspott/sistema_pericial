# Costes 2B

# Objetivo

Implementar COSTES-2B: captura rapida desde pantallazo para crear partidas de
costes con revision manual, manteniendo trazabilidad de imagen y fuente.

# Modulo

Costes de reparacion.

# Riesgo

Medio-alto por subida de archivos y nuevas rutas SSR. Mitigado con extensiones
limitadas, nombre UUID, rutas relativas bajo uploads temporal en tests y sin
OCR/importador/relacion con patologias.

# Archivos permitidos

- `app/routers/costes.py`
- `templates/costes/listado.html` solo enlace local a capturas.
- `templates/costes/capturas_listado.html`
- `templates/costes/captura_form.html`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- este plan y episodio harness.

# Archivos prohibidos

- DB real, backups, informes, fotos, logs y secretos.
- Patologias, expedientes, inspecciones, valoraciones, CRM, emails,
  facturacion e informes.
- Navegacion global/drawer.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

Playbooks: `docs/harness/PLAYBOOKS/base_datos.md` y
`docs/harness/PLAYBOOKS/jinja.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir cambios en router, templates, test, plan y episodio. Descartar DB y
uploads temporales generados por pytest.

# Fuera de alcance

- OCR real o automatico.
- Importador BC3/FIEBDC.
- Conexion con patologias, expedientes, informes o facturacion.
- Descarte avanzado o borrado fisico de imagenes.
- Navegacion global.

# Aprobacion humana requerida

No requerida: fase aislada solicitada por el usuario. Requerida si una fase
posterior usa OCR real, integra BC3 o conecta costes con patologias/informes.

Estado: completado
