# Valoracion Workbench UX-VAL-6

Fecha: 2026-06-01

## Objetivo

Hacer accesible el workbench de valoracion desde la UX normal del sistema sin
reemplazar la valoracion clasica ni redirigir automaticamente.

## Cambios

- Se anadio acceso secundario "Workbench de valoracion" en el detalle de
  expediente solo para `tipo_informe='valoracion'`.
- Se anadio acceso secundario desde la pantalla de testigos vinculados del
  expediente de valoracion.
- Ambos accesos apuntan a
  `/expediente/{expediente_id}/valoracion/workbench` e incluyen texto breve:
  "Analisis tecnico de comparables, homogeneizacion y ponderacion".
- Se actualizaron smokes para comprobar que el acceso aparece en valoracion,
  no aparece en patologias y la ruta del workbench sigue renderizando.

## Fuera de alcance

- No se sustituyen rutas ni CTAs legacy.
- No hay redirects automaticos.
- No se tocan informes, calculos, esquema ni datos.

## Riesgos

- El enlace sigue siendo una entrada secundaria. Si el workbench pasa a ser
  flujo principal, requerira una fase de navegacion especifica y QA visual.
