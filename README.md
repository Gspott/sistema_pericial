# Sistema Pericial

Aplicacion web local para la gestion integral de actividad pericial en Espana. Esta pensada para uso diario desde iPhone/Mac y cubre flujo comercial, expedientes, visitas, patologias, informes, propuestas, facturacion, gastos, exportaciones y backups.

## Stack

- Python + FastAPI.
- Jinja2 server-side rendering.
- SQLite local.
- HTML/CSS mobile first.
- JavaScript minimo y progresivo.
- Sin framework frontend.

## Arquitectura de aplicacion

| Ruta | Proposito |
|---|---|
| `app/main.py` | Arranque FastAPI, routers y logica historica de expedientes. |
| `app/database.py` | `init_db()` y evolucion defensiva SQLite con `asegurar_columna()`. |
| `app/config.py` | Configuracion local, rutas y entorno. |
| `app/routers/` | Routers modulares. |
| `app/services/` | Servicios auxiliares de informes, propuestas, facturacion, backups e integraciones. |
| `templates/` | Vistas Jinja2 renderizadas en servidor. |
| `templates/partials/` | Shell visual, navegacion y parciales reutilizables. |
| `static/mobile.css` | CSS principal mobile first. |
| `static/app_shell.js` | Drawer, overlay y shell de navegacion. |
| `static/pwa.js` | Registro PWA/service worker. |
| `data/pericial.db` | Base de datos SQLite local. |

## Arquitectura documental

El proyecto ha pasado de una documentacion acumulativa a un sistema documental modular y gobernado:

- `AGENTS.md` es la capa normativa resumida: canon, reglas invariantes, anti-patrones, matriz de impacto y Definition of Done documental.
- `agents.md` es alias sincronizado de `AGENTS.md`.
- `/docs` contiene documentacion tematica detallada.
- `docs/adr/` contiene ADRs con decisiones activas.
- `scripts/audit_docs.py` audita drift documental.
- `docs/changelog.md` registra decisiones y consolidaciones documentales.
- `docs/onboarding_ia.md` y `docs/ia_workflow.md` guian el trabajo asistido por IA.

## Estructura documental

| Ruta | Proposito |
|---|---|
| [AGENTS.md](AGENTS.md) | Canon normativo, reglas invariantes, anti-patrones y matriz de impacto. |
| [docs/ux.md](docs/ux.md) | UX, navegacion, drawer global, CTAs y mobile first. |
| [docs/pwa.md](docs/pwa.md) | PWA, offline, service worker y validacion JS. |
| [docs/informes.md](docs/informes.md) | Informes, PDF, DOCX editable y completitud tecnica. |
| [docs/backend.md](docs/backend.md) | Endpoints minimos, FastAPI, subprocess e integraciones. |
| [docs/revision_probatoria.md](docs/revision_probatoria.md) | Revision probatoria, detecciones y prioridades. |
| [docs/modelos_datos.md](docs/modelos_datos.md) | Reglas de datos, `rol_final`, soft delete y persistencia. |
| [docs/adr/README.md](docs/adr/README.md) | Indice de decisiones arquitectonicas. |
| [docs/changelog.md](docs/changelog.md) | Historial documental y trazabilidad. |
| [docs/ia_workflow.md](docs/ia_workflow.md) | Flujo recomendado para IA. |
| [docs/onboarding_ia.md](docs/onboarding_ia.md) | Guia rapida para nuevas sesiones IA. |
| [docs/documentation_governance.md](docs/documentation_governance.md) | Gobernanza documental, estados y anti-drift. |
| [docs/document_graph.md](docs/document_graph.md) | Grafo documental y dependencias principales. |
| [docs/documentation_debt.md](docs/documentation_debt.md) | Deuda documental aceptada, temporal y pendiente. |
| [docs/templates/](docs/templates/) | Plantillas oficiales de ADR, decision, checklist y changelog. |

## Flujo recomendado para desarrollo asistido por IA

1. Leer este `README.md`.
2. Leer [AGENTS.md](AGENTS.md).
3. Revisar los documentos tematicos afectados.
4. Revisar ADRs relacionadas en [docs/adr/README.md](docs/adr/README.md).
5. Revisar anti-patrones, reglas invariantes y matriz de impacto.
6. Ejecutar auditoria documental antes de cerrar cambios.

