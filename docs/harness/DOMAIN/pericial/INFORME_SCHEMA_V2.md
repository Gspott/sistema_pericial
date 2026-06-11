# INFORME_SCHEMA_V2

## Objetivo

Definir la estructura oficial candidata para el futuro `INFORME_SCHEMA_V2` del modulo pericial de Sistema Pericial.

Este documento no implementa cambios. Es una definicion documental y de analisis para orientar fases posteriores sin modificar codigo, base de datos, rutas, plantillas PDF, migraciones ni funcionalidades.

El caso piloto usado para validar la estructura es el expediente `019-26`, actualmente el caso real mas avanzado inspeccionado para danos por filtraciones durante una obra de reparacion de cubierta.

## Principios de diseno

- El informe debe ser defendible ante abogado, aseguradora, perito contrario y juzgado.
- La estructura nace del expediente `019-26`, no de un modelo teorico.
- Las patologias justifican los danos; las actuaciones de reparacion justifican la valoracion economica.
- La lectura principal debe permitir entender el caso sin recorrer decenas de fichas.
- La prueba detallada debe conservarse en anexos y fichas, no bloquear la comprension del cuerpo principal.
- La propuesta de reparacion no debe mezclarse con recomendaciones preventivas o comprobaciones futuras.
- Las limitaciones deben ser explicitas y proteger tecnicamente el alcance real de las conclusiones.
- La valoracion economica debe trazar dano, reparacion y coste, manteniendo snapshots de precios cuando existan.
- V2 debe poder convivir con informes actuales: capitulos nuevos deben ser opcionales o condicionales cuando no haya datos.

## Fuentes inspeccionadas

- Documentacion de informes: `docs/informes.md`.
- Playbook de informes: `docs/harness/PLAYBOOKS/informes.md`.
- Revision probatoria: `docs/revision_probatoria.md`.
- Modelos de datos: `docs/modelos_datos.md`.
- Patron de contexto de informe: `docs/harness/PATTERNS/build_informe_context_extension.md`.
- Generacion real de informes: `app/services/informe.py`.
- Template PDF/HTML actual: `templates/informes/imprimir.html`.
- Workbench de actuaciones: `templates/actuaciones_reparacion.html`.
- Vista de presupuesto por patologias: `templates/presupuesto_reparacion.html`.
- Modulo de costes y BC3/OCR: `app/routers/costes.py`, `app/services/costes_parser.py`, `app/services/bc3_parser.py`.
- Expediente `019-26` consultado en SQLite en modo solo lectura.

## FASE A - Estado actual del sistema

### Informacion que recoge actualmente

El sistema ya recoge informacion suficiente para construir una base pericial amplia:

- Datos identificativos del expediente: numero, tipo de informe, destinatario, inmueble, direccion administrativa, descripcion del dano, causa probable, pruebas o indicios y propuesta de reparacion.
- Visitas: fecha, tecnico, ambito de visita y observaciones.
- Estancias: nombre, tipo de estancia, planta y observaciones de inspeccion.
- Patologias interiores: estancia, elemento, patologia, localizacion, detalle, observaciones, rol observado y fotografias.
- Patologias exteriores: zona exterior, elemento, localizacion, patologia, observaciones y fotografias.
- Mapas y cuadrantes de patologias cuando existen.
- Evidencia fotografica de visita, estancias y patologias.
- Biblioteca de costes tipo BC3/FIEBDC: bases, conceptos, descompuestos, fuentes, capturas OCR e importaciones BC3.
- Costes vinculados a patologias mediante `patologia_costes`.
- Actuaciones de reparacion por expediente mediante `actuaciones_reparacion` y `actuacion_partidas`.
- Anexo economico opcional si se solicita explicitamente la generacion con anexo.
- Campos y flujos de valoracion inmobiliaria como referencia de UX de escritorio, aunque no forman parte del informe de danos.

### Informacion que exporta actualmente el informe PDF

El informe de patologias actual exporta, de forma resumida:

- Portada e indice.
- Objeto del informe.
- Descripcion del inmueble.
- Datos especificos de patologias.
- Encargo judicial, si aplica.
- Inspeccion y visita.
- Patologias interiores.
- Patologias exteriores.
- Mapas de localizacion, si existen.
- Propuesta de reparacion.
- Anexo economico de reparacion si el flag de generacion esta activo y existen costes.
- Conclusiones tecnicas.
- Conclusiones periciales.

