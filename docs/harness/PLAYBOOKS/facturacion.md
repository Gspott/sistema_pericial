# Playbook: Facturacion

## Que leer primero

- `docs/harness/RISK_MAP.md`.
- `docs/backend.md`.
- `docs/modelos_datos.md`.
- `app/routers/facturacion.py`.
- `app/services/verifactu.py`.
- Templates en `templates/facturacion/`.

## Archivos sensibles

- `app/routers/facturacion.py`.
- `app/services/verifactu.py`.
- `app/services/exportaciones.py`.
- `app/database.py`.
- DB real.

## Acciones permitidas

- Leer codigo de forma dirigida.
- Crear o ajustar tests con datos de prueba.
- Cambios documentales.
- Cambios funcionales solo con aprobacion humana.

## Acciones prohibidas

- Cambiar numeracion fiscal sin checklist.
- Emitir, anular o rectificar facturas reales.
- Tocar DB real.
- Cambiar hash/Verifactu sin plan.

## Validaciones

- `python3 -m compileall app`.
- Tests de calculo fiscal.
- Smoke de factura demo en DB temporal.
- `git diff --check`.

## Senales de alarma

- Cambios en `siguiente_numero_factura`.
- Cambios en estados `emitida`, `cobrada`, `anulada`.
- Cambios en rectificativas.
- Cambios en IVA/IRPF o hash.

## Rollback

- Revertir diff.
- Descartar DB temporal.
- No aplicar migraciones sobre datos reales.

