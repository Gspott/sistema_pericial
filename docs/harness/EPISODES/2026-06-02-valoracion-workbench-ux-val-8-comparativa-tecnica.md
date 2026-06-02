# UX-VAL-8 Comparativa Tecnica Enriquecida

Fecha: 2026-06-02

## Objetivo

Enriquecer el Workbench SSR de valoracion con atributos tecnicos de testigos
reutilizables para facilitar comparacion visual de calidad, estado, superficies
y equipamiento sin cambiar calculos, DB, Biblioteca de Testigos ni informes.

## Cambios

- `build_informe_context()` conserva mas atributos tecnicos de
  `testigos_valoracion` dentro de `comparables_valoracion` modernos:
  superficie construida/util, banos, planta, ascensor, exterior, balcon,
  terraza, patio, anos, climatizacion, garaje, trastero y certificacion
  energetica.
- El Workbench muestra columnas compactas de superficies, atributos tecnicos y
  estado de conservacion.
- El panel contextual incorpora la seccion "Caracteristicas tecnicas del
  testigo".
- QA visual no bloqueante:
  - 4 planta o superior sin ascensor.
  - Superficie util/construida muy divergente.
  - Falta superficie util y construida.
  - Estado de conservacion desconocido.
  - Ano de construccion ausente.

## Riesgos

- Los avisos son heuristicas visuales y no sustituyen criterio pericial.
- Los campos legacy pueden no traer atributos tecnicos; el template degrada a
  guion o aviso de dato pendiente.
- No se modifican pesos, homogeneizacion ni valor final.

## Validacion prevista

- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_valoracion_workbench.py -q`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

## Fuera de alcance

- Cambios de DB.
- Cambios en Biblioteca de Testigos.
- Cambios de informes HTML/PDF/DOCX.
- Cambios de calculo, ponderacion o adopcion automatica de valor final.
