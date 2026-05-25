# Playbook: Propuestas

## Que leer primero

- `docs/backend.md`.
- `docs/harness/RISK_MAP.md`.
- `app/routers/propuestas.py`.
- `app/services/propuestas_catalogo.py`.
- Templates en `templates/propuestas/`.

## Archivos sensibles

- `app/routers/propuestas.py`.
- `templates/propuestas/imprimir.html`.
- `static/propuestas_detalle.js`.
- `static/propuestas_templates.js`.

## Acciones permitidas

- Mejorar UI comercial acotada.
- Ajustar textos comerciales.
- Validar PDF/email con mock.
- Crear tests de flujo propuesta.

## Acciones prohibidas

- Enviar emails reales sin orden.
- Crear facturas reales.
- Cambiar calculos de honorarios sin validacion.
- Romper compatibilidad con propuestas antiguas sin lineas.

## Validaciones

- `python3 -m compileall app`.
- `node --check` si se toca JS.
- Smoke propuesta demo, PDF y email mock.

## Senales de alarma

- Cambios en `recalcular_totales_propuesta`.
- Cambios en creacion de factura desde propuesta.
- Cambios en estados o envio email.

## Rollback

- Revertir diff.
- Eliminar solo datos demo creados en DB temporal.

