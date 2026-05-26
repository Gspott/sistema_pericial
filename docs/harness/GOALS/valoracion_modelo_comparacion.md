# Valoracion Inmobiliaria - Diseno De Modelo Por Comparacion

Fecha: 2026-05-25.
Estado: Pending validation
Plan: `valoracion-mover-campos-diseno.md`.

## Objetivo

Disenar la evolucion segura del modelo de valoracion inmobiliaria para separar
datos estables de expediente, observaciones de visita y testigos/comparables
reutilizables, preparando metodo de comparacion profesional sin implementar
todavia esquema, migracion, calculo ni homogeneizacion.

## Nota Sobre PDF De Referencia

El PDF adjunto no aparece como archivo accesible en el workspace. Solo se
detectaron PDFs en `uploads/`, que no se han leido por restriccion explicita.
Por tanto, este diseno usa como referencia funcional la estructura indicada por
el usuario: informe de tasacion profesional con identificacion, documentacion,
entorno, descripcion del inmueble, metodo de comparacion, metodo de coste,
testigos, ajustes, valor unitario ajustado, valor por comparacion, limitaciones
y trazabilidad.

No se copia maquetacion ni estilo visual.

## Auditoria Actual

### `expedientes`

Ya contiene datos estables generales:

- `tipo_informe`, `destinatario`, `cliente`, `direccion`, `codigo_postal`,
  `ciudad`, `provincia`.
- Identificacion fisica general: `tipo_inmueble`, `orientacion_inmueble`,
  `anio_construccion`, `uso_inmueble`, `observaciones_generales`.
- Superficies ya existentes: `superficie_construida`, `superficie_util`.
- Unidad/edificio: `planta_unidad`, `puerta_unidad`, `observaciones_bloque`,
  `observaciones_unidad`, dormitorios, banos.
- Reforma compatible: `reformado`, `fecha_reforma`,
  `observaciones_reforma`.
- Judicial/pericial general: `objeto_pericia`, `alcance_limitaciones`,
  `metodologia_pericial`.

No contiene todavia el bloque estructurado especifico de valoracion:
solicitante, finalidad, documentacion, datos registrales, situacion legal,
metodos previstos, limitaciones generales y variables de mercado base.

### `visitas`

Contiene lo observable durante visita:

- Fecha, tecnico y `observaciones_visita`.
- Ambito/nivel/unidad para visita multiunidad.
- Fotos exteriores y datos de inspeccion/habitabilidad relacionados.

Para valoracion, la visita debe conservar solo hechos observados o
comprobados: estado real, ocupacion observada, reforma observada, incidencias,
comprobaciones fisicas, notas tecnicas y fotos.

### `valoracion_visita`

Tabla actual 1:1 con visita. Mezcla datos estables, datos observados, datos de
mercado, metodo y resultado:

- Encargo: solicitante, NIF/CIF, domicilio, entidad, finalidad.
- Documentacion: documentacion utilizada, datos registrales.
- Identificacion/superficies.
- Situacion legal/urbanistica.
- Entorno.
- Edificio/inmueble.
- Constructivo.
- Estado/ocupacion/fechas.
- Metodo/mercado.
- Resultado y limitaciones.

Problema: varios campos pueden rellenarse antes de visitar, reutilizarse en
informes futuros o pertenecer al expediente, no a una visita concreta.

### `comparables_valoracion`

Tabla actual dependiente de `visita_id`. Sirve como testigo local de una visita
y se borra al borrar la visita. Campos actuales:

- Direccion, fuente, fecha.
- Precio oferta, valor unitario.
- Superficies.
- Tipologia, planta, dormitorios, banos.
- Estado, antiguedad, calidad constructiva.
- Visitado y observaciones.

Problema: no es reutilizable entre expedientes, no tiene versionado, validacion,
precio cierre, trazabilidad de fuente, fotos futuras ni ajustes por expediente.

### Contexto Y Outputs

`build_informe_context()` ya expone:

