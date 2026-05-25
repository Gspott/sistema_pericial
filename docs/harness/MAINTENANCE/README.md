# Harness Maintenance

Rutina ligera para evitar entropia documental y mantener el harness util para Codex.

## Frecuencia

- Semanal: ejecutar [weekly_cleanup.md](weekly_cleanup.md).
- Mensual: ejecutar [monthly_review.md](monthly_review.md).
- Cuando una doc quede obsoleta: aplicar [dead_docs_policy.md](dead_docs_policy.md).

## Reglas

- Priorizar enlaces y consolidacion antes que crear documentos nuevos.
- No duplicar specs que ya vivan en `docs/`.
- Mantener `AGENTS.md` como indice corto.
- Cerrar planes activos o dejarlos con siguiente accion explicita.
- Registrar deuda real en [docs/harness/PLANS/tech_debt_tracker.md](../PLANS/tech_debt_tracker.md).

## Salida esperada

Cada mantenimiento debe dejar:

- Warnings actuales identificados.
- Planes activos revisados.
- Deuda tecnica actualizada si cambia.
- Docs obsoletas archivadas, fusionadas o enlazadas.
- Validacion documental ejecutada.
