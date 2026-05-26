# Episode: Valoracion Modelo Helpers Fallback

Fecha: 2026-05-25
Plan: `docs/harness/PLANS/active/valoracion-modelo-helpers-fallback.md`
Task pack: `docs/harness/TASK_PACKS/db_change.md`

## Contexto

Tras crear la DB defensiva de valoracion inmobiliaria, convivian tablas nuevas
con `valoracion_visita` y `comparables_valoracion`. Antes de tocar formularios
se necesitaba una capa unica de lectura para evitar doble fuente de verdad.

## Cambios

- Se crean helpers de lectura en `app/services/informe.py`:
  - `cargar_valoracion_expediente_con_fallback()`
  - `cargar_comparables_valoracion_con_fallback()`
- `build_informe_context()` usa esos helpers manteniendo las claves existentes:
  - `valoracion`
  - `comparables_valoracion`
  - `completitud_valoracion`
- Los datos nuevos prevalecen sobre legacy.
- Los resultados se componen desde `valoracion_resultados`.
- Los comparables nuevos incluyen metadatos de origen, snapshot y ajustes, sin
  cambiar el render actual.

## Precedencia

- Datos estables: `valoracion_expediente` primero; fallback a la ultima
  `valoracion_visita` con datos.
- Observaciones: `valoracion_visita_observaciones` primero; fallback a campos
  legacy de `valoracion_visita` cuando no existe modelo nuevo.
- Testigos: `valoracion_expediente_testigos` + `testigos_valoracion` +
  `valoracion_testigo_ajustes` primero; fallback a `comparables_valoracion`.
- Resultados: `valoracion_resultados` alimenta el grupo `resultado` cuando se
  usa modelo nuevo.

## Fuera De Alcance

- Sin formularios.
- Sin templates HTML/PDF/DOCX.
- Sin calculo ni homogeneizacion.
- Sin migracion de datos.
- Sin tocar DB real, uploads, informes reales, backups ni secretos.

## Riesgos

- La UI aun escribe en legacy; hasta que existan formularios nuevos, los datos
  pueden quedar repartidos si se introducen manualmente por SQL en sandbox.
- Los campos numericos del modelo nuevo se renderizan como texto simple en el
  informe; el formateo monetario queda para una fase posterior.