- `tipo_informe`.
- `es_valoracion`.
- `valoracion` agrupada por secciones.
- `comparables_valoracion`.
- `completitud_valoracion` no bloqueante.

HTML/PDF moderno y DOCX editable moderno ya consumen el contexto moderno. El
DOCX legacy mantiene su propia ruta de respaldo.

## Principio De Separacion

- Expediente: datos estables del encargo, bien, documentacion y criterio
  previsto.
- Visita: hechos observados, comprobaciones fisicas, fotos, incidencias y notas.
- Testigo reutilizable: dato de mercado observado en una fecha/fuente concreta.
- Vinculo expediente-testigo: seleccion para una valoracion concreta,
  ajustes, ponderacion, descarte y trazabilidad.
- Resultado: calculo derivado versionado, no campo manual primario.

## Matriz De Decision De Campos De Valoracion

| Campo | Actual | Futuro | Motivo | UX | Informe | Calculo | Compatibilidad/Fallback | Nueva tabla | Nueva columna |
|---|---|---|---|---|---|---|---|---|---|
| `nombre_solicitante` | `valoracion_visita` | expediente | Encargo estable | Editar desde expediente | Portada/encargo | No calcula | Leer visita si expediente vacio | No | Si |
| `nif_cif_solicitante` | `valoracion_visita` | expediente | Encargo estable | Expediente | Encargo | No calcula | Fallback visita | No | Si |
| `domicilio_solicitante` | `valoracion_visita` | expediente | Encargo estable | Expediente | Encargo | No calcula | Fallback visita | No | Si |
| `entidad_financiera` | `valoracion_visita` | expediente | Dato de encargo | Expediente | Encargo | No calcula | Fallback visita | No | Si |
| `finalidad_valoracion` | `valoracion_visita` | expediente | Finalidad del informe | Expediente con ayuda rapida | Objeto/encargo | Puede condicionar metodo | Fallback visita | No | Si |
| `finalidad_valoracion_detallada` | `valoracion_visita` | expediente | Alcance estable | Expediente | Objeto/encargo | No calcula | Fallback visita | No | Si |
| `documentacion_utilizada` | `valoracion_visita` | expediente | Base documental no depende de visita | Expediente, editable posterior | Documentacion | Puede afectar limitaciones | Fallback visita | No | Si |
| `datos_registrales` | `valoracion_visita` | expediente | Dato registral estable | Expediente | Identificacion/legal | No calcula | Fallback visita | No | Si |
| `identificacion_bien` | `valoracion_visita` | expediente | Describe bien valorado | Expediente | Identificacion | Base del informe | Fallback visita | No | Si |
| `superficie_valoracion` | `valoracion_visita` | expediente | Magnitud principal de calculo | Expediente con aviso de fuente | Resultado | Multiplica valor unitario | Fallback a superficie construida/visita | No | Si |
| `superficie_util` | expediente y `valoracion_visita` | expediente | Ya existe parcialmente | Expediente | Identificacion | Puede informar comparacion | Usar expediente, fallback visita | No | Puede reutilizar existente |
| `superficie_terraza` | `valoracion_visita` | expediente | Estable del inmueble | Expediente | Identificacion | Ajuste futuro | Fallback visita | No | Si |
| `superficie_zonas_comunes` | `valoracion_visita` | expediente | Estable del inmueble | Expediente | Identificacion | Ajuste futuro | Fallback visita | No | Si |
| `superficie_total` | `valoracion_visita` | expediente | Estable/derivado | Expediente | Identificacion | Puede derivarse | Fallback visita; no calcular aun | No | Si |
| `superficie_comprobada` | `valoracion_visita` | visita o hibrido | Es comprobacion fisica | Check visita | Limitaciones | Afecta confianza | Fallback visita | No | Posible en visita_valoracion_observada |
| `situacion_ocupacion` | `valoracion_visita` | expediente + visita observada | Puede cambiar; hay dato juridico y observado | Expediente y visita | Legal/estado | Puede ajustar | Fallback visita | No | Si en expediente y visita |
| `situacion_urbanistica` | `valoracion_visita` | expediente | Dato estable/documental | Expediente | Legal | Riesgo/limitacion | Fallback visita | No | Si |
| `servidumbres` | `valoracion_visita` | expediente | Dato legal estable | Expediente | Legal | Puede limitar valor | Fallback visita | No | Si |
| `linderos` | `valoracion_visita` | expediente | Dato registral/catastral | Expediente | Legal/identificacion | No calcula | Fallback visita | No | Si |
| `ubicacion_valoracion` | `valoracion_visita` | expediente | Localizacion del bien | Expediente | Entorno | Ajuste ubicacion | Fallback direccion/visita | No | Si |
| `descripcion_entorno` | `valoracion_visita` | expediente | Entorno estable | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `grado_consolidacion` | `valoracion_visita` | expediente | Mercado/zona | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `antiguedad_entorno` | `valoracion_visita` | expediente | Zona/mercado | Expediente | Entorno | No principal | Fallback visita | No | Si |
| `rasgos_urbanos` | `valoracion_visita` | expediente | Zona/mercado | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `nivel_renta` | `valoracion_visita` | expediente | Variable de mercado | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `uso_predominante` | `valoracion_visita` | expediente | Entorno estable | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `equipamientos` | `valoracion_visita` | expediente | Entorno estable | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `infraestructuras` | `valoracion_visita` | expediente | Entorno estable | Expediente | Entorno | Ajuste ubicacion | Fallback visita | No | Si |
| `tipo_edificio` | `valoracion_visita` | expediente | Caracteristica estable | Expediente | Edificio | Comparabilidad | Fallback visita/tipo_inmueble | No | Si |
| `numero_portales` | `valoracion_visita` | expediente | Edificio estable | Expediente | Edificio | No principal | Fallback visita | No | Si |
| `numero_escaleras` | `valoracion_visita` | expediente | Edificio estable | Expediente | Edificio | No principal | Fallback visita | No | Si |
| `numero_ascensores` | `valoracion_visita` | expediente | Edificio estable | Expediente | Edificio | Ajuste futuro | Fallback visita | No | Si |
| `estado_conservacion` | `valoracion_visita` | visita + expediente resumen | Observado en visita, resumen puede persistir | Visita primero | Estado | Ajuste estado | Fallback visita | No | Posible columna visita_valoracion |
| `antiguedad` | `valoracion_visita` | expediente | Estable | Expediente | Edificio | Ajuste antiguedad | Fallback anio_construccion/visita | No | Si o derivar |
| `calidades` | `valoracion_visita` | expediente + visita | Estable pero puede observarse | Expediente editable, visita verifica | Edificio/estado | Ajuste calidades | Fallback visita | No | Si |
| `vistas` | `valoracion_visita` | expediente + visita | Puede observarse | Visita con prefill expediente | Edificio | Ajuste futuro | Fallback visita | No | Si |
| `uso_residencial` | `valoracion_visita` | expediente | Estable | Expediente | Edificio | Comparabilidad | Fallback uso_inmueble/visita | No | Si |
| `estructura` | `valoracion_visita` | expediente | Caracteristica constructiva | Expediente | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `cubierta` | `valoracion_visita` | expediente | Edificio estable | Expediente | Constructivo | Ajuste futuro | Fallback visita | No | Si |
| `cerramientos` | `valoracion_visita` | expediente | Constructivo estable | Expediente | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `aislamiento` | `valoracion_visita` | expediente | Constructivo estable | Expediente | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `carpinteria` | `valoracion_visita` | expediente + visita | Puede observarse | Visita verifica | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `acristalamiento` | `valoracion_visita` | expediente + visita | Puede observarse | Visita verifica | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `instalaciones` | `valoracion_visita` | expediente + visita | Puede observarse | Visita verifica | Constructivo | Ajuste constructivo | Fallback visita | No | Si |
| `estado_inmueble` | `valoracion_visita` | visita | Estado observado | Visita | Estado | Ajuste estado/calidades | Fallback visita actual | No | En tabla observacion visita |
| `regimen_ocupacion` | `valoracion_visita` | visita + expediente | Observado/legal | Visita y expediente | Estado/legal | Puede limitar | Fallback visita | No | Si |
| `inmueble_arrendado` | `valoracion_visita` | expediente + visita | Situacion juridica/observada | Expediente y visita | Estado/legal | Metodo rentas futuro | Fallback visita | No | Si |
| `fecha_visita` | `valoracion_visita` | visita | Ya existe `visitas.fecha` | Sin duplicar | Estado | No calcula | Usar visita.fecha | No | No |
| `fecha_emision` | `valoracion_visita` | informe/expediente | Fecha de documento | En generacion informe | Portada | No calcula | Fecha actual/contexto | No | Opcional |
| `fecha_caducidad` | `valoracion_visita` | expediente o resultado | Validez de valoracion | Expediente/resultado | Resultado | No calcula | Fallback visita | No | Si |
| `criterios_metodo_valoracion` | `valoracion_visita` | expediente | Metodo previsto | Expediente | Metodo | Determina calculo | Fallback visita | No | Si |
| `testigos_comparables` | `valoracion_visita` | sustituir por vinculos | Texto libre obsoleto | Mostrar resumen generado | Metodo | No fiable para calculo | Mantener legacy como nota | Si | No |
| `observaciones_testigos` | `valoracion_visita` | expediente-testigo | Observacion de seleccion | En seleccion de testigos | Comparables | Trazabilidad | Fallback visita | Si | No |
| `variables_mercado` | `valoracion_visita` | expediente/resultado | Marco de mercado | Expediente | Metodo | Contexto del calculo | Fallback visita | No | Si |
| `metodo_homogeneizacion` | `valoracion_visita` | resultado/version | Pertenece al calculo | Pantalla ajustes | Metodo | Regla de calculo | Fallback visita | Si | No |
| `valor_unitario` | `valoracion_visita` | resultado calculado | Derivado | Solo lectura con override | Resultado | Resultado intermedio | Fallback visita manual | Si | No |
| `valor_resultante` | `valoracion_visita` | resultado calculado | Derivado | Solo lectura con override | Resultado | Resultado | Fallback visita manual | Si | No |
| `valor_tasacion_final` | `valoracion_visita` | resultado final + override | Resultado final | Revision final | Resultado | Resultado | Fallback visita manual | Si | No |
| `condicionantes_limitaciones_valoracion` | `valoracion_visita` | expediente | Limitaciones generales | Expediente | Limitaciones | Puede afectar validez | Fallback visita | No | Si |
| `observaciones_valoracion` | `valoracion_visita` | hibrido | Observaciones generales o visita | Separar expediente/visita | Limitaciones/notas | No calcula | Fallback visita | No | Si |

