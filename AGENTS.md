# AGENTS.md

Guia operativa para Codex en este repositorio. Este documento es especifico de Sistema Pericial y debe usarse para mantener cambios pequenos, coherentes y seguros.

Ultima consolidacion normativa: 2026-05
Documento canonico: AGENTS.md
Alias sincronizado: agents.md

## Canon actual del proyecto

- El archivo canonico es `AGENTS.md`. Si existe `agents.md`, debe considerarse copia o alias y mantenerse sincronizado, o renombrarse para evitar divergencias.
- La navegacion principal activa es hamburguesa izquierda + drawer. `_top_nav.html` queda como patron secundario/legacy y solo debe usarse donde ya exista o se indique expresamente.
- La revision probatoria detecta visita sin climatologia, cuadrantes incompletos si aplica, fotos faltantes, patologias sin documentacion suficiente, estancias incompletas e informe pendiente.
- Orden recomendado de siguiente accion en revision probatoria:
  1. Climatologia de la visita.
  2. Cuadrantes obligatorios/incompletos si aplica.
  3. Estancias sin foto o datos minimos.
  4. Patologias sin foto/documentacion.
  5. Otros datos tecnicos opcionales.
  6. Generar informe, solo cuando la visita este suficientemente documentada.
- Formula canonica de rol final: `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.
- Soft delete aplica a entidades de biblioteca mediante `activo`.
- Los registros concretos de una visita/caso pueden eliminarse fisicamente si el flujo lo requiere.
- Duplicado/eliminacion: interiores soportados como flujo ordinario; exteriores solo soportados si existe endpoint/implementacion especifica documentada. Si el duplicado exterior existe, debe marcarse expresamente como soportado.

## Estado del sistema

### Activo

- Hamburguesa izquierda + drawer como navegacion principal.
- Drawer `+` para altas globales.
- CTAs contextuales solo cuando aporten pre-relleno, dependan del registro actual o reduzcan pasos reales.
- Revision probatoria con climatologia, cuadrantes, estancias, fotos, patologias e informe pendiente.
- Formula canonica de rol final: `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.
- Soft delete en biblioteca mediante `activo`.
- Borrado fisico permitido para registros de caso/visita cuando el flujo lo requiere.
- Generacion manual de informe.
- Validacion JS con `node --check <archivo.js>`.

### Legacy / secundario

- `_top_nav.html` como patron secundario/legacy.
- Cualquier navegacion superior flotante que duplique la navegacion principal.

### Experimental / condicionado

- Duplicado/eliminacion exterior solo si existe endpoint o implementacion especifica documentada.
- Cualquier endpoint auxiliar que dispare flujos existentes, siempre que no cree logica de negocio paralela.

### Pendiente / revisar

- Cualquier parte del documento que siga sin implementacion clara.
- Cualquier regla que dependa de codigo no verificado.
- Cualquier seccion antigua que contradiga el canon.

## Supuestos del sistema

- El uso principal es mobile first, especialmente desde iPhone durante visitas reales.
- Puede existir conectividad intermitente; los flujos deben tolerar trabajo parcial y reanudacion.
- Las visitas parcialmente completas estan permitidas y no deben bloquear la continuidad del trabajo de campo.
- La generacion de informe debe ser tolerante a datos faltantes y mostrar advertencias cuando proceda.
- El backend evoluciona de forma incremental sobre el sistema existente.
- Reutilizar flujos implementados tiene prioridad sobre crear flujos paralelos.
- La compatibilidad con trabajo de campo movil pesa mas que optimizaciones desktop-first.

## Reglas invariantes

- Mobile first.
- No duplicar navegacion principal.
- No crear APIs de negocio paralelas.
- Reutilizar flujos existentes antes de crear nuevos.
- Drawer para altas globales; CTA contextual solo si aporta contexto real.
- La visita no debe bloquearse por campos tecnicos secundarios.
- Separar "completo para continuar visita" de "completo tecnicamente para informe".
- La revision probatoria debe detectar y priorizar con el mismo criterio.
- El informe debe poder generarse manualmente, aunque no sea CTA recomendada si faltan datos.
- La biblioteca usa soft delete; los registros de caso pueden tener borrado fisico.
- No hardcodear versiones de service worker/PWA.
- Validar cualquier JS modificado con `node --check <archivo.js>`.
- Mantener `AGENTS.md` y `agents.md` sincronizados.

## Patrones aprobados

