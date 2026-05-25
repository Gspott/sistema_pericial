# Minimal Checks

## Checks permitidos por defecto

Primer check documental obligatorio:

```bash
python3 scripts/audit_docs.py
```

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

## Checks documentales para cambios solo en harness

```bash
python3 scripts/audit_docs.py
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
