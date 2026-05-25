# Objetivo

Detectar automaticamente incoherencias estructurales y drift entre documentacion, reglas y codigo real.

# Modulo

Harness documental, auditoria documental, validacion y deuda tecnica.

# Riesgo

Medio. Se leen archivos de codigo estables (`static/pwa.js`, `static/sw.js`, `app/main.py`) sin modificarlos. No se usa DB real ni datos generados.

# Archivos permitidos

- `scripts/audit_docs.py`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/PLANS/tech_debt_tracker.md`
- Este plan activo.

# Archivos prohibidos

- `app/`, `templates/`, `static/` como edicion.
- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs`, `exports/`.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/runner.md`
- `docs/harness/RISK_MAP.md`

# Validaciones

```bash
python3 scripts/audit_docs.py
bash scripts/validate_harness.sh
git diff --check
git status --short
```

# Rollback

Revertir cambios en `scripts/audit_docs.py`, documentacion de validacion/deuda y este plan.

# Fuera de alcance

- Modificar PWA real.
- Modificar rutas funcionales.
- DB real.
- Refactors.
- Integraciones externas.

# Aprobacion humana requerida

No prevista mientras los cambios sean auditoria/documentacion y los nuevos drifts informativos sean warnings no bloqueantes.

