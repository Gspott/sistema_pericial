# Routers Not Included Legacy

## Que Se Detecto

Los routers `app/routers/expedientes.py`, `app/routers/visitas.py`,
`app/routers/estancias.py` y `app/routers/patologias.py` existen y contienen
rutas, pero no estan incluidos en `app/main.py`.

La auditoria comparativa concluye que son extraccion parcial/legacy, no modulos
listos para `include_router()`.

## Riesgo

- Activar rutas duplicadas con logica antigua.
- Saltarse ownership y validaciones modernas.
- Romper contextos Jinja actuales.
- Perder soporte multiunidad, fotos relacionadas, exterior, mapas,
  climatologia avanzada, PDF/DOCX y revision probatoria.
- Confundir codigo legacy con fuente funcional actual.

## Como Evitar Regresion

- Consultar `docs/harness/AGENT_MAPS/main_vs_routers_map.md` antes de tocar
  expedientes, visitas, estancias o patologias.
- Mantener `app/main.py` como fuente funcional actual de esos flujos hasta
  extraccion planificada.
- Exigir smoke tests de ownership y flujo antes de mover una ruta.
- Extraer una ruta/flujo cada vez, con diff pequeno y reversible.

## Que NO Hacer

- No hacer `app.include_router()` de estos routers completos.
- No borrar routers legacy por parecer no usados.
- No mover rutas masivamente desde `app/main.py`.
- No asumir equivalencia entre rutas con el mismo path.
- No tocar uploads/fotos reales para validar comportamiento.

## Validaciones Antes De Mover Rutas

- `python3 -m compileall app`
- `python3 -m compileall tests`
- `python3 -m pytest tests/smoke -q`
- Smoke especifico del flujo afectado.
- Smoke de ownership si hay `owner_user_id`.
- `bash scripts/validate_harness.sh`
- Revision de contexto Jinja esperado por la plantilla.

## Decision Humana Requerida

Antes de incluir, archivar o eliminar cualquier router legacy completo.
