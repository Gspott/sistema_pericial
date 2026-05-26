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

## Expediente valoracion a informe

1. Expediente con `tipo_informe='valoracion'`.
2. Visita asociada.
3. Datos de valoracion en `valoracion_visita`.
4. Comparables en `comparables_valoracion`.
5. `build_informe_context()` expone `valoracion`,
   `comparables_valoracion` y advertencias de completitud no bloqueantes.
6. HTML/PDF moderno renderiza secciones de valoracion sin bloques de
   patologias.
7. DOCX editable moderno usa el mismo contexto de valoracion.

Controles:

- No tocar PDF/DOCX moderno sin `TASK_PACK` de informes y smoke especifico.
- No crear calculo/homogeneizacion sin plan de modelo de datos.
- No mover campos estables de visita a expediente sin migracion planificada.
- El smoke debe usar DB temporal y no datos reales.

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
