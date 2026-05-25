# Goal: Seguridad Y Backups

## Objetivo

Proteger datos sensibles, secretos, backups y capacidad de recuperacion sin tocar datos reales por defecto.

## Tareas permitidas

- Auditorias de nombres de variables sensibles.
- Documentar procedimientos.
- Tests de backup con copia temporal.
- Checks de archivos sensibles trackeados.

## Tareas prohibidas

- Mostrar secretos completos.
- Borrar backups.
- Restaurar sobre DB real.
- Tocar carpetas externas.

## Criterios de terminado

- Riesgo identificado sin exponer valores.
- Procedimiento reproducible.
- Rollback claro.

## Validaciones obligatorias

- `git status --short`.
- Check de archivos sensibles trackeados.
- `bash -n` para scripts modificados.

