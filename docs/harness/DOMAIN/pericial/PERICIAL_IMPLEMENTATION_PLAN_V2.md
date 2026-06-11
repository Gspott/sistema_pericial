# PERICIAL_IMPLEMENTATION_PLAN_V2

## Objetivo

Definir la implementacion minima necesaria para disponer de un primer Workbench pericial de escritorio operativo, priorizando productividad en escritorio y manteniendo intacto el flujo mobile-first actual.

Este documento no implementa nada. Es un plan tecnico de fases.

Documentos de referencia:

- `docs/harness/DOMAIN/pericial/INFORME_SCHEMA_V2.md`.
- `docs/harness/DOMAIN/pericial/FIELD_MAP_V2.md`.
- `docs/harness/DOMAIN/pericial/PERICIAL_WORKBENCH_V2.md`.
- `docs/harness/DOMAIN/pericial/PERICIAL_DATA_V2.md`.

Caso piloto principal: expediente `019-26`.

## Principios de implementacion

- No sustituir pantallas existentes.
- No romper mobile-first.
- No bloquear generacion de informes actuales.
- No alterar PDF/DOCX en la primera fase operativa.
- Reutilizar datos y helpers existentes antes de crear esquema nuevo.
- Empezar por una vista de escritorio SSR de analisis y redaccion asistida.
- Separar claramente diagnostico, redaccion, evidencia y economia.
- Evitar que el primer Workbench sea un formulario mas.

## FASE A - Auditoria tecnica de reutilizacion

### Modelos y datos existentes reutilizables

#### `expedientes`

Campos ya disponibles:

- `objeto_pericia`.
- `alcance_limitaciones`.
- `metodologia_pericial`.
- `descripcion_dano`.
- `causa_probable`.
- `pruebas_indicios`.
- `evolucion_preexistencia`.
- `propuesta_reparacion`.
- `urgencia_gravedad`.
- `ambito_patologias`.

Uso recomendado:

- Usar como fuente principal de textos periciales existentes.
- No crear campos nuevos para metodologia y limitaciones en el MVP, porque ya existen.
- Mostrar estado de completitud de esos campos en el Workbench.

#### `visitas`

Campos ya disponibles:

- fecha;
- tecnico;
- ambito de visita;
- observaciones de visita.

Uso recomendado:

- Alimentar metodologia basica.
- Alimentar panel de evidencia/contexto.

#### `estancias`

Campos ya disponibles:

- nombre;
- tipo;
- planta;
- observaciones;
- acabados;
- ventilacion.

Uso recomendado:

- Inventario resumido de danos.
- Contexto para patologias.
- Deteccion de limitaciones o incertidumbres dispersas.

#### `registros_patologias` y `registros_patologias_exteriores`

Campos ya disponibles:

- elemento;
- patologia;
- localizacion;
- detalle;
- observaciones;
- rol observado en patologias interiores;
- fotos asociadas.

Uso recomendado:

- Agrupar danos.
- Crear inventario resumido.
- Alimentar analisis causal.
- Generar panel derecho de evidencia.

#### Fotografias

Tablas reutilizables:

- `visita_fotos`.
- `estancia_fotos`.
- `registro_patologia_fotos`.
- `registro_patologia_exterior_fotos`.

Uso recomendado:

- Panel de evidencia contextual.
- Conteos y advertencias.
- En MVP no seleccionar evidencia clave persistente; solo mostrar y filtrar.

#### Costes y actuaciones

Tablas reutilizables:

- `actuaciones_reparacion`.
- `actuacion_partidas`.
- `costes_conceptos`.
- `costes_bases`.
- `patologia_costes` como fallback heredado.

Uso recomendado:

- Panel economico por actuaciones.
- Total PEM.
- Aviso si no hay trazabilidad dano-actuacion.
- No crear presupuesto paralelo.

### Rutas existentes reutilizables

- `/detalle-expediente/{expediente_id}`: puerta de entrada y estado general.
- `/editar-expediente/{expediente_id}`: edicion existente de metodologia, limitaciones y textos periciales.
- `/registrar-patologias/{visita_id}` y `/editar-registro/{registro_id}`: captura/edicion mobile-first de patologias.
- `/expedientes/{expediente_id}/actuaciones-reparacion`: actuaciones y PEM por expediente.
- `/expedientes/{expediente_id}/presupuesto-reparacion`: presupuesto por patologias, si existe.
- `/costes`: biblioteca de costes.
- `/informes/{expediente_id}/imprimir`: vista actual de informe.
- `/expediente/{expediente_id}/valoracion/workbench`: patron tecnico de workbench SSR de escritorio.

