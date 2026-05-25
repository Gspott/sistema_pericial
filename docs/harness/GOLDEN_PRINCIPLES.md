# Golden Principles

Reglas nucleo para mantener a Codex dentro de un margen operativo seguro. Si una tarea contradice un principio, debe pedir aprobacion humana antes de continuar.

1. Nunca tocar DB real, backups reales, uploads, informes, fotos, logs ni datos generados sin orden explicita.
2. Mantener cada diff minimo, reversible y limitado al objetivo aprobado.
3. Toda tarea relevante termina con `bash scripts/validate_harness.sh`.
4. Toda tarea real usa un `TASK_PACK` o justifica por que no aplica.
5. [docs/SOURCE_OF_TRUTH.md](../SOURCE_OF_TRUTH.md) manda ante conflicto documental.
6. PDF y DOCX comparten fuente de datos; no duplicar logica de informe.
7. No borrar columnas ni datos en migraciones automaticas.
8. No emitir, anular ni rectificar facturas sin validacion y aprobacion humana.
9. No introducir SPA, React, Vue, Angular, PostgreSQL ni arquitectura SaaS.
10. No crear navegacion paralela que compita con drawer/hamburguesa.
11. No mostrar, copiar ni registrar secretos completos.
12. No enviar emails reales salvo orden explicita.
13. No usar backups reales para pruebas; usar sandbox o copia temporal.
14. El repo versionado es la fuente de verdad que Codex puede reutilizar.
15. Plan cerrado y validado no permanece en `PLANS/active/`.
16. Si aparece una invariante nueva, documentarla o proponerla en la fuente normativa.
