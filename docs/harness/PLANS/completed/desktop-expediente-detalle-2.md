# Desktop Expediente Detalle 2

# Objetivo

Implementar `desktop-expediente-detalle-2` como mejora del Desktop Workbench de
detalle de expediente, anadiendo un panel de navegacion de estancias en la
sidebar para trabajo postvisita.

Mantener intactos rutas, permisos, persistencia, logica de negocio,
comportamiento movil, BD, migraciones, PDFs, emails y datos reales.

# Modulo

Expedientes / detalle de expediente.

Ruta auditada:

- `GET /detalle-expediente/{expediente_id}` en `app/main.py`.

Template afectado:

- `templates/detalle_expediente.html`.

# Riesgo

Medio. `detalle_expediente` es pantalla central y toca expedientes, visitas,
patologias, informe, valoracion y costes. Mitigacion: cambio SSR/read-only,
una unica consulta agregada para estancias, sin endpoints nuevos ni cambios de
acciones existentes.

# Archivos permitidos

- `app/main.py`
- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-expediente-detalle-2.md`
- `docs/harness/EPISODES/2026-06-20-desktop-expediente-detalle-2.md`

# Archivos prohibidos

- Bases SQLite reales, backups, uploads, informes generados, fotos y logs.
- Migraciones, cambios de esquema, PDFs, emails, facturacion fiscal,
  autenticacion y permisos.
- Rutas nuevas o APIs paralelas.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `harness_change`.

Playbooks/patrones revisados:

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`
- `docs/ux.md`

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m pytest tests/smoke/test_expediente_desktop_workbench.py`
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

# Rollback

Revertir el helper/contexto en `app/main.py`, el panel/estilos en
`templates/detalle_expediente.html`, el smoke ampliado y este plan/episodio.
No hay datos ni persistencia que revertir.

# Fuera de alcance

- Cambiar comportamiento de la accion rapida "Patologias"; debe seguir creando
  o registrando patologias mediante ruta existente.
- Nuevas rutas, endpoints, permisos, persistencia o migraciones.
- Cambiar flujos mobile-first de visita/estancias/patologias.
- Introducir frameworks, SPA o JavaScript nuevo.
- Consultas nuevas para metricas opcionales que no sean necesarias para el
  panel.

# Aprobacion humana requerida

No requerida mientras el cambio se limite a lectura SSR y template. Requerida
si se toca persistencia, permisos, rutas, facturacion, PDF, email, BD, datos
reales o migraciones.


# Auditoria backend

Ruta: `GET /detalle-expediente/{expediente_id}`.

Protecciones existentes:

- `get_current_user(request)`.
- `get_owned_expediente(cur, expediente_id, current_user["id"])`.
- `require_row(expediente, "Expediente no encontrado")`.

Contexto existente antes de esta fase:

| Variable | Disponible | Requiere consulta | Fuente |
|---|---|---|---|
| `expediente` | si | no nueva | `get_owned_expediente` + derivadas |
| `visitas` | si | ya existia | consulta de visitas con contadores |
| contadores de estancias por visita | si | ya existia | subconsulta `COUNT(*) FROM estancias` |
| contadores de patologias por visita | si | ya existia | subconsulta `COUNT(*) FROM registros_patologias` |
| lista de estancias | no | si | no estaba en contexto de detalle |
| patologias por estancia | no como lista | si | solo contadores globales/por visita |
| fotos por estancia | no | si | no estaba en contexto de detalle |
| enlaces a editar estancia | ruta existente | no endpoint nuevo | `/editar-estancia/{estancia_id}` |
| registrar patologias por estancia | ruta existente | no endpoint nuevo | `/registrar-patologias/{visita_id}?estancia_id=...` |
| revisar estructura | ruta existente | no endpoint nuevo | `/definir-estancias/{visita_id}#estructura-interior` |

Decision de consulta:

- No se uso `preparar_resumen_registro_expediente()` porque arrastra consultas
  de fotos exteriores y patologias exteriores que no son necesarias para el
  panel desktop.
- Se anadio una unica consulta de lectura en
  `preparar_estructura_estancias_desktop()` para traer estancias del
  expediente con `total_patologias` y `total_fotos`.
- Se reutilizan helpers existentes: `calcular_estancia_rellena()`,
  `etiquetar_opcion()`, `limpiar_texto()` y
  `preparar_grupos_estructura_estancias()`.

# Cambios aplicados

- Nuevo helper read-only `preparar_estructura_estancias_desktop()`.
- Nuevo contexto `estructura_estancias_desktop` en `detalle_expediente`.
- Nuevo panel desktop "Estructura del inmueble" dentro de `.desktop-sidebar`.
- Acciones por estancia:
  - abrir;
  - registrar datos;
  - registrar patologias si aplica;
  - revisar estructura.
- Indicadores cuando vienen en la unica consulta:
  - patologias;
  - fotos;
  - estado pendiente/revisada.
- Smoke ampliado para expediente con estancias y expediente sin estancias.

# Estado

Completado pendiente de validacion y cierre.

Estado: completado