El punto de integracion real es `build_informe_context()` en `app/services/informe.py`, compartido por HTML/PDF y DOCX. El template principal es `templates/informes/imprimir.html`.

### Informacion existente pero no exportada o no estructurada

- Las actuaciones de reparacion existen como entidad operativa, pero no son aun un capitulo principal del cuerpo del informe V1.
- La biblioteca de costes conserva fuentes, capturas, OCR, BC3 y descompuestos, pero el informe solo usa el anexo economico opcional, no una justificacion completa de precios en cuerpo principal.
- La revision probatoria detecta faltas de climatologia, estancias, fotos, patologias e informe pendiente, pero no se convierte en metodologia ni limitaciones del informe.
- Las observaciones de estancias contienen datos tecnicos relevantes, pero no se sintetizan como inventario de danos.
- La propuesta de reparacion puede incluir reparacion, comprobaciones futuras y recomendaciones, todo en el mismo bloque.
- Las incertidumbres tecnicas aparecen como texto implicito, no como capitulo formal.
- La trazabilidad dano -> actuacion de reparacion -> coste existe parcialmente por actuaciones y partidas, pero no como narrativa pericial cerrada.

### Informacion que falta para un informe de reclamacion de danos

- Resumen ejecutivo legible en menos de un minuto.
- Metodologia formal de inspeccion: visitas, documentacion, medios, pruebas realizadas y pruebas no realizadas.
- Limitaciones formalizadas: zonas inaccesibles, elementos ocultos, ausencia de catas, ausencia de ensayos e incertidumbres.
- Inventario resumido de danos agrupado por zonas o familias de dano.
- Actuaciones ejecutadas u observadas, separadas de la propuesta de reparacion.
- Verificacion de partidas presupuestadas o ejecutadas frente a danos observados.
- Recomendaciones tecnicas independientes de la reparacion estricta.
- Justificacion estructurada de incertidumbres y riesgos futuros.
- Trazabilidad explicita entre danos, reparaciones necesarias y coste PEM.
- Registro de documentacion aportada por la propiedad o terceros.

## FASE B - Analisis del expediente 019-26

### Datos reales observados en la base inspeccionada

En la base local inspeccionada constan para `019-26`:

- Tipo de informe: patologias.
- Ambito: interior y exterior.
- Inmueble: vivienda plurifamiliar en Ayora, Valencia.
- Una visita registrada el 2026-06-03, con ambito de edificio completo.
- 14 estancias documentadas.
- 21 patologias interiores.
- 2 patologias exteriores.
- 16 fotografias de estancias, 84 fotografias de patologias interiores, 4 fotografias de patologias exteriores y 3 fotografias de visita.
- 2 actuaciones de reparacion con partidas economicas.
- Total PEM actualmente asociado a actuaciones: 8.616,00 EUR.
- No constan costes vinculados mediante `patologia_costes` para este expediente en la base inspeccionada.

Estos datos confirman que el expediente tiene mucha prueba detallada y una valoracion economica incipiente, pero necesita una estructura de lectura y defensa.

### Informacion ya presente

#### Danos observados

El expediente documenta danos por agua, humedades, moho, deterioro de revestimientos interiores, eflorescencias, danos en carpinterias, desprendimientos, afecciones en falsos techos, pavimentos y fachada.

Tambien describe impactos materiales relevantes: caida o sustitucion de falsos techos, afeccion a paredes y techos, danos en mobiliario y colchones, rotura de elementos de huecos y danos exteriores relacionados con la obra de cubierta.

#### Analisis causal

La causa probable ya esta formulada: entrada de agua de lluvia al interior durante una sustitucion de cubierta.

El expediente contiene indicios coherentes con esa causa: escorrentias superficiales, manchas, grietas, eflorescencias, zonas expuestas directamente a lluvia y elementos con perdida de resistencia.

#### Patologias causa y efecto

El sistema tiene campos de rol de patologia. En `019-26`, los registros inspeccionados no tienen rol observado informado, por lo que la separacion causa/efecto existe como capacidad del sistema pero no esta explotada en el caso piloto.

Este hueco es importante: para defensa ante terceros, V2 debe obligar a distinguir entre hechos causales, danos consecuencia e incertidumbres.

#### Fotografias

La evidencia fotografica es abundante: 107 fotografias asociadas entre visita, estancias y patologias.

La necesidad no es recoger mas fotos, sino organizarlas mejor: cuerpo principal con seleccion probatoria y anexo fotografico completo.

