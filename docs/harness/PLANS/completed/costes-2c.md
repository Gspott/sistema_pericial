# Costes 2C

# Objetivo

Implementar COSTES-2C: extraccion asistida local/opcional desde capturas de
costes, con revision manual obligatoria y sin guardado automatico.

# Modulo

Costes de reparacion.

# Riesgo

Medio-alto por procesado local de imagen y parser heuristico. Mitigado con
OCR opcional, sin dependencias obligatorias nuevas, sin IA externa, sin red y
sin crear conceptos desde la accion de extraccion.

# Archivos permitidos

- `app/services/costes_ocr.py`
- `app/services/costes_parser.py`
- `app/routers/costes.py`
- `templates/costes/captura_revision.html`
- `tests/smoke/test_costes_capturas.py`
- este plan y episodio harness.

# Archivos prohibidos

- DB real, backups, informes, fotos, logs, secretos.
- Patologias, expedientes, inspecciones, valoraciones, CRM, emails,
  facturacion e informes.
- Importador BC3.
- Navegacion global.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

Playbooks: `docs/harness/PLAYBOOKS/base_datos.md` y
`docs/harness/PLAYBOOKS/jinja.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_costes_capturas.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_costes_db.py tests/smoke/test_costes_workbench.py tests/smoke/test_costes_capturas.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir servicios, ruta `/extraer`, cambios de template/test, plan y episodio.
Descartar DB/uploads temporales generados por pytest.

# Fuera de alcance

- IA externa.
- Servicios online.
- OCR obligatorio o definitivo.
- Importador BC3.
- Conexion con patologias, informes o facturacion.
- Validacion automatica de la partida extraida.

# Aprobacion humana requerida

No requerida para esta fase aislada solicitada. Requerida si una fase posterior
usa servicios externos, introduce dependencia obligatoria, conecta patologias o
importa BC3.

Estado: completado
