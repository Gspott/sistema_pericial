# Harness Metrics

Metricas manuales para observar salud del harness sin introducir automatizacion prematura.

| Metrica | Valor actual | Fuente | Cadencia |
|---|---:|---|---|
| Smoke tests | 10 | `pytest tests/smoke -q` | Semanal |
| Tiempo aproximado de `validate_harness.sh` | < 5 s en entorno local habitual | `bash scripts/validate_harness.sh` | Semanal |
| Warnings activos | 2 | `python3 scripts/audit_docs.py` | Semanal |
| Tamano `app/main.py` | > 8000 lineas | `scripts/audit_docs.py` | Mensual |
| Task Packs existentes | 9 | `docs/harness/TASK_PACKS/` | Mensual |
| Docs normativos principales | 10 | `docs/SOURCE_OF_TRUTH.md` | Mensual |
| Planes activos | Revisar directorio | `docs/harness/PLANS/active/` | Semanal |
| Deuda tecnica abierta | Revisar tabla | `docs/harness/PLANS/tech_debt_tracker.md` | Mensual |
| Failures documentados | 3 | `docs/harness/FAILURES/` | Mensual |
| Patrones reutilizables | 5 | `docs/harness/PATTERNS/` | Mensual |
| Backlog por prioridad | critical: 0, high: 3, medium: 3, low: 0, icebox: 0 | `docs/harness/BACKLOG/` | Semanal |
| Warnings activos documentados | 2 | `docs/harness/STATE/known_risks.md` | Semanal |

## Warnings conocidos

- Drift PWA entre registro de service worker y cache.
- `app/main.py` supera el umbral informativo de monolito.

## Uso

- Actualizar valores cuando una fase cambie tests, warnings, planes o deuda.
- No perseguir metricas cosmeticas: medir solo lo que ayuda a operar con seguridad.
- Si una metrica requiere mucho mantenimiento manual, simplificarla.
