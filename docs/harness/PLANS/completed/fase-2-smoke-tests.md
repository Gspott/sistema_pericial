# Objetivo

Crear smoke tests minimos con pytest para comprobar imports criticos, arranque/import de la app FastAPI y rutas GET basicas, sin tocar datos reales ni ejecutar integraciones externas.

# Modulo

Harness, validacion, app boot, imports criticos y rutas no destructivas.

# Riesgo

Alto por importar `app.main`, que inicializa configuracion, directorios y SQLite. Mitigacion obligatoria: variables de entorno a rutas temporales y bloqueo de lectura de `.env` real durante imports de test.

# Archivos permitidos

- `tests/conftest.py`
- `tests/smoke/test_app_boot.py`
- `tests/smoke/test_health_imports.py`
- `tests/smoke/test_routes_basic.py`
- `pytest.ini`
- `docs/harness/VALIDATION/minimal_checks.md`
- Este plan activo.

# Archivos prohibidos

- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs/`, `exports/`.
- `app/`, salvo ajuste minimo imprescindible y aprobado por necesidad tecnica.
- `templates/`, `static/`, scripts funcionales y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/secretos.md`
- `docs/harness/RISK_MAP.md`

# Validaciones

```bash
python3 scripts/audit_docs.py
python3 -m compileall app
pytest tests/smoke -q
git diff --check
git status --short
```

# Rollback

Eliminar el diff de `tests/`, `pytest.ini`, `docs/harness/VALIDATION/minimal_checks.md` y este plan. No hay migraciones ni datos reales que restaurar.

# Fuera de alcance

- Integraciones externas.
- Emails reales.
- Facturacion fiscal.
- Backups reales.
- Refactors.
- Lectura de datos generados o secretos completos.

# Aprobacion humana requerida

No prevista si los cambios se limitan a tests, pytest config y documentacion de validacion. Si hiciera falta tocar logica de aplicacion, detenerse y pedir aprobacion.

