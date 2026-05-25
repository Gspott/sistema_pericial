# Playbook: Deploy / Acceso Remoto

## Que leer primero

- `docs/despliegue.md`.
- `docs/backend.md`.
- Scripts de arranque solo si son necesarios.
- `deploy/Caddyfile` si aplica.

## Archivos sensibles

- `.env` y variantes.
- `start_all.sh`.
- `start_server.sh`.
- `stop_all.sh`.
- `status.sh`.
- `scripts/update_duckdns.sh`.
- `deploy/Caddyfile`.

## Acciones permitidas

- Leer documentacion.
- Validar sintaxis shell con `bash -n`.
- Proponer cambios sin aplicarlos si afectan exposicion externa.

## Acciones prohibidas

- Cambiar DuckDNS/Caddy sin aprobacion.
- Abrir puertos o tuneles.
- Mostrar tokens.
- Ejecutar deploy real.

## Validaciones

- `bash -n start_all.sh start_server.sh stop_all.sh status.sh backup.sh backup_now.sh`.
- `git diff --check`.

## Senales de alarma

- Cambios en host, puerto o `BASE_URL`.
- Comandos que inician servicios externos.
- Tokens en logs o docs.

## Rollback

- Revertir diff.
- Detener servicios solo si la tarea los arranco con autorizacion.

