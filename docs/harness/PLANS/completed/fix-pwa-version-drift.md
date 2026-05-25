# Fix PWA Version Drift

## Objetivo

Eliminar el drift entre la version de registro del service worker y la version de cache activa.

## Modulo

PWA/mobile.

## Riesgo

Medio-alto. Cambio acotado a versionado PWA.

## Archivos Permitidos

- `static/pwa.js`
- `static/sw.js` solo para inspeccion o ajuste minimo si fuera imprescindible
- `docs/pwa.md`
- `docs/harness/FAILURES/pwa_version_drift.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/STATE/known_risks.md`
- `docs/harness/PLANS/active/fix-pwa-version-drift.md`

## Archivos Prohibidos

- `app/`
- `templates/`
- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes, fotos, logs y secretos

## Playbook Aplicable

- `docs/harness/TASK_PACKS/mobile_ui.md`
- `docs/harness/PATTERNS/mobile_partial_structure.md`

## Validaciones

- `python3 scripts/audit_docs.py`
- `node --check static/pwa.js`
- `node --check static/sw.js`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Rollback

Restaurar el registro anterior del service worker y revertir las notas documentales de cierre.

## Fuera De Alcance

- Cambiar assets cacheados.
- Cambiar estrategia de cache.
- Cambiar app shell, navegacion o comportamiento mobile.
- Limpiar caches reales en dispositivos.

## Aprobacion Humana Requerida

Requerida si se cambia `CACHE_NAME`, lista de assets, estrategia de fetch o comportamiento de instalacion/activacion.
