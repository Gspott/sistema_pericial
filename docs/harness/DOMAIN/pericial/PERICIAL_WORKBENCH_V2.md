# PERICIAL_WORKBENCH_V2

## Objetivo

Definir el futuro Workbench de escritorio para redaccion y analisis de informes periciales complejos.

Este documento no disena formularios, tablas, base de datos ni modelos. Tampoco implementa funcionalidades. Es una definicion documental de UX para entender como debe trabajar un tecnico cuando ya no esta capturando informacion en visita, sino preparando un informe defendible.

Documentos de referencia:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`.
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`.

Caso piloto principal: expediente `019-26`.

## Problema que resuelve

El sistema actual esta muy orientado a capturar evidencia durante la visita: crear visita, definir estancias, registrar patologias, tomar fotos y completar datos tecnicos. Ese flujo es correcto para campo.

El trabajo de escritorio cambia de naturaleza. El tecnico necesita:

- analizar lo observado;
- agrupar danos repetidos;
- relacionar causa, recorrido y efectos;
- revisar fotografias como evidencia;
- separar reparacion, recomendacion e incertidumbre;
- comprobar partidas economicas;
- redactar conclusiones defendibles;
- preparar una salida legible para abogado, aseguradora, perito contrario o juzgado.

El Workbench V2 debe ser una mesa de redaccion pericial. No debe sustituir los formularios mobile-first existentes ni convertirse en un formulario gigante. Debe reunir contexto, evidencia y escritura en una sola vista de escritorio.

## Perfil de usuario

Tecnico o perito redactando un informe complejo desde ordenador.

Caracteristicas del uso:

- trabajo con pantalla ancha;
- lectura comparada de muchos registros;
- edicion de textos largos;
- revision de fotografias;
- comprobacion economica;
- necesidad de mantener trazabilidad tecnica;
- alternancia constante entre evidencia y redaccion.

No es el usuario en visita con movil. En movil el Workbench debe degradar a una columna o redirigir a los flujos existentes, sin romper la captura.

## Caso piloto 019-26

El expediente `019-26` representa un caso de danos por filtraciones durante reparacion de cubierta.

Datos relevantes inspeccionados:

- 1 visita.
- 14 estancias.
- 21 patologias interiores.
- 2 patologias exteriores.
- 107 fotografias entre visita, estancias y patologias.
- Descripcion de dano, causa probable, pruebas/indicios, evolucion/preexistencia, urgencia/gravedad y propuesta de reparacion informadas.
- Objeto pericial, metodologia pericial y alcance/limitaciones vacios.
- 2 actuaciones de reparacion con partidas economicas.
- PEM por actuaciones: 8.616,00 EUR.
- Sin `patologia_costes` para el expediente.
- Sin roles causa/efecto informados en patologias.

La necesidad principal no es capturar mas registros. Es ordenar y defender lo que ya existe.

## FASE A - Flujo real de trabajo inferido

El flujo real del tecnico para terminar `019-26` no parece lineal. Se infiere a partir de las pantallas, campos y datos existentes:

1. Revisar estado del expediente.
   - Pantalla actual: detalle de expediente.
   - El tecnico ve visitas, estancias, patologias y pendientes probatorios.

2. Revisar danos por estancia.
   - Pantallas actuales: visita, registros de patologias, detalle de expediente.
   - En `019-26`, muchos danos son repetitivos: falsos techos, paramentos, humedades y carpinterias.

3. Revisar fotografias.
   - Origen actual: fotos de visita, estancias y patologias.
   - En `019-26`, 107 fotos obligan a seleccionar evidencia representativa, no solo acumular imagenes.

4. Agrupar danos.
   - Origen actual: patologias y estancias.
   - El sistema tiene 23 patologias registradas, pero el informe necesita familias de dano legibles.

5. Determinar y comprobar la causa.
   - Origen actual: `causa_probable`, `pruebas_indicios`, observaciones y fotos.
   - En `019-26`, la causa esta redactada, pero los roles causa/efecto no estan informados.

6. Identificar limitaciones e incertidumbres.
   - Origen actual: observaciones dispersas, `evolucion_preexistencia`, `urgencia_gravedad`.
   - El campo especifico `alcance_limitaciones` esta vacio.

7. Separar reparacion necesaria de recomendaciones.
   - Origen actual: `propuesta_reparacion`, observaciones y urgencia.
   - En `019-26`, hay reparaciones y comprobaciones futuras mezcladas.

8. Valorar reparaciones por actuaciones.
   - Pantalla actual: actuaciones de reparacion.
   - En `019-26`, la valoracion esta estructurada por 2 actuaciones, no por cada patologia.

