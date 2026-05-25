# Goal: Facturacion Segura

## Objetivo

Mantener calculos, estados, numeracion, rectificativas, IVA/IRPF, Verifactu interno y exportaciones bajo control estricto.

## Tareas permitidas

- Tests de calculo fiscal con datos de prueba.
- Correcciones pequenas con aprobacion.
- Mejoras de claridad en plantillas sin cambiar calculos.

## Tareas prohibidas

- Cambiar numeracion sin checklist humano.
- Cambiar emision, anulacion o rectificativas sin aprobacion.
- Ejecutar validaciones sobre DB real.
- Manipular facturas reales.

## Criterios de terminado

- Calculos verificados.
- No hay regresion en estados.
- Facturas demo pasan smoke test.

## Validaciones obligatorias

- `python3 -m compileall app`.
- Tests de calculo cuando existan.
- Smoke de emision/rectificativa en DB temporal si aplica.

