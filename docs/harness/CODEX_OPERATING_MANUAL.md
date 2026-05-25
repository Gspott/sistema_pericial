# Codex Operating Manual

## Obligatorio antes de tocar

1. Leer el harness aplicable.
2. Clasificar modulo y riesgo.
3. Rellenar mentalmente `templates/TASK_ENVELOPE.md`.
4. Elegir un `TASK_PACK` o justificar por que no aplica.
5. Elegir playbook.
6. Inspeccionar solo el contexto necesario.
7. Hacer plan corto.
8. Ejecutar diff minimo.
9. Validar.
10. Reportar alcance y no tocado.

## Reglas de conocimiento

- `AGENTS.md` es indice, no enciclopedia.
- Antes de tareas relevantes, leer `docs/harness/GOLDEN_PRINCIPLES.md`.
- Antes de modificar un area funcional, consultar `docs/SOURCE_OF_TRUTH.md`.
- Si hay conflicto entre docs, aplicar la jerarquia de `docs/SOURCE_OF_TRUTH.md`.
- Los planes activos viven en `docs/harness/PLANS/active/` solo mientras la tarea esta en curso.
- El conocimiento que Codex deba usar debe estar versionado en repo.
- Cuando una tarea revele una regla nueva, proponerla en la doc fuente correspondiente, no solo en el harness.
- Los mapas para agentes viven en `docs/harness/AGENT_MAPS/` y deben ser indices legibles, no copias completas del codigo.
- Antes de tareas grandes, revisar `docs/harness/BACKLOG/` y `docs/harness/STATE/`.
- Registrar fallos relevantes en `docs/harness/FAILURES/`.
- Reutilizar `docs/harness/PATTERNS/` antes de inventar estructuras nuevas.
- Antes de planificar una tarea real, elegir un `TASK_PACK` o justificar por que no aplica.
- Al iniciar una tarea con plan, preferir `python3 scripts/harness_new_plan.py <slug> [task_pack]`.
- Antes de cerrar tareas relevantes, ejecutar `bash scripts/validate_harness.sh`.
- Al cerrar una tarea validada con plan activo, preferir `bash scripts/validate_harness.sh --close-plan <plan.md>`.
- Si una tarea contradice un Golden Principle, pedir aprobacion humana antes de continuar.
- Ejecutar mantenimiento mensual del harness siguiendo `docs/harness/MAINTENANCE/monthly_review.md`.
- En toda tarea con plan activo, si las validaciones pasan y la tarea queda cerrada, mover el plan de `docs/harness/PLANS/active/` a `docs/harness/PLANS/completed/`.
- Actualizar `docs/harness/METRICS.md` cuando cambien planes activos, smoke tests, backlog o warnings.
- Si una tarea queda incompleta, dejar el plan en `active/` con estado pendiente claro y siguiente accion.
- No usar cierre automatico si la tarea queda incompleta o requiere aprobacion humana pendiente.

## Reglas de actuacion

- No resolver fuera de alcance sin permiso.
- No ampliar refactors porque el archivo este cerca.
- No tocar datos reales.
- No mostrar secretos completos.
- No modificar modulos criticos sin playbook.
- Si una tarea requiere aprobacion humana, parar y presentar formato de `WORKFLOWS/diff_approval.md`.

## Cierre obligatorio

La respuesta final debe incluir:

- Explicacion breve.
- Archivos modificados.
- Cambios exactos.
- Validaciones ejecutadas y resultado.
- Riesgos o compatibilidad.
- Confirmacion de lo que no se ha tocado.
