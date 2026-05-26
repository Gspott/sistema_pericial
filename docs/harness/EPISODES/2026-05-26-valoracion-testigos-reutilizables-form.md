# Valoracion Testigos Reutilizables Form

Fecha: 2026-05-26

## Objetivo

Crear formularios server-side para la base reutilizable de testigos de
valoracion y para vincular testigos a expedientes de valoracion con snapshot,
sin implementar ajustes, homogeneizacion ni calculo final.

## Cambios

- Rutas CRUD minimas sin borrado para `testigos_valoracion`.
- Rutas de seleccion por expediente en `valoracion_expediente_testigos`.
- Snapshot JSON al vincular testigo a expediente.
- Orden, incluido y notas de seleccion editables por vinculo.
- CTA contextual "Testigos de valoracion" solo en expedientes de valoracion.
- `build_informe_context()` expone orden, incluido y notas de seleccion en los
  comparables del modelo nuevo.
- Smoke temporal de creacion, edicion, vinculacion, snapshot, actualizacion,
  retirada de vinculo y fallback legacy.

## Decisiones

- No se borra el testigo base al quitarlo de un expediente.
- La recomendacion de 6 testigos queda como advertencia no bloqueante.
- No se gestionan fotos de testigo en esta fase.
- `comparables_valoracion` sigue siendo fallback legacy cuando no hay testigos
  vinculados en el modelo nuevo.

## Riesgos

- `app/main.py` sigue siendo monolitico y cualquier ruta nueva aumenta el coste
  de mantenimiento.
- El snapshot actual conserva campos textuales y numericos del testigo base,
  pero no versiona cambios sucesivos del testigo reusable.
- La homogeneizacion queda pendiente; no hay validacion de coeficientes ni
  calculo automatico.

## Validaciones Esperadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`