9. Revisar costes y trazabilidad economica.
   - Pantallas actuales: actuaciones, biblioteca de costes, anexo economico.
   - Falta una vista que muestre dano, actuacion y partida economica en la misma lectura.

10. Redactar conclusiones tecnicas y periciales.
    - Origen actual: informe generado y textos del expediente.
    - El tecnico necesita escribir mirando evidencia, limitaciones y coste, no en una pantalla aislada.

11. Revisar salida final.
    - Pantalla actual: vista de informe PDF/HTML.
    - El Workbench debe acercar la previsualizacion estructural, pero no sustituir la generacion de informe.

## Casos de uso principales

### Patologias

Agrupar patologias repetidas, revisar observaciones, confirmar elementos afectados y seleccionar evidencia fotografica representativa.

### Reclamaciones

Construir una narrativa defendible: antecedente, causa, dano, prueba, reparacion y valoracion.

### Danos por agua

Relacionar entrada de agua, recorrido probable, manchas, moho, eflorescencias, desprendimientos, carpinterias afectadas y riesgos futuros.

### Informes con valoracion economica

Revisar actuaciones, partidas, mediciones, subtotales y total PEM sin convertir el informe en presupuesto comercial.

### Comprobacion de partidas ejecutadas

Distinguir entre:

- dano observado;
- reparacion necesaria;
- actuacion ya observada o alegada;
- partida economica;
- recomendacion o comprobacion futura.

## Estructura general propuesta

El Workbench V2 deberia usar tres zonas:

- Panel izquierdo: indice de trabajo y estado argumental.
- Panel central: redaccion y organizacion del capitulo activo.
- Panel derecho: evidencia reutilizable y contexto.

Esta estructura se justifica porque el tecnico necesita mantener simultaneamente:

- el mapa del informe;
- el texto que esta construyendo;
- la prueba que respalda ese texto.

El patron se inspira en el workbench de valoracion: vista SSR de escritorio, panel contextual, densidad mayor y degradacion a una columna en movil. La diferencia es que aqui no se comparan testigos, sino que se construye un argumento pericial.

## Panel izquierdo - Indice de trabajo

### Funcion

Orientar al tecnico dentro del informe V2 y mostrar que partes estan fuertes, incompletas o pendientes.

### Contenido recomendado

- Resumen ejecutivo.
- Antecedentes y objeto.
- Metodologia.
- Limitaciones.
- Analisis causal.
- Inventario de danos.
- Actuaciones ejecutadas.
- Propuesta de reparacion.
- Valoracion economica.
- Recomendaciones.
- Conclusiones tecnicas.
- Conclusiones periciales.
- Anexos.

### Senales utiles

- Completo.
- Parcial.
- Vacio.
- Requiere revision.
- Tiene evidencia asociada.
- Tiene coste asociado.

### Justificacion para 019-26

En `019-26`, el tecnico necesita ver inmediatamente que:

- danos, causa, pruebas y propuesta tienen contenido;
- metodologia y limitaciones estan vacias;
- inventario puede construirse desde 23 patologias;
- valoracion economica existe por actuaciones;
- recomendaciones estan mezcladas;
- roles causa/efecto no estan informados.

El panel izquierdo evita que el tecnico descubra esos huecos al final, en la previsualizacion del informe.

## Panel central - Redaccion y estructura activa

### Funcion

Ser el area principal de trabajo. Debe permitir revisar y redactar el capitulo activo del informe V2 con contexto suficiente.

### Que se edita o compone

Segun el capitulo seleccionado:

- resumen ejecutivo;
- antecedentes y objeto;
- metodologia;
- limitaciones;
- analisis causal;
- inventario resumido;
- propuesta de reparacion;
- recomendaciones;
- conclusiones.

Para costes y actuaciones, el panel central no debe duplicar toda la biblioteca de costes. Debe mostrar la estructura economica del expediente y enlazar con las vistas existentes cuando haga falta editar en detalle.

### Como deberia organizarse

Cada capitulo deberia tener:

- estado de cobertura;
- texto actual o borrador;
- datos reutilizables detectados;
- huecos visibles;
- enlaces a origen;
- vista de como apareceria en V2.

Ejemplo para `Analisis causal` en `019-26`:

- texto de causa probable;
- pruebas/indicios;
- patologias agrupadas por dano;
- fotos relacionadas;
- aviso: roles causa/efecto no informados;
- bloque para redactar recorrido causa-efecto.

Ejemplo para `Valoracion economica`:

