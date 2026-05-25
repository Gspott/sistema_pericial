# Flow Propuesta Factura

# Objetivo

Anadir un smoke flow seguro para propuesta demo aceptada -> factura borrador,
sin DB real, SMTP, Verifactu, emision fiscal ni numeracion real.

# Modulo

Propuestas / facturacion.

# Riesgo

Alto. Toca cobertura de flujo comercial-fiscal, pero solo mediante tests sobre
SQLite temporal.

# Archivos permitidos

- `tests/smoke/test_flow_propuesta_factura.py`
- Memoria harness relacionada si aparecen hallazgos.

# Archivos prohibidos

- DB real, backups, uploads, informes, fotos, logs y secretos.
- Logica de emision fiscal, numeracion real, Verifactu o SMTP.

# Playbook aplicable

Task Pack sugerido: `facturacion_change`.
Playbook: `docs/harness/PLAYBOOKS/facturacion.md`.
Patron: `docs/harness/PATTERNS/proposal_to_invoice_flow.md`.


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

- Emision fiscal.
- Verifactu real.
- SMTP/email real.
- Numeracion fiscal real.
- Refactor de propuestas o facturacion.

# Aprobacion humana requerida

Si el cambio necesitara tocar calculos fiscales, numeracion, emision,
rectificativas, Verifactu real o datos reales.

Estado: completado
