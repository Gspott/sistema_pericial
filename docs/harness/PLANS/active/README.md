# Active Plans

Los planes activos viven aqui solo mientras una tarea esta en curso. Ninguna tarea validada y cerrada debe permanecer en este directorio.

## Como crear un plan activo

1. Crear un archivo con nombre descriptivo y fecha si ayuda: `YYYY-MM-DD-modulo-objetivo.md`.
2. Incluir objetivo, modulo, riesgo, archivos permitidos, archivos prohibidos, playbook, validaciones y rollback.
3. Mantener el plan pequeno y actualizable.
4. No mezclar modulos criticos no relacionados.
5. Cerrar o archivar el plan al terminar la tarea.

## Cierre obligatorio

- Si las validaciones pasan y la tarea queda cerrada, mover el plan a `../completed/`.
- Si la tarea queda incompleta, dejar el plan en `active/` con estado pendiente claro y siguiente accion.
- Actualizar `../tech_debt_tracker.md` o `../../METRICS.md` si cambia deuda, planes activos, smoke tests o warnings.

## Plantilla recomendada

Usar [../../templates/TASK_ENVELOPE.md](../../templates/TASK_ENVELOPE.md) como base.

## Reglas

- Un plan activo no autoriza por si mismo tocar datos reales.
- `active/` no es archivo historico; solo contiene trabajo en curso.
- Si aparece una regla nueva, actualizar `docs/harness/` o proponerlo.
- Si requiere aprobacion humana, seguir [../../WORKFLOWS/diff_approval.md](../../WORKFLOWS/diff_approval.md).