- Hamburguesa izquierda + drawer como navegacion principal.
- Drawer `+` para altas globales.
- CTAs contextuales con pre-relleno o dependencia del registro actual.
- Endpoint FastAPI ligero que solo dispara flujos existentes.
- `subprocess` para lanzar procesos ya existentes cuando este justificado.
- Soft delete con campo `activo` solo para biblioteca/catalogos.
- Borrado fisico para registros de caso/visita si el flujo ya lo contempla.
- Formula canonica de `rol_final`.
- Checklist previo a despliegue.
- Validacion de JS modificado con `node --check <archivo.js>`.
- Versionado PWA mediante placeholder o incremento explicito, no version fija obsoleta.

## Anti-patrones

- Reintroducir navegacion paralela que compita con el drawer.
- Duplicar CTAs globales en listados si ya existen en el drawer.
- Crear APIs de negocio paralelas.
- Crear endpoints que reimplementen logica ya existente.
- Bloquear la continuidad de visita por campos tecnicos opcionales.
- Mezclar criterios de deteccion y prioridad en revision probatoria.
- Usar formulas alternativas para `rol_final`.
- Aplicar soft delete global a registros de caso sin decision explicita.
- Asumir que exterior soporta duplicado/eliminacion si no esta documentado.
- Hardcodear versiones fijas u obsoletas de service worker/PWA.
- Validar solo `static/app_shell.js` cuando se han tocado otros JS.
- Anadir reglas nuevas sin indicar si son activas, legacy, experimentales o pendientes.

## Definition of Done documental

Un cambio documental no se considera cerrado hasta validar:

- Impacto cruzado en la matriz de impacto.
- Documentos tematicos afectados.
- Decisiones activas y ADRs relacionadas.
- Anti-patrones aplicables.
- Checklist correspondiente.
- `docs/changelog.md` si cambia una decision.
- Sincronizacion `AGENTS.md` / `agents.md` si aplica.

## Reglas de migracion documental

Toda regla nueva debe:

- Tener ubicacion normativa clara.
- Tener estado de madurez.
- Tener Decision ID si afecta arquitectura, UX, datos, informes, PWA o backend.
- Indicar impactos.
- Evitar duplicacion.
- Actualizar documentos tematicos relacionados.
- Actualizar `docs/changelog.md` si cambia una decision existente.

## 1. Arquitectura del proyecto

Sistema Pericial es una aplicacion web local para gestion integral de actividad pericial en Espana.

Stack real:

- Python + FastAPI.
- SQLite con `sqlite3.Row`.
- Jinja2 server-side rendering.
- HTML/CSS mobile-first.
- JavaScript minimo y progresivo.
- Sin framework frontend.
- Uso principal en iPhone, Mac y Safari iOS/macOS.
- Entorno local, con DuckDNS/Caddy cuando procede.

Estructura principal:

- `app/main.py`: nucleo historico de expedientes, visitas, estancias, patologias, resumen, informes y autenticacion.
- `app/database.py`: conexion SQLite, `init_db()` y evolucion defensiva con `asegurar_columna()`.
- `app/config.py`: configuracion, `.env`, rutas y cookies.
- `app/routers/`: routers modulares para areas ya separadas.
- `app/services/`: servicios de informes, Catastro, clima, direccion, exportaciones, facturacion y backups.
- `templates/`: vistas Jinja renderizadas en servidor.
- `templates/partials/`: shell visual, navegacion y componentes reutilizables.
- `static/mobile.css`: CSS principal mobile-first.
- `static/pwa.js`: registro de service worker y comportamiento movil de la navegacion superior.
- `static/app_shell.js`: drawer lateral y acciones rapidas.
- `static/sw.js`: service worker.

Routers existentes:

- `app/routers/dashboard.py`
- `app/routers/leads.py`
- `app/routers/clientes.py`
- `app/routers/propuestas.py`
- `app/routers/facturacion.py`
- `app/routers/gastos.py`
- `app/routers/backups.py`
- `app/routers/expedientes.py`
- `app/routers/estancias.py`
- `app/routers/patologias.py`
- `app/routers/visitas.py`

Patron arquitectonico:

- Preparar los datos en backend y mantener los templates simples.
- Renderizar HTML desde Jinja; no crear APIs de negocio paralelas. Si se necesitan integraciones, se permiten endpoints minimos para disparar flujos existentes.
- Reutilizar parciales existentes antes de crear bloques nuevos.
- Mantener CSS centralizado en `static/mobile.css` salvo estilos muy locales o imprimibles.
- Mantener JS pequeno, sin dependencias y como mejora progresiva.
- El sistema esta en una fase avanzada y consolidada: la prioridad no es modernizar el stack ni rehacer arquitectura, sino estabilidad, velocidad operativa, UX movil, automatizacion documental, coherencia visual e integracion incremental.