Ruta candidata para fase de implementacion:

- `GET /expedientes/{expediente_id}/pericial-workbench`

Esta ruta no debe sustituir `detalle-expediente` ni redirigir automaticamente. Debe aparecer como accion secundaria contextual para expedientes de patologias.

### Plantillas y componentes reutilizables

#### `templates/valoracion_workbench.html`

Patrones reutilizables:

- layout wide de escritorio;
- hero con metricas;
- barra de diagnostico;
- area principal + panel sticky;
- densidad de datos;
- degradacion responsive;
- microedicion acotada como patron futuro, no en MVP inicial.

#### `templates/actuaciones_reparacion.html`

Patrones reutilizables:

- resumen economico por actuaciones;
- total PEM destacado;
- tabla de partidas snapshot;
- enlaces a biblioteca e informe con anexo.

#### `templates/detalle_expediente.html`

Patrones reutilizables:

- tarjeta de estado;
- acciones principales/secundarias;
- revision probatoria;
- acceso a informe actual.

#### `templates/informes/imprimir.html`

Uso en MVP:

- No tocar.
- Solo enlazar a previsualizacion actual para comparar salida V1 con diagnostico V2.

### Helpers reutilizables

- `build_informe_context(expediente_id)`: fuente compartida para datos de informe y compatibilidad.
- `preparar_actuaciones_reparacion_expediente(cur, expediente_id)`: actuaciones y PEM por expediente.
- `preparar_presupuesto_reparacion_expediente(cur, expediente_id)`: fallback por patologias.
- Helpers del workbench de valoracion para diagnostico, seleccion, orden y panel contextual como referencia de forma, no necesariamente reutilizacion literal.

## FASE B - Arquitectura minima propuesta

### 1. Workbench escritorio

#### Arquitectura minima

- Nueva ruta SSR `GET /expedientes/{expediente_id}/pericial-workbench`.
- Nueva plantilla `templates/pericial_workbench.html`.
- Nuevo helper de preparacion de contexto, idealmente aislado:
  - opcion minima: funciones en `app/main.py` junto al patron actual;
  - opcion mas limpia: `app/services/pericial_workbench.py`.
- Acceso desde detalle de expediente como accion secundaria solo para `tipo_informe=patologias`.
- Sin modificar flujos de captura ni pantallas existentes.

#### Contenido MVP

- Hero con expediente, tipo, estado y acceso a informe actual.
- Metric tiles:
  - visitas;
  - estancias;
  - patologias;
  - fotos;
  - actuaciones;
  - PEM.
- Panel izquierdo/diagnostico:
  - metodologia;
  - limitaciones;
  - analisis causal;
  - inventario de danos;
  - propuesta/recomendaciones;
  - valoracion economica.
- Panel central:
  - resumen ejecutivo preliminar no persistente;
  - inventario resumido de danos;
  - metodologia basica desde visita;
  - limitaciones detectadas o vacias;
  - propuesta y recomendaciones candidatas;
  - economia por actuaciones.
- Panel derecho:
  - patologias compactas;
  - fotos y conteos;
  - observaciones tecnicas;
  - costes/actuaciones;
  - enlaces a origen.

#### Complejidad estimada

Media si es solo lectura/diagnostico. Alta si intenta editar y persistir todo desde el primer paso.

### 2. Metodologia

#### Reutilizacion maxima

- `expedientes.metodologia_pericial`.
- `visitas.fecha`.
- `visitas.tecnico`.
- `visitas.ambito_visita`.
- `visitas.observaciones_visita`.
- Conteo de fotos, estancias y patologias.

#### Implementacion minima

- Mostrar bloque de metodologia generada desde visita.
- Mostrar si `metodologia_pericial` esta vacia.
- Enlazar a `editar-expediente` para completarla.
- No crear nuevos campos en MVP.

#### Complejidad estimada

Baja.

### 3. Limitaciones

#### Reutilizacion maxima

- `expedientes.alcance_limitaciones`.
- `estancias.observaciones`.
- `registros_patologias.observaciones`.
- `evolucion_preexistencia`.
- `urgencia_gravedad`.

#### Implementacion minima

- Mostrar estado del campo `alcance_limitaciones`.
- Mostrar pistas candidatas extraidas de observaciones largas o de textos de urgencia/evolucion.
- Enlazar a `editar-expediente` para completar el campo actual.
- No crear nuevos campos en MVP.

#### Complejidad estimada

