# Task Pack: Backup / Restore Change

## Cuando usarlo

Para backups, restore, descarga, borrado o alcance de copias.

## Cuando NO usarlo

No usar para validaciones que solo leen documentacion de recovery.

## Riesgo base

Critico.

## Archivos normalmente permitidos

- `app/services/backups.py` si esta aprobado.
- `app/routers/backups.py` si esta aprobado.
- Scripts `backup*.sh` si esta aprobado.
- Tests sandbox.

## Archivos normalmente prohibidos

- Backups reales.
- DB real.
- Uploads, informes, fotos y logs reales.
- `.env`.

## Lectura previa obligatoria

- `docs/recovery.md`.
- `docs/RESTORE.md`.
- `docs/RECOVERY_CHECKLIST.md`.
- `docs/harness/PLAYBOOKS/backups_restore.md`.

## Playbook relacionado

`docs/harness/PLAYBOOKS/backups_restore.md`.

## Fuente normativa

- [docs/RESTORE.md](../../RESTORE.md)
- [docs/RECOVERY_CHECKLIST.md](../../RECOVERY_CHECKLIST.md)

## Checklist antes de editar

- Usar solo sandbox/copia.
- No borrar backups.
- No restaurar sobre DB real.
- Verificar que `.env` no se incluye.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- Backup sandbox si cambia alcance.

## Validaciones recomendadas

- Listar contenido zip sin extraer datos sensibles.
- Restore en copia temporal si aplica.

## Senales de alarma

- `unlink`, `rm`, restore directo.
- Inclusion de secretos.
- Rutas fuera del repo.

## Cuando pedir aprobacion humana

Para restaurar, borrar, mover backups reales o cambiar alcance de backup.

## Rollback

Revertir diff. Conservar backups existentes.

## Criterios Done

- Sandbox verificado.
- Ningun backup real tocado.
- Rollback claro.

## Mini TASK_ENVELOPE

- Operacion backup/restore:
- Sandbox:
- Rutas prohibidas:
- Aprobacion humana:
- Validaciones:
- Rollback:
