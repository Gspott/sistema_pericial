# Playbook: Backups / Restore

## Que leer primero

- `docs/recovery.md`.
- `docs/RESTORE.md`.
- `docs/RECOVERY_CHECKLIST.md`.
- `app/services/backups.py`.
- `app/routers/backups.py`.

## Archivos sensibles

- Backups reales.
- DB real.
- `uploads/`, `informes/`, `fotos/`, `logs/`.
- Scripts `backup*.sh`.

## Acciones permitidas

- Documentar procedimiento.
- Crear backup solo si el usuario lo ordena.
- Validar restore en copia temporal.
- Revisar nombres de archivos sin abrir contenido sensible.

## Acciones prohibidas

- Borrar backups.
- Restaurar sobre DB real.
- Leer documentos/fotos reales.
- Cambiar alcance del backup sin aprobacion.

## Validaciones

- `bash -n backup.sh backup_now.sh`.
- Prueba de backup en entorno temporal si se autoriza.
- Listado de zip sin extraer datos sensibles.

## Senales de alarma

- `unlink`, `rm`, `DELETE` o restore directo.
- Backups fuera del repo.
- Inclusion accidental de `.env`.

## Rollback

- Revertir diff.
- Conservar backups existentes.
- Restaurar solo con checklist humano.

