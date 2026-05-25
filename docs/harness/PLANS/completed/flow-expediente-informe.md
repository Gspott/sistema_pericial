# Flow Expediente Informe

# Objetivo

Anadir un smoke flow seguro para expediente demo -> visita -> `build_informe_context()`,
sin DB real, expedientes reales, PDF/DOCX, Playwright ni datos reales.

# Modulo

Informes / expedientes / visitas.

# Riesgo

Critico por pertenecer al nucleo documental, limitado a tests sobre SQLite
temporal y sin generacion real de documentos.

# Archivos permitidos

- `tests/smoke/test_flow_expediente_informe.py`
- Memoria harness relacionada si aparecen hallazgos.

# Archivos prohibidos

- DB real, expedientes reales, informes reales, fotos, uploads, logs y secretos.
- Generacion PDF/DOCX real.
- Playwright real.
- Refactor de `build_informe_context()` salvo ajuste minimo imprescindible.

# Playbook aplicable

Task Pack sugerido: `informe_change`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.
Patron: `docs/harness/PATTERNS/build_informe_context_extension.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m compileall tests`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

# Rollback

Eliminar el test nuevo y revertir cambios de memoria/metricas asociados.

# Fuera de alcance

- Generar PDF real.
- Generar DOCX real.
- Usar Playwright.
- Leer expedientes, informes o fotos reales.
- Reestructurar informes.

# Aprobacion humana requerida

Si el cambio necesitara alterar conclusiones tecnicas, estructura del informe,
generacion documental real, Playwright o datos reales.

Estado: completado