#### Propuesta de reparacion

Existe propuesta de reparacion con actuaciones como sustitucion de falso techo de cañizo por placa de yeso, saneado de paramentos, guarnecido y enlucido, retirada de papel adherido y comprobaciones durante la reparacion.

Parte del texto mezcla reparacion necesaria con inspecciones futuras, por ejemplo revisar elementos estructurales de madera o posible aparicion de insectos.

#### Valoracion economica

El expediente ya contiene actuaciones de reparacion separadas:

- Demolicion de falso techo de cañizo: 200 m2 x 6,51 EUR/m2 = 1.302,00 EUR.
- Colocacion de falso techo de carton-yeso: 200 m2 x 36,57 EUR/m2 = 7.314,00 EUR.

Total PEM actual: 8.616,00 EUR.

Esto demuestra que la valoracion economica debe estructurarse por actuaciones de reparacion y no necesariamente por cada patologia repetida por estancia.

### Informacion parcialmente presente

- Limitaciones de inspeccion: aparecen de forma implicita en observaciones de estancias con baja visibilidad, elementos ocultos, necesidad de inspeccionar madera durante la reparacion y falta de certeza sobre insectos.
- Incertidumbres tecnicas: existen sobre estructura de madera, humedad retenida, alcance oculto de danos y posible evolucion biologica, pero no estan formalizadas.
- Comprobaciones realizadas: hay inspeccion visual, fotografias y observaciones; no hay capitulo que distinga lo comprobado de lo no comprobado.
- Riesgos futuros: se intuyen por humedad, moho, insectos o madera, pero no forman un apartado independiente.
- Recomendaciones implicitas: aparecen mezcladas con la propuesta de reparacion.

### Informacion ausente

- Resumen ejecutivo.
- Actuaciones ejecutadas u observadas como capitulo propio.
- Verificacion de partidas presupuestadas o ejecutadas.
- Recomendaciones tecnicas independientes.
- Trazabilidad dano -> reparacion -> coste.
- Limitaciones formalizadas.
- Justificacion estructurada de incertidumbres.
- Registro claro de documentacion aportada por propiedad o terceros.

## Preguntas obligatorias

### 1. Entrega actual a abogado, aseguradora, perito contrario o juzgado

#### Que partes sobran o pesan demasiado

- Fichas de patologias en bloque antes de ofrecer una vision ejecutiva del caso.
- Repeticion de danos similares por estancia sin una agrupacion previa.
- Mezcla de reparaciones necesarias, recomendaciones futuras e inspecciones pendientes dentro de la propuesta de reparacion.
- Detalle fotografico sin jerarquia suficiente entre prueba principal y anexo.
- Campos sin contenido o datos secundarios si aparecen en cuerpo principal.

#### Que partes faltan

- Resumen ejecutivo.
- Capitulo de limitaciones.
- Metodologia de inspeccion separada de la mera visita.
- Cadena causal completa y ordenada.
- Inventario resumido de danos.
- Actuaciones ejecutadas u observadas.
- Separacion entre propuesta de reparacion y recomendaciones.
- Trazabilidad entre danos, actuaciones, mediciones y PEM.
- Justificacion de precios y descompuestos cuando el coste vaya a defenderse ante tercero.

#### Que partes deberian reordenarse

El orden defendible seria:

1. Portada e indice.
2. Resumen ejecutivo.
3. Antecedentes y objeto.
4. Metodologia.
5. Limitaciones.
6. Analisis causal.
7. Inventario resumido de danos.
8. Actuaciones ejecutadas u observadas.
9. Propuesta de reparacion.
10. Valoracion economica.
11. Recomendaciones tecnicas.
12. Conclusiones tecnicas.
13. Conclusiones periciales.
14. Anexos.

### 2. Capitulos V2 que nacen directamente de 019-26

- Resumen ejecutivo: necesario por el volumen de estancias, patologias y fotografias.
- Limitaciones: necesario por elementos ocultos, ausencia de catas y dudas sobre madera/insectos.
- Analisis causal: necesario para conectar obra de cubierta, entrada de lluvia y danos interiores/exteriores.
- Inventario resumido de danos: necesario para no obligar al lector a recorrer todas las fichas.
- Actuaciones ejecutadas: necesario porque en el caso hay trabajos o sustituciones observadas y partidas que deben verificarse.
- Propuesta de reparacion separada: necesario porque hoy mezcla reparacion e inspecciones recomendadas.
- Valoracion economica por actuaciones: necesario porque los danos son repetidos y no hay relacion 1:1 entre patologia y partida.
- Recomendaciones tecnicas: necesario para separar prevencion, comprobacion futura y seguimiento.
- Anexos diferenciados: necesario por volumen fotografico, fichas de patologias, coste y justificacion de precios.

