# Completed Plans

Los planes completados se archivan aqui cuando la tarea ya esta validada, cerrada y no requiere accion inmediata.

## Como cerrar un plan

1. Confirmar archivos tocados.
2. Registrar validaciones ejecutadas.
3. Anotar riesgos residuales.
4. Indicar rollback disponible o razon por la que ya no aplica.
5. Mover el plan desde `active/` a `completed/`.

## Criterios de archivo

- La tarea esta cerrada.
- No quedan validaciones pendientes.
- La respuesta final o el plan documenta que validaciones pasaron.
- `docs/harness/METRICS.md` esta actualizado si cambiaron planes activos, smoke tests, backlog o warnings.
- Las decisiones permanentes se han movido a ADR o documentacion normativa.
- La deuda restante se ha pasado a [../tech_debt_tracker.md](../tech_debt_tracker.md).
