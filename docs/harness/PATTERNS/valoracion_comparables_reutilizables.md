# Valoracion Comparables Reutilizables

## Cuando Usarlo

Cuando se vaya a evolucionar la valoracion inmobiliaria desde comparables
ligados a visita hacia una base reutilizable de testigos de mercado.

## Patron

- Separar testigo base de su uso en un expediente.
- Guardar snapshot del testigo cuando se vincula a una valoracion.
- Guardar ajustes por testigo vinculado, no en el testigo base.
- Mantener historico/versionado si cambia precio, fuente, fecha o validacion.
- Conservar fallback legacy desde `comparables_valoracion` mientras dure la
  transicion.

## Tablas Orientativas

- `testigos_valoracion`: base reusable.
- `testigos_valoracion_fotos`: metadatos de fotos o capturas manuales de testigo; no implica descarga remota ni scraping.
- `testigo_valoracion_versiones`: historico opcional, pendiente si se necesita versionar cambios de fuente/precio.
- `valoracion_expediente_testigos`: seleccion/snapshot por expediente.
- `valoracion_testigo_ajustes`: coeficientes y justificacion.
- `valoracion_resultados`: resultado versionado por metodo.

## Reglas

- No borrar `comparables_valoracion` en la primera fase.
- No migrar datos reales automaticamente.
- No recalcular informes antiguos cuando cambia un testigo reutilizable.
- Limitar coeficientes individuales de ajuste a -20%/+20%.
- Mantener ownership y soft delete (`activo`) en la base reutilizable.
- Persistir fotos de testigo como metadatos solo cuando exista flujo seguro de archivos; el esquema puede prepararse antes sin crear uploads.
- Centralizar lectura antes de tocar UI: `build_informe_context()` debe leer
  primero el modelo nuevo y degradar a legacy solo si no hay datos nuevos.
- Los resultados de valoracion no viven en `valoracion_expediente`; para el
  grupo de resultado se componen desde `valoracion_resultados`.
- La UI inicial de testigos se implementa con formularios server-side:
  `/valoracion/testigos` para la base reusable y
  `/expedientes/{expediente_id}/valoracion/testigos` para la seleccion concreta
  del expediente.
- `/valoracion/testigos` debe evolucionar como biblioteca: busqueda simple,
  cards mobile-first, unidades profesionales para importes/superficies,
  estado de validacion, enlace de fuente, detalle del testigo y acciones
  claras para editar o seleccionar desde expediente.
- Las fotos de testigo pueden subirse manualmente desde el detalle usando
  `testigos_valoracion_fotos`. No automatizar descarga de imagenes de portales
  ni OCR sin una fase independiente de captura asistida.
- La subida manual de fotos debe reutilizar uploads contextuales del proyecto,
  validar extensiones/tipo de imagen y tamaño maximo razonable, y registrar solo
  metadatos en `testigos_valoracion_fotos`. El borrado fisico de archivos queda
  fuera salvo fase explicita con rollback y criterio sobre uploads reales.
- El alta rapida desktop puede enriquecer el testigo base con atributos
  tecnicos propios del anuncio: superficies especificas, banos, planta,
  exterior/interior, ascensor, balcon, terraza, patio, anos, estado,
  climatizacion, calefaccion, certificacion energetica, garaje y trastero. Debe
  reutilizar columnas existentes cuando las haya y anadir solo columnas
  defensivas para atributos sin equivalente.
- Al vincular un testigo se guarda `snapshot_json`, `orden`, `incluido` y
  `notas_seleccion` en `valoracion_expediente_testigos`. Quitar un testigo del
  expediente elimina solo el vinculo, nunca el testigo base.
- La biblioteca desktop puede vincular un testigo a un expediente solo cuando
  recibe contexto explicito `expediente_id` y el expediente pertenece al usuario
  y es de tipo `valoracion`. Debe evitar duplicados y no debe guardar peso,
  inclusion/exclusion ni representatividad como datos globales del testigo.
- El maximo habitual de 6 testigos debe tratarse como recomendacion no
  bloqueante hasta que exista una regla funcional explicita.
- Los ajustes de homogeneizacion se guardan en `valoracion_testigo_ajustes`
  asociados al vinculo, no al testigo base. Cada coeficiente individual se
  valida entre -0.20 y +0.20.
- Antes del calculo final solo se permite persistir `coeficiente_total = 1 +
  suma de ajustes` y `valor_unitario_ajustado` del vinculo cuando exista
  `valor_unitario_base`.

## Validaciones

- Inicializacion DB temporal.
- Smoke de insercion defensiva: expediente de valoracion, observaciones de visita, testigo reusable, snapshot por expediente, ajustes y resultado demo.
- Smoke de `build_informe_context()` con fallback legacy.
- Smoke de precedencia: datos nuevos prevalecen sobre `valoracion_visita` y
  `comparables_valoracion`.
- Smoke de seleccion de testigos con datos demo cuando exista UI.
- Smoke de snapshot: editar el testigo base antes de vincular queda reflejado en
  el snapshot; quitar el vinculo conserva el testigo base.
- Smoke de ajustes: GET/POST de ajustes por vinculo, validacion de rango,
  coeficiente total, valor unitario ajustado y no modificacion del testigo base.
- Smoke de biblioteca: listado con busqueda, formato con unidades, detalle de
  testigo, ownership y subida manual de foto en DB temporal.

## Anti-Patrones

- Guardar ajustes directamente en el testigo reusable.
- Hacer que un testigo editado cambie informes pasados.
- Usar una unica tabla para testigo, seleccion, ajustes y resultado.
- Implementar calculo final antes de tener trazabilidad de ajustes.
- Descargar imagenes remotas, hacer scraping u OCR desde la biblioteca sin fase
  especifica y validacion humana.