### 3. Nuevos campos necesarios para completar 019-26

Campos documentales candidatos para futuras fases:

- `resumen_ejecutivo.origen_danos`
- `resumen_ejecutivo.alcance`
- `resumen_ejecutivo.danos_principales`
- `resumen_ejecutivo.coste_estimado`
- `resumen_ejecutivo.conclusion_resumida`
- `metodologia.documentacion_analizada`
- `metodologia.medios_utilizados`
- `metodologia.pruebas_realizadas`
- `metodologia.pruebas_no_realizadas`
- `limitaciones.zonas_inaccesibles`
- `limitaciones.elementos_ocultos`
- `limitaciones.ausencia_catas`
- `limitaciones.ausencia_ensayos`
- `limitaciones.incertidumbres_tecnicas`
- `analisis_causal.origen`
- `analisis_causal.recorrido_danos`
- `analisis_causal.relacion_causa_efecto`
- `danos_resumen.grupo`
- `danos_resumen.zonas_afectadas`
- `danos_resumen.evidencias_clave`
- `actuaciones_ejecutadas.descripcion`
- `actuaciones_ejecutadas.estado`
- `actuaciones_ejecutadas.evidencia`
- `actuaciones_ejecutadas.adecuacion_tecnica`
- `propuesta_reparacion.actuacion`
- `propuesta_reparacion.dano_vinculado`
- `valoracion.trazabilidad_dano`
- `valoracion.trazabilidad_actuacion`
- `valoracion.criterio_medicion`
- `recomendaciones.tipo`
- `recomendaciones.justificacion`
- `documentacion_aportada.tipo`
- `documentacion_aportada.fecha`
- `documentacion_aportada.origen`

Estos campos no implican migracion en esta fase.

### 4. Mejoras compatibles con informes actuales

- Mantener V1 como salida por defecto.
- Introducir V2 como contrato documental antes de tocar `build_informe_context()`.
- Hacer los nuevos capitulos condicionales cuando no haya datos.
- Reutilizar actuaciones de reparacion como fuente principal economica cuando existan.
- Mantener fallback a `patologia_costes` para expedientes anteriores.
- Separar anexos sin eliminar fichas actuales.
- Preservar el flag explicito de anexo economico.
- Evitar cambiar rutas y plantillas hasta una fase de implementacion especifica.
- Anadir datos nuevos como extensiones del contexto compartido, no como logica aislada en templates.

## FASE C - Estructura completa INFORME_SCHEMA_V2

### 1. Portada

- Finalidad: identificar expediente, inmueble, emisor, destinatario, fecha y tipo de informe.
- Origen de informacion: `expedientes` y contexto de informe actual.
- Obligatoriedad: obligatoria.
- Para `019-26`: debe presentar el caso sin exponer aun detalle probatorio.

### 2. Indice

- Finalidad: facilitar navegacion por cuerpo y anexos.
- Origen de informacion: estructura generada del informe.
- Obligatoriedad: obligatoria.
- Para `019-26`: imprescindible por volumen de danos, fotos y anexos.

### 3. Resumen ejecutivo

- Finalidad: permitir comprender el caso en menos de un minuto.
- Contenido esperado: origen de los danos, alcance, danos principales, coste estimado y conclusion resumida.
- Origen de informacion: expediente, analisis causal, inventario de danos, actuaciones y valoracion economica.
- Obligatoriedad: obligatoria para informes de reclamacion de danos.
- Para `019-26`: debe explicar que los danos se atribuyen a entrada de agua de lluvia durante reparacion de cubierta, con afeccion interior/exterior y PEM actualmente estimado en 8.616,00 EUR para actuaciones registradas.

### 4. Antecedentes y objeto

- Finalidad: explicar encargo recibido, finalidad del informe y alcance solicitado.
- Origen de informacion: `expedientes.objeto_pericia`, `descripcion_dano`, `destinatario`, tipo de informe y documentacion aportada.
- Obligatoriedad: obligatoria.
- Hueco actual: `019-26` tiene descripcion de dano, pero el objeto pericial esta poco formalizado.

