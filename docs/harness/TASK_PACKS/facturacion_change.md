# Task Pack: Facturacion Change

## Cuando usarlo

Para facturacion, IVA, IRPF, propuestas a factura, rectificativas, Verifactu interno, cobros o exportaciones fiscales.

## Cuando NO usarlo

No usar para UI comercial no fiscal o textos sin impacto economico; usar `bugfix.md` o `mobile_ui.md` si procede.

## Riesgo base

Critico.

## Archivos normalmente permitidos

- `app/routers/facturacion.py` si esta aprobado.
- `app/services/verifactu.py` si esta aprobado.
- `app/services/exportaciones.py` si esta aprobado.
- Templates de facturacion si esta aprobado.
- Tests/smoke fiscales.

## Archivos normalmente prohibidos

- DB real.
- Facturas reales.
- `.env`.
- Backups reales.

## Lectura previa obligatoria

- `docs/harness/RISK_MAP.md`.
- `docs/harness/PLAYBOOKS/facturacion.md`.
- `docs/backend.md`.
- `docs/modelos_datos.md`.

## Playbook relacionado

`docs/harness/PLAYBOOKS/facturacion.md`.

## Checklist antes de editar

- Confirmar si cambia calculo, estado o numeracion.
- Preparar DB temporal.
- Identificar smoke fiscal.
- Definir rollback.

## Validaciones obligatorias

- `pytest tests/smoke -q`.
- `bash scripts/validate_harness.sh`.

## Validaciones recomendadas

- Tests especificos de calculo.
- Smoke de factura borrador en DB temporal.

## Senales de alarma

- Cambios en numeracion.
- Emision/anulacion/rectificativas.
- Hash, QR o Verifactu.
- Exportaciones fiscales.

## Cuando pedir aprobacion humana

Siempre que cambie numeracion, emision, anulacion, hash, exportaciones fiscales, rectificativas o calculos.

## Rollback

Revertir diff y descartar DB temporal. No restaurar DB real salvo proceso aprobado.

## Criterios Done

- Smoke fiscal pasa.
- No se ha tocado DB real.
- Cambios criticos tienen aprobacion.

## Mini TASK_ENVELOPE

- Objetivo fiscal:
- Calculo/estado afectado:
- Aprobacion humana:
- DB temporal:
- Smoke obligatorio:
- Rollback:

