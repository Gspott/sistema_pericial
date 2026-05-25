# Objetivo

Añadir smoke tests minimos de negocio para detectar regresiones criticas sin usar datos reales ni integraciones externas.

# Modulo

Facturacion, propuestas, informes y backups, ejercitados solo desde tests con entorno temporal.

# Riesgo

Critico por tocar superficies fiscales, documentales y backups mediante imports y helpers. Mitigacion: no cambiar logica, no usar DB real, no enviar emails, no usar Playwright, no llamar integraciones externas y no ejecutar POST/rutas destructivas.

# Archivos permitidos

- `tests/smoke/test_facturacion_calculos.py`
- `tests/smoke/test_propuestas_flow.py`
- `tests/smoke/test_informe_context.py`
- `tests/smoke/test_backup_zip.py`
- `tests/conftest.py` si hace falta reutilizar fixtures temporales.
- `docs/harness/VALIDATION/minimal_checks.md`
- Este plan activo.

# Archivos prohibidos

- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs/`, `exports/`.
- `app/`, salvo ajuste minimo imprescindible y previa aprobacion.
- `templates/`, `static/`, scripts funcionales y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/PLAYBOOKS/facturacion.md`
- `docs/harness/PLAYBOOKS/propuestas.md`
- `docs/harness/PLAYBOOKS/informes.md`
- `docs/harness/PLAYBOOKS/backups_restore.md`
- `docs/harness/PLAYBOOKS/base_datos.md`

# Validaciones

```bash
python3 scripts/audit_docs.py
python3 -m compileall app
python3 -m compileall tests
pytest tests/smoke -q
git diff --check
git status --short
```

# Rollback

Revertir los nuevos tests, cualquier ajuste puntual de `tests/conftest.py`, la actualizacion de validacion documental y este plan. No hay datos reales que restaurar.

# Fuera de alcance

- DB real.
- Emails/SMTP reales.
- Playwright real.
- Catastro, OpenAI, Telegram, clima, DuckDNS.
- Numeracion fiscal, emision/anulacion/rectificativas.
- Generacion PDF/DOCX real compleja.
- Refactors.

# Aprobacion humana requerida

No prevista mientras los cambios queden en tests y documentacion. Si se necesita tocar logica de negocio, detenerse y pedir aprobacion.

