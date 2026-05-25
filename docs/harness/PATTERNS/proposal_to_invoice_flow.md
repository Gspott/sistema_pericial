# Proposal To Invoice Flow

## Cuando Usarlo

Cambios en propuesta aceptada, factura borrador o continuidad comercial.

## Cuando NO Usarlo

- Emision fiscal real.
- Numeracion, anulaciones o rectificativas sin aprobacion humana.
- Cambios aislados de email sin tocar propuesta/factura.

## Estructura Recomendada

- Revisar `docs/facturacion.md` y playbooks de propuestas/facturacion.
- Mantener propuesta como origen de factura borrador, no factura emitida.
- Preservar lineas, subtotal, IVA, IRPF y total.
- Evitar duplicados de factura borrador.

## Riesgos

- Duplicar facturas.
- Alterar calculos fiscales.
- Mezclar email, propuesta y facturacion en un solo diff.

## Validaciones

- `pytest tests/smoke/test_facturacion_calculos.py -q`
- `pytest tests/smoke/test_propuestas_flow.py -q`
- `bash scripts/validate_harness.sh`

## Anti-Patrones

- Emitir factura al aceptar propuesta sin paso explicito.
- Recalcular fiscalidad en frontend.
- Crear flujo paralelo de propuestas.