## 2. Filosofia de cambios

Codex debe trabajar siempre con:

- Cambios quirurgicos.
- Diffs minimos.
- Ediciones localizadas.
- Lectura previa del contexto real.
- Reutilizacion de patrones existentes.
- Compatibilidad con Safari iOS/macOS.
- Compatibilidad con SQLite y bases existentes.

Reglas de trabajo:

- Inspeccionar antes de modificar.
- No reescribir archivos completos si basta un bloque concreto.
- No refactorizar si no se pide expresamente.
- No anadir dependencias sin peticion explicita.
- No introducir React, Vue, Angular ni frontend SPA.
- No crear rutas nuevas si ya existe una ruta que resuelve el flujo.
- No tocar modulos no relacionados.
- No cambiar comportamiento existente salvo que sea el objetivo de la tarea.
- Preferir soluciones server-side con Jinja y datos preparados en Python.
- Evitar propuestas invasivas, excesivamente arquitectonicas o desconectadas del flujo real de trabajo del usuario.
- Asumir que muchas automatizaciones ya existen fuera del repo y que el backend coordina mas de lo que procesa.
- No reemplazar scripts externos ni flujos ya funcionales salvo peticion explicita.

## Documentacion modular

Los detalles tematicos viven en `docs/`. Antes de modificar una zona funcional, consultar el documento correspondiente:

- UX, navegacion, drawer, CTAs y flujo movil: [docs/ux.md](docs/ux.md)
- PWA, service worker, cache y validacion JS: [docs/pwa.md](docs/pwa.md)
- Informes, PDF, DOCX editable y checklist de generacion: [docs/informes.md](docs/informes.md)
- Backend, endpoints minimos, subprocess e integraciones: [docs/backend.md](docs/backend.md)
- Revision probatoria, detecciones y prioridad: [docs/revision_probatoria.md](docs/revision_probatoria.md)
- Modelos de datos, `rol_final`, soft delete y duplicado/eliminacion: [docs/modelos_datos.md](docs/modelos_datos.md)
- Flujo de trabajo para futuros chats IA: [docs/ia_workflow.md](docs/ia_workflow.md)
- Gobernanza documental: [docs/documentation_governance.md](docs/documentation_governance.md)
- Onboarding IA: [docs/onboarding_ia.md](docs/onboarding_ia.md)
- Changelog documental y decisiones trazables: [docs/changelog.md](docs/changelog.md)
- ADRs iniciales e indice: [docs/adr/README.md](docs/adr/README.md)
- Plantillas documentales: [docs/templates/](docs/templates/)
- Grafo documental: [docs/document_graph.md](docs/document_graph.md)
- Deuda documental: [docs/documentation_debt.md](docs/documentation_debt.md)

## Matriz de impacto

| Cambio | Revisar |
|---|---|
| Estancias | [docs/ux.md](docs/ux.md), [docs/revision_probatoria.md](docs/revision_probatoria.md), [docs/informes.md](docs/informes.md), [docs/modelos_datos.md](docs/modelos_datos.md) |
| Patologias | [docs/modelos_datos.md](docs/modelos_datos.md), [docs/revision_probatoria.md](docs/revision_probatoria.md), [docs/informes.md](docs/informes.md), [docs/ux.md](docs/ux.md) |
| Navegacion | [docs/ux.md](docs/ux.md), [docs/pwa.md](docs/pwa.md), [docs/ia_workflow.md](docs/ia_workflow.md) |
| PWA | [docs/pwa.md](docs/pwa.md), [docs/ux.md](docs/ux.md), [docs/backend.md](docs/backend.md) |
| Modelos de datos | [docs/modelos_datos.md](docs/modelos_datos.md), [docs/backend.md](docs/backend.md), [docs/informes.md](docs/informes.md), [docs/revision_probatoria.md](docs/revision_probatoria.md) |
| Revision probatoria | [docs/revision_probatoria.md](docs/revision_probatoria.md), [docs/ux.md](docs/ux.md), [docs/informes.md](docs/informes.md), [docs/modelos_datos.md](docs/modelos_datos.md) |
| Informes | [docs/informes.md](docs/informes.md), [docs/modelos_datos.md](docs/modelos_datos.md), [docs/backend.md](docs/backend.md), [docs/revision_probatoria.md](docs/revision_probatoria.md) |
| Drawer global | [docs/ux.md](docs/ux.md), [docs/pwa.md](docs/pwa.md) |
| Service worker | [docs/pwa.md](docs/pwa.md), [docs/ux.md](docs/ux.md) |
| Roles de patologias | [docs/modelos_datos.md](docs/modelos_datos.md), [docs/informes.md](docs/informes.md), [docs/revision_probatoria.md](docs/revision_probatoria.md) |

## Indice semantico para IA

| Si modificas... | Lee primero |
|---|---|
| Navegacion / drawer / CTAs | [docs/ux.md](docs/ux.md) |
| PWA / service worker / offline | [docs/pwa.md](docs/pwa.md) |
| Informes / PDF / completitud tecnica | [docs/informes.md](docs/informes.md) |
| Revision probatoria / prioridades | [docs/revision_probatoria.md](docs/revision_probatoria.md) |
| Roles / soft delete / duplicados | [docs/modelos_datos.md](docs/modelos_datos.md) |
| Endpoints / FastAPI / subprocess | [docs/backend.md](docs/backend.md) |
| Flujo de trabajo IA | [docs/ia_workflow.md](docs/ia_workflow.md) |
| Cambios documentales historicos | [docs/changelog.md](docs/changelog.md) |

## Areas operativas resumidas

### UX y visita

- Navegacion principal activa: hamburguesa izquierda + drawer.
- Drawer `+`: altas globales.
- CTAs contextuales: solo con pre-relleno, dependencia del registro actual o reduccion real de pasos.
- Mobile first y continuidad de visita por encima de campos tecnicos secundarios.
- Ver [docs/ux.md](docs/ux.md).

### Revision probatoria

- La revision debe detectar y priorizar con el mismo criterio.
- Generar informe sigue disponible manualmente, pero no debe ser CTA recomendada si faltan datos.
- Ver [docs/revision_probatoria.md](docs/revision_probatoria.md).

### Backend e integraciones

- No crear APIs de negocio paralelas.
- Se permiten endpoints minimos para disparar flujos existentes.
- `subprocess` solo para procesos ya existentes y justificados.
- Ver [docs/backend.md](docs/backend.md).

### Datos

- Formula canonica: `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.
- Soft delete solo en biblioteca/catalogos mediante `activo`.
- Registros de caso/visita pueden tener borrado fisico si el flujo lo contempla.
- Ver [docs/modelos_datos.md](docs/modelos_datos.md).

### PWA y JS

- No hardcodear versiones fijas u obsoletas de service worker/PWA.
- Validar cualquier JS tocado con `node --check <archivo.js>`.
- Ver [docs/pwa.md](docs/pwa.md).

### Informes

- HTML/PDF es el estandar visual principal.
- DOCX editable es version secundaria para Apple Pages.
- `build_informe_context()` es fuente unica de datos para PDF y DOCX editable.
- Ver [docs/informes.md](docs/informes.md).

## Validaciones obligatorias

Para cambios Python:

```bash
python3 -m compileall app
```

Para cambios JS:

```bash
node --check <archivo.js>
```

Para `control_app.py`:

```bash
python3 -m compileall control_app.py
```

Para scripts shell:

```bash
bash -n start_all.sh
bash -n start_server.sh
bash -n stop_all.sh
bash -n status.sh
```

Para cambios solo documentales:

- No hace falta compilar Python.
- Validacion documental: `python3 scripts/audit_docs.py`.
- Verificar `git status --short`.
- Confirmar que no se han tocado archivos funcionales.

## 17. Formato de respuestas esperado de Codex

Despues de cada tarea, responder con:

1. Explicacion breve.
2. Archivos modificados.
3. Cambios exactos.
4. Validaciones ejecutadas.
5. Notas de compatibilidad o riesgos.
6. Confirmacion explicita de que NO se ha tocado lo que estaba fuera de alcance.

Reglas de respuesta:

- Ser breve si el cambio es pequeno.
- Separar backend, templates, CSS y JS cuando aplique.
- Indicar ubicacion exacta de los cambios.
- Evitar respuestas gigantescas para cambios minimos.
- Sugerir commits claros cuando tenga sentido.

Ejemplos de commits:

- `fix(propuestas): remove redundant action buttons`
- `improve(control-app): show startup errors`
- `docs: update Codex agent guide`

<!-- audit sync -->
