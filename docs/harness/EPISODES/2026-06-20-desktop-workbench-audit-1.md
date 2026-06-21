# Episode: Desktop Workbench Audit 1

## Fecha

2026-06-20


## Tarea

Crear la auditoria inicial y formalizar `DESKTOP-WORKBENCH-STANDARD-1`.

## Plan asociado

desktop-workbench-audit-1.md


## Task Pack usado

`docs/harness/TASK_PACKS/documentation.md`

## Objetivo

Mantener mobile-first como canon, proteger el registro de visita en campo y
definir una capa desktop reutilizable para el trabajo posterior a la visita.

## Archivos modificados

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/README.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/VALIDATION/project_standards_guard.md`
- `docs/harness/PLANS/completed/desktop-workbench-audit-1.md`
- `docs/harness/EPISODES/2026-06-20-desktop-workbench-audit-1.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`

## Resultado

Se crea el patron `DESKTOP-WORKBENCH-STANDARD-1` y se documenta la auditoria
`desktop-workbench-audit-1` con:

- inventario de paginas y rutas principales;
- matriz por area con estado, prioridad y observaciones;
- excepciones mobile-first;
- estandar visual desktop propuesto;
- rollout por paquetes pequenos;
- primera candidata recomendada: `desktop-expediente-detalle-1`.

Clasificacion principal:

- Desktop suficiente: Workbench pericial, Informe V2, Workbench de valoracion,
  CRM prospeccion, Costes listado/detalle, Facturacion workbench.
- Parcial: Expediente detalle, propuestas, dashboard, documentos/anexos/fotos,
  facturas detalle/form, costes capturas/OCR/BC3, CRM agenda/enviados.
- Excluido: registro de visita en campo, captura tactil de evidencias,
  backups/login/usuarios y acciones sensibles sin plan especifico.

## Warnings

`audit_docs.py` mantiene warnings historicos no introducidos por esta tarea:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

## Rollback

Revertir los documentos harness listados. No hay cambios funcionales ni datos
persistidos afectados.

## Memoria actualizada

Patron nuevo agregado al indice y a `PROJECT-STANDARDS-GUARD-1`.
Plan cerrado en `docs/harness/PLANS/completed/desktop-workbench-audit-1.md`.

## Decisiones humanas

No requerida aprobacion adicional: fase estrictamente documental, sin codigo
funcional ni datos reales.

## Proximos pasos

Implementar por paquetes reversibles. Primer candidato recomendado:
`desktop-expediente-detalle-1`.
