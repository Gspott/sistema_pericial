# BIB-TEST-4 Deteccion Defensiva De Duplicados

Fecha: 2026-06-02

## Objetivo

Avisar de posibles testigos duplicados al crear desde el alta rapida desktop,
sin bloquear el alta y sin fusionar automaticamente.

## Criterios

- Misma URL del anuncio.
- Misma fuente y referencia/titulo similar.
- Mismo municipio con precio y superficie parecidos.
- Direccion o zona normalizada de forma simple.

## Comportamiento

- Si hay candidatos, el formulario muestra aviso no bloqueante y lista datos
  clave del candidato.
- El usuario puede revisar, cancelar o pulsar `Guardar de todos modos`.
- Hasta que se confirma, no se inserta ningun testigo nuevo.
- No se fusiona, no se borra y no se modifica ningun testigo existente.

## Limites

- La normalizacion es simple y defensiva; puede generar falsos positivos.
- No hay IA, scoring avanzado, scraping ni conexion externa.
