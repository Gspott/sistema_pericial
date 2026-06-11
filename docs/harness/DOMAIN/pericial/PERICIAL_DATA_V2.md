# PERICIAL_DATA_V2

## Objetivo

Identificar la informacion nueva realmente imprescindible para soportar `INFORME_SCHEMA_V2` y el flujo de trabajo definido en `PERICIAL_WORKBENCH_V2`.

Este documento no disena tablas, columnas, relaciones, migraciones, modelos ni pantallas. Es una decision documental de modelo conceptual.

Documentos de referencia:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`.
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`.
- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`.

Caso piloto principal: expediente `019-26`.

## Principio de contencion

Anadir campos o entidades tiene coste permanente:

- coste de captura;
- coste de mantenimiento;
- coste de migracion;
- coste de compatibilidad con informes actuales;
- coste cognitivo para el tecnico.

Por tanto, este documento solo acepta informacion nueva si cumple tres condiciones:

1. Es necesaria para el informe V2.
2. No existe ya en el sistema.
3. No puede derivarse de forma razonable desde datos existentes.

## FASE A - Revision critica

### Necesidades ya cubiertas

El sistema ya cubre suficientemente:

- Datos identificativos del expediente.
- Descripcion del dano.
- Causa probable.
- Pruebas e indicios en texto.
- Visitas, estancias y observaciones.
- Patologias interiores y exteriores.
- Fotografias de visita, estancias y patologias.
- Propuesta de reparacion en texto.
- Urgencia/gravedad.
- Evolucion/preexistencia.
- Biblioteca de costes.
- Actuaciones de reparacion con partidas snapshot.
- PEM por actuaciones.
- Anexo economico opcional.

En `019-26`, esos datos permiten construir una version preliminar relevante del informe V2 sin partir de cero.

### Necesidades parcialmente cubiertas

- Resumen ejecutivo: puede componerse con descripcion, causa, urgencia y PEM, pero no existe como pieza validada.
- Metodologia: existen visita, fecha, tecnico y ambito; falta documentacion, medios y pruebas/no pruebas.
- Limitaciones: existe campo textual, pero en `019-26` esta vacio y las limitaciones reales estan dispersas.
- Analisis causal: hay causa y pruebas, pero no recorrido ni relacion causa-efecto estructurada.
- Inventario resumido: puede derivarse de patologias, pero falta seleccion editorial de danos principales.
- Actuaciones ejecutadas: hay indicios y actuaciones de reparacion, pero no estado de ejecucion/verificacion.
- Recomendaciones: aparecen mezcladas con propuesta, evolucion y urgencia.
- Trazabilidad economica: existen actuaciones y partidas, pero no puente conceptual dano -> reparacion -> coste.

### Necesidades sin solucion suficiente

- Limitaciones formalizadas.
- Metodologia pericial minima.
- Trazabilidad dano -> actuacion -> coste.
- Actuaciones ejecutadas/verificadas.
- Recomendaciones tecnicas separadas.
- Documentacion aportada por terceros.
- Seleccion de evidencias clave para cuerpo principal.

## FASE B - Huecos reales en 019-26

### Imprescindible

1. Metodologia pericial minima.
2. Limitaciones e incertidumbres formalizadas.
3. Trazabilidad dano -> reparacion -> coste.
4. Actuaciones ejecutadas/verificadas.
5. Recomendaciones tecnicas separadas.

### Recomendable

1. Resumen ejecutivo validado.
2. Evidencias clave seleccionadas.
3. Documentacion aportada.
4. Recorrido causal estructurado.

### Opcional

1. Severidad sintetica por grupo de dano.
2. Nivel de confianza por conclusion.
3. Justificacion BC3/descompuestos vinculada al expediente.
4. Checklist de defensa por destinatario.

## FASE C - Propuesta conceptual de datos V2

### 1. Metodologia pericial minima

Prioridad: Imprescindible.

#### Problema que resuelve

El informe V2 necesita explicar como se inspecciono, que se reviso y que no se hizo. Hoy la visita recoge fecha, tecnico, ambito y observaciones, pero no basta para defender metodologia ante terceros.

#### Justificacion basada en 019-26

`019-26` tiene una visita registrada y abundante evidencia fotografica, pero `metodologia_pericial` esta vacio. Para un caso de filtraciones con danos extensos, el informe debe diferenciar inspeccion visual, revision fotografica, documentacion disponible y pruebas no realizadas.

#### Informacion minima necesaria

- Visitas consideradas.
- Documentacion revisada.
- Medios utilizados.
- Pruebas realizadas.
- Pruebas no realizadas.
- Alcance real de la inspeccion.

#### Alternativas consideradas

Reutilizar solo `visitas.observaciones_visita` y `metodologia_pericial`. No es suficiente en `019-26`: el campo especifico esta vacio y las observaciones de visita no distinguen pruebas realizadas/no realizadas.

#### Decision

Debe existir como dato V2 conceptual. Puede comenzar como bloque estructurado minimo, no como entidad compleja.

### 2. Limitaciones e incertidumbres formalizadas

Prioridad: Imprescindible.

#### Problema que resuelve

Protege tecnicamente al perito y acota conclusiones. Sin limitaciones, el informe parece afirmar mas de lo que puede comprobar.

#### Justificacion basada en 019-26

El caso contiene indicios de elementos ocultos, necesidad de revisar estructura de madera durante reparacion, baja visibilidad en alguna estancia, posible evolucion por humedad/moho e incertidumbre biologica. Sin embargo, `alcance_limitaciones` esta vacio.

#### Informacion minima necesaria

- Zonas o elementos no comprobados.
- Elementos ocultos.
- Ausencia de catas.
- Ausencia de ensayos.
- Incertidumbres tecnicas.
- Consecuencia de esas limitaciones sobre las conclusiones.

#### Alternativas consideradas

Extraerlo de observaciones, urgencia y evolucion. Es util como ayuda, pero no basta porque queda disperso y no garantiza que el informe incluya la proteccion tecnica.

#### Decision

Debe existir como dato V2 conceptual. Es uno de los tres datos con mejor valor/complejidad.

### 3. Trazabilidad dano -> reparacion -> coste

Prioridad: Imprescindible.

#### Problema que resuelve

Permite explicar por que una partida economica pertenece al informe pericial y que dano justifica cada actuacion.

#### Justificacion basada en 019-26

`019-26` tiene 23 patologias, 2 actuaciones y PEM de 8.616,00 EUR. La valoracion por actuaciones es correcta, pero no existe un puente formal entre familias de dano, actuaciones y partidas.

#### Informacion minima necesaria

- Dano o grupo de danos que justifica la actuacion.
- Actuacion de reparacion vinculada.
- Partida o partidas economicas usadas.
- Criterio de medicion.
- Observacion justificativa.

#### Alternativas consideradas

Usar `patologia_costes` o `actuacion_partidas`. `patologia_costes` no existe para `019-26` y ademas fuerza una relacion demasiado granular. `actuacion_partidas` da coste, pero no explica que dano lo justifica.

#### Decision

Debe existir como dato V2 conceptual. No se disena relacion ni tabla en esta fase, pero el informe V2 no puede defender bien la valoracion sin esta traza.

### 4. Actuaciones ejecutadas/verificadas

Prioridad: Imprescindible.

#### Problema que resuelve

Distingue trabajos observados, trabajos alegados, trabajos presupuestados y trabajos pendientes. Evita mezclar estado de obra con propuesta de reparacion.

#### Justificacion basada en 019-26

El expediente menciona sustitucion o intervencion en falsos techos y necesita comprobar partidas ejecutadas. Las `actuaciones_reparacion` actuales sirven para valorar, pero no indican si una actuacion esta ejecutada, observada, propuesta o pendiente.

#### Informacion minima necesaria

- Actuacion observada o alegada.
- Estado: ejecutada, parcial, pendiente, no verificada.
- Evidencia asociada.
- Adecuacion tecnica observada.
- Observaciones de verificacion.

#### Alternativas consideradas

Reutilizar `actuaciones_reparacion`. No es suficiente: esas actuaciones son estructura economica y propuesta de reparacion, no registro de ejecucion/verificacion.

#### Decision

Debe existir como dato V2 conceptual si el informe va a comprobar partidas ejecutadas o presupuestadas.

### 5. Recomendaciones tecnicas separadas

Prioridad: Imprescindible.

#### Problema que resuelve

Separa reparacion estricta de recomendaciones, comprobaciones futuras y seguimiento. Esto evita debilitar la reclamacion economica mezclando lo necesario para reparar con lo prudente o preventivo.

#### Justificacion basada en 019-26

La propuesta de reparacion incluye saneado y sustitucion, pero tambien revisar madera e insectos durante la reparacion. Esas comprobaciones deben vivir separadas de la reparacion estricta.

#### Informacion minima necesaria

- Recomendacion.
- Motivo tecnico.
- Relacion con limitacion o incertidumbre.
- Prioridad orientativa.
- Seguimiento recomendado.

#### Alternativas consideradas

Extraer recomendaciones de `propuesta_reparacion`, `urgencia_gravedad` y `evolucion_preexistencia`. Puede ayudar, pero si se deja solo como texto mezclado se repite el problema actual.

#### Decision

Debe existir como dato V2 conceptual, aunque puede empezar con una estructura sencilla.

### 6. Resumen ejecutivo validado

Prioridad: Recomendable.

#### Problema que resuelve

Permite entregar una lectura rapida del caso a abogado, aseguradora o juzgado.

#### Justificacion basada en 019-26

El expediente tiene muchos datos; un resumen evita que el lector recorra todas las fichas para entender causa, alcance y PEM.

#### Informacion minima necesaria

- Origen de danos.
- Alcance.
- Danos principales.
- Coste estimado.
- Conclusion resumida.

#### Alternativas consideradas

Componerlo automaticamente desde datos existentes. Es posible para una version preliminar, pero no sustituye revision humana.

#### Decision

Recomendable, no imprescindible como dato nuevo inicial. Puede derivarse y validarse en Workbench antes de crear estructura persistente.

### 7. Evidencias clave seleccionadas

Prioridad: Recomendable.

#### Problema que resuelve

Reduce ruido fotografico y permite diferenciar prueba principal de anexo completo.

#### Justificacion basada en 019-26

Hay 107 fotografias. El informe necesita seleccionar evidencias representativas para el cuerpo principal.

#### Informacion minima necesaria

- Evidencia seleccionada.
- Motivo de seleccion.
- Capitulo o dano al que apoya.

#### Alternativas consideradas

Usar todas las fotos en anexos. No resuelve el cuerpo principal. Usar la primera foto por patologia puede ser demasiado automatico.

#### Decision

Recomendable. Aporta mucho, pero puede posponerse si el MVP usa anexos y fichas actuales.

### 8. Documentacion aportada

Prioridad: Recomendable.

#### Problema que resuelve

Permite listar fotografias previas, presupuestos, comunicaciones u otros documentos aportados por propiedad o terceros.

#### Justificacion basada en 019-26

El caso menciona evidencia de estado previo en fachada y requiere defender el origen de la informacion. El sistema actual no tiene anexo documental formalizado.

#### Informacion minima necesaria

- Documento o referencia.
- Origen.
- Fecha si se conoce.
- Uso en el informe.
- Observacion.

#### Alternativas consideradas

Incluirlo en observaciones generales o anexos manuales. Genera perdida de trazabilidad.

#### Decision

Recomendable. No es el primer dato imprescindible para terminar `019-26`, pero si para defensa documental madura.

### 9. Recorrido causal estructurado

Prioridad: Recomendable.

#### Problema que resuelve

Explica de forma ordenada origen, recorrido y efectos.

#### Justificacion basada en 019-26

La causa probable esta escrita, pero el recorrido de agua por el edificio y la relacion con grupos de dano no estan estructurados.

#### Informacion minima necesaria

- Origen.
- Recorrido probable.
- Danos vinculados.
- Evidencias.
- Incertidumbres.

#### Alternativas consideradas

Usar `causa_probable` y `pruebas_indicios`. Es suficiente para una version preliminar, pero menos solido ante contradiccion.

#### Decision

Recomendable, no imprescindible si primero se refuerzan limitaciones y trazabilidad economica.

## FASE D - DATOS QUE NO DEBEN CREARSE

### 1. Duplicado de patologias resumidas

No crear un segundo registro de patologias para el inventario resumido.

Justificacion: el inventario puede derivarse de patologias, estancias, elementos y observaciones. Crear otra lista duplicaria datos y generaria divergencias.

### 2. Resumen automatico obligatorio por cada foto

No crear metadatos extensos para cada fotografia en esta fase.

Justificacion: `019-26` tiene 107 fotos. Forzar descripcion avanzada por foto aumentaria mucho la carga. Basta con seleccionar evidencias clave si se necesita.

### 3. Severidad obligatoria por cada patologia

No crear severidad granular obligatoria ahora.

Justificacion: puede parecer util, pero el informe V2 puede priorizar por grupos de dano y evidencia. En 019-26 el problema principal es agrupacion y argumentacion, no puntuar cada registro.

### 4. Nuevo presupuesto paralelo

No crear otro presupuesto independiente del sistema de actuaciones y costes.

Justificacion: ya existen `actuaciones_reparacion`, `actuacion_partidas`, biblioteca de costes y anexo economico. Crear otro presupuesto duplicaria importes y snapshots.

### 5. Conclusiones separadas por destinatario

No crear conclusiones distintas para abogado, aseguradora, perito contrario y juzgado.

Justificacion: el informe debe ser unico y defendible. Lo que cambia es la claridad de la estructura, no una conclusion por lector.

### 6. Checklist juridico complejo

No crear un modelo juridico detallado en esta fase.

Justificacion: Sistema Pericial debe mantener foco tecnico. La defensa juridica se beneficia de claridad, limitaciones y trazabilidad, no de juridificar el dato.

### 7. Nueva entidad BC3 por expediente si no hay fuente

No crear estructura BC3 asociada al expediente cuando no existe importacion o fuente real.

Justificacion: `019-26` no tiene BC3 registrado. La biblioteca de costes ya conserva descompuestos y fuentes cuando existen.

### 8. Roles causa/efecto duplicados fuera de patologias

No crear otro rol de patologia paralelo sin decidir antes como usar el campo existente.

Justificacion: `registros_patologias.rol_patologia_observado` ya existe. El problema en `019-26` es que esta vacio, no que falte otro campo equivalente.

## FASE E - Evaluacion de impacto

| Dato conceptual | Informes | UX | Captura movil | PDF | Mantenimiento |
|---|---|---|---|---|---|
| Metodologia pericial minima | Alto: capitulo defendible | Medio: bloque de redaccion | Bajo: puede completarse en escritorio | Medio: nuevo capitulo/orden | Medio |
| Limitaciones e incertidumbres | Muy alto: protege al perito | Medio: requiere claridad | Bajo: no debe bloquear visita | Alto: capitulo obligatorio | Medio |
| Trazabilidad dano-reparacion-coste | Muy alto: defiende PEM | Alto: necesita Workbench | Bajo-medio: no es captura de visita | Alto: valoracion mas solida | Alto |
| Actuaciones ejecutadas/verificadas | Alto: separa hechos de propuesta | Medio-alto | Medio si se observa en visita | Medio-alto | Alto |
| Recomendaciones tecnicas | Alto: separa reparacion de prevencion | Medio | Bajo | Medio | Medio |
| Resumen ejecutivo validado | Alto | Bajo-medio | Bajo | Medio | Bajo-medio |
| Evidencias clave | Alto en legibilidad | Alto | Medio si se selecciona en visita | Alto | Medio |
| Documentacion aportada | Medio-alto | Medio | Bajo | Medio-alto | Medio-alto |
| Recorrido causal estructurado | Alto | Medio | Bajo | Alto | Medio |

## Conclusion obligatoria

### Tres datos nuevos con mejor relacion valor/complejidad

1. Limitaciones e incertidumbres formalizadas.
   - Valor muy alto: protege tecnicamente el informe.
   - Complejidad moderada: puede empezar como bloque conceptual sencillo.

2. Metodologia pericial minima.
   - Valor alto: explica como se hizo la inspeccion.
   - Complejidad baja-media: parte de visitas ya existentes.

3. Recomendaciones tecnicas separadas.
   - Valor alto: limpia la propuesta de reparacion.
   - Complejidad moderada: puede extraerse de textos actuales y revisarse manualmente.

### Tres datos que NO merece la pena crear

1. Duplicado de patologias resumidas.
   - El inventario puede derivarse de registros existentes.

2. Nuevo presupuesto paralelo.
   - Ya existen actuaciones, partidas snapshot y biblioteca de costes.

3. Roles causa/efecto duplicados fuera de patologias.
   - Ya existe `rol_patologia_observado`; falta usarlo, no duplicarlo.

### Porcentaje estimado tras anadir solo datos imprescindibles

`FIELD_MAP_V2` estimaba que `019-26` podria construir aproximadamente el 62% del informe V2 con datos actuales.

Anadiendo solo los datos imprescindibles definidos aqui:

- metodologia pericial minima;
- limitaciones e incertidumbres;
- trazabilidad dano -> reparacion -> coste;
- actuaciones ejecutadas/verificadas;
- recomendaciones tecnicas separadas;

la cobertura estimada subiria a aproximadamente 82%.

Justificacion:

- Los capitulos mas debiles de `019-26` eran metodologia, limitaciones, actuaciones ejecutadas, recomendaciones y trazabilidad economica.
- La prueba, las patologias, las fotos, la causa probable, la propuesta y el PEM ya existen.
- No hace falta duplicar patologias, fotos ni presupuesto.
- Lo que falta es convertir informacion dispersa en decisiones periciales explicitamente defendibles.

## Decision final

La evolucion de datos V2 debe ser pequena y orientada a defensa pericial.

Prioridad real:

1. Formalizar como se inspecciono.
2. Formalizar que no pudo comprobarse.
3. Separar que se recomienda de que se repara.
4. Vincular dano, actuacion y coste.
5. Distinguir actuaciones ejecutadas/verificadas de propuesta economica.

Todo lo demas debe esperar hasta demostrar necesidad real en mas expedientes.