### 5. Metodologia de inspeccion

- Finalidad: documentar visitas realizadas, documentacion analizada, medios utilizados y pruebas realizadas.
- Origen de informacion: visitas, fotos, revision probatoria, documentos aportados y futuros campos de metodologia.
- Obligatoriedad: obligatoria.
- Para `019-26`: debe registrar visita del 2026-06-03, ambito de edificio completo, inspeccion visual y evidencia fotografica.

### 6. Limitaciones

- Finalidad: acotar tecnicamente conclusiones y proteger al perito.
- Contenido esperado: zonas inaccesibles, elementos ocultos, ausencia de catas, ausencia de ensayos, incertidumbres tecnicas y alcance real de conclusiones.
- Origen de informacion: observaciones de visita/estancias/patologias y futuros campos especificos de limitaciones.
- Obligatoriedad: obligatoria, aunque pueda indicar que no se aprecian limitaciones relevantes.
- Para `019-26`: debe recoger visibilidad reducida en determinadas zonas, elementos ocultos de madera, ausencia de catas/ensayos y necesidad de verificar danos durante reparacion.

### 7. Analisis causal

- Finalidad: explicar origen, recorrido de los danos, relacion causa-efecto y coherencia tecnica observada.
- Origen de informacion: causa probable, pruebas/indicios, patologias, fotografias y observaciones.
- Obligatoriedad: obligatoria.
- Para `019-26`: es la base argumental del informe: reparacion de cubierta, entrada de lluvia, recorrido por edificio y danos por humedad.

### 8. Inventario resumido de danos

- Finalidad: presentar danos de forma legible antes de fichas detalladas.
- Origen de informacion: patologias interiores/exteriores, estancias, fotos y grupos de dano futuros.
- Obligatoriedad: obligatoria cuando haya mas de una patologia o estancia afectada.
- Para `019-26`: debe agrupar danos por familias como falsos techos, paramentos, pavimentos, carpinterias, fachada y elementos expuestos a lluvia.

### 9. Actuaciones ejecutadas

- Finalidad: verificar partidas presupuestadas, comprobar reparaciones ejecutadas, valorar adecuacion tecnica y documentar actuaciones observadas.
- Origen de informacion: futuras actuaciones ejecutadas, observaciones de estancia, documentacion aportada, fotografias y actuaciones de reparacion existentes cuando representen trabajos observados.
- Obligatoriedad: condicional; obligatorio si existen reparaciones ya ejecutadas, presupuestadas o alegadas.
- Para `019-26`: nace directamente del caso piloto porque ya se observa sustitucion o intervencion en falsos techos y hay necesidad de separar lo ejecutado de lo pendiente.

### 10. Propuesta de reparacion

- Finalidad: recoger exclusivamente actuaciones necesarias para reparar los danos.
- Origen de informacion: `propuesta_reparacion`, patologias, inventario de danos y actuaciones de reparacion.
- Obligatoriedad: obligatoria cuando el informe incluya reparacion o cuantificacion.
- Regla V2: no mezclar recomendaciones preventivas, inspecciones adicionales ni seguimiento futuro.
- Para `019-26`: debe contener saneado, picado, reposicion de yesos, falsos techos y pintura, dejando inspecciones de madera/insectos para recomendaciones.

### 11. Valoracion economica

- Finalidad: cuantificar PEM de reparacion con partidas, mediciones, importes, subtotales y total.
- Origen de informacion: actuaciones de reparacion y `actuacion_partidas`; fallback a `patologia_costes`; biblioteca de costes; BC3; capturas trazables.
- Obligatoriedad: condicional; obligatoria si se reclama o defiende importe.
- Para `019-26`: debe estructurarse por actuaciones, no por repeticion de patologias; total actual registrado: 8.616,00 EUR.

### 12. Recomendaciones tecnicas

- Finalidad: recoger inspecciones adicionales, actuaciones preventivas, actuaciones recomendadas y seguimiento futuro.
- Origen de informacion: observaciones tecnicas, limitaciones, incertidumbres y criterio pericial.
- Obligatoriedad: condicional; obligatoria si existen riesgos o incertidumbres relevantes.
- Para `019-26`: debe incluir comprobacion de madera, posible actividad biologica y seguimiento de humedad/moho si procede, sin contaminar la propuesta estricta de reparacion.

### 13. Conclusiones tecnicas

