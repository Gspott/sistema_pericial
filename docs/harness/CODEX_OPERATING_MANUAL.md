# Codex Operating Manual

## Obligatorio antes de tocar

1. Leer el harness aplicable.
2. Clasificar modulo y riesgo.
3. Rellenar mentalmente `templates/TASK_ENVELOPE.md`.
4. Elegir un `TASK_PACK` o justificar por que no aplica.
5. Elegir playbook.
6. Inspeccionar solo el contexto necesario.
7. Crear plan activo con `bash scripts/start_harness_task.sh SLUG TASK_PACK`.
8. Ejecutar diff minimo.
9. Validar y cerrar con `bash scripts/finish_harness_task.sh`.
10. Reportar alcance y no tocado.

## Reglas de conocimiento

- `AGENTS.md` es indice, no enciclopedia.
- Antes de tareas relevantes, leer `docs/harness/GOLDEN_PRINCIPLES.md`.
- Antes de actuar con autonomia, aplicar `docs/harness/EXECUTION_POLICY.md`.
- Antes de modificar un area funcional, consultar `docs/SOURCE_OF_TRUTH.md`.
- Si hay conflicto entre docs, aplicar la jerarquia de `docs/SOURCE_OF_TRUTH.md`.
- Los planes activos viven en `docs/harness/PLANS/active/` solo mientras la tarea esta en curso. La ruta canonica existente es `PLANS/` en mayusculas; no crear una estructura paralela `plans/` ni `TASKS/`.
- El conocimiento que Codex deba usar debe estar versionado en repo.
- Cuando una tarea revele una regla nueva, proponerla en la doc fuente correspondiente, no solo en el harness.
- Los mapas para agentes viven en `docs/harness/AGENT_MAPS/` y deben ser indices legibles, no copias completas del codigo.
- Antes de tareas grandes, revisar `docs/harness/BACKLOG/` y `docs/harness/STATE/`.
- Registrar fallos relevantes en `docs/harness/FAILURES/`.
- Reutilizar `docs/harness/PATTERNS/` antes de inventar estructuras nuevas.
- Antes de planificar una tarea real, elegir un `TASK_PACK` o justificar por que no aplica.
- Para tareas de valoracion inmobiliaria, preferir `docs/harness/TASK_PACKS/valoracion_change.md`; combinarlo con `db_change.md`, `informe_change.md` o `mobile_ui.md` si la fase toca esquema, outputs o UX sensible.
- Antes de tocar archivos en cualquier fase relevante, crear un plan en `docs/harness/PLANS/active/` con `bash scripts/start_harness_task.sh SLUG TASK_PACK`; el wrapper actualiza `docs/harness/STATE/current_plan.txt` con la ruta relativa del plan.
- `scripts/start_harness_task.sh` falla si ya hay un plan activo, salvo uso explicito de `--force`; no autocrear planes de forma silenciosa durante la validacion.
- Antes de cerrar tareas relevantes, ejecutar `bash scripts/validate_harness.sh`.
- Al cerrar una tarea validada con plan activo, preferir `bash scripts/finish_harness_task.sh`; valida el plan activo y delega en `validate_harness.sh`.
- Para tareas pequenas, se puede usar `--smoke-scope docs|app|valoracion|full`.
  El scope por defecto es `full`; `audit_docs` y `git diff --check` siguen
  siendo obligatorios en todos los scopes.
- Si `current_plan.txt` apunta a un plan activo, el runner lo cierra automaticamente tras validaciones exitosas.
- Usar `bash scripts/validate_harness.sh --close-plan <plan.md>` solo para cierre explicito; ese flag tiene prioridad sobre `current_plan.txt`.
- Si una tarea contradice un Golden Principle, pedir aprobacion humana antes de continuar.
- Si una tarea supera el nivel permitido por `EXECUTION_POLICY.md`, parar y pedir aprobacion humana.
- Ejecutar mantenimiento mensual del harness siguiendo `docs/harness/MAINTENANCE/monthly_review.md`.
- En toda tarea relevante, si las validaciones pasan y la tarea queda cerrada, mover el plan de `docs/harness/PLANS/active/` a `docs/harness/PLANS/completed/`.
- Actualizar `docs/harness/METRICS.md` cuando cambien planes activos, smoke tests, backlog o warnings.
- Si una tarea queda incompleta o bloqueada, mover el plan a `docs/harness/PLANS/blocked/` si esa carpeta existe. Si no existe, dejarlo en `active/` con `Estado: bloqueado`, bloqueo concreto y siguiente accion humana.
- Si fallan validaciones, el runner no cierra ningun plan.
- No cerrar una fase relevante sin plan registrado. `validate_harness.sh` debe bloquear cambios sin plan activo y mostrar el comando exacto `bash scripts/start_harness_task.sh SLUG TASK_PACK`.
- No usar cierre automatico si la tarea queda incompleta o requiere aprobacion humana pendiente; limpiar o corregir `current_plan.txt` antes de validar si hace falta.
- Al cerrar tareas relevantes con cambio real, crear un episodio breve con `python3 scripts/harness_episode.py <slug> --plan <plan.md>`.
- No crear episodio para cambios triviales sin valor historico.

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
