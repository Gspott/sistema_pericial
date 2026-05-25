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