## Matriz De Decision De Comparables Actuales

| Campo | Actual | Futuro | Motivo | UX | Informe | Calculo | Compatibilidad/Fallback | Nueva tabla | Nueva columna |
|---|---|---|---|---|---|---|---|---|---|
| `direccion_testigo` | `comparables_valoracion` | testigo reutilizable | Identidad del testigo | Alta/catalogo | Tabla testigos | No calcula | Copiar desde comparable legacy | Si | Si |
| `fuente_testigo` | `comparables_valoracion` | testigo reutilizable + version | Trazabilidad | Campo obligatorio recomendado | Tabla/fuente | Confianza | Legacy | Si | Si |
| `fecha_testigo` | `comparables_valoracion` | testigo reutilizable/version | Mercado temporal | Campo de fecha | Tabla/fuente | Actualidad | Legacy | Si | Si |
| `precio_oferta` | `comparables_valoracion` | testigo version | Dato mercado | Numerico con texto fuente | Tabla testigos | Base €/m2 | Legacy texto | Si | Si |
| `precio_cierre` | no existe | testigo version | Mejor dato si existe | Opcional | Tabla testigos | Preferente frente oferta | Vacio | Si | Si |
| `valor_unitario` | `comparables_valoracion` | calculado/cache | Derivado de precio/superficie | Solo lectura/override | Tabla testigos | Base ajuste | Legacy manual | Si | Si |
| `superficie_construida` | `comparables_valoracion` | testigo reutilizable | Base €/m2 | Numerico | Tabla testigos | Base principal | Legacy | Si | Si |
| `superficie_util` | `comparables_valoracion` | testigo reutilizable | Dato auxiliar | Opcional | Tabla testigos | Ajuste futuro | Legacy | Si | Si |
| `tipologia` | `comparables_valoracion` | testigo reutilizable | Comparabilidad | Select/texto | Tabla testigos | Filtro | Legacy | Si | Si |
| `planta` | `comparables_valoracion` | testigo reutilizable | Comparabilidad | Campo simple | Tabla testigos | Ajuste futuro | Legacy | Si | Si |
| `dormitorios` | `comparables_valoracion` | testigo reutilizable | Comparabilidad | Campo simple | Tabla testigos | Filtro | Legacy | Si | Si |
| `banos` | `comparables_valoracion` | testigo reutilizable | Comparabilidad | Campo simple | Tabla testigos | Filtro | Legacy | Si | Si |
| `estado_conservacion` | `comparables_valoracion` | testigo reutilizable | Ajuste estado/calidad | Select/texto | Tabla testigos | Ajuste calidades | Legacy | Si | Si |
| `antiguedad` | `comparables_valoracion` | testigo reutilizable | Ajuste antiguedad | Campo simple | Tabla testigos | Ajuste ±20% | Legacy | Si | Si |
| `calidad_constructiva` | `comparables_valoracion` | testigo reutilizable | Ajuste calidades | Select/texto | Tabla testigos | Ajuste ±20% | Legacy | Si | Si |
| `visitado` | `comparables_valoracion` | testigo version/validacion | Confianza | Toggle/estado | Trazabilidad | Peso/confianza futuro | Legacy | Si | Si |
| `observaciones` | `comparables_valoracion` | testigo + vinculo | Puede ser generica o de seleccion | Dos campos | Tabla/notas | Auditoria | Legacy en nota de vinculo | Si | Si |
| ascensor | no existe | testigo reutilizable | Variable de comparacion | Toggle/texto | Tabla testigos | Ajuste futuro | Vacio | Si | Si |
| garaje | no existe | testigo reutilizable | Variable de comparacion | Toggle/texto | Tabla testigos | Ajuste futuro | Vacio | Si | Si |
| trastero | no existe | testigo reutilizable | Variable de comparacion | Toggle/texto | Tabla testigos | Ajuste futuro | Vacio | Si | Si |
| ubicacion | parcial direccion | testigo reutilizable | Ajuste ubicacion | Zona/barrio | Tabla testigos | Ajuste ±20% | Derivar de direccion si vacio | Si | Si |
| referencia | no existe | testigo reutilizable | Identificador fuente | Campo texto | Trazabilidad | No calcula | Vacio | Si | Si |
| validacion | no existe | testigo reutilizable | Control calidad | Estado validado/dudoso/descartado | Trazabilidad | Puede excluir | Default pendiente | Si | Si |
| reutilizable | no existe | testigo reutilizable | Privacidad/calidad | Toggle | No siempre mostrar | Permite base comun | Default si | Si | Si |

