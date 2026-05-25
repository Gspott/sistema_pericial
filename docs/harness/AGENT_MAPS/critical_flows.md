# Critical Flows

## Lead a cliente a propuesta a email

1. Lead registrado.
2. Conversion o vinculacion a cliente.
3. Creacion de propuesta.
4. Lineas de propuesta.
5. PDF o email de propuesta.

Controles:

- No enviar email real sin orden explicita.
- No crear factura real durante este flujo salvo instruccion.

## Propuesta aceptada a factura borrador

1. Propuesta aceptada.
2. Creacion de factura borrador.
3. Revision manual.
4. Emision solo con confirmacion humana.

Controles:

- Factura borrador no equivale a factura emitida.
- Numeracion/emision es zona critica.

## Expediente a visita a informe PDF/DOCX

1. Expediente.
2. Visita.
3. Estancias/patologias/climatologia/fotos.
4. Revision probatoria.
5. Informe PDF/DOCX.

Controles:

- `build_informe_context()` debe seguir siendo fuente unica.
- La visita parcial debe poder continuar.

## Gasto a factura/contabilidad

1. Gasto manual o importado.
2. Adjuntos y revision.
3. Resumen IVA/exportacion.

Controles:

- No leer adjuntos reales salvo orden.
- No usar OpenAI/network salvo orden explicita.

## Backup a restore en copia

1. Crear o localizar backup.
2. Validar contenido sin exponer datos sensibles.
3. Restaurar solo en copia temporal.
4. Confirmar resultado.

Controles:

- No borrar backups.
- No restaurar sobre DB real.

