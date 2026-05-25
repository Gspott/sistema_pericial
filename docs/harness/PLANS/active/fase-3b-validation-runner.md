# Objetivo

Crear un runner unico y seguro para validar el sistema completo sin tocar datos reales.

# Modulo

Harness, validacion documental, compilacion, JS syntax checks y smoke tests.

# Riesgo

Medio-alto por ejecutar imports de app durante smoke tests. Mitigacion: los tests usan DB y rutas temporales, no arrancan servidor real persistente y no ejecutan integraciones externas.

# Archivos permitidos

- `scripts/validate_harness.sh`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `Makefile` si se anade alias minimo.
- Este plan activo.

# Archivos prohibidos

- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs`, `exports/`.
- `app/`, `templates/`, `static/`, scripts funcionales distintos del runner y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/SAFE_WORKSPACE.md`
- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/secretos.md`

# Validaciones

```bash
bash scripts/validate_harness.sh
git diff --check
git status --short
```

# Rollback

Revertir `scripts/validate_harness.sh`, `docs/harness/VALIDATION/runner.md`, cambios en `minimal_checks.md`, `CODEX_OPERATING_MANUAL.md`, `Makefile` si existe y este plan.

# Fuera de alcance

- DB real.
- Integraciones externas.
- Emails.
- Playwright real.
- Servidor persistente.
- Backups reales.
- Refactors o cambios de logica.

# Aprobacion humana requerida

No prevista mientras el cambio se limite a runner, documentacion y alias Makefile simple.

