# Task Pack: Bugfix

## Cuando usarlo

Para bugs pequenos, reversibles y localizados.

## Cuando NO usarlo

No usar para facturacion fiscal, autenticacion, backups, DB real, deploy, service worker o cambios de rutas publicas.

## Riesgo base

Medio.

## Archivos normalmente permitidos

- Archivo funcional concreto del bug.
- Test relacionado.
- Documentacion minima si cambia criterio operativo.

## Archivos normalmente prohibidos

- DB real.
- `.env`.
- Backups, uploads, informes, fotos y logs.
- Modulos criticos no relacionados.

## Lectura previa obligatoria

- `AGENTS.md`.
- `docs/harness/RISK_MAP.md`.
- Playbook del modulo afectado.

## Playbook relacionado

Playbook del modulo tocado.

## Fuente normativa

- [docs/SOURCE_OF_TRUTH.md](../../SOURCE_OF_TRUTH.md)

## Checklist antes de editar

- Bug reproducido o entendido.
- Archivo y funcion acotados.
- Rollback claro.
- Sin impacto fiscal/auth/backup.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- Validacion especifica del modulo.

## Validaciones recomendadas

- Smoke test del flujo afectado.
- `python3 -m compileall app` si toca Python.

## Senales de alarma

- El bug exige tocar varios modulos.
- Aparecen datos reales.
- Cambia comportamiento publico.

## Cuando pedir aprobacion humana

Si el bug afecta datos reales, fiscalidad, auth, backups, deploy o rutas publicas.

## Rollback

Revertir diff del bug y descartar datos temporales.

## Criterios Done

- Bug cubierto por validacion.
- Diff pequeno.
- No hay cambios fuera de alcance.

## Mini TASK_ENVELOPE

- Objetivo:
- Modulo:
- Riesgo:
- Archivos permitidos:
- Playbook:
- Validaciones:
- Rollback:
