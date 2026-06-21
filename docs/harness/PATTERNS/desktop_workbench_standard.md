# DESKTOP-WORKBENCH-STANDARD-1

## Objetivo

Mantener Sistema Pericial como aplicacion mobile-first, pero asegurar una capa
de escritorio comoda para el trabajo posterior a la visita: revision,
redaccion, valoracion, costes, CRM, propuestas, facturacion, documentos,
anexos, fotos, busqueda y dashboard.

La visita en campo sigue siendo la excepcion principal: debe continuar
optimizada para movil, con pantallas tactiles, scroll vertical y acciones
directas.

## Principio central

Desktop workbench es una capa adicional, no una sustitucion del flujo movil.

Una pagina puede tener:

- flujo mobile-first base;
- vista desktop en la misma template mediante CSS responsive;
- ruta SSR de workbench cuando la densidad, comparacion o revision lo justifica.

No se debe introducir SPA, React, Vue, Angular ni una navegacion paralela.

## Entorno de referencia desktop

La resolucion de referencia principal para productividad de escritorio es el
monitor principal del autor:

- 2560x1440, QHD, 16:9.
- Uso principal: trabajo postvisita y de oficina.

Este entorno cubre expedientes, informes, valoracion, costes, CRM,
propuestas, facturacion, documentos, fotos, busqueda y dashboard. No cambia el
canon mobile-first de visita en campo.

## Cuando aplica

Evaluar desktop workbench cuando la pantalla se usa sobre todo despues de la
visita y cumple alguna condicion:

- revisa informacion de varias fuentes;
- compara registros o documentos;
- redacta textos largos;
- organiza fotos, anexos o evidencias;
- prepara informes, costes, propuestas, CRM o facturacion;
- requiere filtros, tablas, panel contextual, diagnostico o QA visual;
- se usa durante sesiones largas de escritorio.

## Cuando no aplica

No convertir en desktop-first:

- registro de visita en campo;
- captura rapida de evidencias durante inspeccion;
- formularios tactiles de estancia/patologia usados in situ;
- acciones irreversibles o fiscales sin plan y aprobacion especifica;
- flujos que ya son simples, cortos y suficientemente claros en movil.

## Estándar visual

Una vista desktop madura debe tender a:

- contenedor ancho controlado, sin romper el shell/drawer global;
- no limitar el ancho util de escritorio de forma innecesaria;
- aprovechar el espacio horizontal disponible en >=1920px y especialmente en
  2560x1440;
- alta densidad de informacion cuando mejora la revision o toma de decisiones;
- layouts de tres columnas y paneles simultaneos cuando aporten productividad;
- evitar grandes areas vacias en monitores QHD;
- cabecera operativa con titulo, contexto y acciones primarias;
- metricas o estado resumido si aporta decision;
- layout de 2 o 3 zonas solo en escritorio ancho;
- columna principal para trabajo activo;
- panel lateral para contexto, diagnostico, pendientes o trazabilidad;
- tablas con wrapper horizontal cuando sea necesario;
- filtros SSR o seleccion reactiva por `change` si cambia vista/contexto;
- paneles sticky solo si no degradan movil;
- estado visual en operaciones lentas o recuperables;
- autosave estandar en formularios largos cuando aplique;
- fallback manual y rutas server-side.

En movil, la misma experiencia debe degradar a una columna, mantener tap
targets claros y no exigir hover, teclado ni precision de escritorio.

## Breakpoints desktop recomendados

Las vistas desktop workbench deben validar y ajustar, como minimo, estas
resoluciones:

- 1280x800.
- 1366x768.
- 1440x900.
- 1920x1080.
- 2560x1440, resolucion de referencia principal.

Recomendaciones por ancho:

- >=1280px: activar Sidebar + Main + Inspector cuando la pantalla lo justifique
  y el contenido no quede comprimido.
- >=1920px: ampliar paneles, reducir scroll innecesario y aumentar densidad de
  informacion sin sacrificar legibilidad.
- >=2560px: aprovechar el ancho completo disponible, permitir paneles
  simultaneos, evitar `max-width` estrechos heredados y permitir columnas
  centrales de 1200-1400px o mas si la pantalla y el contenido lo soportan.

## Reglas de convivencia

- Respetar `PROJECT-STANDARDS-GUARD-1`.
- Respetar `AUTOSAVE-STANDARD-1` en formularios largos o criticos.
- Respetar `TIMEZONE-STANDARD-1` para fechas visibles.
- No duplicar fuentes de datos de informes, PDF o DOCX.
- No crear APIs de negocio paralelas si existe ruta SSR o helper canonico.
- No sustituir el guardado manual.
- No mover acciones destructivas a controles ambiguos.
- No convertir tablas densas en unica forma de uso en movil.

## Smokes mínimos

Cada paquete desktop debe incluir smoke proporcional:

- render de la vista desktop o breakpoint/capa esperada;
- acceso desde la pantalla canonica sin romper navegacion mobile-first;
- persistencia o accion principal en DB temporal si hay edicion;
- no regresion del flujo movil existente cuando aplique;
- proteccion de autosave/concurrencia si hay formulario largo;
- `git diff --check` y `python3 scripts/audit_docs.py`.

## Rollout recomendado

1. `desktop-expediente-detalle-1`
2. `desktop-informe-v2-hardening-1`
3. `desktop-valoracion-continuidad-1`
4. `desktop-costes-review-1`
5. `desktop-crm-hardening-1`
6. `desktop-propuestas-facturacion-1`
7. `desktop-documentos-fotos-1`
8. `desktop-dashboard-busqueda-1`

Cada paquete debe ser pequeno, reversible y con una frontera funcional clara.

## Referentes existentes

- `templates/valoracion_workbench.html`
- `templates/informe_v2_editor.html`
- `templates/crm/prospeccion.html`
- `templates/costes/detalle.html`
- `templates/facturacion/workbench.html`
- `templates/pericial_workbench.html`
- `templates/valoracion_testigos_biblioteca.html`

Estos referentes no deben copiarse sin criterio; sirven para extraer patrones:
SSR, grids de escritorio, tablas con scroll, panel contextual, degradacion
movil y acciones server-side.