## Modelo Futuro Recomendado

### Tablas Candidatas

`valoracion_expediente`

- 1:1 con `expedientes`.
- Guarda datos estables especificos de valoracion sin inflar `expedientes`.
- Campos candidatos: solicitante, finalidad, documentacion, datos registrales,
  superficies de valoracion, situacion legal/urbanistica, entorno,
  descripcion general, caracteristicas constructivas, metodos previstos,
  limitaciones generales y variables de mercado.
- Alternativa: columnas defensivas en `expedientes`. Recomendacion: tabla 1:1
  para evitar que `expedientes` siga creciendo.

`valoracion_visita_observaciones`

- 1:1 con `visitas`.
- Guarda estado observado, reforma observada, ocupacion observada,
  comprobaciones fisicas, incidencias y notas del tecnico.
- Puede convivir temporalmente con `valoracion_visita`.

`testigos_valoracion`

- Base reutilizable de mercado.
- Campos: direccion, referencia, fuente, fecha, superficies, antiguedad,
  estado, calidades, constructivo, planta, ascensor, garaje, trastero,
  ubicacion, precio oferta, precio cierre, valor unitario cacheado,
  observaciones, estado_validacion, reutilizable, owner_user_id, activo.
- Soft delete mediante `activo`, porque es catalogo/base reutilizable.

