# FIELD_MAP_V2

## Objetivo

Mapear los datos existentes de Sistema Pericial contra los capitulos definidos en `INFORME_SCHEMA_V2`.

La finalidad es determinar que parte de un informe V2 puede construirse hoy con informacion ya almacenada, sin modificar codigo, base de datos, formularios, rutas, plantillas PDF ni migraciones.

Documento de referencia obligatorio: `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`.

Caso piloto obligatorio: expediente `019-26`.

## Alcance y metodo

Este documento es solo analisis documental. No disena nuevas entidades, pantallas ni funcionalidades.

Fuentes inspeccionadas:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`.
- `docs/informes.md`.
- `docs/revision_probatoria.md`.
- `docs/modelos_datos.md`.
- `templates/informes/imprimir.html`.
- `templates/nuevo_expediente.html`.
- `templates/editar_expediente.html`.
- `templates/nueva_visita.html`.
- `templates/editar_registro.html`.
- `templates/actuaciones_reparacion.html`.
- `templates/presupuesto_reparacion.html`.
- `templates/costes/`.
- `app/services/informe.py`.
- `app/main.py`.
- Base SQLite local consultada en modo solo lectura.

## Resumen del expediente 019-26

En la base inspeccionada constan:

- Tipo de informe: `patologias`.
- Ambito de patologias: `interior_exterior`.
- Inmueble: vivienda plurifamiliar en Ayora, Valencia.
- 1 visita registrada, con ambito `edificio_completo`.
- 14 estancias.
- 21 patologias interiores.
- 2 patologias exteriores.
- 107 fotografias asociadas a visita, estancias y patologias.
- 2 actuaciones de reparacion con partidas economicas.
- Total PEM por actuaciones: 8.616,00 EUR.
- 0 costes vinculados mediante `patologia_costes`.
- 0 mapas/cuadrantes de patologias en el expediente.
- 0 roles causa/efecto informados en patologias interiores.

Campos relevantes ya informados en `expedientes`:

- `descripcion_dano`: informado.
- `causa_probable`: informado.
- `pruebas_indicios`: informado.
- `evolucion_preexistencia`: informado.
- `propuesta_reparacion`: informado.
- `urgencia_gravedad`: informado.

Campos relevantes existentes pero vacios en `019-26`:

- `objeto_pericia`.
- `alcance_limitaciones`.
- `metodologia_pericial`.
- `observaciones_generales`.
- `observaciones_bloque`.
- `observaciones_unidad`.

## FASE A - Inventario de datos actuales

| Dato | Origen | Entidad / tabla | Pantalla donde se edita | Exporta actualmente | Uso parcial |
|---|---|---|---|---|---|
| Datos identificativos del expediente | Alta/edicion expediente | `expedientes` | `nuevo_expediente.html`, `editar_expediente.html` | Si, portada y datos del inmueble | Si |
| Objeto pericial | Expediente | `expedientes.objeto_pericia` | `nuevo_expediente.html`, `editar_expediente.html` | Si, si esta informado | En `019-26` esta vacio |
| Alcance y limitaciones | Expediente | `expedientes.alcance_limitaciones` | `nuevo_expediente.html`, `editar_expediente.html` | Si, si esta informado | Existe campo, pero `019-26` esta vacio |
| Metodologia pericial | Expediente | `expedientes.metodologia_pericial` | `nuevo_expediente.html`, `editar_expediente.html` | Si, si esta informado | Existe campo, pero `019-26` esta vacio |
| Descripcion del dano | Expediente | `expedientes.descripcion_dano` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Base para resumen, antecedentes e inventario |
| Causa probable | Expediente | `expedientes.causa_probable` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Base para analisis causal y resumen |
| Pruebas e indicios | Expediente | `expedientes.pruebas_indicios` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Base para analisis causal; no esta normalizado por prueba |
| Evolucion / preexistencia | Expediente | `expedientes.evolucion_preexistencia` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Puede alimentar riesgos e incertidumbre |
| Urgencia / gravedad | Expediente | `expedientes.urgencia_gravedad` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Puede alimentar resumen y recomendaciones |
| Propuesta de reparacion | Expediente | `expedientes.propuesta_reparacion` | `nuevo_expediente.html`, `editar_expediente.html` | Si | Mezcla reparacion y recomendaciones |
| Visita | Inspeccion | `visitas` | `nueva_visita.html` | Si | Fecha, tecnico, ambito y observaciones |
| Observaciones de visita | Inspeccion | `visitas.observaciones_visita` | `nueva_visita.html` | Si | Puede alimentar metodologia, pero es texto libre |
| Estancias | Inspeccion | `estancias` | `nueva_visita.html` | Si, en fichas/recorrido de patologias | Puede alimentar inventario resumido |
| Acabados y ventilacion de estancias | Inspeccion | `estancias.ventilacion`, `acabado_*` | `nueva_visita.html` | Parcial | En `019-26` esta bastante informado |
| Observaciones tecnicas de estancia | Inspeccion | `estancias.observaciones` | `nueva_visita.html` | Parcial | En `019-26` 5 de 14 estancias tienen observaciones |
| Patologias interiores | Inspeccion | `registros_patologias` | `editar_registro.html` | Si | Base fuerte para inventario y anexos |
| Rol causa/efecto | Patologias | `registros_patologias.rol_patologia_observado` | `editar_registro.html` | Si, si esta informado | En `019-26` no esta informado |
| Patologias exteriores | Inspeccion | `registros_patologias_exteriores` | Flujo de visita/patologias exteriores | Si | Base para inventario exterior |
| Fotografias | Visita, estancia, patologia | `visita_fotos`, `estancia_fotos`, `registro_patologia_fotos`, `registro_patologia_exterior_fotos` | Flujos de visita y patologias | Si | Base para anexo fotografico |
| Mapas y cuadrantes | Inspeccion | `mapas_patologia`, `cuadrantes_mapa_patologia` | Flujo de mapas | Si, si existen | En `019-26` no existen |
| Costes de biblioteca | Costes | `costes_bases`, `costes_conceptos`, `costes_descompuestos` | `templates/costes/` | Solo si se vinculan o usan en anexo | Biblioteca operativa; 7 conceptos validados |
| Capturas OCR | Costes | `costes_capturas`, `costes_fuentes` | `templates/costes/captura_*` | No como cuerpo V1 | Trazabilidad tecnica interna |
| BC3 | Costes | `costes_fuentes`, `costes_conceptos`, `costes_descompuestos` | `templates/costes/bc3_importar.html` | No como justificacion completa V1 | En `019-26` no hay fuente BC3 registrada |
| Costes vinculados a patologias | Costes/patologias | `patologia_costes` | `editar_registro.html` | Si, como fallback de anexo economico | En `019-26` no hay vinculos |
| Actuaciones de reparacion | Costes/expediente | `actuaciones_reparacion`, `actuacion_partidas` | `actuaciones_reparacion.html` | Si, en anexo economico opcional | En `019-26` hay 2 actuaciones y 2 partidas |
| Informe HTML/PDF/DOCX | Informes | Contexto `build_informe_context()` | Rutas de informe | Si | V1 no separa todos los capitulos V2 |

## FASE B - Mapeo contra INFORME_SCHEMA_V2

Los porcentajes son estimaciones operativas:

- Cobertura sistema: cuanto puede construir hoy Sistema Pericial con datos existentes.
- Cobertura `019-26`: cuanto puede construirse hoy para el caso piloto concreto sin rellenar nada mas.

### 1. Portada

- Datos reutilizables: expediente, inmueble, destinatario, tipo de informe, fecha/contexto de generacion.
- Datos parcialmente reutilizables: encargo judicial si aplica.
- Datos inexistentes: ninguno critico.
- Cobertura sistema: 95%.
- Cobertura `019-26`: 90%.

### 2. Indice

- Datos reutilizables: estructura del template actual e ids de seccion.
- Datos parcialmente reutilizables: numeracion variable con anexos.
- Datos inexistentes: indice V2 exacto todavia no implementado.
- Cobertura sistema: 90%.
- Cobertura `019-26`: 90%.

### 3. Resumen ejecutivo

- Datos reutilizables: `descripcion_dano`, `causa_probable`, `urgencia_gravedad`, total PEM de actuaciones, numero de estancias/patologias/fotos.
- Datos parcialmente reutilizables: conclusion resumida puede inferirse de causa, pruebas, propuesta y urgencia, pero no existe como campo.
- Datos inexistentes: resumen ejecutivo redactado, alcance ejecutivo, danos principales seleccionados y conclusion ejecutiva.
- Cobertura sistema: 65%.
- Cobertura `019-26`: 60%.

### 4. Antecedentes y objeto

- Datos reutilizables: expediente, destinatario, tipo de informe, descripcion del dano, datos judiciales si existen.
- Datos parcialmente reutilizables: `objeto_pericia` y `alcance_limitaciones` existen, pero dependen de estar informados.
- Datos inexistentes: estructura separada de encargo recibido, finalidad y alcance solicitado.
- Cobertura sistema: 75%.
- Cobertura `019-26`: 55%, porque `objeto_pericia` esta vacio.

### 5. Metodologia de inspeccion

- Datos reutilizables: visitas, fecha, tecnico, ambito de visita, observaciones de visita, fotografias.
- Datos parcialmente reutilizables: `metodologia_pericial` existe como campo de expediente.
- Datos inexistentes: documentacion analizada, medios utilizados, pruebas realizadas/no realizadas como lista estructurada.
- Cobertura sistema: 65%.
- Cobertura `019-26`: 45%, porque `metodologia_pericial` esta vacio.

### 6. Limitaciones

- Datos reutilizables: `alcance_limitaciones` existe; observaciones de estancias y patologias contienen indicios de baja visibilidad, elementos ocultos o comprobaciones pendientes.
- Datos parcialmente reutilizables: `evolucion_preexistencia` y `urgencia_gravedad` pueden alimentar incertidumbres y riesgos.
- Datos inexistentes: zonas inaccesibles, elementos ocultos, ausencia de catas, ausencia de ensayos e incertidumbres como campos separados.
- Cobertura sistema: 55%.
- Cobertura `019-26`: 35%, porque el campo especifico esta vacio y las limitaciones estan dispersas.

### 7. Analisis causal

- Datos reutilizables: `causa_probable`, `pruebas_indicios`, patologias, fotografias, observaciones.
- Datos parcialmente reutilizables: roles causa/efecto existen en patologias interiores.
- Datos inexistentes: recorrido causal estructurado y vinculacion causa-efecto por grupo de dano.
- Cobertura sistema: 75%.
- Cobertura `019-26`: 65%, porque la causa y pruebas estan informadas pero los roles causa/efecto no.

### 8. Inventario resumido de danos

- Datos reutilizables: patologias interiores/exteriores, estancias, elementos, localizaciones, observaciones, fotografias.
- Datos parcialmente reutilizables: agrupacion por elemento/patologia puede generarse, pero no hay campo de grupo pericial.
- Datos inexistentes: resumen curado por familia de dano, severidad sintetica y seleccion de evidencias clave.
- Cobertura sistema: 85%.
- Cobertura `019-26`: 80%, porque hay 23 patologias y localizaciones completas, aunque falta agrupacion editorial.

### 9. Actuaciones ejecutadas

- Datos reutilizables: observaciones de estancias donde se menciona sustitucion o intervencion observada; actuaciones de reparacion existentes si se usan como proxy.
- Datos parcialmente reutilizables: `actuaciones_reparacion` documenta actuaciones economicas, pero no distingue ejecutada/propuesta/observada.
- Datos inexistentes: entidad o campo formal de actuacion ejecutada, fecha, estado, evidencia, adecuacion tecnica y verificacion.
- Cobertura sistema: 35%.
- Cobertura `019-26`: 30%.

### 10. Propuesta de reparacion

- Datos reutilizables: `propuesta_reparacion`, patologias y actuaciones de reparacion.
- Datos parcialmente reutilizables: algunas recomendaciones y comprobaciones futuras estan mezcladas en el texto.
- Datos inexistentes: reparaciones separadas por actuacion, dano vinculado y criterio de medicion.
- Cobertura sistema: 80%.
- Cobertura `019-26`: 75%.

### 11. Valoracion economica

- Datos reutilizables: actuaciones de reparacion, partidas snapshot, cantidad, unidad, precio unitario, importe, total PEM, biblioteca de costes.
- Datos parcialmente reutilizables: capturas OCR y descompuestos existen en biblioteca, pero no se exportan como justificacion completa.
- Datos inexistentes: trazabilidad explicita dano -> actuacion -> partida -> coste y justificacion BC3 asociada al expediente.
- Cobertura sistema: 80%.
- Cobertura `019-26`: 70%, porque tiene 2 actuaciones y PEM, pero no BC3 ni `patologia_costes`.

### 12. Recomendaciones tecnicas

- Datos reutilizables: `urgencia_gravedad`, `evolucion_preexistencia`, observaciones de patologias y propuesta de reparacion.
- Datos parcialmente reutilizables: recomendaciones aparecen mezcladas con reparacion o incertidumbre.
- Datos inexistentes: recomendaciones como bloque independiente con tipo, justificacion y seguimiento.
- Cobertura sistema: 50%.
- Cobertura `019-26`: 45%.

### 13. Conclusiones tecnicas

- Datos reutilizables: descripcion del dano, causa, pruebas, propuesta, urgencia, patologias y evidencia.
- Datos parcialmente reutilizables: el informe actual ya genera conclusiones, pero no con dependencias V2 explicitas.
- Datos inexistentes: sintesis tecnica versionada por schema y control de incertidumbre.
- Cobertura sistema: 70%.
- Cobertura `019-26`: 65%.

### 14. Conclusiones periciales

- Datos reutilizables: conclusiones actuales, causalidad, alcance, limitaciones, valoracion.
- Datos parcialmente reutilizables: puede redactarse con datos existentes, pero falta separar certeza tecnica, probabilidad e incertidumbre.
- Datos inexistentes: conclusion pericial V2 estructurada y defendible por nivel de seguridad.
- Cobertura sistema: 65%.
- Cobertura `019-26`: 60%.

### 15. Anexos

- Datos reutilizables: fotos, fichas de patologias, valoracion economica, costes y descompuestos.
- Datos parcialmente reutilizables: documentacion aportada y justificacion BC3 no estan formalizadas como anexos V2.
- Datos inexistentes: anexo V de documentacion aportada; anexo IV completo de justificacion BC3 por expediente cuando no hay fuentes.
- Cobertura sistema: 75%.
- Cobertura `019-26`: 65%.

## Matriz resumida de cobertura

| Capitulo V2 | Sistema hoy | Expediente 019-26 | Lectura |
|---|---:|---:|---|
| Portada | 95% | 90% | Casi completo |
| Indice | 90% | 90% | Reorganizacion |
| Resumen ejecutivo | 65% | 60% | Componible, no almacenado |
| Antecedentes y objeto | 75% | 55% | Campo clave vacio |
| Metodologia de inspeccion | 65% | 45% | Visita si, metodologia formal no |
| Limitaciones | 55% | 35% | Existe campo, falta contenido |
| Analisis causal | 75% | 65% | Texto fuerte, roles vacios |
| Inventario resumido de danos | 85% | 80% | Alto potencial con agrupacion |
| Actuaciones ejecutadas | 35% | 30% | Mayor hueco estructural |
| Propuesta de reparacion | 80% | 75% | Requiere separar recomendaciones |
| Valoracion economica | 80% | 70% | Actuaciones cubren PEM, falta traza |
| Recomendaciones tecnicas | 50% | 45% | Disperso en textos |
| Conclusiones tecnicas | 70% | 65% | Requiere sintesis V2 |
| Conclusiones periciales | 65% | 60% | Requiere sintesis V2 |
| Anexos | 75% | 65% | Fotos y fichas si; BC3/docs no |

Promedio estimado:

- Cobertura sistema hoy: 70%.
- Cobertura real `019-26`: 62%.

## FASE C - APROVECHAMIENTO DE DATOS EXISTENTES

### Capitulos que pueden implementarse inmediatamente sin tocar base de datos

- Portada.
- Indice.
- Antecedentes y objeto, con datos existentes y huecos visibles.
- Metodologia de inspeccion basica desde visitas.
- Analisis causal basico desde causa probable y pruebas/indicios.
- Inventario resumido de danos desde patologias y estancias.
- Propuesta de reparacion desde `propuesta_reparacion`.
- Valoracion economica desde actuaciones de reparacion.
- Anexos fotograficos y fichas de patologias.

### Capitulos que requieren unicamente reorganizacion sin nuevos campos

- Resumen ejecutivo: puede componerse desde descripcion, causa, urgencia, inventario y PEM.
- Inventario resumido de danos: puede agruparse por estancia, elemento y patologia.
- Propuesta de reparacion: puede separarse editorialmente del texto actual.
- Recomendaciones tecnicas: pueden extraerse de `urgencia_gravedad`, `evolucion_preexistencia`, observaciones y propuesta.
- Conclusiones tecnicas/periciales: pueden reformularse con datos existentes, manteniendo V1 como fallback.
- Anexo economico detallado: puede usar actuaciones y partidas snapshot.

### Capitulos que requieren nuevos campos

Sin disenar entidades todavia, los huecos de campo mas claros son:

- Resumen ejecutivo redactado o validado.
- Metodologia: documentacion analizada, medios utilizados, pruebas realizadas y pruebas no realizadas.
- Limitaciones: zonas inaccesibles, elementos ocultos, ausencia de catas, ausencia de ensayos e incertidumbres.
- Analisis causal: recorrido de danos y relacion causa-efecto estructurada.
- Inventario resumido: grupo de dano, severidad sintetica y evidencias clave.
- Actuaciones ejecutadas: estado, fecha, evidencia y adecuacion tecnica.
- Recomendaciones: tipo, justificacion y seguimiento.
- Documentacion aportada: tipo, origen, fecha y descripcion.

### Capitulos que requieren nuevas entidades

No se disenan entidades en esta fase, pero si se identifican necesidades que probablemente no encajan bien como texto plano:

- Documentacion aportada por propiedad o terceros, porque necesita multiples documentos y trazabilidad.
- Actuaciones ejecutadas/verificadas, porque pueden ser varias, con fecha, estado, evidencia y relacion con presupuesto.
- Trazabilidad dano -> reparacion -> coste, porque puede cruzar grupos de danos, actuaciones y partidas.
- Limitaciones e incertidumbres, si se quiere seguimiento granular y no un unico bloque textual.

## FASE D - Priorizacion

### Impacto alto / esfuerzo bajo

- Generar resumen ejecutivo preliminar con datos existentes.
- Reordenar el informe V2 sin nuevos campos en modo preliminar.
- Crear inventario resumido de danos agrupando patologias.
- Separar recomendaciones implicitas de la propuesta de reparacion.
- Mostrar metodologia basica desde visitas y evidencia fotografica.

### Impacto alto / esfuerzo medio

- Formalizar limitaciones usando campo existente y extraccion de observaciones dispersas.
- Crear valoracion economica V2 basada en actuaciones de reparacion.
- Crear anexo fotografico y fichas como anexos diferenciados.
- Reforzar conclusiones tecnicas/periciales con estructura V2.

### Impacto alto / esfuerzo alto

- Trazabilidad completa dano -> actuacion -> partida -> coste.
- Registro estructurado de documentacion aportada.
- Actuaciones ejecutadas/verificadas con estado, evidencia y adecuacion tecnica.
- Justificacion de precios/descompuestos BC3 vinculada al expediente.
- Matriz de incertidumbres, pruebas no realizadas y nivel de confianza.

## Conclusion obligatoria

Si manana hubiera que generar una version preliminar del INFORME V2 para el expediente `019-26` sin modificar la base de datos, podria construirse aproximadamente el 62% del informe usando informacion ya existente.

Justificacion:

- El expediente tiene una base probatoria fuerte: danos descritos, causa probable, pruebas/indicios, patologias, estancias y 107 fotografias.
- El sistema ya tiene campos para objeto, metodologia y limitaciones, pero en `019-26` esos campos estan vacios.
- La valoracion economica existe por actuaciones y partidas snapshot, con PEM de 8.616,00 EUR, pero falta trazabilidad dano -> actuacion -> coste y no hay BC3 asociado al expediente.
- El inventario resumido de danos puede construirse agrupando patologias, pero no existe como bloque curado.
- Las recomendaciones tecnicas existen solo de forma implicita y mezclada.
- Actuaciones ejecutadas es el hueco mas debil: hay indicios y actuaciones economicas, pero no un registro formal de lo ejecutado, verificado o pendiente.

La conclusion operativa es que V2 no parte de cero. La mayoria de la prueba existe. Lo que falta realmente es estructura, trazabilidad y campos de defensa pericial para metodologia, limitaciones, actuaciones ejecutadas y documentacion aportada.

## Tres huecos funcionales mas importantes

1. Limitaciones e incertidumbres formalizadas: existen indicios, pero no una estructura rellena en `019-26`.
2. Trazabilidad dano -> reparacion -> coste: existen patologias y actuaciones, pero no el puente pericial completo.
3. Actuaciones ejecutadas/verificadas: el caso necesita distinguir trabajos observados, trabajos propuestos y partidas economicas.
