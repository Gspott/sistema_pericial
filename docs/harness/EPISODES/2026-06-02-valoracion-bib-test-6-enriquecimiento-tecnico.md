# Valoracion BIB-TEST-6 Enriquecimiento Tecnico

Fecha: 2026-06-02

## Objetivo

Enriquecer la ficha de testigos reutilizables con atributos tecnicos habituales
en anuncios inmobiliarios y ampliar el pegado asistido desktop, sin scraping,
OCR, IA externa ni cambios en Workbench/informes.

## Campos Reutilizados

- `banos`
- `superficie_construida`
- `superficie_util`
- `planta`
- `ascensor`
- `terraza`
- `garaje`
- `trastero`
- `estado_conservacion`
- `codigo_postal`

## Columnas Defensivas Nuevas

- `es_exterior`
- `balcon`
- `patio`
- `ano_construccion`
- `ano_reforma`
- `aire_acondicionado`
- `tipo_calefaccion`
- `certificacion_energetica`

## UX

El alta rapida desktop incorpora secciones compactas:

- Caracteristicas.
- Superficies.
- Estado y calidades.
- Equipamiento.

El formulario mobile-first completo se mantiene intacto.

## Pegado Asistido

La heuristica local detecta baños, superficies construida/util, planta, exterior
o interior, ascensor, balcon, terraza, patio, años, estado, aire acondicionado,
calefaccion y certificacion energetica. Los valores detectados son propuestas
editables y no se guardan hasta la accion final de guardado.

## Fuera De Alcance

- Scraping de portales.
- OCR o IA externa.
- Fotografias/capturas.
- Datos especificos de expediente.
- Informes y Workbench.
