# Active Plans

Los planes activos viven aqui mientras una tarea amplia esta en curso.

## Como crear un plan activo

1. Crear un archivo con nombre descriptivo y fecha si ayuda: `YYYY-MM-DD-modulo-objetivo.md`.
2. Incluir objetivo, modulo, riesgo, archivos permitidos, archivos prohibidos, playbook, validaciones y rollback.
3. Mantener el plan pequeno y actualizable.
4. No mezclar modulos criticos no relacionados.
5. Cerrar o archivar el plan al terminar la tarea.

## Plantilla recomendada

Usar [../../templates/TASK_ENVELOPE.md](../../templates/TASK_ENVELOPE.md) como base.

## Reglas

- Un plan activo no autoriza por si mismo tocar datos reales.
- Si aparece una regla nueva, actualizar `docs/harness/` o proponerlo.
- Si requiere aprobacion humana, seguir [../../WORKFLOWS/diff_approval.md](../../WORKFLOWS/diff_approval.md).

