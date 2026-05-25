# Monthly Review

Revision mensual para mantener el harness pequeno, vigente y verificable.

## Pasos

1. Revisar [docs/harness/PLANS/tech_debt_tracker.md](../PLANS/tech_debt_tracker.md).
2. Revisar si algun `TASK_PACK` quedo obsoleto o demasiado generico.
3. Revisar docs huerfanas o solapadas con [docs/SOURCE_OF_TRUTH.md](../../SOURCE_OF_TRUTH.md).
4. Confirmar que `app/main.py` sigue tratado como riesgo estructural, no como refactor libre.
5. Revisar specs normativas: backend, modelos, informes, UX, PWA, facturacion y gastos.
6. Revisar warnings recurrentes del runner y decidir si son deuda aceptada o trabajo planificado.
7. Actualizar [docs/harness/METRICS.md](../METRICS.md).

## Criterios Done

- Deuda tecnica abierta clasificada.
- Specs normativas principales siguen enlazadas desde `docs/SOURCE_OF_TRUTH.md`.
- Task Packs siguen apuntando a fuentes normativas reales.
- No se crean docs nuevas sin necesidad clara.
