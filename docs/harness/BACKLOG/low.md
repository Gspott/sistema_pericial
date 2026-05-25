# Low Backlog

Usar esta prioridad para limpieza, ergonomia documental o mejoras de lectura sin impacto funcional inmediato.

## Pendientes

## Revisar `templates/partials/_main_nav.html`

- Impacto: posible parcial legacy no referenciado que duplica navegacion.
- Modulos: UX, Jinja, mobile.
- Riesgo: Bajo.
- Task Pack recomendado: `docs/harness/TASK_PACKS/mobile_ui.md`.
- Validaciones minimas: busqueda de referencias, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea desarrollo.
- Dependencias: confirmar con `docs/ux.md` y ADR de navegacion antes de archivar o eliminar.

## Revisar `templates/partials/_quick_actions.html`

- Impacto: posible parcial legacy no referenciado; acciones rapidas viven en drawer.
- Modulos: UX, Jinja, mobile.
- Riesgo: Bajo.
- Task Pack recomendado: `docs/harness/TASK_PACKS/mobile_ui.md`.
- Validaciones minimas: busqueda de referencias, `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea desarrollo.
- Dependencias: confirmar que no hay includes dinamicos ni uso previsto antes de archivar o eliminar.

## Decidir Conservacion Historica De Routers Legacy

- Impacto: reduce ambiguedad futura sobre routers no incluidos.
- Modulos: expedientes, visitas, estancias, patologias.
- Riesgo: Bajo.
- Task Pack recomendado: `docs/harness/TASK_PACKS/safe_refactor.md`.
- Validaciones minimas: mapa ruta a ruta completo y `bash scripts/validate_harness.sh`.
- Bloqueo/no bloqueo: No bloquea trabajo quirurgico.
- Dependencias: no archivar ni eliminar hasta decision humana posterior al mapa completo.
