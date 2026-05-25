# Task Pack: Mobile UI

## Cuando usarlo

Para cambios CSS, Jinja o JS mobile-first.

## Cuando NO usarlo

No usar para facturacion fiscal, auth, DB o service worker sin revisar riesgo especifico.

## Riesgo base

Medio-alto.

## Archivos normalmente permitidos

- Templates Jinja afectados.
- `static/mobile.css`.
- JS pequeno y progresivo.
- Partials del shell si esta justificado.

## Archivos normalmente prohibidos

- Frameworks SPA.
- React, Vue o Angular.
- Rutas backend no relacionadas.
- Datos reales.

## Lectura previa obligatoria

- `docs/ux.md`.
- `docs/pwa.md` si hay PWA/cache.
- `docs/harness/PLAYBOOKS/css_mobile.md`.
- `docs/harness/PLAYBOOKS/jinja.md`.

## Playbook relacionado

`css_mobile.md` y `jinja.md`.

## Fuente normativa

- [docs/ux.md](../../ux.md)
- [docs/pwa.md](../../pwa.md)

## Checklist antes de editar

- Drawer sigue siendo navegacion principal.
- No se duplican CTAs globales.
- No se rompen rutas existentes.
- Cambios acotados y mobile-first.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- `node --check` sobre cada JS tocado.

## Validaciones recomendadas

- Revision visual mobile.
- Smoke de rutas afectadas.

## Senales de alarma

- Solapes.
- Navegacion paralela.
- Cambio de service worker.
- Logica de negocio en navegador.

## Cuando pedir aprobacion humana

Si cambia service worker, rutas publicas, navegacion principal o flujo critico.

## Rollback

Revertir CSS/Jinja/JS y limpiar cache solo si se toco PWA con aprobacion.

## Criterios Done

- Mobile-first conservado.
- Drawer protegido.
- JS validado.

## Mini TASK_ENVELOPE

- Pantalla:
- Dispositivo objetivo:
- Archivos UI:
- JS tocado:
- Validaciones:
- Rollback:
