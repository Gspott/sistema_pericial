# Episode: Valoracion Expediente Form Minimo

Fecha: 2026-05-25
Plan: `docs/harness/PLANS/active/valoracion-expediente-form-minimo.md`
Task pack: `docs/harness/TASK_PACKS/db_change.md`

## Contexto

El modelo defensivo ya separaba datos estables de expediente y observaciones de
visita. Los helpers de fallback hacian que `build_informe_context()` priorizase
el modelo nuevo, pero faltaba una primera pantalla server-side para editar
`valoracion_expediente`.

## Cambios

- Se anaden rutas server-side:
  - `GET /expedientes/{expediente_id}/valoracion`
  - `POST /expedientes/{expediente_id}/valoracion`
- El GET valida ownership, exige `tipo_informe='valoracion'`, carga
  `valoracion_expediente` o formulario vacio y muestra valores legacy solo como
  referencia.
- El POST valida ownership y hace upsert en `valoracion_expediente`.
- Se anade CTA contextual "Editar datos de valoracion" en el detalle de
  expediente solo para valoracion.
- Se anade template mobile-first con bloques plegables, sin SPA ni JavaScript
  obligatorio.
- Se anade smoke con DB temporal para GET, POST, persistencia nueva, no
  modificacion legacy y lectura por `build_informe_context()`.

## Fuera De Alcance

- Sin migracion automatica desde `valoracion_visita`.
- Sin eliminar campos legacy de `nueva_visita.html`.
- Sin calculo/homogeneizacion.
- Sin cambios en HTML/PDF/DOCX.
- Sin tocar DB real, uploads, informes reales, backups ni secretos.

## Riesgos

- Durante la transicion, el usuario puede seguir viendo campos legacy en visita;
  la fuente de informe ya prioriza `valoracion_expediente`.
- El formulario no incluye resultados ni testigos; esos bloques quedan para
  fases especificas.
