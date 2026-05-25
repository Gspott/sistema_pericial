# Codex Operating Manual

## Obligatorio antes de tocar

1. Leer el harness aplicable.
2. Clasificar modulo y riesgo.
3. Rellenar mentalmente `templates/TASK_ENVELOPE.md`.
4. Elegir playbook.
5. Inspeccionar solo el contexto necesario.
6. Hacer plan corto.
7. Ejecutar diff minimo.
8. Validar.
9. Reportar alcance y no tocado.

## Reglas de conocimiento

- `AGENTS.md` es indice, no enciclopedia.
- Los planes activos viven en `docs/harness/PLANS/active/`.
- El conocimiento que Codex deba usar debe estar versionado en repo.
- Cuando una tarea revele una regla nueva, actualizar `docs/harness/` o proponerlo.
- Los mapas para agentes viven en `docs/harness/AGENT_MAPS/` y deben ser indices legibles, no copias completas del codigo.
- Antes de cerrar tareas relevantes, ejecutar `bash scripts/validate_harness.sh`.

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