`testigo_valoracion_versiones`

- Historico opcional cuando un testigo cambia precio, fuente, fecha o
  validacion.
- Permite conservar snapshots de mercado sin mutar informes antiguos.
- Si se quiere simplificar fase inicial, se puede posponer y usar snapshot en
  el vinculo expediente-testigo.

`valoracion_expediente_testigos`

- Relacion N:M entre expediente y testigo.
- Guarda seleccion concreta para el informe: orden, incluido/excluido,
  motivo_descarte, snapshot de precio/superficie en el momento de usarlo,
  notas de seleccion y peso futuro.
- Normalmente 6 testigos seleccionados por comparacion, sin imponerlo como
  limite duro.

`valoracion_testigo_ajustes`

- Ajustes por testigo vinculado.
- Campos: factor (`superficie_construida`, `ubicacion`, `antiguedad`,
  `calidades`, `caracteristicas_constructivas`), coeficiente, justificacion,
  valor_unitario_base, valor_unitario_ajustado parcial/final futuro.
- Limite de coeficiente: -0.20 a +0.20.

`valoracion_resultados`

- Resultado versionado por expediente.
- Metodo comparacion: valor_unitario_medio_ajustado, superficie_base,
  valor_comparacion, redondeo, override_manual, justificacion_override.
- Metodo coste: campos reservados para valor suelo/construccion/depreciacion
  en fase futura.
