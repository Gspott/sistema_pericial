# Minimal Checks

## Checks permitidos por defecto

Primer check documental obligatorio:

```bash
python3 scripts/audit_docs.py
```

`audit_docs.py` incluye avisos informativos de `PROJECT-STANDARDS-GUARD-1`; en particular, alerta sobre posibles usos nuevos de `datetime.now()` o `datetime.utcnow()` en archivos Python modificados.

Comando principal recomendado:

```bash
bash scripts/validate_harness.sh
```

Scopes de validacion disponibles:

```bash
bash scripts/validate_harness.sh --smoke-scope docs
bash scripts/validate_harness.sh --smoke-scope app
bash scripts/validate_harness.sh --smoke-scope valoracion
bash scripts/validate_harness.sh --smoke-scope full
```

`full` es el valor por defecto. `docs` y `app` reducen coste, pero no saltan
`audit_docs` ni `git diff --check`. `valoracion` ejecuta la seleccion de smoke
con `pytest tests/smoke -q -k valoracion`.

El runner calcula un scope minimo por paths modificados y eleva
automaticamente scopes insuficientes. Ejemplo: pedir `docs` con cambios en
`templates/valoracion_testigos.html` acaba ejecutando `valoracion`. El override
`--allow-unsafe-scope` existe, pero debe reservarse para casos justificados y
documentados.

Checks generales:

```bash
python3 scripts/audit_docs.py
python3 -m compileall app
node --check ./static/app_shell.js
node --check static/pwa.js
node --check static/sw.js
bash -n start_all.sh start_server.sh stop_all.sh status.sh backup.sh backup_now.sh
git diff --check
git status --short
```

## Smoke tests minimos actuales

```bash
pytest tests/smoke -q
```

Obligatorios para cambios de harness/testing:

- `tests/smoke/test_app_boot.py`
- `tests/smoke/test_health_imports.py`
- `tests/smoke/test_routes_basic.py`
- `tests/smoke/test_facturacion_calculos.py`
- `tests/smoke/test_propuestas_flow.py`
- `tests/smoke/test_informe_context.py`
- `tests/smoke/test_backup_zip.py`

Requieren entorno extra:

- `pytest` instalado desde `requirements.txt`.
- No requieren SMTP, Playwright, Catastro, OpenAI, Telegram, clima ni DuckDNS.

## Checks documentales para cambios solo en harness

```bash
bash scripts/finish_harness_task.sh --smoke-scope docs
git diff --check
git status --short
```

## Smoke tests recomendados futuros

```bash
pytest tests/smoke/test_app_boot.py
pytest tests/smoke/test_facturacion_calculos.py
pytest tests/smoke/test_propuestas_flow.py
pytest tests/smoke/test_email_mock.py
pytest tests/smoke/test_backup_zip.py
pytest tests/smoke/test_informe_context.py
```

## Reglas

- No ejecutar pruebas que toquen datos reales.
- No enviar emails reales.
- No levantar tuneles o deploy externo como parte de validacion automatica.
- Usar DB temporal para smoke tests de persistencia.
- Revisar `docs/harness/VALIDATION/project_standards_guard.md` cuando una tarea toque fechas, formularios largos, seleccion reactiva, estado visual, concurrencia, PDF/documentos o flujos mobile/desktop.
