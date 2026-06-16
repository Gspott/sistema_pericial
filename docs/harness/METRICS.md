# Harness Metrics

Metricas manuales para observar salud del harness sin introducir automatizacion prematura.

| Metrica | Valor actual | Fuente | Cadencia |
|---|---:|---|---|
| Smoke tests | 22 | `pytest tests/smoke -q` | Semanal |
| Tiempo aproximado de `validate_harness.sh` | < 5 s en entorno local habitual | `bash scripts/validate_harness.sh` | Semanal |
| Warnings activos | 1 | `python3 scripts/audit_docs.py` | Semanal |
| Tamano `app/main.py` | > 8000 lineas | `scripts/audit_docs.py` | Mensual |
| Task Packs existentes | 8 | `docs/harness/TASK_PACKS/` | Mensual |
| Politicas de ejecucion | 1 | `docs/harness/EXECUTION_POLICY.md` | Mensual |
| Docs normativos principales | 10 | `docs/SOURCE_OF_TRUTH.md` | Mensual |
| Planes activos | 1 | `docs/harness/PLANS/active/` | Semanal |
| Deuda tecnica abierta | Revisar tabla | `docs/harness/PLANS/tech_debt_tracker.md` | Mensual |
| Failures documentados | 5 | `docs/harness/FAILURES/` | Mensual |
| Patrones reutilizables | 5 | `docs/harness/PATTERNS/` | Mensual |
| Episodios | 4 | `docs/harness/EPISODES/` | Mensual |
| Backlog por prioridad | critical: 1, high: 5, medium: 3, low: 3, icebox: 0 | `docs/harness/BACKLOG/` | Semanal |
| Warnings activos documentados | 1 | `docs/harness/STATE/known_risks.md` | Semanal |

## Warnings conocidos

- `app/main.py` supera el umbral informativo de monolito.

## Uso

- Actualizar valores cuando una fase cambie tests, warnings, planes o deuda.
- No perseguir metricas cosmeticas: medir solo lo que ayuda a operar con seguridad.
- Si una metrica requiere mucho mantenimiento manual, simplificarla.

## Métricas generadas

| Metrica | Valor |
|---|---|
| Smoke tests | 154 |
| Planes activos | 1 |
| Planes completados | 86 |
| Failures documentados | 5 |
| Patterns reutilizables | 10 |
| Task Packs | 10 |
| Episodios | 52 |
| Warning monolito | WARNING: app/main.py tiene 17552 lineas |
| Warning PWA | OK |