- No implementar calculo en esta fase.

### Relaciones

- `expedientes.id` -> `valoracion_expediente.expediente_id`.
- `visitas.id` -> `valoracion_visita_observaciones.visita_id`.
- `testigos_valoracion.id` -> `valoracion_expediente_testigos.testigo_id`.
- `expedientes.id` -> `valoracion_expediente_testigos.expediente_id`.
- `valoracion_expediente_testigos.id` ->
  `valoracion_testigo_ajustes.expediente_testigo_id`.
- `expedientes.id` -> `valoracion_resultados.expediente_id`.

### Compatibilidad

- Mantener `valoracion_visita` y `comparables_valoracion` como legacy activo
  durante varias fases.
- `build_informe_context()` debe leer primero el modelo nuevo y completar con
  fallback desde `valoracion_visita`/`comparables_valoracion`.
- No mover datos automaticamente en produccion.
- Si se migra, hacerlo solo en sandbox/copia temporal y con reporte antes de
  cualquier decision real.

## Sistema De Ajustes / Homogeneizacion

No implementar todavia. Diseno conceptual:

1. Cada testigo vinculado tiene un `valor_unitario_base`.
2. Se aplican coeficientes independientes de -20% a +20%:
   - superficie construida;
   - ubicacion;
   - antiguedad;
   - calidades;
   - caracteristicas constructivas.
3. El coeficiente debe guardar:
   - factor;
   - porcentaje;
   - justificacion;
   - usuario/fecha futura si se anade auditoria;
   - si se aplica o queda como borrador.
