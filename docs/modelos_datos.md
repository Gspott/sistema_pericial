# Modelos de datos y persistencia

Documento tematico de datos. La normativa resumida esta en `AGENTS.md`.

## Fuente normativa

Fuente normativa: este documento.

La definicion canonica de `rol_final`, soft delete y persistencia de registros de caso/visita vive aqui.

## Dependencias

Depende de:

- [docs/backend.md](backend.md)
- [docs/informes.md](informes.md)
- [docs/revision_probatoria.md](revision_probatoria.md)

Puede impactar:

- Generacion de informes.
- Revision probatoria.
- Formularios de registro.
- Consultas SQLite.

## Decisiones

Decision ID: DATA-001
Estado: Active
Categoria: Datos

La formula canonica es `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.

Decision ID: DATA-002
Estado: Active
Categoria: Datos

El soft delete aplica a biblioteca/catalogos mediante `activo`; los registros de caso/visita pueden borrarse fisicamente si el flujo lo requiere.

Decision ID: DATA-003
Estado: Active
Categoria: Datos

La trazabilidad de patologias usa `1 patologia = 1 registro`; el duplicado no copia fotos ni comparte referencias.

Decision ID: PROP-001
Estado: Active
Categoria: Datos

Cuando una propuesta tiene lineas en `propuesta_lineas`, esas lineas son la fuente economica de verdad. Los importes agregados de `propuestas` se conservan por compatibilidad y se sincronizan desde el desglose.

## Madurez

- `rol_final`: Activo.
- Soft delete en biblioteca: Activo.
- Borrado fisico de registros de caso/visita: Activo si el flujo lo contempla.
- Duplicado/eliminacion interior: Activo.
- Duplicado/eliminacion exterior: Experimental / condicionado a endpoint o implementacion especifica documentada.
- Propuestas con lineas de servicio estructuradas: Activo.

## Invariantes

- SQLite-first.
- Nunca borrar columnas ni datos reales en migraciones automaticas.
- Mantener compatibilidad hacia atras con bases existentes.
- Preferir soft delete en biblioteca/catalogos cuando aplique.
- Campos nuevos mediante patron existente tipo `asegurar_columna()` si aplica.
- No inventar relaciones nuevas sin migracion planificada.

## Rol final de patologia

Formula canonica:

```python
rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca
```

Reglas:

- No usar formulas alternativas.
- `rol_patologia` pertenece a biblioteca.
- `rol_patologia_observado` es ajuste puntual del registro concreto.
- En registros exteriores puede no existir `rol_patologia_observado`; normalizar queries o usar acceso defensivo.

## Biblioteca de patologias

La biblioteca describe patologias genericas, no casos concretos.

Campos internos:

- `categoria`
- `elemento_afectado`
- `mecanismo`
- `rol_patologia`
- `activo`

`rol_patologia` admite:

- `causa`
- `efecto`
- `mixta`

`activo` se usa para soft delete en biblioteca/catalogos. Las patologias inactivas no deben mostrarse como seleccionables.

## Registros de caso/visita

- Los registros concretos de una visita/caso pueden eliminarse fisicamente si el flujo lo requiere.
- No aplicar soft delete global a registros de caso sin decision explicita.
- Mantener trazabilidad: `1 patologia = 1 registro`.
- No agrupar multiples patologias en un unico registro.
- No mezclar fotos de varias patologias.

## Duplicado/eliminacion

- Interiores: duplicado y eliminacion soportados como flujo ordinario.
- Exteriores: solo soportados si existe endpoint/implementacion especifica documentada.
- Al duplicar, copiar solo datos descriptivos.
- No copiar fotos ni compartir referencias de fotos entre registros.
- El nuevo registro empieza sin fotos.

## Estancias

- Completa para continuar visita: nombre, tipo de estancia y al menos una foto pueden bastar.
- Completa tecnicamente para informe: ventilacion, acabados, observaciones y otros campos tecnicos enriquecen el informe.
- `planta` solo es obligatoria si la unidad asociada tiene `tiene_varias_plantas = 1`.

## Relaciones comerciales

- Lead puede convertirse a cliente.
- Lead conserva registro y se enlaza con `cliente_id`.
- Reutilizar cliente existente por email o telefono si es posible.
- Cliente puede abrir nuevo expediente con datos precargados.
- Propuesta puede crear/enlazar expediente.
- `propuestas.expediente_id` se actualiza al crear expediente desde propuesta.
- `expedientes` aun no tiene `cliente_id`; no inventar relacion sin migracion planificada.

## Propuestas y lineas de servicio

`propuesta_lineas` representa el desglose economico y documental de una propuesta cuando existe.

Campos activos del desglose:

- `categoria_servicio`: categoria funcional de la linea.
- `concepto`: titulo economico/documental de la linea.
- `descripcion`: detalle de la actuacion o calculo.
- `incluye`: alcance incluido para esa linea.
- `no_incluye`: exclusiones especificas de esa linea.
- `condiciones`: condiciones especificas de esa linea.
- `cantidad`, `precio_unitario`, `iva_porcentaje`, `total`, `orden`: importes y ordenacion.

Categorias activas:

- `estudio_documental`: Estudio preliminar y analisis documental.
- `visita_tecnica`: Visita tecnica.
- `informe_pericial`: Redaccion de informe pericial.
- `ratificacion_judicial`: Ratificacion judicial.
- `desplazamientos`: Desplazamientos y dietas.
- `extras`: Servicios adicionales.
- Categoria vacia: fallback compatible para lineas antiguas.

Reglas de compatibilidad:

- Las propuestas antiguas sin lineas siguen usando `base_imponible`, `iva`, `importe_iva`, `total` y `total_propuesta`.
- Si existen lineas, los importes globales no deben editarse como fuente economica primaria desde el formulario general.
- El recalculo de totales parte de las lineas y actualiza los agregados de `propuestas`.
- No eliminar ni renombrar columnas existentes en `propuestas` o `propuesta_lineas`.
- Las columnas nuevas de `propuesta_lineas` se anaden de forma defensiva con `asegurar_columna()`.

Reglas monetarias:

- Los importes monetarios se redondean a 2 decimales.
- Cada linea calcula base, IVA y total con la misma logica auxiliar del router de propuestas.
- La propuesta mantiene coherencia entre suma de lineas, `base_imponible`, `importe_iva`, `total` y `total_propuesta`.
- Cantidad, precio unitario e IVA no pueden ser negativos en alta/edicion manual ni en servicios rapidos.

Servicios rapidos activos:

- Ratificacion judicial: se crea como linea normal con categoria `ratificacion_judicial`; no es un checkbox del informe.
- Desplazamientos/dietas: se crea como linea normal de categoria `desplazamientos` con calculo `km x precio/km`.
- Recargo por urgencia: se crea como linea normal de categoria `extras`, calculada sobre base imponible sin IVA.
- Suplemento por complejidad: se crea como linea normal de categoria `extras`, con nivel `baja`, `media` o `alta`, calculado sobre base imponible sin IVA.

Seguridad y borrado:

- Alta, edicion y borrado de lineas deben validar ownership de propuesta/linea.
- El borrado de lineas exige confirmacion server-side mediante `confirmar_eliminar`.
- El recalculo de totales solo debe ejecutarse cuando la linea se crea, actualiza o borra realmente.

## Criterios Done

- `bash scripts/validate_harness.sh` pasa.
- Cambios de esquema se prueban solo sobre DB temporal/copia.
- No hay borrado de columnas ni datos reales.
- Compatibilidad con registros existentes documentada.
- Documentos dependientes actualizados si cambia una regla de datos.
