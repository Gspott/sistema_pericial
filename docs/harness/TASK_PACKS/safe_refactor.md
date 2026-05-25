# Task Pack: Safe Refactor

## Cuando usarlo

Para refactors pequenos con equivalencia de comportamiento.

## Cuando NO usarlo

No usar para facturacion, auth, backups, DB, deploy o informes criticos sin pack especifico.

## Riesgo base

Alto.

## Archivos normalmente permitidos

- Archivo objetivo acotado.
- Tests que demuestran equivalencia.

## Archivos normalmente prohibidos

- Multiples modulos criticos.
- DB real.
- Cambios de comportamiento.

## Lectura previa obligatoria

- `docs/harness/RISK_MAP.md`.
- Playbook del modulo.
- Tests existentes o smoke aplicable.

## Playbook relacionado

Playbook del modulo afectado.

## Checklist antes de editar

- Definir comportamiento preservado.
- Limitar diff.
- Tener validacion antes/despues.
- Evitar cambios cosmeticos mezclados.

## Validaciones obligatorias

- `pytest tests/smoke -q`.
- `bash scripts/validate_harness.sh`.

## Validaciones recomendadas

- Test especifico del helper extraido.

## Senales de alarma

- Cambia salida observable.
- Aumenta alcance.
- Toca fiscalidad/auth/backups.

## Cuando pedir aprobacion humana

Si el refactor toca modulos criticos o requiere cambiar contratos publicos.

## Rollback

Revertir diff completo.

## Criterios Done

- Misma conducta.
- Smoke tests pasan.
- Diff limitado.

## Mini TASK_ENVELOPE

- Codigo objetivo:
- Equivalencia esperada:
- Tests:
- Riesgo:
- Rollback:

