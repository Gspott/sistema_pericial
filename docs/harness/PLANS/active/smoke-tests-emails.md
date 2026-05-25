# Smoke Tests Emails

## Objetivo

Añadir cobertura smoke segura para emails sin enviar correos reales ni usar SMTP real.

## Modulo

Emails, SMTP mock y adjuntos simulados.

## Riesgo

Alto por sensibilidad SMTP, mitigado con monkeypatch, entorno aislado y sin red.

## Archivos Permitidos

- `tests/smoke/test_email_mock.py`
- `docs/harness/BACKLOG/medium.md`
- `docs/harness/STATE/recent_changes.md`
- `docs/harness/METRICS.md`
- `docs/harness/PLANS/active/smoke-tests-emails.md`

## Archivos Prohibidos

- `.env`
- Credenciales SMTP
- DB real
- Adjuntos reales
- Backups, uploads, informes, fotos, logs y secretos

## Playbook Aplicable

- `docs/harness/TASK_PACKS/email_change.md`
- `docs/harness/PLAYBOOKS/emails.md`

## Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m compileall tests`
- `python3 -m pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`
- `git diff --check`
- `git status --short`

## Cobertura Añadida

- Imports seguros de router y servicio email.
- Construccion MIME con adjunto demo en memoria.
- Preparacion de adjunto simulado sin leer rutas reales.
- Bloqueo de envio cuando SMTP no esta configurado.
- Fallo SMTP simulado sin exponer password en logs.

## Rollback

Eliminar el test nuevo y revertir las notas de memoria operativa.

## Fuera De Alcance

- Envio real.
- SMTP real.
- Cambios en configuracion.
- Cambios en plantillas corporativas.
- Refactor de router o servicio email.

## Aprobacion Humana Requerida

Requerida si se propone usar SMTP real, leer `.env`, tocar credenciales, enviar emails o adjuntar archivos reales.
