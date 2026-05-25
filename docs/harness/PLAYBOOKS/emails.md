# Playbook: Emails

## Que leer primero

- `docs/backend.md`.
- `app/routers/emails.py`.
- `app/services/email_sender.py`.
- `app/services/email_templates.py`.
- `app/services/email_log.py`.

## Archivos sensibles

- `.env` y variantes.
- `app/services/email_sender.py`.
- `app/routers/emails.py`.
- Adjuntos subidos.

## Acciones permitidas

- Usar mock SMTP.
- Validar nombres de variables sin mostrar valores.
- Ajustar plantillas HTML/texto.
- Mejorar logs sin secretos.

## Acciones prohibidas

- Enviar correo real sin orden explicita.
- Mostrar contrasenas SMTP.
- Adjuntar rutas arbitrarias.
- Guardar MIME completo o adjuntos binarios en DB.

## Validaciones

- `python3 -m compileall app`.
- Prueba email mock.
- Validacion de adjunto y escape HTML.

## Senales de alarma

- Logs que imprimen credenciales.
- Cambios en SMTP SSL/STARTTLS.
- Cambios en limites de adjuntos.

## Rollback

- Revertir diff.
- Desactivar envio real y volver a mock.

