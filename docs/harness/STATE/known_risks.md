# Known Risks

- Drift PWA entre registro de service worker y cache.
- `app/main.py` sigue siendo monolito grande.
- Warning Starlette `TemplateResponse` en smoke tests.
- Facturacion, backups, auth, DB e informes son modulos criticos.
- Datos locales sensibles existen fuera del alcance de pruebas y auditorias.
- Carpeta anidada `sistema_pericial/` pendiente de decision humana.
