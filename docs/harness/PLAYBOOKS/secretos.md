# Playbook: Secretos

## Que leer primero

- `docs/harness/PERMISSIONS.md`.
- `.gitignore`.
- `.env.example`.
- Documentacion de despliegue.

## Archivos sensibles

- `.env`.
- `.env.*`.
- Tokens DuckDNS/Telegram.
- Credenciales SMTP.
- `SESSION_SECRET_KEY`.
- API keys.

## Acciones permitidas

- Enumerar nombres de variables.
- Confirmar si archivos sensibles estan trackeados con `git ls-files`.
- Recomendar rotacion sin mostrar valores.

## Acciones prohibidas

- Mostrar valores completos.
- Copiar secretos a docs.
- Subir secretos a git.
- Probar credenciales reales sin orden.

## Validaciones

- `git ls-files | rg '(^|/)(\\.env|.*\\.db|data/|uploads/|informes/|fotos/|backups/|logs/)|\\.sqlite|\\.sqlite3|\\.tar\\.gz|\\.zip' || true`.
- `git status --short`.

## Senales de alarma

- `.env` trackeado.
- Backups que incluyen `.env`.
- Logs con tokens o passwords.

## Rollback

- Si se expone un secreto, parar, informar sin repetirlo y recomendar rotacion.

