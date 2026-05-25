# Validation Runner

## Proposito

`scripts/validate_harness.sh` es el runner recomendado para validar el sistema de forma segura antes de cerrar tareas relevantes.

No arranca servidor persistente, no instala paquetes, no envia emails, no usa Playwright real y no debe tocar datos reales.

## Uso

Validacion normal:

```bash
bash scripts/validate_harness.sh
```

La validacion normal cierra automaticamente el plan indicado en `docs/harness/STATE/current_plan.txt` si existe en `docs/harness/PLANS/active/` y todas las validaciones pasan. Si las validaciones fallan, no cierra ningun plan.

Validacion y cierre mecanico explicito de plan, solo si todo pasa:

```bash
bash scripts/validate_harness.sh --close-plan nombre-del-plan.md
```

El cierre con `--close-plan` tiene prioridad sobre `current_plan.txt`, mueve el plan desde `docs/harness/PLANS/active/` a `docs/harness/PLANS/completed/` y despues actualiza metricas con `scripts/harness_metrics.py`.

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

Si `pytest` no esta instalado, el runner marca los smoke tests como `[SKIP]` y explica como habilitarlos mediante dependencias del proyecto.

## Automatizacion de planes y metricas

Crear plan activo:

```bash
python3 scripts/harness_new_plan.py smoke-tests-emails email_change
make new-plan NAME=smoke-tests-emails PACK=email_change
```

Al crear el plan, el script escribe el nombre del archivo en `docs/harness/STATE/current_plan.txt`.

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

## Que detecta

- Drift documental cubierto por `scripts/audit_docs.py`.
- Drift estructural indirecto cubierto por `scripts/audit_docs.py`: harness incompleto, enlaces obligatorios de `AGENTS.md`, smoke tests no referenciados, drift PWA y warnings de monolito.
- Errores sintacticos Python en `app/` y `tests/`.
- Errores sintacticos JS en shell/PWA/service worker.
- Fallos de smoke tests cuando `pytest` esta instalado.
- Problemas de whitespace en el diff.

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
