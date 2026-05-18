# UX, navegacion y flujo movil

Documento tematico de UX para Sistema Pericial. La capa normativa resumida esta en `AGENTS.md`.

## Dependencias

Depende de:

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/revision_probatoria.md](revision_probatoria.md)
- [docs/pwa.md](pwa.md)

Puede impactar:

- UX movil de visita.
- Revision probatoria.
- Generacion de informes.
- Navegacion PWA.
- Propuestas, formularios comerciales e imprimibles/PDF.

## Decisiones

Decision ID: UX-001
Estado: Active
Categoria: UX

La navegacion principal es hamburguesa izquierda + drawer. `_top_nav.html` queda como patron secundario/legacy.

Decision ID: UX-002
Estado: Active
Categoria: UX

El drawer global `+` se reserva para altas globales. Los CTAs contextuales solo se mantienen si aportan pre-relleno, dependen del registro actual o reducen pasos reales.

Decision ID: UX-003
Estado: Active
Categoria: UX

El sistema es mobile first y debe priorizar continuidad de visita, tap targets claros y no perdida de evidencia.

## Madurez

- Drawer global: Activo.
- Navegacion hamburguesa izquierda: Activo.
- `_top_nav.html`: Legacy / secundario.
- CTAs contextuales: Activo, condicionados a contexto real.

## Estado activo

- La navegacion principal activa es hamburguesa izquierda + drawer.
- El drawer `+` se usa para altas globales: Nuevo lead, Nueva propuesta, Nuevo cliente, Nuevo expediente, Nueva factura y Nuevo gasto.
- Solo puede haber un drawer activo a la vez.
- Overlay, Escape y botones `X` cierran drawers.
- `_top_nav.html` es patron secundario/legacy y solo debe usarse donde ya exista o se indique expresamente.
- No reintroducir navegacion paralela que compita con el drawer.

## CTAs y acciones

- No duplicar CTAs globales en dashboard/home/listados si ya existen en el drawer.
- Si una accion aporta pre-relleno, depende del registro actual o reduce pasos reales, puede mantenerse como CTA contextual.
- El drawer `+` permite altas globales; eso no convierte facturacion, IVA, gastos o backups en acciones principales de visita.
- El dashboard debe priorizar estado, navegacion y resumenes, con bajo ruido visual.

## Mobile first

- Pensar siempre en uso desde iPhone durante visita real.
- Mantener tap targets claros, pantallas scroll-friendly y botones visibles.
- Evitar tablas pesadas, sidebars complejas, modales pesados y flujos multi-step innecesarios.
- Priorizar no perder evidencia sobre completar campos secundarios.

## Propuestas

El detalle de propuesta usa formularios server-side y debe seguir siendo usable en movil.

Reglas activas:

- Las lineas de propuesta se muestran como bloques editables y eliminables.
- Los servicios rapidos viven en una seccion discreta y plegable para no convertir el detalle en un formulario enorme.
- Ratificacion judicial, desplazamientos/dietas, urgencia y complejidad se anaden como lineas normales, editables y borrables.
- El formulario general de honorarios avisa cuando existen lineas y evita editar importes globales como fuente primaria.
- El borrado de lineas requiere confirmacion visible en el formulario y confirmacion server-side.
- Los campos `incluye`, `no_incluye` y `condiciones` deben aparecer solo cuando aporten contenido; no generar ruido visual si estan vacios.
- La vista imprimible/PDF debe separar objeto del encargo, alcance, honorarios, condiciones economicas, exclusiones, limitaciones y validez.

Patrones recomendados:

- Usar `details/summary` para bloques secundarios de servicios rapidos.
- Mantener inputs numericos con `min="0"` como ayuda de interfaz, pero confiar en validacion backend.
- Evitar JavaScript obligatorio para crear, editar, borrar o imprimir propuestas.

## Detalle de expediente

- La tarjeta superior "Estado del expediente" muestra visitas, estancias, patologias y CTA de siguiente paso.
- Las acciones principales de flujo viven en esta tarjeta.
- Acciones secundarias se agrupan como "Otras acciones".
- Borrar expediente queda separado como accion destructiva.
- Si un expediente ya tiene visitas, debe seguir existiendo "Registrar nueva visita" como accion secundaria.
- No recomendar generar informe como siguiente accion automatica durante visita si aun hay pendientes probatorios.

## Flujo real de visita de patologias

1. Crear visita desde expediente.
2. Guardar visita.
3. Registrar exterior del edificio.
4. Anadir fotos exteriores descriptivas.
5. Registrar patologias exteriores si aplica.
6. Continuar a estancias.
7. Crear estancias durante la visita, no desde expediente.
8. Completar estancia con foto.
9. Registrar patologias por estancia.
10. Volver a estructura interior.
11. Revision final de pendientes.

## Estructura interior

- `Estructura interior` es el centro operativo de `definir_estancias.html`.
- Debe verse como `resumen_registro.html`, usando tarjetas anidadas: Nivel, Unidad, Estancia.
- No reintroducir listados duplicados de estancias.
- Dentro de cada estancia: boton Editar, boton camara solo como icono `📷`, badge Pendiente/Completa y badge clicable de patologias.
- `Sin patologias registradas` o `X patologias registradas` debe enlazar a `/registrar-patologias/{visita_id}?estancia_id={estancia_id}#formulario_patologia_interior`.
- El boton camara debe volver con `next=/definir-estancias/{visita_id}#estructura-interior`.

## Modo inspector

- Se activa por URL: `/registrar-patologias/{visita_id}?estancia_id={id}`.
- No es un estado persistido.
- Debe mostrar primero el formulario de patologia interior.
- La estancia debe estar preseleccionada.
- El formulario exterior queda secundario/colapsado.
- No mostrar "Generar informe" en modo inspector.
- Tras guardar una patologia desde modo inspector, volver a `/definir-estancias/{visita_id}#estructura-interior`.
- Si existe `next`, `next` tiene prioridad.

## Edicion de estancia y fotos

- Los botones de navegacion en `editar_estancia.html` deben guardar antes de navegar.
- Acciones como Registrar patologias de esta estancia, Siguiente estancia, Estancia anterior, Volver a estructura interior e Ir a revision deben ser `submit` con `redirect_after_save`, no enlaces directos.
- Inputs de foto usan `accept="image/*"` y `capture="environment"`.
- Botones de foto usan `.camera-button`, `.camera-button-inline`, `.camera-button-required`, `.camera-input` y `.sr-only`.
- En estructura interior el boton debe verse solo como `📷`, con `aria-label`.

## Tipo de inmueble y reforma

- En vivienda unifamiliar, ocultar planta de la unidad, puerta/unidad y observaciones de unidad.
- En piso/vivienda plurifamiliar, mostrar planta de la unidad, puerta/unidad y observaciones de unidad.
- "Observaciones del bloque" pasa a llamarse "Observaciones del edificio".
- Reforma se edita desde visita/exterior del edificio y sigue guardandose en expediente por compatibilidad.
