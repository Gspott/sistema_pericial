# Desktop Workbench Audit 1

# Objetivo

Auditar el estado de escritorio del proyecto y formalizar
`DESKTOP-WORKBENCH-STANDARD-1` como estandar transversal:

- mantener mobile-first;
- no degradar visita en campo;
- identificar paginas con desktop suficiente;
- identificar paginas pendientes;
- proponer paquetes pequenos de rollout.

Esta fase es documental. No implementa nuevas vistas ni cambia comportamiento
funcional.

# Modulo

Transversal UX/harness.

Documentos y patrones afectados:

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/VALIDATION/project_standards_guard.md`
- `docs/harness/PATTERNS/README.md`

Fuentes inspeccionadas:

- `docs/ux.md`
- templates principales en `templates/`
- rutas SSR en `app/main.py` y `app/routers/*`
- patrones existentes de autosave, timezone y project standards guard.

# Riesgo

Bajo. Es una auditoria documental. El riesgo principal es clasificar como
cubierta una pagina que solo tiene layout movil o proponer un estandar que
rompa la excepcion mobile-first de visita en campo.

Mitigaciones:

- no tocar codigo funcional;
- no tocar templates de visita;
- clasificar explicitamente las exclusiones;
- proponer rollout por paquetes pequenos;
- mantener `PROJECT-STANDARDS-GUARD-1` como guardia.

# Archivos permitidos

- `docs/harness/PATTERNS/desktop_workbench_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/VALIDATION/project_standards_guard.md`
- `docs/harness/PATTERNS/README.md`
- `docs/harness/PLANS/active/desktop-workbench-audit-1.md`
- `docs/harness/EPISODES/*desktop-workbench-audit-1*.md`

# Archivos prohibidos

- Codigo funcional Python, JS o templates.
- Bases SQLite reales, backups, uploads, informes generados, fotos y logs.
- Facturacion fiscal, PDFs, emails, service worker, deploy o migraciones.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/documentation.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- cierre harness con smoke scope documental adecuado
- `git diff --check`

# Rollback

Revertir los documentos harness modificados o anadidos. No hay cambios
funcionales ni datos persistidos afectados.

# Fuera de alcance

- Implementar layouts desktop.
- Cambiar templates o CSS funcional.
- Reordenar navegacion.
- Cambiar facturacion, PDFs, emails, costes, CRM o informe.
- Tocar registro de visita mobile-first.

# Aprobacion humana requerida

No requerida mientras la fase sea documental. Cualquier implementacion futura
en facturacion, PDF, emails, datos reales o migraciones requerira el playbook y
aprobaciones que correspondan.

# Inventario y matriz

Estados:

- `desktop suficiente`: ya ofrece una experiencia comoda de escritorio.
- `parcial`: tiene alguna capa desktop o enlace a workbench, pero quedan zonas
  importantes mobile/card o sin panel de revision.
- `pendiente`: requiere paquete futuro.
- `excluida`: debe mantenerse mobile-first o queda fuera por riesgo funcional.

| Area | Paginas/rutas principales | Estado | Prioridad | Observaciones |
|---|---|---|---|---|
| Expediente detalle | `templates/detalle_expediente.html`, `/detalle-expediente/{id}` | parcial | P1 | Tiene resumen, CTAs y enlaces a workbenches, pero la pagina canonica sigue siendo card/mobile. Candidata a primer paquete desktop. |
| Workbench pericial | `templates/pericial_workbench.html`, `/expedientes/{id}/pericial-workbench` | desktop suficiente | P1 mantener | Ya usa hero, metricas, layout 3 zonas, paneles, tablas y degradacion responsive. |
| Informe V2 | `templates/informe_v2_editor.html`, `/expedientes/{id}/informe-v2-editor` | desktop suficiente | P1 mantener | Editor con indice, panel central, contexto, diagnosticos, laminas y anexos. Requiere hardening, no reconstruccion. |
| Valoracion workbench | `templates/valoracion_workbench.html` | desktop suficiente | P1 mantener | Referente principal: layout wide, tabla, panel lateral, filtros SSR, autosave. |
| Valoracion biblioteca/testigos | `templates/valoracion_testigos_biblioteca.html`, `valoracion_testigo_form.html`, `valoracion_expediente_testigos.html` | parcial | P2 | Biblioteca desktop madura; formularios y seleccion tienen mejoras, pero conviene homogeneizar con el estandar. |
| Costes listado/detalle | `templates/costes/listado.html`, `templates/costes/detalle.html` | desktop suficiente | P2 mantener | Workbench/listado con tabla y detalle en grid, autosave en partida existente. |
| Costes capturas/OCR/BC3 | `templates/costes/captura_revision.html`, `bc3_*` | parcial | P3 | Hay tablas/paneles, pero mezclan revision, importacion y creacion estructural. Requieren paquetes especificos. |
| CRM prospeccion | `templates/crm/prospeccion.html` | desktop suficiente | P2 mantener | Workbench real con tabla, seleccion, panel, preview, acciones y autosave de notas. |
| CRM agenda/enviados | `templates/crm/prospeccion_agenda.html`, `prospeccion_enviados.html` | parcial | P3 | Funcionales, pero pendientes de unificar como bandeja desktop secundaria. |
| Propuestas listado/detalle/form | `templates/propuestas/listado.html`, `detalle.html`, `form.html` | parcial | P2 | Formulario existente tiene autosave, pero detalle y lineas siguen como bloques moviles. Necesita workbench comercial sin tocar fiscalidad. |
| Asistente propuesta-factura | `templates/propuestas/crear_factura_asistente.html` | parcial | P3 | Ya tiene layout/preview, pero toca frontera fiscal: paquetes pequenos y validacion fuerte. |
| Facturacion workbench | `templates/facturacion/workbench.html` | desktop suficiente | P2 mantener | Workbench economico especifico, sin modificar fiscalidad. |
| Facturas detalle/form/listado/IVA | `templates/facturacion/*` | parcial | P3 | Hay tablas y vistas imprimibles, pero facturacion es critica: mejorar solo con planes acotados. |
| Documentos/anexos | `pericial_workbench.html`, Informe V2 anexos | parcial | P2 | Cubierto dentro de workbench pericial e Informe V2; falta vista global de documentos/anexos por expediente si se necesita. |
| Fotos/laminas | Informe V2 laminas, visitas/estancias/fotos | parcial | P3 | Laminas en Informe V2 son maduras; gestion global de fotos queda pendiente. Mantener captura movil en visita. |
| Dashboard | `templates/dashboard.html` | parcial | P2 | Tiene cards y resumen, pero no vista de escritorio para priorizar trabajo post-visita. |
| Busqueda | APIs direccion/Catastro, filtros dispersos | pendiente | P4 | No hay workbench de busqueda global. Mejor plan posterior si hay necesidad real. |
| Clientes/leads clasicos | `templates/clientes/*`, `templates/leads/*` | parcial | P4 | Listados/detalles simples; CRM cubre el trabajo comercial pesado. |
| Gastos | `templates/gastos/*` | parcial | P4 | Algunos formularios tienen layout, pero gastos no esta en prioridad inicial del estandar. |
| Backups/usuarios/login | `templates/backups/*`, login, usuario | excluida | P0 no tocar | Flujos operativos/sensibles; no requieren workbench desktop salvo plan especifico. |
| Nueva visita/editar visita | `templates/nueva_visita.html`, `editar_visita.html` | excluida | P0 no tocar | Excepcion explicita: registro de visita en campo sigue mobile-first. |
| Patologias/estancias en campo | `registrar_patologias.html`, `definir_estancias.html`, `editar_estancia.html`, `editar_registro*.html` | excluida/parcial | P0/P3 | Captura en campo sigue movil; revision post-visita puede vivir en expediente/pericial workbench. |
| Mapas/cuadrantes | `editar_mapa_patologia.html`, `editar_cuadrante_mapa_patologia.html` | parcial | P3 | Cuadrante tiene autosave; mapa estructural requiere plan separado. |

# Estándar visual propuesto

Ver `docs/harness/PATTERNS/desktop_workbench_standard.md`.

Resumen operativo:

- desktop como capa adicional SSR;
- hero/cabecera operativa;
- metricas y estado cuando ayuden a decidir;
- layout 2-3 zonas solo en escritorio ancho;
- panel lateral para diagnostico/contexto;
- tabla con scroll horizontal;
- filtros SSR o seleccion reactiva;
- autosave estandar si hay formulario largo;
- degradacion movil a una columna;
- sin SPA ni navegacion paralela.

# Rollout propuesto

1. `desktop-expediente-detalle-1`
   - Objetivo: convertir el detalle de expediente en centro desktop post-visita
     sin perder la tarjeta mobile-first.
   - Candidato de primera implementacion.
   - Riesgo: alto por centralidad del expediente, pero reversible si se limita a
     layout/template y smoke de render.

2. `desktop-informe-v2-hardening-1`
   - Objetivo: consolidar como referente, revisar overflow, paneles sticky,
     indice y smokes de desktop.
   - No redisenar PDF ni `build_informe_context()`.

3. `desktop-valoracion-continuidad-1`
   - Objetivo: homogeneizar biblioteca/testigos/formularios con el patron wide
     ya existente del workbench.

4. `desktop-costes-review-1`
   - Objetivo: revisar capturas/OCR/BC3 como vistas de revision, sin autosalvar
     ni ejecutar importaciones estructurales.

5. `desktop-crm-hardening-1`
   - Objetivo: compactar agenda/enviados y reforzar seleccion reactiva/estado
     visual sin tocar envios reales.

6. `desktop-propuestas-workbench-1`
   - Objetivo: vista de escritorio para propuesta existente y lineas como
     revision comercial. No tocar importes/facturacion salvo lectura.

7. `desktop-facturacion-review-1`
   - Objetivo: mejorar ergonomia de borradores/listados manteniendo fiscalidad
     intocable salvo aprobacion.

8. `desktop-documentos-fotos-1`
   - Objetivo: vista post-visita para anexos/fotos/laminas, sin cambiar captura
     movil ni generacion PDF.

9. `desktop-dashboard-busqueda-1`
   - Objetivo: dashboard de priorizacion y busqueda global si se confirma
     necesidad real.

# Candidatas a primera implementacion

1. `desktop-expediente-detalle-1`
   - mayor impacto transversal;
   - no toca fiscalidad ni datos reales;
   - conecta visitas, patologias, informes, valoracion y documentos;
   - permite medir el estandar sin invadir modulos criticos.

2. `desktop-dashboard-busqueda-1`
   - bajo riesgo funcional si se limita a lectura y enlaces;
   - mejora orientacion inicial.

3. `desktop-propuestas-workbench-1`
   - impacto comercial claro, pero requiere frontera estricta con facturacion.

# Planes harness sugeridos

- `desktop-expediente-detalle-1`
- `desktop-informe-v2-hardening-1`
- `desktop-valoracion-continuidad-1`
- `desktop-costes-review-1`
- `desktop-crm-hardening-1`
- `desktop-propuestas-workbench-1`
- `desktop-facturacion-review-1`
- `desktop-documentos-fotos-1`
- `desktop-dashboard-busqueda-1`

Estado: completado
