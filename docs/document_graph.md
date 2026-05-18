# Grafo documental

## Documentos normativos

| Documento | Proposito |
|---|---|
| [AGENTS.md](../AGENTS.md) | Capa normativa resumida y puerta de entrada. |
| [docs/documentation_governance.md](documentation_governance.md) | Reglas de gobernanza, estados, ownership conceptual y anti-drift. |
| [docs/ia_workflow.md](ia_workflow.md) | Flujo recomendado para futuros chats IA. |
| [docs/changelog.md](changelog.md) | Trazabilidad documental por periodo y Decision ID. |

## Documentos tematicos

| Documento | Depende de | Puede impactar |
|---|---|---|
| [docs/ux.md](ux.md) | modelos_datos, revision_probatoria, pwa | UX movil, revision probatoria, informes, PWA |
| [docs/pwa.md](pwa.md) | ux, backend | navegacion movil, sesiones, cache, validaciones JS |
| [docs/informes.md](informes.md) | modelos_datos, revision_probatoria, backend | PDF, DOCX, revision probatoria, datos |
| [docs/backend.md](backend.md) | modelos_datos, revision_probatoria, pwa | SQLite, integraciones, informes, PWA |
| [docs/revision_probatoria.md](revision_probatoria.md) | modelos_datos, ux, informes | UX, CTAs, informe, completitud tecnica |
| [docs/modelos_datos.md](modelos_datos.md) | backend, informes, revision_probatoria | informes, revision, formularios, SQLite |

## ADRs

| ADR | Decision ID | Fuente normativa |
|---|---|---|
| [ADR-001](adr/ADR-001-navegacion-principal.md) | UX-001 | docs/ux.md |
| [ADR-002](adr/ADR-002-drawer-global.md) | UX-002 | docs/ux.md |
| [ADR-003](adr/ADR-003-revision-probatoria.md) | REV-001 | docs/revision_probatoria.md |
| [ADR-004](adr/ADR-004-rol-final.md) | DATA-001 | docs/modelos_datos.md |
| [ADR-005](adr/ADR-005-soft-delete.md) | DATA-002 | docs/modelos_datos.md |
| [ADR-006](adr/ADR-006-endpoints-minimos.md) | API-001 | docs/backend.md |
| [ADR-007](adr/ADR-007-generacion-manual-informe.md) | INF-001 | docs/informes.md |
| [ADR-008](adr/ADR-008-propuestas-lineas-servicio.md) | PROP-001 | docs/modelos_datos.md |

## Documentos operacionales

| Documento | Proposito |
|---|---|
| [docs/operations.md](operations.md) | Indice de despliegue/operaciones. |
| [docs/recovery.md](recovery.md) | Indice de recuperacion/restauracion. |

## Dependencias principales

| Cambio | Revisar |
|---|---|
| Navegacion | ux, pwa, ia_workflow |
| PWA | pwa, ux, backend |
| Informes | informes, modelos_datos, backend, revision_probatoria |
| Propuestas | modelos_datos, backend, ux, informes |
| Revision probatoria | revision_probatoria, ux, informes, modelos_datos |
| Datos | modelos_datos, backend, informes, revision_probatoria |

## Impactos principales

| Dominio | Impacta normalmente |
|---|---|
| UX | navegacion, visita movil, revision probatoria |
| PWA | cache, sesiones, navegacion movil |
| Datos | informes, revision probatoria, consultas SQLite |
| Backend | integraciones, seguridad, persistencia |
| Informes | PDF, DOCX, completitud tecnica |
| Propuestas | lineas de servicio, honorarios, PDF comercial, email |

## Documentos historicos/referenciados

| Documento | Referencia |
|---|---|
| `docs/RESTORE.md` | [docs/recovery.md](recovery.md) |
| `docs/RECOVERY_CHECKLIST.md` | [docs/recovery.md](recovery.md) |
| `docs/despliegue.md` | [docs/operations.md](operations.md) |
