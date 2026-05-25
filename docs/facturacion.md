# Facturacion

Spec operativa de facturacion para Sistema Pericial. No es teoria fiscal generica.

## Fuente normativa

Fuente normativa: este documento.

## Dependencias

Depende de:

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/backend.md](backend.md)

Puede impactar:

- Propuestas.
- Clientes.
- Gastos e IVA.
- Exportaciones.
- Verifactu interno.

## Alcance

La facturacion cubre facturas emitidas, lineas fiscales, IVA, IRPF, cobros, anulaciones, rectificativas, exportaciones y registro tecnico interno.

## Estados de factura

- `borrador`: editable y no emitida.
- `emitida`: factura fiscalmente emitida.
- `cobrada`: emitida con cobro registrado o marcada como cobrada.
- `anulada`: factura anulada segun flujo existente.
- Rectificativa: factura vinculada a una factura rectificada cuando el flujo lo contempla.

## Propuesta a factura borrador

- Una propuesta puede crear factura borrador.
- Propuesta aceptada no implica factura emitida.
- Factura borrador no implica numeracion/emision definitiva.
- Las lineas de propuesta pueden alimentar lineas de factura, conservando calculos fiscales separados.

## Lineas fiscales

Cada linea de factura debe conservar:

- Concepto.
- Cantidad.
- Precio unitario.
- IVA porcentaje.
- IRPF porcentaje.
- Subtotal.
- IVA importe.
- IRPF importe.
- Total.

## Calculos

- `subtotal = cantidad * precio_unitario`.
- `iva_importe = subtotal * iva_porcentaje / 100`.
- `irpf_importe = subtotal * irpf_porcentaje / 100`.
- `total = subtotal + iva_importe - irpf_importe`.
- Los totales agregados de factura derivan de sus lineas.

## Numeracion y emision

- Numeracion y emision son zona critica.
- No cambiar numeracion sin aprobacion humana.
- No emitir facturas reales desde tests.
- No regenerar hash/registro tecnico sin validar impacto.

## Rectificativas y anulaciones

- Rectificativas y anulaciones requieren plan, smoke test y aprobacion humana.
- No crear rectificativas sobre datos reales durante pruebas.
- Evitar estados ambiguos entre anulada, rectificada y cobradas.

## Cobros

- Cobros registran fecha, importe, metodo y notas.
- Cobro no debe alterar historico fiscal salvo flujo existente.
- Factura cobrada debe conservar trazabilidad de eventos.

## Verifactu interno

- El registro tecnico interno puede generar hash, hash anterior, cadena hash y payload QR interno.
- No asumir envio externo si no esta implementado/documentado.
- Cambios en hash o cadena requieren aprobacion humana.

## Exportaciones

- Exportaciones deben usar datos consistentes de facturas y gastos.
- No incluir archivos fuera de rutas permitidas.
- Exportar no debe modificar facturas.

## Invariantes fiscales

- No tocar DB real.
- No cambiar numeracion, emision, anulacion, rectificativas, hash o exportaciones sin aprobacion humana.
- Factura borrador no es factura emitida.
- Propuesta aceptada no emite factura automaticamente.
- Los calculos fiscales viven en backend, no en Jinja ni JS.
- Smoke obligatorio para cambios fiscales.

## Edge cases

- Factura sin cliente: debe degradar de forma controlada o bloquearse segun flujo existente.
- Propuesta antigua sin lineas: mantener fallback compatible.
- Factura borrador duplicada: evitar crear duplicados si ya existe borrador vinculado.
- Rectificativa de factura anulada: requiere decision humana antes de cambiar comportamiento.
- Cambio de IVA/IRPF: no debe alterar historico emitido salvo flujo explicito.
- Error Verifactu/exportacion: debe reportarse sin romper facturacion ordinaria.

## Criterios Done

- `pytest tests/smoke -q` pasa.
- `bash scripts/validate_harness.sh` pasa.
- No se ha usado DB real.
- No se han emitido facturas reales.
- Cambios criticos tienen aprobacion humana.

## Enlaces

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/backend.md](backend.md)
- [docs/harness/TASK_PACKS/facturacion_change.md](harness/TASK_PACKS/facturacion_change.md)
- [tests/smoke/test_facturacion_calculos.py](../tests/smoke/test_facturacion_calculos.py)
- [tests/smoke/test_propuestas_flow.py](../tests/smoke/test_propuestas_flow.py)
