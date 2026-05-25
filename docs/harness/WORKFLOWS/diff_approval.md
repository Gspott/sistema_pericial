# Workflow: Diff Approval

## Cambios que requieren aprobacion humana

- Autenticacion.
- Numeracion fiscal.
- Emision, anulacion o rectificativas.
- Backups o restore.
- Eliminacion de columnas.
- Rutas publicas.
- Service worker.
- Deploy.
- DuckDNS o Caddy.
- Emails reales.
- Datos reales.

## Formato obligatorio

Antes de tocar, presentar:

```md
# Objetivo

# Archivos

# Riesgo

# Diff previsto

# Validaciones

# Rollback
```

## Regla

Si el usuario no aprueba explicitamente, no aplicar el cambio.