Baja-media.

### 4. Recomendaciones tecnicas

#### Reutilizacion maxima

- `propuesta_reparacion`.
- `urgencia_gravedad`.
- `evolucion_preexistencia`.
- observaciones de patologias/estancias.

#### Implementacion minima

- Mostrar una seccion "Recomendaciones candidatas" derivada de textos existentes.
- Separar visualmente "reparacion necesaria" y "comprobaciones/recomendaciones" sin persistir una nueva estructura.
- En MVP no modificar DB.

#### Necesidad futura

Persistir recomendaciones separadas probablemente requerira campo nuevo o estructura nueva. No debe ser requisito para el primer Workbench operativo.

#### Complejidad estimada

Media.

### 5. Actuaciones verificadas

#### Reutilizacion maxima

- `actuaciones_reparacion`.
- `actuacion_partidas`.
- observaciones de estancias y patologias.
- fotos asociadas.

#### Implementacion minima

- Mostrar actuaciones existentes como "actuaciones economicas".
- Mostrar aviso: "estado de ejecucion/verificacion no registrado".
- Mostrar posibles observaciones relacionadas.
- Enlazar a actuaciones de reparacion para editar partidas y cantidades.

#### Necesidad futura

Verificacion real requiere una entidad o estructura nueva que distinga ejecutada, parcial, pendiente o no verificada, con evidencia asociada. No debe bloquear el Workbench inicial.

#### Complejidad estimada

Media en modo diagnostico. Alta si se implementa verificacion persistente.

## FASE C - Matriz por bloque

| Bloque | Reutiliza datos existentes | Requiere nuevos campos | Requiere nueva entidad | Complejidad |
|---|---|---|---|---|
| Workbench escritorio solo lectura | Si: expediente, visitas, patologias, fotos, actuaciones, contexto informe | No | No | Media |
| Metodologia | Si: `metodologia_pericial` y visitas | No para MVP | No | Baja |
| Limitaciones | Si: `alcance_limitaciones` y observaciones | No para MVP | No | Baja-media |
| Recomendaciones tecnicas | Parcial: propuesta, urgencia, evolucion | Si para persistencia separada | No necesariamente inicial | Media |
| Actuaciones verificadas | Parcial: actuaciones y observaciones | Si para estado simple | Probablemente si hay multiples verificaciones/evidencias | Media-alta |
| Inventario resumido | Si: patologias y estancias | No para MVP | No | Media |
| Panel economico | Si: actuaciones y partidas snapshot | No para MVP | No | Baja-media |
| Trazabilidad dano-actuacion-coste | Parcial | Si para traza manual | Probablemente si se formaliza | Alta |

## FASE D - MVP para mejorar 019-26

### Objetivo del MVP

Dar al tecnico una vista unica de escritorio que permita terminar mejor `019-26` sin cambiar captura movil ni generar informe V2 definitivo.

### Alcance MVP recomendado

1. Nueva vista SSR de Workbench pericial.
2. Diagnostico V2 por capitulos.
3. Inventario resumido de danos derivado de patologias.
4. Metodologia basica desde visita y estado de `metodologia_pericial`.
5. Limitaciones: estado de `alcance_limitaciones` y pistas candidatas.
6. Recomendaciones candidatas desde propuesta/urgencia/evolucion.
7. Economia por actuaciones y PEM.
8. Enlaces a pantallas existentes para editar:
   - expediente;
   - patologias;
   - actuaciones;
   - biblioteca de costes;
   - informe actual.

### Fuera de alcance MVP

- Modificar PDF/DOCX.
- Guardar resumen ejecutivo V2.
- Crear campos nuevos.
- Crear tablas nuevas.
- Seleccionar evidencias clave persistentes.
- Verificar actuaciones con estado persistente.
- Trazabilidad dano-actuacion-coste persistente.
- Sustituir el detalle de expediente.

### Mejora concreta para 019-26

El MVP permitiria ver en una sola pantalla:

- que metodologia y limitaciones estan vacias;
- que hay 23 patologias agrupables;
- que hay 107 fotos;
- que la causa y pruebas estan informadas;
- que recomendaciones estan mezcladas con propuesta;
- que el PEM por actuaciones es 8.616,00 EUR;
- que no hay trazabilidad formal dano-actuacion-coste;
- que no hay roles causa/efecto informados.

Ese salto mejora productividad sin tocar datos permanentes.

## Plan tecnico por fases

### Fase 1 - Workbench diagnostico de solo lectura

#### Alcance