- total PEM;
- actuaciones;
- partidas;
- mediciones;
- advertencia de que no hay BC3 asociado;
- advertencia de que no hay `patologia_costes`;
- enlace a actuaciones de reparacion y biblioteca de costes.

### Justificacion para 019-26

El caso tiene suficiente contenido para redactar una version preliminar, pero no en el orden adecuado. El panel central debe transformar registros dispersos en capitulos defendibles.

## Panel derecho - Evidencia y contexto reutilizable

### Funcion

Mantener cerca la informacion que el tecnico consulta mientras redacta, sin obligarle a abandonar el capitulo activo.

### Bloques recomendados

#### Evidencia fotografica

- fotos de patologias;
- fotos de estancias;
- fotos de visita;
- filtros por estancia, elemento o patologia;
- contador y seleccion de evidencia clave.

Para `019-26`, este bloque es critico por las 107 fotos.

#### Patologias relacionadas

- listado compacto de patologias;
- estancia;
- elemento;
- localizacion;
- observacion breve;
- foto asociada si existe.

Debe ayudar a redactar inventario y causalidad sin abrir cada registro.

#### Observaciones tecnicas

- observaciones de visita;
- observaciones de estancias;
- observaciones de patologias;
- evolucion/preexistencia;
- urgencia/gravedad.

Debe servir para extraer limitaciones, incertidumbres y recomendaciones.

#### Costes y actuaciones

- actuaciones de reparacion;
- partidas snapshot;
- subtotal por actuacion;
- total PEM;
- base/origen de precios si existe.

Para `019-26`, debe mostrar dos actuaciones: demolicion de falso techo y colocacion de falso techo de carton-yeso.

#### Cobertura V2

- campos existentes;
- campos vacios;
- datos parcialmente reutilizables;
- advertencias de estructura.

Este bloque convierte `FIELD_MAP_V2` en ayuda de redaccion, sin implementar aun el informe.

### Justificacion

El panel derecho reduce los saltos entre detalle de expediente, patologias, fotos, actuaciones, costes e informe. Es la memoria auxiliar del tecnico.

## FASE C - Fricciones del sistema actual

### Dificultades al redactar 019-26

- La evidencia es abundante, pero esta repartida entre visita, estancias, patologias y fotos.
- La causa probable esta informada, pero no se ve junto a los danos agrupados y la prueba visual.
- Las patologias repetidas obligan a leer muchas fichas para entender el alcance global.
- Metodologia y limitaciones tienen campos existentes, pero estan vacios en el expediente.
- La propuesta de reparacion mezcla reparacion estricta con comprobaciones futuras.
- La valoracion economica por actuaciones existe, pero vive fuera del flujo de redaccion.
- Las conclusiones se revisan en la salida del informe, no en una mesa de argumentacion.

### Cambios constantes de pantalla

Hoy el tecnico debe saltar entre:

- detalle de expediente para textos principales;
- visita para estancias y fotografias;
- registros de patologias para observaciones concretas;
- actuaciones de reparacion para presupuesto por actuaciones;
- biblioteca de costes para revisar partidas;
- informe HTML/PDF para comprobar salida;
- resumen de pendientes para revision probatoria.

El Workbench debe reunir lectura y redaccion sin eliminar esas pantallas.

### Informacion demasiado dispersa

- Fotografias.
- Observaciones tecnicas.
- Danos repetidos por estancia.
- Costes y actuaciones.
- Limitaciones implicitas.
- Recomendaciones implicitas.
- Trazabilidad entre dano, reparacion y coste.

### Informacion duplicada o mezclada

- Propuesta de reparacion contiene reparacion, comprobacion futura y recomendacion.
- Actuaciones de reparacion pueden parecer propuesta, presupuesto o anexo economico segun donde se consulten.
- Patologias repetidas por estancia documentan bien la prueba, pero duplican lectura si se usan como cuerpo principal.
- Urgencia/gravedad y evolucion/preexistencia contienen material que tambien puede alimentar recomendaciones y limitaciones.

## FASE D - Datos nuevos vs datos existentes

