# Episodes

Trazas breves de ejecuciones reales de Codex. Sirven para revisar que paso en una tarea sin depender del chat.

## Cuando crear un episodio

- Cambios reales en codigo, tests, scripts o harness.
- Tareas con validaciones relevantes.
- Incidentes, warnings o decisiones que conviene recordar.

## Cuando NO crear un episodio

- Cambios triviales sin valor historico.
- Ediciones puramente mecanicas sin riesgo.
- Tareas incompletas que ya tienen plan activo claro.

## Reglas

- Mantener cada episodio breve y factual.
- No incluir secretos, datos reales ni contenido sensible.
- Enlazar plan, Task Pack o validaciones cuando ayude.
- No sustituye `PLANS/`, `FAILURES/`, ADRs ni changelog.

## Crear episodio

```bash
python3 scripts/harness_episode.py smoke-tests-emails --plan smoke-tests-emails.md
make episode NAME=smoke-tests-emails PLAN=smoke-tests-emails.md
```
