# VAL-QA-1 Consolidacion Valoracion Y Biblioteca De Testigos

Fecha: 2026-06-02

## Objetivo

Revisar Workbench de Valoracion y Biblioteca de Testigos tras las fases UX-VAL y
BIB-TEST, sin anadir funcionalidades nuevas.

## Alcance Auditado

- Workbench SSR: ruta, filtros/ordenacion, microedicion, trazabilidad,
  comparativa tecnica, fotos, wide desktop y degradacion.
- Biblioteca de Testigos: vista desktop, alta rapida, pegado asistido,
  duplicados, vinculacion a expediente, enriquecimiento tecnico, fotos y edicion
  wide.
- Compatibilidad: fallback legacy, mobile-first, informes y rutas antiguas.

## Hallazgos

- El filtro/diagnostico `advertencias` del workbench no contabilizaba
  `advertencias_tecnicas`, aunque el template si las mostraba. Esto podia
  ocultar testigos con problemas tecnicos de UX-VAL-8 al filtrar por
  advertencias.
- La carga de fotos del workbench podia asumir que todos los IDs de testigo del
  contexto eran numericos. El contexto moderno los emite asi, pero se reforzo la
  degradacion defensiva.
- No se detectaron duplicidades funcionales que requieran refactor grande.
- No se detecto mezcla de datos globales de biblioteca con ponderacion
  especifica de expediente.
- Las fotos siguen siendo evidencias auxiliares y no entran en informes.

## Correcciones

- `workbench_comparable_advertencias()` suma advertencias de calculo,
  homogeneizacion y tecnicas.
- `cargar_fotos_workbench_testigos()` ignora IDs vacios o no numericos.
- Smoke del workbench cubre `filtro=advertencias` con advertencia tecnica.

## Aplazados

- QA visual real con navegador/screenshot de biblioteca y workbench en desktop
  ancho y movil.
- Eventual extraccion de helpers de `app/main.py` cuando exista fase de refactor
  segura; no se aborda por el monolito y el alcance de QA.
- Consolidar estilos compartidos de vistas desktop solo si aparece duplicacion
  mantenible; no se hizo para evitar refactor visual transversal.

## Validacion

- Smoke focal de workbench ejecutado antes del cierre.
- Validacion completa del harness prevista al cierre.