| Bloque Workbench | Reutiliza datos existentes | Requiere reorganizacion | Requerira campos futuros |
|---|---|---|---|
| Estado V2 del informe | Si: FIELD_MAP_V2, expediente, visitas, patologias, actuaciones | Si: presentar cobertura por capitulo | No necesariamente para MVP |
| Resumen ejecutivo | Si: descripcion, causa, urgencia, PEM, conteos | Si: sintetizar | Si, si se quiere guardar resumen validado |
| Antecedentes y objeto | Si: expediente, descripcion, destinatario | Si: separar encargo/finalidad/alcance | Si, si se quiere estructura fina |
| Metodologia | Si: visita, tecnico, fecha, ambito, fotos | Si: convertir visita en metodologia | Si: documentacion, medios, pruebas realizadas/no realizadas |
| Limitaciones | Parcial: observaciones, evolucion, urgencia | Si: extraer de textos dispersos | Si: limitaciones tipadas |
| Analisis causal | Si: causa, pruebas, patologias, fotos | Si: relacionar origen-recorrido-efecto | Si: recorrido causal y vinculos causa/efecto |
| Inventario de danos | Si: patologias, estancias, fotos | Si: agrupar por familia/zona | Si: grupo/severidad/evidencia clave |
| Actuaciones ejecutadas | Parcial: observaciones y actuaciones | Si: distinguir observado/propuesto | Si: estado, fecha, evidencia, adecuacion |
| Propuesta de reparacion | Si: propuesta y actuaciones | Si: separar recomendaciones | Posible, para actuaciones necesarias estructuradas |
| Valoracion economica | Si: actuaciones, partidas, costes | Si: mostrar traza y PEM | Si: vinculo dano-actuacion-partida |
| Recomendaciones | Parcial: urgencia, evolucion, propuesta | Si: separar de reparacion | Si: tipo, justificacion, seguimiento |
| Conclusiones | Si: textos y datos principales | Si: ordenar segun V2 | Si, si se versionan conclusiones |
| Anexos | Si: fotos, fichas, costes | Si: separar anexo fotografico/economico | Si: documentacion aportada y BC3 por expediente |

## FASE E - Priorizacion

### MVP

Lo minimo para mejorar radicalmente la redaccion:

- Panel izquierdo con capitulos V2 y estado de cobertura.
- Panel central para redactar/revisar el capitulo activo.
- Panel derecho con evidencia contextual: patologias, fotos, observaciones y costes.
- Inventario resumido automatico de danos como lectura compacta.
- Vista economica resumida por actuaciones y total PEM.
- Avisos de huecos criticos: metodologia vacia, limitaciones vacias, roles causa/efecto vacios, recomendaciones mezcladas.

### V2

Mejoras importantes:

- Selector de evidencia fotografica clave.
- Agrupacion editable de danos por familia.
- Vista de trazabilidad dano -> actuacion -> partida.
- Separacion asistida de propuesta de reparacion y recomendaciones.
- Previsualizacion de capitulos V2 dentro del Workbench.
- Comparador entre informe actual V1 y estructura V2.

### V3

Mejoras avanzadas:

- Matriz de incertidumbres y nivel de confianza.
- Revision de partidas ejecutadas frente a presupuesto/documentacion aportada.
- Justificacion BC3/descompuestos integrada como anexo tecnico.
- Registro estructurado de documentacion aportada.
- Flujo de defensa pericial con checklist para abogado/aseguradora/juzgado.

## Conclusion obligatoria

Si manana hubiera que terminar el expediente `019-26` utilizando un Workbench de escritorio, las tres herramientas que mas productividad aportarian serian:

### 1. Panel de evidencia contextual

Justificacion: `019-26` tiene 107 fotografias y 23 patologias. La mayor perdida de tiempo esta en alternar entre fichas, fotos y texto. Un panel derecho con fotos, patologias y observaciones filtradas por capitulo permitiria redactar causalidad, inventario y conclusiones sin saltar constantemente.

### 2. Inventario resumido de danos

Justificacion: el dano principal se repite por estancias y elementos. El tecnico necesita una vision agrupada por familias: revestimientos interiores, falsos techos, carpinterias, pavimentos, moho, eflorescencias y fachada. Esto reduce la lectura repetitiva y mejora el cuerpo principal del informe.

### 3. Panel economico por actuaciones

Justificacion: `019-26` ya tiene 2 actuaciones con PEM de 8.616,00 EUR. La valoracion no debe depender de repetir partidas por cada patologia. Un panel economico por actuaciones permite revisar mediciones, subtotales y relacion con reparacion necesaria mientras se redacta el anexo economico o la valoracion.

## Decision principal

El Workbench V2 no debe ser un formulario mas. Debe ser una vista de escritorio de sintesis y argumentacion.

Su funcion es convertir datos existentes en un informe:

- legible;
- defendible;
- trazable;
- economicamente coherente;
- compatible con los flujos actuales.

Para `019-26`, la mejora especifica es pasar de un expediente con mucha evidencia dispersa a una mesa de redaccion donde causa, danos, fotos, reparacion y coste se ven juntos.
