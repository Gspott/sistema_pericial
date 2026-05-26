# Valoracion Ajustes Homogeneizacion Manual

Fecha: 2026-05-26

## Objetivo

Crear formulario minimo server-side para ajustes manuales de homogeneizacion por
testigo vinculado a expediente de valoracion, sin calcular todavia el valor
final del expediente.

## Cambios

- Rutas GET/POST para
  `/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes`.
- Template mobile-first `valoracion_testigo_ajustes.html`.
- Validacion backend de cada ajuste entre -0.20 y +0.20.
- Upsert manual en `valoracion_testigo_ajustes`.
- Calculo limitado de `coeficiente_total = 1 + suma de ajustes`.
- Actualizacion de `valor_unitario_ajustado` en el vinculo cuando existe
  `valor_unitario_base`.
- Pantalla de testigos por expediente muestra coeficiente total, valor unitario
  base, valor unitario ajustado y boton de ajustes.
- `build_informe_context()` expone coeficiente total, valor unitario base,
  valor unitario ajustado y justificacion de ajustes.
- Smoke con DB temporal para guardar ajustes, rechazar rango invalido y
  confirmar que el testigo base no cambia.

## Fuera De Alcance

- Valor final del expediente.
- Promedios o ponderacion de seis testigos.
- Metodo de coste.
- Fotos de testigos.
- Migracion desde legacy.

## Riesgos

- El calculo limitado puede parecer valoracion final si se presenta sin
  contexto; la documentacion lo mantiene como dato preparatorio por testigo.
- `app/main.py` sigue concentrando rutas nuevas en el monolito.

## Validaciones Esperadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`
