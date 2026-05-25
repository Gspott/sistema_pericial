# Validation Runner

## Proposito

`scripts/validate_harness.sh` es el runner recomendado para validar el sistema de forma segura antes de cerrar tareas relevantes.

No arranca servidor persistente, no instala paquetes, no envia emails, no usa Playwright real y no debe tocar datos reales.

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

## Reglas para nuevas validaciones

- Deben poder ejecutarse desde la raiz del repo.
- Deben fallar rapido si hay regresion.
- Deben documentar dependencias extra.
- Deben evitar datos reales, secretos, backups reales e integraciones externas.
