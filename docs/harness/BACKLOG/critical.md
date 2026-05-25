# Critical Backlog

Usar esta prioridad para tareas que puedan comprometer datos reales, secretos, autenticacion, facturacion fiscal, backups/restore o continuidad operativa inmediata.

## Formato

- Titulo:
- Impacto:
- Modulos:
- Riesgo:
- Task Pack recomendado:
- Validaciones minimas:
- Bloqueo/no bloqueo:
- Dependencias:

## Pendientes

## Revisar `.env.backup.smtp` Sin Exponer Secretos

- Impacto: posible presencia de credenciales SMTP o configuracion sensible en archivo local ignorado.
- Modulos: secretos, emails, seguridad operativa.
- Riesgo: Critico.
- Task Pack recomendado: `docs/harness/TASK_PACKS/email_change.md` y `docs/harness/PLAYBOOKS/secretos.md`.
- Validaciones minimas: no mostrar valores completos; `python3 scripts/audit_docs.py`; `git status --short`.
- Bloqueo/no bloqueo: Bloquea cualquier limpieza automatica de secretos.
- Dependencias: revision humana o procedimiento especifico de secretos.
