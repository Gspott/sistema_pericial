# Task Pack: Email Change

## Cuando usarlo

Para SMTP, plantillas email, adjuntos, registro de emails o flujo de propuesta por email.

## Cuando NO usarlo

No usar para cambios de propuesta sin envio o para facturacion fiscal.

## Riesgo base

Alto.

## Archivos normalmente permitidos

- `app/routers/emails.py` si esta aprobado.
- `app/services/email_sender.py` si esta aprobado.
- `app/services/email_templates.py` si esta aprobado.
- `app/services/email_log.py` si esta aprobado.
- Tests con mock/dry-run.

## Archivos normalmente prohibidos

- `.env`.
- Credenciales SMTP.
- Adjuntos reales.
- Envio real sin orden explicita.

## Lectura previa obligatoria

- `docs/backend.md`.
- `docs/harness/PLAYBOOKS/emails.md`.
- `docs/harness/PLAYBOOKS/secretos.md`.

## Playbook relacionado

`docs/harness/PLAYBOOKS/emails.md`.

## Checklist antes de editar

- No mostrar credenciales.
- Mock o dry-run obligatorio.
- Adjuntos controlados.
- Logs sin secretos.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- Test/mock de email si cambia envio.

## Validaciones recomendadas

- Validar HTML/texto.
- Validar limite y nombre de adjunto.

## Senales de alarma

- SMTP real.
- Passwords en logs.
- Adjuntos desde rutas arbitrarias.

## Cuando pedir aprobacion humana

Para envio real, cambios SMTP, adjuntos sensibles o cambios en plantilla corporativa critica.

## Rollback

Revertir diff y volver a mock/dry-run.

## Criterios Done

- No se envio email real.
- No se expusieron secretos.
- Mock pasa.

## Mini TASK_ENVELOPE

- Tipo de email:
- SMTP real: no/si aprobado
- Mock/dry-run:
- Adjuntos:
- Validaciones:
- Rollback:

