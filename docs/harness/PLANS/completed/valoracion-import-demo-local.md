# Valoracion Import Demo Local

# Objetivo

Importar casos demo ficticios de valoracion inmobiliaria en la DB local de
desarrollo actual, con backup previo y sin borrar ni modificar datos existentes
fuera de los casos `DEMO-VAL-*`.

# Modulo

Valoracion inmobiliaria / datos demo locales / DB desarrollo.

# Riesgo

Critico por tocar la SQLite local de desarrollo. Mitigado con backup previo,
script idempotente, prefijo `DEMO-VAL-*`, verificacion posterior y sin borrar
datos.

# Archivos permitidos

- `scripts/create_valoracion_demo_cases.py`
- `tests/fixtures/valoracion_demo_cases.py`
- `tests/smoke/test_valoracion_demo_cases.py`
- `docs/harness/EPISODES/`
- Este plan.

# Archivos prohibidos

- Datos reales existentes salvo lectura de conteos/verificacion.
- Uploads, informes reales, backups existentes y secretos.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy.
- Borrados o migraciones destructivas.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/demo_data.md`.
Task Pack no encontrado; se aplica control equivalente de demo data local con
backup previo.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m py_compile scripts/create_valoracion_demo_cases.py`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_demo_cases.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Con la app parada:

```bash
cp /Users/carlosblanco/sistema_pericial/data/before_valoracion_demo_import_20260526_095549.sqlite /Users/carlosblanco/sistema_pericial/data/pericial.db
```

# Fuera de alcance

- Produccion.
- Borrar datos.
- Usar datos reales nuevos.
- Tocar uploads/fotos/informes reales.
- Activar routers legacy.

# Aprobacion humana requerida

Ya existe peticion explicita del usuario para importar en DB local de
desarrollo. Cualquier importacion en produccion, borrado, migracion o lectura
de secretos requeriria nueva aprobacion humana.

Estado: Active

Estado: completado
