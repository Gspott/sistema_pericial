# Auditoria Transversal Estandares

# Objetivo

Auditar transversalmente el estado de Sistema Pericial para detectar mejoras
parciales que deban convertirse en estandares globales, especialmente
autoguardado, zona horaria, proteccion frente a sobrescritura, versionado,
validaciones, generacion documental/PDF, workbenches, CRM, costes, valoracion,
facturacion, propuestas, dashboard, harness y smoke tests.

La tarea no implementa cambios funcionales. El entregable es diagnostico,
matriz de riesgos y plan por fases pequenas.

# Modulo

Harness/documentacion transversal. Lectura dirigida de `app/`, `templates/`,
`static/`, `tests/` y `docs/` solo para inventario y evidencia.

# Riesgo

Medio. La auditoria toca zonas criticas en modo lectura y documenta propuestas,
pero no cambia comportamiento de negocio ni datos.

# Archivos permitidos

- `docs/harness/PLANS/active/auditoria-transversal-estandares.md`
- `docs/harness/EPISODES/`
- Documentacion harness estrictamente necesaria para registrar el diagnostico
  o el episodio.

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- Bases SQLite reales
- `backups/`
- `uploads/`
- Informes generados
- Fotos
- Logs
- Secretos y `.env`
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/harness_change.md`.

Playbooks/documentos consultados: `PROJECT_RULES`, `PERMISSIONS`,
`CONTEXT_STRATEGY`, `RISK_MAP`, `CODEX_OPERATING_MANUAL`,
`VALIDATION/minimal_checks`, `GOLDEN_PRINCIPLES`, `SOURCE_OF_TRUTH` y documentos
tematicos afectados.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir el plan/episodio documental creado para esta auditoria. No hay
migraciones ni cambios funcionales.

# Fuera de alcance

- Implementar autoguardado.
- Cambiar timestamps o zona horaria.
- Modificar routers, servicios, templates, JS o tests.
- Leer datos reales, informes generados, fotos, uploads, backups, logs o
  secretos.
- Refactors grandes.

# Aprobacion humana requerida

Requerida antes de ejecutar cualquier fase funcional posterior, especialmente
si afecta facturacion, autenticacion, backups/restore, DB real, informes/PDF
productivos, emails reales o cambios de esquema.

# Diagnostico general

Estado observado: Sistema Pericial ha incorporado mejoras maduras en modulos
concretos, especialmente Informe V2/PDF V2, valoracion, costes, CRM y harness.
El patron general sigue siendo server-side, SQLite, Jinja, formularios POST y
JavaScript minimo, coherente con las reglas del proyecto.

Hallazgo principal: varias mejoras nacidas de caso real ya funcionan como
estandares locales, pero todavia no existen como contrato transversal:

- Autosave avanzado existe solo en Informe V2.
- `updated_at` existe en muchas tablas, pero solo Informe V2 lo usa como
  proteccion activa frente a sobrescritura.
- SQLite `CURRENT_TIMESTAMP` se usa de forma masiva y guarda UTC sin zona
  explicita; otros puntos usan `datetime.now()` local y `date.today()`.
- La presentacion de fechas/hora no esta normalizada: algunos templates muestran
  `created_at`/`updated_at` tal cual y otros transforman UTC a hora local.
- Snapshots/versionado estan maduros en valoracion, costes e Informe V2, pero
  no hay criterio global de "cuando versionar, cuando snapshotear y cuando solo
  auditar evento".
- PDF V2, anexos, bookmarks, perfiles de exportacion, paginacion y diagnosticos
  tienen un nivel alto de industrializacion comparado con propuestas,
  facturacion y otros documentos imprimibles.
- Smoke tests han crecido mucho: 272 funciones `test_` en `tests/smoke`.
  Destacan `test_pericial_workbench.py` (86), CRM (29), costes capturas (21),
  valoracion workbench (17) y testigos reutilizables (17).

# Matriz por modulo

| Modulo | Estado actual | Riesgos | Mejoras parciales detectadas | Prioridad |
|---|---|---|---|---|
| Informe V2 / editor | Muy avanzado. Editor SSR con autosave, estado visual, borrador local, historial, restauracion y proteccion por `updated_at`. | Alto/critico por informes tecnicos y anexos. Riesgo de ser patron aislado y dificil de mantener dentro de `app/main.py`. | Autosave, conflictos 409, versionado de capitulos, respaldo JSON, estados de revision, anexos derivados, laminas fotograficas. | P0 como referencia canonica; no refactor grande. |
| PDF V2 / anexos | Muy avanzado. Perfiles de exportacion, fusion de anexos, diagnostico de peso, paginacion final y bookmarks. | Critico por entrega documental. Posible divergencia con PDF/propuestas/facturas si no se extraen criterios comunes. | Bookmarks jerarquicos, portadillas/indices de anexo A, diagnostico de anexos pesados, perfiles master/email/judicial/solo informe. | P0 para documentar estandar; P1 para extender criterios. |
| Valoracion | Maduro en modelo nuevo defensivo y workbench SSR. | Alto por coexistencia legacy/fallback y datos historicos. | Snapshots en `valoracion_expediente_testigos`, `valoracion_resultados` versionado, ajustes acotados, filtros SSR, QA visual no bloqueante. | P1. |
| Costes | Maduro en capturas, parser, BC3, workbench y snapshots de partidas. | Alto por impacto economico en informes/anexos. | `descripcion_snapshot`, `precio_unitario_snapshot`, `version_parser`, revision manual obligatoria, estados borrador/validado. | P1. |
| CRM/prospeccion | Avanzado en workbench, plantillas, envios programados, agenda y smokes. | Alto por emails reales, agenda temporal y mezcla de `datetime.now()`/`CURRENT_TIMESTAMP`. | Estados de lead/email, programacion, preview, seguimiento, mock SMTP en tests. | P1 por zona horaria. |
| Propuestas | Estructurado, SSR, lineas como fuente economica y PDF/email compartidos. | Alto por conversion a factura y PDF comercial. | Recalculo centralizado, lineas detalladas, servicios rapidos como lineas normales, fallback antiguo. | P2 para proteccion de edicion y fecha/hora. |
| Facturacion | Critico y protegido por docs/tests. | Critico por numeracion, emision, Verifactu, cobros y anulaciones. No tocar sin aprobacion. | Lineas fiscales, smoke de calculos, eventos, hash interno. Fechas mezcladas (`date.today`, `datetime.now`, `CURRENT_TIMESTAMP`). | P1 solo auditoria TZ; cambios funcionales requieren aprobacion. |
| Gastos | Estable, con importacion/OCR opcional y tests mock. | Alto por adjuntos y resumen fiscal. | Degradacion a manual, temporales en tests, deducibilidad. | P2. |
| Expedientes/visitas/patologias | Funcional y mobile-first, principalmente POST manual. | Alto por captura en visita real y posible perdida de datos si se abandona formulario largo. | Revision probatoria, fotos contextuales, completitud no bloqueante. | P1 para autosave o borrador local en formularios largos. |
| Dashboard | Operativo, bajo ruido. | Medio; muestra fechas derivadas de tareas/CRM sin estandar TZ. | Resumen de estado y tareas vencidas. | P3. |
| Emails manuales | Estable con HTML/texto, adjuntos y logs. | Alto por envio real y logs temporales. | Registro `emails_enviados`, mocks. | P2 por TZ y estados. |
| Backups/exportaciones | Operativo, sensible. | Critico. Timestamps de nombre con `datetime.now()` local; no tocar backups reales. | ZIPs, rutas controladas, listado por `mtime`. | P2 documental/TZ; funcional solo con aprobacion. |
| PWA/JS | Minimalista, versionado documentado. | Medio-alto por cache y sesiones. | Drift PWA resuelto y auditado. | P3. |
| Harness | Robusto, con task packs, scopes, episodios y smokes. | Medio. Hay otro plan activo (`harness-consolidation-audit.md`) y `audit_docs` avisa de planes completados vacios. | Validacion por scope, current plan, backlog, patterns, episodes. | P1 para limpieza documental no funcional. |

# Auditoria de autoguardado

Evidencia:

- Solo aparecen `autosave`/`data-autosave` en `app/main.py`,
  `templates/informe_v2_editor.html` y `tests/smoke/test_pericial_workbench.py`.
- Hay al menos 136 formularios POST en templates. Muchos son acciones cortas o
  destructivas donde autosave no aplica, pero varios son formularios largos o
  criticos que dependen de boton manual.
- Informe V2 implementa el patron mas completo:
  - endpoint `/informes-v2/{expediente_id}/autosave`;
  - debounce de 1000 ms;
  - estados visuales `ready`, `dirty`, `saving`, `saved`, `error`,
    `conflict`;
  - `updated_at` oculto por campo;
  - conflicto 409 si el servidor tiene version mas reciente;
  - bloqueo de autosave que vacia contenido existente;
  - copia local en `localStorage`;
  - fallback manual con POST principal;
  - tests smoke de presencia UI, endpoint y conflicto.

Formularios candidatos a estandarizar, sin implementar todavia:

- Expediente/visita/patologias: `nuevo_expediente`, `editar_expediente`,
  `nueva_visita`, `editar_visita`, `editar_estancia`,
  `registrar_patologias`, `editar_registro`.
- Valoracion: `valoracion_expediente`, `valoracion_visita_observaciones`,
  `valoracion_testigo_form`, `valoracion_testigo_biblioteca_form`,
  `valoracion_expediente_testigos`, `valoracion_testigo_ajustes`,
  microedicion de workbench.
- Costes: `costes/captura_revision`, `costes/detalle`, `actuaciones_reparacion`.
- CRM: cuerpo de email editado, lead rapido, tareas/seguimientos.
- Propuestas: detalle de lineas y formulario principal si se editan textos
  largos (`objeto`, `alcance`, `condiciones`, exclusiones).

Estandar recomendado de autosave:

- Solo para formularios largos, redaccionales, con visita real, anexos, captura
  tecnica o alto coste de perdida. No aplicar a acciones destructivas, emision
  fiscal, backups, login ni botones de estado simples.
- Progressive enhancement: el POST manual debe seguir siendo la fuente segura.
- Endpoint minimo por flujo existente, no API de negocio paralela.
- Debounce inicial 1000-1500 ms; guardado por campo o por seccion.
- `updated_at` por entidad/seccion como control optimista; respuesta 409 con
  mensaje claro y sin sobrescribir.
- Estado visual obligatorio: listo, cambios pendientes, guardando, guardado con
  hora local, error, conflicto.
- Borrador local opcional para textos largos o uso en visita; clave con entidad,
  usuario y campo.
- Fallback manual visible y probado.
- Tests minimos:
  - render contiene marcadores autosave;
  - endpoint guarda con DB temporal;
  - conflicto por `updated_at` devuelve 409;
  - POST manual sigue funcionando;
  - si hay JS modificado: `node --check`.

# Auditoria de zona horaria

Diagnostico:

- El desfase observado de -2h respecto a Europe/Madrid es compatible con
  mostrar directamente valores de SQLite `CURRENT_TIMESTAMP`: SQLite genera UTC
  y, en junio, Europe/Madrid es UTC+2.
- El proyecto mezcla tres familias:
  - SQLite `CURRENT_TIMESTAMP` en esquemas y updates (`app/database.py`,
    `app/main.py`, routers de costes, CRM, propuestas, facturacion, leads,
    gastos, clientes, verifactu).
  - Python `datetime.now()`/`date.today()` sin timezone para nombres de archivo,
    fechas fiscales, informes, backups, exportaciones y CRM.
  - JavaScript `new Date()`, `Date.now()` y `toISOString()` en Informe V2/CRM.
- Informe V2 ya contiene una solucion local: parsea timestamps sin zona como UTC
  (`... + "Z"`) y muestra con `toLocaleTimeString("es-ES")`.
- Otros templates muestran campos tal cual: clientes, costes, CRM, facturacion,
  valoracion workbench, capturas.
- No se ha detectado un helper comun tipo `app/utils/timezone.py` ni uso de
  `ZoneInfo("Europe/Madrid")`.

Estrategia unica recomendada:

- Definir una politica canonica:
  - almacenamiento tecnico: UTC aware en ISO 8601 con offset o `Z`;
  - almacenamiento de fechas civiles/fiscales: `YYYY-MM-DD` sin hora;
  - presentacion: Europe/Madrid por defecto;
  - input `datetime-local`: tratarlo como Europe/Madrid salvo que se indique UTC.
- Crear helpers centrales:
  - `now_utc_iso()`;
  - `today_madrid()`;
  - `now_madrid_iso_for_filename()`;
  - `parse_local_datetime_madrid(valor)`;
  - filtro/helper Jinja `format_datetime_madrid(valor)`.
- Migracion compatible:
  - no reescribir datos historicos en primera fase;
  - al leer valores sin offset con formato SQLite, interpretarlos como UTC si
    proceden de `CURRENT_TIMESTAMP`;
  - mantener fechas de factura/propuesta como fecha civil, no timestamp.
- Reglas por area:
  - PDFs/informes: fecha de emision en Europe/Madrid, generada desde helper.
  - Emails/CRM/tareas: programacion en Europe/Madrid, almacenamiento UTC o ISO
    con offset, comparaciones normalizadas.
  - Facturacion: fechas fiscales son fechas civiles; `verifactu_fecha_generacion`
    debe usar helper timezone-aware cuando se toque con aprobacion.
  - Backups/exportaciones/logs: nombres de archivo con hora Madrid o UTC
    explicita, pero consistente y documentado.
  - Tests: congelar o inyectar reloj; no depender de hora real.

# Estandares transversales recomendados

1. Autosave progresivo para formularios largos: estado visual, debounce,
   `updated_at`, fallback manual y smoke.
2. Optimistic locking suave: cualquier workflow con edicion larga debe enviar
   `updated_at` y resolver 409 sin perder contenido.
3. Politica TZ unica: UTC tecnico + Europe/Madrid de presentacion + fechas
   civiles sin hora para documentos fiscales.
4. Snapshot/versionado por riesgo:
   - Informe redactado: versionar contenido editable.
   - Valoracion/testigos/costes: snapshot cuando el dato de origen puede cambiar
     y el informe debe conservar evidencia historica.
   - Facturacion: eventos/auditoria, no mutar historico fiscal sin aprobacion.
5. Validacion previa no bloqueante donde proceda: warnings de completitud y QA
   visual, sin impedir generacion manual si la norma del modulo lo permite.
6. PDF/documentos: perfiles, diagnostico de anexos, paginacion/bookmarks y
   smoke por documento relevante.
7. Workbench desktop no sustituye mobile-first: vistas densas SSR para analisis,
   formularios moviles conservados.
8. Tests smoke por contrato: cada estandar transversal debe tener al menos un
   smoke de render, persistencia temporal y degradacion.
9. Harness: cada mejora transversal se ejecuta en fases pequenas con task pack
   especifico y plan propio.

# Plan de implementacion por fases

Fase 0 - Documentar estandares canonicos.

- Crear docs/patron o doc tematico para autosave y zona horaria.
- No tocar codigo.
- Validacion: `audit_docs`, `finish_harness_task --smoke-scope docs`.

Fase 1 - Zona horaria solo lectura/format.

- Crear helpers TZ y filtros de presentacion.
- Aplicar primero a templates que muestran `created_at`/`updated_at` crudos,
  sin cambiar almacenamiento.
- Smokes de formato sobre DB temporal.

Fase 2 - Autosave base reutilizable.

- Extraer patron JS minimo desde Informe V2 solo si no rompe su flujo.
- Documentar contrato endpoint/HTML.
- No aplicar aun a modulos criticos.

Fase 3 - Autosave en formularios de visita/expediente.

- Empezar por un formulario largo de bajo riesgo relativo, con POST manual
  intacto y `updated_at`.
- Medir UX mobile y Safari.

Fase 4 - Valoracion/costes.

- Aplicar control de sobrescritura y autosave selectivo a formularios largos de
  valoracion y revision de capturas/costes.
- Mantener snapshots existentes.

Fase 5 - CRM/propuestas.

- Normalizar programacion TZ y guardado de cuerpos editados.
- No enviar emails reales en tests.

Fase 6 - Facturacion/backups/exportaciones.

- Solo con aprobacion humana. Separar fecha civil fiscal de timestamp tecnico.
- No cambiar numeracion ni historico.

Fase 7 - PDF/documentos transversales.

- Evaluar extender diagnostico/bookmarks/perfiles a propuestas/facturas solo si
  aporta valor real y con tests.

# Propuesta de nombres de planes harness posteriores

- `autosave-standard-docs-1`
- `timezone-standard-docs-1`
- `timezone-format-helpers-1`
- `timezone-raw-template-display-1`
- `autosave-visit-forms-1`
- `autosave-valoracion-forms-1`
- `autosave-costes-review-1`
- `crm-timezone-scheduled-emails-1`
- `propuestas-edit-conflict-guard-1`
- `facturacion-timezone-audit-1`
- `pdf-document-standards-crosscheck-1`
- `harness-plan-warnings-cleanup-1`

# Evidencia resumida

- `python3 scripts/audit_docs.py`: OK, con warnings existentes por monolito
  `app/main.py` y planes completados vacios.
- `rg -l "data-autosave|autosave" templates static app tests`: solo Informe V2,
  `app/main.py` y su smoke.
- `rg` de timestamps: concentracion principal en `app/database.py` (55
  apariciones), `app/main.py` (47), CRM, propuestas, facturacion, costes e
  Informe V2 tests.
- `rg "^def test_" tests/smoke`: 272 smokes.
- No se inspeccionaron bases SQLite reales, backups, uploads, informes
  generados, fotos, logs, secretos ni carpeta anidada `sistema_pericial/`.

Estado: completado
