# Main Vs Legacy Routers Map

Auditoria solo lectura realizada el 2026-05-25.

## Resumen

`app/routers/expedientes.py`, `app/routers/visitas.py`,
`app/routers/estancias.py` y `app/routers/patologias.py` existen, pero no estan
incluidos con `include_router()` en `app/main.py`.

No tratarlos como codigo listo para activar. El estado observado es extraccion
parcial/legacy respecto al flujo actual de `app/main.py`.

## Tabla Por Router

| Router | Clasificacion | Riesgo | Estado |
|---|---|---|---|
| `app/routers/expedientes.py` | Extraccion parcial / copia antigua | Alto | Duplica rutas base, pero no conserva ownership, propuesta -> expediente, `tipo_informe`, judicial, multiunidad, imagen catastro moderna ni revision probatoria. |
| `app/routers/visitas.py` | Copia antigua | Alto | Solo cubre nueva/guardar visita. Falta edicion, fotos, climatologia, multiunidad, inspeccion, habitabilidad, valoracion y ownership. |
| `app/routers/estancias.py` | Copia antigua | Alto | CRUD minimo. Falta unidad/multiunidad, ventilacion/acabados completos, fotos, modo inspector, propagacion de acabados, redirects seguros y borrado moderno. |
| `app/routers/patologias.py` | Copia antigua / experimental obsoleta | Critico | Patologias interiores basicas. Falta ownership, multiples fotos, exteriores, mapas/cuadrantes, rol tecnico, localizacion, redirects, PDF/DOCX modernos y flujo probatorio actual. |

## Rutas Duplicadas

- `/`
- `/autocompletar-direccion`
- `/buscar-direcciones`
- `/expedientes`
- `/nuevo-expediente`
- `/guardar-expediente`
- `/detalle-expediente/{expediente_id}`
- `/editar-expediente/{expediente_id}`
- `/actualizar-expediente/{expediente_id}`
- `/nueva-visita/{expediente_id}`
- `/guardar-visita/{expediente_id}`
- `/definir-estancias/{visita_id}`
- `/generar-estancias-base`
- `/guardar-estancia`
- `/borrar-estancia/{estancia_id}`
- `/registrar-patologias/{visita_id}`
- `/guardar-registro`
- `/editar-registro/{registro_id}`
- `/actualizar-registro/{registro_id}`
- `/borrar-registro/{registro_id}`
- `/anadir-climatologia/{visita_id}`
- `/generar-informe/{expediente_id}`

## Rutas Solo En Routers Legacy

- `/iphone`
- `/iPhone`

## Rutas Solo En `app/main.py`

- Niveles y unidades de expediente.
- Edicion y actualizacion avanzada de visita.
- Fotos de visita, estancia, patologia, exterior y cuadrantes.
- Mapas de patologia y cuadrantes.
- Patologias exteriores.
- Duplicado de registros interiores/exteriores.
- Informe HTML imprimible.
- PDF profesional.
- DOCX editable.
- Descarga de informe.
- Borrado completo de expediente.
- Borrado completo de visita.
- Climatologia avanzada y API climatologia.
- Flujo de inspeccion, habitabilidad y valoracion.

## Divergencias Criticas

- Los routers legacy no usan `get_current_user()` ni helpers `get_owned_*`.
- Hacen consultas directas por `id`, sin validar `owner_user_id`.
- Usan `request.app.state.templates.TemplateResponse`, pero no inyectan
  `current_user` como `render_template()` de `app/main.py`.
- `expedientes.py` recibe `numero_expediente` desde formulario; `app/main.py`
  lo genera transaccionalmente.
- `patologias.py` usa foto unica legacy; `app/main.py` usa multiples fotos
  relacionadas y sincronizacion de foto principal.
- `estancias.py` borra registros interiores simples; `app/main.py` conserva
  logica de fotos relacionadas y contexto multiunidad.
- `visitas.py` copia estancias antiguas; `app/main.py` usa
  `crear_visita_si_no_existe()`, asociacion a nivel/unidad y formularios por
  tipo de informe.

## Dependencias Peligrosas

- `request.app.state.templates` como dependencia implicita del setup de
  `app/main.py`.
- `UPLOAD_DIR` directo en `app/routers/patologias.py`.
- `get_connection()` directo en todos los routers legacy.
- Helper `app.utils.helpers.borrar_foto_si_existe`, distinto de helpers modernos
  concentrados en `app/main.py`.
- No hay imports cruzados hacia `app/main.py`, lo cual evita ciclos, pero
  tambien confirma que no reutilizan la logica moderna.

## Por Que No Hacer `include_router()` Todavia

1. Registraria rutas duplicadas con `app/main.py`.
2. El orden de registro podria activar logica antigua o dejar rutas inalcanzables.
3. Falta ownership/autenticacion explicita.
4. Se perderian flujos modernos de propuestas, multiunidad, informes, fotos,
   exterior, mapas y revision probatoria.
5. Los contextos Jinja no coinciden con las plantillas actuales.
6. Borrados y uploads tienen comportamiento antiguo.

## Estrategia Futura Segura

1. No activar routers legacy completos.
2. Crear mapa ruta a ruta antes de cualquier extraccion.
3. Elegir un flujo pequeno y de bajo riesgo.
4. Extraer helpers comunes desde `app/main.py` solo cuando haya smoke test.
5. Mantener misma ruta, mismo contexto Jinja y mismas validaciones.
6. Ejecutar smoke antes/despues.
7. Sustituir una ruta cada vez.
8. No borrar routers legacy hasta completar mapa y decision humana.