- Finalidad: sintetizar hechos tecnicos y razonamiento.
- Origen de informacion: analisis causal, inventario, limitaciones, propuesta y valoracion.
- Obligatoriedad: obligatoria.
- Para `019-26`: debe cerrar tecnicamente la coherencia entre cubierta, entrada de agua y danos observados.

### 14. Conclusiones periciales

- Finalidad: formular conclusion final defendible ante terceros.
- Origen de informacion: conclusiones tecnicas, alcance del encargo y limitaciones.
- Obligatoriedad: obligatoria.
- Para `019-26`: debe ser breve, clara y resistente a contradiccion, diferenciando certeza, probabilidad tecnica e incertidumbre.

### 15. Anexos

#### Anexo I - Reportaje fotografico

- Finalidad: conservar evidencia visual completa o seleccionada.
- Origen: fotos de visita, estancias y patologias.
- Obligatoriedad: obligatoria si hay fotografias.

#### Anexo II - Fichas detalladas de patologias

- Finalidad: mantener detalle tecnico sin saturar el cuerpo principal.
- Origen: registros de patologias interiores y exteriores.
- Obligatoriedad: obligatoria si hay patologias.

#### Anexo III - Valoracion economica detallada

- Finalidad: presentar mediciones, partidas, subtotales y PEM.
- Origen: actuaciones, partidas snapshot y costes vinculados.
- Obligatoriedad: condicional si hay valoracion.

#### Anexo IV - Justificacion de precios y descompuestos BC3

- Finalidad: soportar precios unitarios, descompuestos y fuentes.
- Origen: biblioteca de costes, descompuestos, BC3, capturas OCR y fuentes.
- Obligatoriedad: condicional si se discuten precios o se necesita defensa economica.

#### Anexo V - Documentacion aportada por la propiedad

- Finalidad: listar documentos, presupuestos, fotografias previas, comunicaciones u otra prueba aportada.
- Origen: futuro registro documental y referencias del expediente.
- Obligatoriedad: condicional si hay documentacion aportada.

## Huecos detectados para implementacion futura

- Falta un modelo estructurado de resumen ejecutivo.
- Falta un modelo estructurado de metodologia y limitaciones.
- Falta clasificar danos por familias o grupos.
- Falta relacionar cada grupo de dano con actuaciones de reparacion.
- Falta distinguir actuaciones ejecutadas de actuaciones propuestas.
- Falta registrar verificacion de partidas presupuestadas o ejecutadas.
- Falta registrar documentacion aportada por terceros.
- Falta representar incertidumbres con nivel de confianza o alcance.
- Falta un modo V2 de anexos que no rompa el informe V1.

## Riesgos de implementacion

- Romper informes actuales si se cambia el orden V1 sin flag o versionado.
- Duplicar logica entre HTML/PDF y DOCX si no se extiende `build_informe_context()`.
- Convertir el informe en demasiado largo si el inventario resumido y los anexos no se separan bien.
- Mezclar recomendaciones con reparacion, debilitando la reclamacion economica.
- Presentar limitaciones de forma defensiva pobre o como ausencia de diligencia.
- Perder trazabilidad economica si se usan precios vivos de biblioteca en vez de snapshots.
- Exponer datos sensibles o documentos reales en pruebas.
- Obligar a rellenar demasiados campos antes de que V2 este maduro.

## Decision de compatibilidad

`INFORME_SCHEMA_V2` debe introducirse como version documental y, en fases posteriores, como capa opcional de contexto. La salida V1 debe seguir funcionando aunque no existan datos V2.

La ruta de implementacion recomendada es:

1. Mantener informe actual como V1.
2. Crear datos V2 como extensiones opcionales.
3. Reutilizar actuaciones de reparacion como fuente principal economica.
4. Usar `patologia_costes` como fallback heredado.
5. Anadir capitulos nuevos solo si tienen datos o si son obligatorios con texto explicito.
6. Separar anexos sin eliminar fichas actuales.

## Conclusion

El expediente `019-26` demuestra que el futuro informe no debe crecer solo acumulando fichas. Debe tener una capa narrativa y probatoria clara:

- que paso;
- que danos produjo;
- como se comprobo;
- que no pudo comprobarse;
- que reparaciones son necesarias;
- que actuaciones ya existen o se alegan;
- cuanto cuesta reparar;
- que recomendaciones quedan fuera de la reparacion estricta.

Por ello, `INFORME_SCHEMA_V2` debe organizar el informe por defensa pericial y no solo por captura de datos.
