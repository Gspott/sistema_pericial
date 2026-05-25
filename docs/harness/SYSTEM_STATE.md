# System State

## Estado real

Sistema Pericial es una aplicacion local privada para gestion pericial, comercial, documental y fiscal. No es SaaS y no debe tratarse como producto multi-tenant.

Stack real:

- FastAPI.
- Jinja2 server-side rendering.
- SQLite local.
- HTML/CSS mobile-first.
- JavaScript minimo y progresivo.

## Arquitectura observada

- `app/main.py` sigue siendo el nucleo historico grande de la aplicacion. Concentra expedientes, visitas, patologias, autenticacion, PWA e informes legacy.
- `app/routers/` contiene routers comerciales y fiscales ya existentes: leads, clientes, propuestas, emails, facturacion, gastos, backups, dashboard y partes de expedientes/visitas/estancias/patologias.
- `app/services/` contiene servicios de informes, propuestas, email, backups, exportaciones, Catastro, clima, Verifactu e importacion/extraccion de gastos.
- `templates/` contiene vistas Jinja operativas.
- `static/mobile.css`, `static/app_shell.js`, `static/pwa.js` y `static/sw.js` soportan la UX mobile-first y PWA.

## Datos fuera de alcance

Los datos reales quedan fuera de alcance salvo autorizacion humana explicita. Esto incluye:

- `.env` y variantes.
- Bases SQLite reales.
- `uploads/`.
- `informes/`.
- `fotos/`.
- `logs/`.
- `backups/`.
- Archivos generados por la aplicacion.

## Zonas delicadas

- Facturacion, emision, anulacion, rectificativas, numeracion fiscal y Verifactu.
- Autenticacion, sesiones y cookies.
- Backups, restore y borrado de backups.
- Informes PDF/DOCX y fuente unica `build_informe_context()`.
- PWA/service worker por impacto en cache movil.
- Deploy, DuckDNS, Caddy, tuneles y acceso remoto.
- Carpeta anidada `sistema_pericial/`, considerada zona delicada y no editable hasta decision humana.

## Drift conocido

Existe drift PWA documentado:

- `static/pwa.js` registra el service worker con query de version `v=4`.
- `static/sw.js` usa cache `sistema-pericial-` + `v5`.

No corregir automaticamente sin playbook PWA/mobile y aprobacion si afecta service worker.

## Tests

No existe actualmente suite `pytest` ni tests de humo consolidados. Cualquier cambio critico debe proponer o crear validacion minima antes de tocar logica.
