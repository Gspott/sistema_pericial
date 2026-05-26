# Validation Runner

## Proposito

`scripts/validate_harness.sh` es el runner recomendado para validar el sistema de forma segura antes de cerrar tareas relevantes.

No arranca servidor persistente, no instala paquetes, no envia emails, no usa Playwright real y no debe tocar datos reales.

## Uso

Validacion normal:

```bash
bash scripts/validate_harness.sh
```

La validacion normal usa `--smoke-scope full` por defecto, cierra
automaticamente el plan indicado en `docs/harness/STATE/current_plan.txt` si
existe en `docs/harness/PLANS/active/` y todas las validaciones pasan. Si las
validaciones fallan, no cierra ningun plan.

Si hay cambios en el worktree y `current_plan.txt` no apunta a un plan activo,
el runner falla. Esto evita cerrar fases con diffs sin plan registrado.

Validacion y cierre mecanico explicito de plan, solo si todo pasa:

```bash
bash scripts/validate_harness.sh --close-plan nombre-del-plan.md
```

El cierre con `--close-plan` tiene prioridad sobre `current_plan.txt`, mueve el plan desde `docs/harness/PLANS/active/` a `docs/harness/PLANS/completed/` y despues actualiza metricas con `scripts/harness_metrics.py`.

Validacion con scope:

```bash
bash scripts/validate_harness.sh --smoke-scope valoracion
bash scripts/finish_harness_task.sh --smoke-scope valoracion
```

El runner resuelve un scope minimo a partir de `git status --porcelain`. Si el
scope pedido es inferior al requerido, lo eleva automaticamente:

```text
[INFO] required_scope=valoracion
[AUTO-UPGRADE] requested_scope=docs insufficient; using scope=valoracion
```

Para saltarse la elevacion existe `--allow-unsafe-scope`; solo debe usarse con
justificacion explicita porque puede cerrar una fase con cobertura inferior a la
heuristica:

```bash
bash scripts/finish_harness_task.sh --smoke-scope docs --allow-unsafe-scope
```

Scopes disponibles:

- `docs`: cambios solo documentales. Ejecuta auditoria documental y whitespace;
  salta compilacion, JS y smoke con mensajes `[SKIP]`.
- `app`: cambios pequenos de app sin smoke especifico. Ejecuta auditoria,
  compilacion Python/JS y whitespace; salta smoke con `[SKIP]`.
- `valoracion`: cambios acotados de valoracion. Ejecuta auditoria,
  compilacion Python/JS, `pytest tests/smoke -q -k valoracion` y whitespace.
- `full`: comportamiento por defecto. Ejecuta toda la suite smoke.

`audit_docs` y `git diff --check` son obligatorios en todos los scopes. Los
scopes no deben usarse para ocultar fallos conocidos ni para cerrar fases
criticas con cobertura insuficiente.

## Smart Dependency Scopes

Reglas actuales del resolver:

- Solo `docs/**`, `AGENTS.md`, `agents.md` o `README.md`: scope requerido
  `docs`.
- `templates/valoracion*`, `tests/smoke/test_valoracion*`,
  `tests/fixtures/valoracion*`, `scripts/create_valoracion_demo_cases.py` o
  `app/services/informe.py`: minimo `valoracion`.
- `static/**`: minimo `app`.
- `app/database.py`, backups, uploads, auth/session/login/password,
  `templates/informes/`, `templates/propuestas/`, PDF/DOCX o routers: `full`.
- Otros cambios en `app/**`, `templates/**` o `tests/**`: minimo `app`.

Limites:

- Es una heuristica por paths, no un analizador de dependencias.
- Ante duda o cambio transversal, usar `full`.
- El resolver no elimina validaciones criticas ni crea planes.

## Comandos ejecutados

```bash
test -d docs/harness
python3 scripts/audit_docs.py
python3 -m compileall app
python3 -m compileall tests
node --check ./static/app_shell.js
node --check static/pwa.js
node --check static/sw.js
pytest tests/smoke -q
git diff --check
```

Con `--smoke-scope valoracion`, el comando de smoke cambia a:

```bash
pytest tests/smoke -q -k valoracion
```

Si `pytest` no esta instalado, el runner marca los smoke tests como `[SKIP]` y explica como habilitarlos mediante dependencias del proyecto.

## Automatizacion de planes y metricas

Crear plan activo:

```bash
bash scripts/start_harness_task.sh smoke-tests-emails email_change
python3 scripts/harness_new_plan.py smoke-tests-emails email_change
make new-plan NAME=smoke-tests-emails PACK=email_change
```

El wrapper recomendado es `scripts/start_harness_task.sh`. Crea el plan,
rechaza pisar otro plan activo salvo `--force` y escribe la ruta relativa en
`docs/harness/STATE/current_plan.txt`.

Cierre recomendado:

```bash
bash scripts/finish_harness_task.sh
```

Este wrapper valida que existe plan activo y delega en
`scripts/validate_harness.sh`, que cierra el plan solo si todo pasa.

Actualizar metricas:

```bash
python3 scripts/harness_metrics.py
make metrics
```

Cerrar plan manualmente, sin ejecutar validaciones:

```bash
python3 scripts/harness_close_plan.py smoke-tests-emails.md
make close-plan PLAN=smoke-tests-emails.md
```

Preferir `bash scripts/validate_harness.sh --close-plan ...` cuando una tarea queda validada.
Preferir `bash scripts/validate_harness.sh` cuando `current_plan.txt` apunta al plan correcto.

Crear episodio:

```bash
python3 scripts/harness_episode.py smoke-tests-emails --plan smoke-tests-emails.md
make episode NAME=smoke-tests-emails PLAN=smoke-tests-emails.md
```

`validate_harness.sh` no crea episodios automaticamente todavia. El episodio se crea de forma explicita cuando la tarea tiene valor historico.

## Que detecta

- Drift documental cubierto por `scripts/audit_docs.py`.
- Drift estructural indirecto cubierto por `scripts/audit_docs.py`: harness incompleto, enlaces obligatorios de `AGENTS.md`, smoke tests no referenciados, drift PWA y warnings de monolito.
- Errores sintacticos Python en `app/` y `tests/`.
- Errores sintacticos JS en shell/PWA/service worker.
- Fallos de smoke tests cuando `pytest` esta instalado.
- Problemas de whitespace en el diff.
- Cambios de worktree sin plan activo cerrable.

Cuando detecta cambios sin plan activo, falla con el comando exacto para crear
uno. El runner no autocrea planes silenciosamente.

## Que no detecta

- Integraciones externas reales.
- Envio SMTP real.
- Playwright/PDF real.
- Restauracion de backups reales.
- Regresiones visuales mobile.
- Errores que dependan de datos reales.

## Como extenderlo

- Anadir solo checks deterministas y rapidos.
- Mantener cada paso con mensaje claro `[STEP]`, `[OK]`, `[FAIL]` o `[SKIP]`.
- No instalar dependencias automaticamente.
- No arrancar servicios persistentes.
- No usar red salvo autorizacion explicita.
- Mantener los tests de persistencia sobre DB temporal.
- No automatizar aprobaciones humanas ni cerrar tareas incompletas.

## Reglas para nuevas validaciones

- Deben poder ejecutarse desde la raiz del repo.
- Deben fallar rapido si hay regresion.
- Deben documentar dependencias extra.
- Deben evitar datos reales, secretos, backups reales e integraciones externas.
