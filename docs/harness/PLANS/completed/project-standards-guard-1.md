# Project Standards Guard 1

# Objetivo

Convertir los estandares transversales maduros en reglas permanentes del proyecto y del harness, con documentacion, checklist y avisos automaticos no invasivos.

# Modulo

Harness engineering, documentacion operativa y validacion documental.

# Riesgo

Bajo-medio. No hay cambios funcionales de negocio ni datos, pero el cambio afecta a normas transversales usadas por futuras tareas. Las validaciones nuevas deben evitar falsos positivos bloqueantes sobre deuda historica conocida.

# Archivos permitidos

- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PATTERNS/README.md`
- `docs/harness/VALIDATION/project_standards_guard.md`
- `docs/harness/VALIDATION/drift_detection.md`
- `docs/harness/VALIDATION/minimal_checks.md`
- `docs/harness/CODEX_OPERATING_MANUAL.md`
- `scripts/audit_docs.py`
- `AGENTS.md` y `agents.md` si se referencia el estandar desde el indice operativo.
- episodio harness asociado.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos, logs, secretos.
- Modulos funcionales de negocio salvo validaciones documentales estrictamente necesarias.
- Refactors o migraciones.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

- `docs/harness/PLAYBOOKS/jinja.md` como referencia para reglas de templates.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m py_compile scripts/audit_docs.py`
- smoke scope adecuado de harness/docs
- `git diff --check`

# Rollback

Revertir los documentos de estandar/checklist y la funcion nueva de `scripts/audit_docs.py`. No hay cambios de datos.

# Fuera de alcance

- Corregir todos los usos historicos de `CURRENT_TIMESTAMP`, `datetime.now()` o `new Date()`.
- Implementar autosave en modulos nuevos.
- Cambiar workflows CRM/valoracion/facturacion.
- Modificar PDF, facturacion, backups o datos reales.

# Aprobacion humana requerida

Solo si se decide convertir warnings informativos en errores bloqueantes o tocar modulos funcionales para corregir deuda historica.

Estado: completado