4. Formula conceptual inicial:
   - `coeficiente_total = 1 + suma(coeficientes)`;
   - `valor_unitario_ajustado = valor_unitario_base * coeficiente_total`;
   - validar que cada coeficiente individual esta entre -0.20 y +0.20.
5. Valor por comparacion:
   - calcular media o media ponderada de los valores unitarios ajustados;
   - multiplicar por superficie de valoracion del inmueble;
   - guardar resultado versionado.
6. Auditoria:
   - conservar snapshot de cada testigo usado;
   - conservar ajustes y justificaciones;
   - no recalcular informes antiguos si cambia el testigo base.

## Flujo UX Futuro

1. Expediente: alta/edicion de datos estables de valoracion.
2. Visita: captura de observaciones fisicas, fotos e incidencias.
3. Testigos: busqueda/alta en base reutilizable.
4. Seleccion: vincular 6 testigos recomendados al expediente.
5. Ajustes: editar coeficientes por testigo con limites visibles.
6. Resultado: previsualizar €/m2 ajustado y valor por comparacion.
7. Informe: renderizar secciones y tabla de trazabilidad.

Debe seguir siendo mobile-first, pero los ajustes pueden requerir una pantalla
compacta tipo lista/tabla responsive, no una tabla pesada en visita.

## Roadmap Tecnico Seguro

### Fase DB Defensiva

- Crear tablas nuevas sin borrar ni renombrar columnas.
- Usar `CREATE TABLE IF NOT EXISTS` y `asegurar_columna()` donde aplique.
- Smoke: inicializacion DB temporal y compatibilidad con informes existentes.
- No migrar datos reales.

### Fase Formularios Expediente

- Crear/ajustar seccion de valoracion en detalle/edicion de expediente.
- Guardar datos estables en `valoracion_expediente`.
- Mantener fallback desde `valoracion_visita`.
- Smoke de alta/edicion con DB temporal.

### Fase Comparables Reutilizables

- Crear base de `testigos_valoracion`.
- Permitir alta manual de testigo y vinculo a expediente.
- Importar/duplicar desde comparable legacy solo en accion explicita sandbox.
- Mantener `comparables_valoracion` hasta completar transicion.

### Fase Ajustes

- Crear `valoracion_expediente_testigos` y `valoracion_testigo_ajustes`.
- Validar limites -20%/+20%.
- Guardar justificacion y snapshot.
- No calcular resultado final todavia, solo persistir ajustes.

### Fase Calculo

- Implementar calculo de valor unitario ajustado y valor por comparacion.
- Definir redondeos, tratamiento de precio oferta/cierre y pesos.
- Incorporar metodo de coste como bloque separado.
- Smoke de calculo con datos demo.

### Fase QA

- Smokes de contexto, HTML/PDF y DOCX.
- QA visual con expediente demo/sandbox.
- Verificar que patologias, inspeccion y habitabilidad no cambian.

### Fase Migracion Opcional Sandbox

- Script sandbox que copie datos desde `valoracion_visita` y
  `comparables_valoracion` a modelo nuevo.
- Reporte de campos no migrables y conflictos.
- Decision humana antes de cualquier migracion real.

## Riesgos

- Duplicar fuente de verdad si se escribe a modelo nuevo y legacy sin regla de
  precedencia.
- Romper informes modernos si `build_informe_context()` no conserva fallback.
- Inflar `expedientes` con demasiadas columnas si no se usa tabla 1:1.
- Convertir ajustes profesionales en calculo opaco sin snapshot ni
  justificacion.
- Usar testigos reutilizables sin ownership, validacion o estado de calidad.

## Recomendacion

La siguiente fase implementable debe ser solo DB defensiva sobre SQLite
temporal:

- `valoracion_expediente`.
- `valoracion_visita_observaciones`.
- `testigos_valoracion`.
- `valoracion_expediente_testigos`.
- `valoracion_testigo_ajustes`.

Sin calculo, sin migracion y con `build_informe_context()` manteniendo lectura
legacy hasta que los formularios nuevos esten listos.
