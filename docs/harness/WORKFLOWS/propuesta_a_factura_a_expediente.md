# Workflow: Propuesta A Factura A Expediente

## Objetivo

Controlar el flujo comercial completo sin mezclar cambios comerciales con fiscalidad critica.

## Secuencia

1. Lead o cliente.
2. Propuesta.
3. Lineas de propuesta.
4. PDF o email de propuesta.
5. Aceptacion.
6. Factura borrador.
7. Emision fiscal solo con confirmacion.
8. Creacion o vinculacion de expediente.

## Reglas

- Propuesta aceptada no implica factura emitida.
- Factura borrador no implica emision.
- Crear expediente desde propuesta debe preservar owner y datos comerciales.
- Envio de email real requiere orden explicita.
- Emision fiscal requiere checklist humano.

## Validaciones

- Smoke propuesta demo.
- Smoke factura borrador demo.
- No ejecutar sobre DB real salvo orden explicita.
- `python3 -m compileall app`.

## Rollback

- Revertir cambios de codigo.
- Descartar DB temporal.
- No borrar registros reales.

