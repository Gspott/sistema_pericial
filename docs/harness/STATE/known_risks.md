# Known Risks

- `app/main.py` sigue siendo monolito grande.
- Facturacion, backups, auth, DB e informes son modulos criticos.
- Datos locales sensibles existen fuera del alcance de pruebas y auditorias.
- Carpeta anidada `sistema_pericial/` es sensible: contiene estructura de app, entorno local y carpetas de datos/generados; no tocar sin decision humana.
- Routers `expedientes`, `visitas`, `estancias` y `patologias` existen pero no estan incluidos en `app/main.py`; no asumir que son codigo muerto.
- Scripts remotos/Telegram/deploy (`start_remote_access.sh`, `stop_remote_access.sh`, `start_tunnel.sh`, `telegram_listener.py`, `update_server.sh`) no deben tocarse sin playbook y aprobacion humana.
