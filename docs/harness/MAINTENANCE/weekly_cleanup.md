# Weekly Cleanup

Checklist semanal de baja friccion.

## Pasos

1. Ejecutar `python3 scripts/audit_docs.py`.
2. Revisar warnings activos y confirmar si siguen siendo esperados.
3. Ejecutar `bash scripts/validate_harness.sh` si hubo cambios relevantes en la semana.
4. Revisar planes activos en `docs/harness/PLANS/active/`.
5. Cerrar, actualizar o dividir planes que ya no tengan siguiente accion clara.
6. Revisar drift PWA documentado entre `static/pwa.js` y `static/sw.js`.
7. Confirmar que `pytest tests/smoke -q` sigue dentro del runner.
8. Actualizar [docs/harness/METRICS.md](../METRICS.md) si cambian tests, warnings o deuda.

## Criterios Done

- Auditoria documental en estado OK o con warnings conocidos.
- Planes activos con estado comprensible.
- No hay tareas abandonadas sin propietario o siguiente accion.
- Los warnings nuevos quedan registrados o convertidos en plan.
