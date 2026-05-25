# Drift Detection

## Proposito

`scripts/audit_docs.py` detecta drift documental y estructural sin tocar datos reales ni ejecutar integraciones externas.

El objetivo es avisar pronto cuando la documentacion, el harness o la estructura de validacion dejan de coincidir con el estado real del repo.

## Drift detectado

- Enlaces Markdown rotos dentro de documentacion.
- Metadatos de decision invalidos.
- ADRs sin campos obligatorios.
- Documentos tematicos sin contrato minimo.
- Estructura minima de `docs/harness/`.
- Playbooks, goals, workflows y docs de validacion criticos.
- Task Packs criticos en `docs/harness/TASK_PACKS/`.
- Docs normativos basicos: `docs/SOURCE_OF_TRUTH.md`, `docs/facturacion.md` y `docs/gastos.md`.
- Enlaces desde Task Packs criticos a alguna fuente normativa.
- Principios dorados, mantenimiento y metricas del harness.
- Memoria operativa persistente: BACKLOG, STATE, FAILURES y PATTERNS.
- Enlaces obligatorios desde `AGENTS.md` al harness.
- Existencia de `pytest.ini`, `tests/smoke/` y referencia a smoke tests desde `scripts/validate_harness.sh`.
- Drift PWA entre version de registro en `static/pwa.js` y cache en `static/sw.js`.
- Tamano excesivo de `app/main.py` como warning informativo.

## Que no detecta

- Correctitud funcional de rutas.
- Reglas fiscales reales.
- Regresiones visuales mobile.
- Envio SMTP real.
- Playwright/PDF real.
- Integraciones externas.
- Calidad semantica completa de informes.
- Drift en datos reales o bases SQLite.

## Ejemplos del proyecto

- Historico resuelto: drift entre registro de service worker y cache PWA.
- `app/main.py` supera el umbral informativo de monolito.
- Smoke tests existen bajo `tests/smoke/` y el runner debe referenciarlos.

## Como extenderlo

- Preferir checks de existencia, enlaces y patrones estables.
- Separar errores bloqueantes de warnings informativos.
- No leer datos reales, `.env`, DB, backups, uploads, informes, fotos ni logs.
- No ejecutar integraciones externas.
- Mantener mensajes claros y accionables.
- Evitar falsos positivos por texto explicativo en docs.
