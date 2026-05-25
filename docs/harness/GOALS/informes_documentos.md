# Goal: Informes Y Documentos

## Objetivo

Mantener informes PDF/DOCX consistentes, con `build_informe_context()` como fuente unica de datos.

## Tareas permitidas

- Mejoras de contexto.
- Ajustes de plantilla imprimible.
- Mejoras DOCX editables.
- Tests de contexto y generacion con datos de prueba.

## Tareas prohibidas

- Duplicar logica de datos entre PDF y DOCX.
- Leer informes reales generados.
- Cambiar conclusiones tecnicas sin revision humana.

## Criterios de terminado

- PDF y DOCX usan la misma fuente de datos.
- No se rompen visitas parciales.
- Advertencias siguen siendo tolerantes a datos faltantes.

## Validaciones obligatorias

- `python3 -m compileall app`.
- Smoke de `build_informe_context()`.
- Generacion PDF/DOCX con datos de prueba cuando exista.

