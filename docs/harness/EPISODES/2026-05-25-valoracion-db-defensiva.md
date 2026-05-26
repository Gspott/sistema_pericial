# Episode: Valoracion DB Defensiva

Fecha: 2026-05-25
Plan: `docs/harness/PLANS/active/valoracion-db-defensiva.md`
Task pack: `docs/harness/TASK_PACKS/db_change.md`

## Contexto

La fase de diseno `valoracion-mover-campos-diseno` definio separar datos estables de expediente, observaciones de visita, testigos reutilizables, snapshots por expediente, ajustes y resultados versionados. Esta fase implementa solo la base defensiva del esquema.

## Cambios

- Se anaden tablas defensivas en `app/database.py`:
  - `valoracion_expediente`
  - `valoracion_visita_observaciones`
  - `testigos_valoracion`
  - `testigos_valoracion_fotos`
  - `valoracion_expediente_testigos`
  - `valoracion_testigo_ajustes`
  - `valoracion_resultados`
- Se anaden indices para claves de consulta frecuentes.
- Se mantiene intacto el fallback legacy `valoracion_visita` y `comparables_valoracion`.
- Se anade smoke con DB temporal para comprobar creacion de tablas e insercion demo completa.

## Fuera De Alcance

- Sin migracion de datos reales.
- Sin borrado ni renombrado de columnas.
- Sin calculo de homogeneizacion.
- Sin formularios ni outputs HTML/PDF/DOCX.
- Sin tocar uploads, fotos reales, informes generados, backups ni secretos.

## Riesgos

- El esquema nuevo convive con tablas legacy; las siguientes fases deben definir helpers de lectura/escritura para evitar doble fuente de verdad.
- Los coeficientes de ajuste aun no aplican validacion funcional de rango -20%/+20%; queda para la fase de calculo/formularios.
- `testigos_valoracion_fotos` almacena solo metadatos; el flujo real de archivos debe disenar permisos, paths y limpieza antes de usarse.
