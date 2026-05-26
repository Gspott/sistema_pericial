# Episode: Valoracion Visita Observaciones Form

Fecha: 2026-05-25
Plan: `docs/harness/PLANS/active/valoracion-visita-observaciones-form.md`
Task pack: `docs/harness/TASK_PACKS/db_change.md`

## Contexto

Tras crear el formulario de datos estables en `valoracion_expediente`, faltaba
separar los datos observados durante la inspeccion de la visita. Esta fase
habilita una pantalla minima para `valoracion_visita_observaciones` sin tocar
legacy, testigos ni calculo.

## Cambios

- Se anaden rutas server-side:
  - `GET /visitas/{visita_id}/valoracion-observaciones`
  - `POST /visitas/{visita_id}/valoracion-observaciones`
- El GET valida ownership con `get_owned_visita()`, exige visita de valoracion,
  carga observaciones nuevas o formulario vacio y muestra legacy solo como
  referencia.
- El POST hace upsert en `valoracion_visita_observaciones`.
- Se anade CTA contextual "Observaciones de valoracion" en cada visita de
  expedientes de valoracion.
- `build_informe_context()` degrada tambien cuando solo existen observaciones
  nuevas y no hay `valoracion_expediente` ni legacy con datos.
- Se anade smoke de GET/POST, persistencia temporal, no modificacion legacy,
  prioridad de contexto y CTA solo en valoracion.

## Fuera De Alcance

- Sin migracion automatica desde `valoracion_visita`.
- Sin eliminar campos legacy de `nueva_visita.html`.
- Sin calculo/homogeneizacion.
- Sin testigos reutilizables ni ajustes.
- Sin tocar DB real, uploads, informes reales, backups ni secretos.

## Riesgos

- Durante la transicion, la pantalla legacy de visita sigue mostrando campos
  amplios de valoracion.
- Los textos observados se renderizan en el grupo de estado del informe; una
  futura fase puede crear un bloque mas especifico si se desea.
