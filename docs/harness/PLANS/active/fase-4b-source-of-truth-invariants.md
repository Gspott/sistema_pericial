# Objetivo

Convertir la documentacion actual en fuente operativa clara para Codex, evitando crear un arbol paralelo de specs innecesario.

# Modulo

Documentacion normativa, fuentes de verdad, invariantes, criterios Done, facturacion y gastos.

# Riesgo

Bajo. Cambios solo documentales y auditoria de existencia/enlaces. No se toca logica ni datos reales.

# Archivos permitidos

- `docs/SOURCE_OF_TRUTH.md`
- `docs/backend.md`
- `docs/modelos_datos.md`
- `docs/informes.md`
- `docs/ux.md`
- `docs/facturacion.md`
- `docs/gastos.md`
- `docs/harness/TASK_PACKS/*.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `scripts/audit_docs.py` si el cambio es simple y seguro.
- Este plan activo.

# Archivos prohibidos

- `app/`, `templates/`, `static/`.
- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`, `backups/`, `informes/`, `fotos/`, `logs`, `exports/`.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `docs/harness/TASK_PACKS/README.md`
- `docs/harness/VALIDATION/drift_detection.md`

# Validaciones

```bash
python3 scripts/audit_docs.py
bash scripts/validate_harness.sh
git diff --check
git status --short
```

# Rollback

Revertir documentos creados/modificados y cambios simples de auditoria.

# Fuera de alcance

- Logica de aplicacion.
- Datos reales.
- Refactors.
- Cambios funcionales.

# Aprobacion humana requerida

No prevista mientras el cambio sea documental y no altere comportamiento funcional.