- Ruta SSR de escritorio.
- Plantilla nueva con layout inspirado en `valoracion_workbench.html`.
- Helper de contexto que reutilice:
  - expediente;
  - visitas;
  - estancias;
  - patologias;
  - fotos;
  - actuaciones;
  - presupuesto por patologias como fallback;
  - campos periciales existentes.
- Enlace desde detalle de expediente.

#### Riesgos

- Cargar demasiada informacion en una sola pantalla.
- Duplicar logica de `build_informe_context()`.
- Romper mobile si no degrada bien.

#### Compatibilidad

- No modifica DB.
- No modifica informes.
- No cambia captura movil.
- No sustituye pantallas existentes.

#### Esfuerzo estimado

Medio: 1-2 sesiones de implementacion con tests smoke.

#### Validaciones esperadas

- GET workbench responde 200.
- Expediente no patologias degrada o bloquea con mensaje.
- `019-26` muestra conteos y PEM.
- No rompe tests existentes.

### Fase 2 - Microedicion de campos existentes

#### Alcance

Permitir guardar desde el Workbench solo campos ya existentes:

- `metodologia_pericial`;
- `alcance_limitaciones`;
- posiblemente `propuesta_reparacion`, `urgencia_gravedad`, `evolucion_preexistencia`.

No crear campos nuevos.

#### Riesgos

- Convertir el Workbench en un formulario grande.
- Duplicar validacion de `editar-expediente`.

#### Compatibilidad

- Usa columnas existentes.
- Mantiene `editar-expediente` como pantalla completa.
- Debe ser opcional y acotado.

#### Esfuerzo estimado

Medio-bajo.

### Fase 3 - Recomendaciones tecnicas persistentes

#### Alcance

Solo si el MVP confirma utilidad, introducir persistencia separada para recomendaciones.

#### Riesgos

- Duplicar propuesta de reparacion.
- Anadir campo permanente con poca estructura.

#### Compatibilidad

- Debe ser opcional.
- Informes V1 no deben cambiar.

#### Esfuerzo estimado

Medio.

### Fase 4 - Actuaciones verificadas

#### Alcance

Introducir capacidad de distinguir:

- ejecutada;
- parcial;
- pendiente;
- no verificada.

Asociar evidencia u observacion de verificacion.

#### Riesgos

- Confundir actuaciones economicas con actuaciones ejecutadas.
- Crear duplicidad con `actuaciones_reparacion`.

#### Compatibilidad

- Mantener `actuaciones_reparacion` como presupuesto/PEM.
- La verificacion debe ser capa adicional.

#### Esfuerzo estimado

Medio-alto.

### Fase 5 - Trazabilidad dano-actuacion-coste

#### Alcance

Formalizar puente entre grupos de dano, actuaciones y partidas economicas.

#### Riesgos

- Sobremodelado.
- Mucha carga de captura.
- Complejidad de UI.

#### Compatibilidad

- Debe poder existir sin `patologia_costes`.
- Debe respetar actuaciones por expediente.

#### Esfuerzo estimado

Alto.

## Orden recomendado de ejecucion

1. Workbench diagnostico de solo lectura.
2. Inventario resumido derivado y panel economico por actuaciones.
3. Microedicion de `metodologia_pericial` y `alcance_limitaciones`.
4. Separacion persistente de recomendaciones tecnicas.
5. Actuaciones verificadas.
6. Trazabilidad dano-actuacion-coste.
7. Integracion con `INFORME_SCHEMA_V2` en PDF/DOCX.

## Riesgos globales

- Tocar informes demasiado pronto.
- Crear DB nueva antes de comprobar productividad del Workbench.
- Introducir una UI pesada que perjudique mobile-first.
- Duplicar datos que ya existen.
- Convertir recomendaciones, propuesta y actuaciones en tres versiones incoherentes de lo mismo.
- Usar `patologia_costes` como unica via economica cuando `019-26` demuestra que la valoracion debe ser por actuaciones.

## Decision de menor esfuerzo / mayor calidad

La ruta de menor esfuerzo para obtener el mayor salto de calidad es:

1. Construir una vista SSR de Workbench pericial de solo lectura.
2. Reutilizar campos existentes de expediente para metodologia y limitaciones.
3. Reutilizar actuaciones de reparacion para economia.
4. Derivar inventario de danos desde patologias.
5. Mostrar recomendaciones candidatas sin persistirlas inicialmente.

Esto no completa todo V2, pero mejora de inmediato la redaccion de `019-26` sin coste permanente de datos nuevos.
