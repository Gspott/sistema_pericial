# Valoracion Workbench UX-VAL-5

Fecha: 2026-06-01

## Objetivo

Mejorar la trazabilidad tecnica de los ajustes de homogeneizacion dentro del
panel contextual del workbench SSR de valoracion, sin cambiar calculos,
persistencia ni flujos mobile-first existentes.

## Cambios

- Se anadio un helper de presentacion en `app/main.py` que reconstruye una
  trazabilidad visual desde `pasos_homogeneizacion`, `unitario_inicial` y
  `unitario_homogeneizado` ya expuestos por `build_informe_context()`.
- El panel contextual de `templates/valoracion_workbench.html` muestra:
  €/m2 inicial, subtotal visual de ajustes, €/m2 homogeneizado, pasos aplicados,
  justificaciones y enlace seguro a edicion de ajustes si existe vinculo nuevo.
- Se anadieron avisos QA no bloqueantes para trazabilidad incompleta y
  discrepancia visual entre subtotal reconstruido y unitario homogeneizado.
- Se ampliaron smokes del workbench para testigos con ajustes, sin ajustes y
  ajustes cuantificados incompletos.

## Fuera de alcance

- No se cambio el servicio de calculo ni se persisten valores nuevos.
- No se implemento edicion inline, batch edit, scoring, outliers, IA ni valor
  final automatico.
- No se tocaron informes HTML/PDF/DOCX.

## Riesgos

- La trazabilidad es una reconstruccion visual sobre datos ya calculados; si en
  el futuro cambia la estructura de `pasos_homogeneizacion`, el helper del
  workbench debera ajustarse.