Ver tambien:

- [docs/onboarding_ia.md](docs/onboarding_ia.md)
- [docs/ia_workflow.md](docs/ia_workflow.md)

## Auditoria documental

Existe un auditor no invasivo:

```bash
python3 scripts/audit_docs.py
```

Valida, entre otros puntos:

- IDs de decision duplicados.
- Referencias Markdown rotas.
- Documentos vacios o sin titulo principal.
- Drift documental conocido.
- Sincronizacion `AGENTS.md` / `agents.md`.
- Estados y categorias de decision.
- ADRs sin campos obligatorios.
- Reglas normativas inconsistentes.

## CI documental

El workflow [`.github/workflows/docs-audit.yml`](.github/workflows/docs-audit.yml) ejecuta:

```bash
python3 scripts/audit_docs.py
```

Se lanza en `push` y `pull_request`. Solo audita documentacion; no despliega ni modifica la aplicacion.

## ADRs (Architecture Decision Records)

Las decisiones importantes se documentan como ADRs en [docs/adr/](docs/adr/). El indice principal esta en [docs/adr/README.md](docs/adr/README.md).

ADRs iniciales:

- Navegacion principal.
- Drawer global.
- Revision probatoria.
- Formula canonica de `rol_final`.
- Soft delete.
- Endpoints minimos.
- Generacion manual de informe.
- Propuestas con lineas de servicio estructuradas.

## Gobernanza documental

La gobernanza documental define:

- Documentacion modular.
- Reglas invariantes.
- Anti-patrones.
- Definition of Done documental.
- Freeze del core normativo.
- Trazabilidad mediante Decision IDs.

Ver:

- [docs/documentation_governance.md](docs/documentation_governance.md)
- [docs/documentation_debt.md](docs/documentation_debt.md)

## Convenciones importantes

Resumen operativo; el detalle vive en `AGENTS.md` y `/docs`:

- Mobile first.
- No crear APIs de negocio paralelas.
- Reutilizar flujos existentes antes de crear nuevos.
- Drawer global como navegacion principal.
- `_top_nav.html` es legacy/secundario.
- Soft delete solo para biblioteca/catalogos.
- `rol_final` tiene formula canonica documentada.
- En propuestas, las lineas de servicio son la fuente economica de verdad cuando existen.
- No hardcodear versiones PWA.
- Validar JS modificado con `node --check <archivo.js>`.

## Propuestas

El generador de propuestas mantiene compatibilidad con propuestas antiguas sin lineas y permite desglose estructurado mediante `propuesta_lineas`.

- Categorias: estudio documental, visita tecnica, informe pericial, ratificacion judicial, desplazamientos/dietas y servicios adicionales.
- Ratificacion judicial, desplazamientos/dietas, recargo por urgencia y suplemento por complejidad se crean como lineas normales.
- El PDF/imprimible muestra tabla de honorarios y campos `incluye`, `no_incluye` y `condiciones` cuando existen.
- Los importes se redondean a 2 decimales y se validan como no negativos en servidor.
- El borrado de lineas exige confirmacion server-side.

## Estado actual de la documentacion

- Documentacion modularizada.
- ADRs activas.
- Auditoria documental operativa.
- CI documental activo.
- Onboarding IA disponible.
- Deuda documental identificada y trazada.

## Documentacion operacional e historica

La documentacion operacional se referencia desde indices para evitar romper enlaces historicos:

- [docs/recovery.md](docs/recovery.md)
- [docs/operations.md](docs/operations.md)

Algunos documentos historicos se mantienen en su ubicacion actual por compatibilidad de referencias existentes.

## Instalacion local

```bash
git clone https://github.com/Gspott/sistema_pericial.git
cd sistema_pericial
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Validaciones utiles

Para cambios de aplicacion, consultar siempre [AGENTS.md](AGENTS.md). Para cambios solo documentales:

```bash
python3 scripts/audit_docs.py
cmp AGENTS.md agents.md
git status --short
```
