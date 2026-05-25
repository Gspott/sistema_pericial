# Task Pack: DB Change

## Cuando usarlo

Para cambios de esquema, columnas, migraciones defensivas o persistencia.

## Cuando NO usarlo

No usar para consultas simples sin cambio de esquema salvo que afecten datos criticos.

## Riesgo base

Critico.

## Archivos normalmente permitidos

- `app/database.py` si esta aprobado.
- Tests con DB temporal.
- Documentacion de modelos.

## Archivos normalmente prohibidos

- DB real.
- Backups reales.
- Migraciones destructivas.

## Lectura previa obligatoria

- `docs/modelos_datos.md`.
- `docs/backend.md`.
- `docs/harness/PLAYBOOKS/base_datos.md`.

## Playbook relacionado

`docs/harness/PLAYBOOKS/base_datos.md`.

## Checklist antes de editar

- Nunca borrar columnas.
- Usar `asegurar_columna()` o patron existente.
- Probar solo sobre DB temporal/copia.
- Definir compatibilidad con bases existentes.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- Inicializacion DB temporal.

## Validaciones recomendadas

- Smoke del modulo que usa la columna.

## Senales de alarma

- `DROP TABLE`.
- `DELETE FROM` amplio.
- Defaults incompatibles.
- Cambios en tablas fiscales o usuarios.

## Cuando pedir aprobacion humana

Para cualquier migracion destructiva, recreacion de tabla, cambio fiscal o cambio auth.

## Rollback

Revertir diff. Descartar DB temporal.

## Criterios Done

- DB temporal inicializa.
- Bases existentes siguen compatibles.
- Sin operaciones destructivas.

## Mini TASK_ENVELOPE

- Tabla:
- Columna/cambio:
- Patron:
- DB temporal:
- Compatibilidad:
- Rollback:

