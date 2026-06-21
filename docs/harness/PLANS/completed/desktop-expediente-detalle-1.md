# Desktop Expediente Detalle 1

# Objetivo

Implementar `desktop-expediente-detalle-1` como primera referencia de
`DESKTOP-WORKBENCH-STANDARD-1`, convirtiendo `detalle_expediente.html` en un
workbench de escritorio para pantallas grandes sin cambiar rutas, permisos,
persistencia ni logica de negocio.

La capa desktop se activa solo con `@media (min-width: 1280px)`. El flujo movil
existente y el registro de visita en campo quedan intactos.

# Modulo

Expedientes / detalle de expediente.

Ruta auditada:

- `GET /detalle-expediente/{expediente_id}` en `app/main.py`.

Template afectado:

- `templates/detalle_expediente.html`.

Smoke nuevo:

- `tests/smoke/test_expediente_desktop_workbench.py`.

# Riesgo

Medio. El detalle de expediente es una pantalla central con dependencias de
visitas, informe, valoracion, costes y facturacion. La mitigacion es limitar el
cambio a estructura/CSS responsive y no tocar backend ni acciones existentes.

# Archivos permitidos

- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-expediente-detalle-1.md`
- `docs/harness/EPISODES/*desktop-expediente-detalle-1*.md`

# Archivos prohibidos

- Bases SQLite reales, backups, uploads, informes generados, fotos y logs.
- Migraciones o cambios de esquema.
- Facturacion fiscal, PDFs, emails, service worker, autenticacion y permisos.
- `app/main.py` salvo auditoria; no se cambia backend en esta fase.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/documentation.md`.

Playbooks/patrones revisados:

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PLAYBOOKS/jinja.md`


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m pytest tests/smoke/test_expediente_desktop_workbench.py`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir los cambios en `templates/detalle_expediente.html`, retirar el smoke
nuevo y revertir plan/episodio. No hay cambios de datos ni backend.

# Fuera de alcance

- Cambiar ruta o contexto backend.
- Anadir queries de fotos/documentos.
- Cambiar permisos, ownership, persistencia o acciones POST.
- Tocar registro de visita mobile-first.
- Facturacion, PDFs, emails, migraciones o datos reales.

# Aprobacion humana requerida

No requerida mientras se mantenga como capa responsive/template y smoke sobre DB
temporal. Requerida si se toca facturacion fiscal, PDF, email, permisos,
persistencia o datos reales.

# Auditoria backend

Ruta: `GET /detalle-expediente/{expediente_id}`.

Permisos:

- `get_current_user(request)`.
- `get_owned_expediente(cur, expediente_id, current_user["id"])`.
- `require_row(expediente, "Expediente no encontrado")`.

No hay cambio de decoradores ni ownership.

Dependencias detectadas:

- visitas: consulta directa a `visitas`, con contadores de estancias y
  patologias;
- fotos: no se envia lista directa al template; se accede mediante flujos de
  visita/informe/busqueda;
- documentos: no se envia lista directa al template; se gestiona en Workbench
  pericial e Informe V2;
- patologias: contadores interiores/exteriores, mapas y cuadrantes para
  expedientes de patologias;
- Informe V2: enlaces existentes a editor, PDF/DOCX y busqueda;
- valoracion: resumen por visita, testigos y enlaces a workbench;
- costes: presupuesto/actuaciones de reparacion y timeline economico;
- facturacion: timeline economico y accion de crear factura;
- CRM: no hay dependencia directa en esta ruta.

## Matriz de contexto

| Variable | Tipo | Opcional | Fuente | Dependencias |
|---|---|---|---|---|
| `expediente` | dict | no | `get_owned_expediente` + etiquetas derivadas | expediente, ownership |
| `visitas` | list[dict] | si, lista vacia | tabla `visitas` + contadores | estancias, patologias, inspeccion, habitabilidad, valoracion |
| `resumen_tipo` | dict | si | consultas condicionadas por `tipo_informe` | patologias, inspeccion, habitabilidad, valoracion |
| `revision_informe` | dict | si | `preparar_pendientes_revision_expediente` | revision probatoria/informe |
| `timeline_economico` | list | si | `construir_timeline_economico_expediente` | propuestas/facturas/costes |
| `busqueda_expediente` | dict | si | `buscar_en_expediente_global` | informe, estancias, patologias, fotos, documentos, valoracion |
| `tiene_presupuesto_reparacion` | bool | no | presupuesto/actuaciones | costes, actuaciones |
| `niveles_edificio` | list | si | `cargar_estructura_multiunidad` | estructura expediente |
| `unidades_expediente` | list | si | `cargar_estructura_multiunidad` | estructura expediente |
| `unidades_sin_nivel` | dict | si | `cargar_estructura_multiunidad` | estructura expediente |
| `anejos_sueltos` | list | si | `cargar_estructura_multiunidad` | estructura expediente |
| `unidades_principales_form` | list | si | `cargar_estructura_multiunidad` | formularios de unidad |
| `tipo_nivel_options` | list[tuple] | no | constantes | formulario nivel |
| `tipo_unidad_options` | list[tuple] | no | constantes | formulario unidad |
| `vinculo_unidad_options` | list[tuple] | no | constantes | formulario unidad |
| `tipo_anejo_options` | list[tuple] | no | constantes | formulario unidad |
| `mensaje` | str | si | query param | estado visual |
| `error` | str | si | query param | estado visual |

# Auditoria template

Bloques principales existentes:

- estado del expediente y siguiente accion;
- busqueda en expediente;
- otras acciones;
- timeline economico;
- datos del expediente;
- estructura del expediente;
- formularios de nivel/unidad;
- listados de niveles/unidades;
- visitas del expediente;
- caracteristicas del edificio/unidad;
- imagen catastral;
- JS local para colapsables y campos de unidad.

Cambio aplicado:

- `desktop-shell` como contenedor global;
- `desktop-toolbar` como cabecera superior;
- `desktop-sidebar` con resumen, metricas y acciones rapidas;
- `desktop-main` envolviendo el contenido existente;
- `desktop-inspector` con tareas, actividad reciente, documentos/fotos, estado
  economico y checklist;
- `desktop-panel`, `desktop-summary-grid`, `desktop-timeline` y
  `desktop-quick-actions`;
- CSS dentro de `@media (min-width: 1280px)`;
- sidebars ocultas fuera del breakpoint desktop.

Estado: completado
