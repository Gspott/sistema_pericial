# Weekly Cleanup

Checklist semanal de baja friccion.

## Pasos

1. Ejecutar `python3 scripts/audit_docs.py`.
2. Revisar warnings activos y confirmar si siguen siendo esperados.
3. Ejecutar `bash scripts/validate_harness.sh` si hubo cambios relevantes en la semana.
4. Ejecutar `make metrics`.
5. Revisar planes activos en `docs/harness/PLANS/active/`; `audit_docs.py` avisa si alguno parece cerrado.
6. Cerrar, actualizar o dividir planes que ya no tengan siguiente accion clara.
7. Revisar drift PWA documentado entre `static/pwa.js` y `static/sw.js`.
8. Confirmar que `pytest tests/smoke -q` sigue dentro del runner.
9. Actualizar [docs/harness/METRICS.md](../METRICS.md) si cambian tests, warnings o deuda no cubierta por metricas generadas.

## Criterios Done

- Auditoria documental en estado OK o con warnings conocidos.
- Planes activos con estado comprensible.
- No hay tareas abandonadas sin propietario o siguiente accion.
- Los warnings nuevos quedan registrados o convertidos en plan.
