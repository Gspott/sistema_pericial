# Execution Policy

Politica de autonomia para Codex en Sistema Pericial.

Esta politica no sustituye `PERMISSIONS.md`, `RISK_MAP.md`,
`GOLDEN_PRINCIPLES.md` ni los `TASK_PACKS`; los convierte en reglas de
ejecucion diaria.

## Principio Base

Codex puede avanzar solo cuando el alcance es pequeno, reversible, validable y
no toca datos reales ni decisiones humanas criticas.

Cuando haya duda razonable sobre seguridad, datos, fiscalidad, autenticacion,
deploy o borrado, Codex debe parar y pedir aprobacion humana.

## Niveles De Autonomia

| Nivel | Significado | Ejemplos |
|---|---|---|
| Permitido automatico | Puede ejecutarse sin aprobacion humana si respeta el alcance. | Crear/cerrar planes, actualizar metricas, crear episodios, actualizar backlog, documentar hallazgos, ejecutar auditoria documental. |
| Permitido con validacion | Puede implementarse si hay rollback claro y validaciones obligatorias. | Smoke tests, drift documental, fixes pequenos reversibles, ajustes documentales, tests sandbox. |
| Requiere aprobacion | Codex debe parar y presentar plan/diff previsto antes de tocar. | Facturacion fiscal, auth, DB real, deploy, emails reales, Verifactu, backups reales, `include_router()`, refactors grandes. |
| Prohibido | No se ejecuta salvo instruccion humana explicita y excepcional. | Borrar archivos, tocar DB real, mostrar secretos completos, migraciones destructivas automaticas, `git reset/rebase/clean`, leer datos generados reales. |

## Permitido Automatico

Codex puede hacer automaticamente:

- Crear planes activos con `bash scripts/start_harness_task.sh SLUG TASK_PACK`.
- Cerrar planes validados con `scripts/validate_harness.sh` cuando el runner pase.
- Actualizar `docs/harness/METRICS.md`.
- Crear episodios para cambios con valor historico.
- Actualizar backlog, known risks, failures y patterns con hallazgos verificados.
- Ejecutar `python3 scripts/audit_docs.py`.
- Ejecutar `bash scripts/validate_harness.sh` si la tarea no toca datos reales.
- Crear o ajustar documentacion del harness.
- Detectar drift documental y registrarlo.

## Permitido Con Validacion

Codex puede hacer sin aprobacion previa, pero con validacion obligatoria:

- Smoke tests sobre SQLite temporal.
- Tests mock/dry-run sin integraciones externas.
- Fixes pequenos y reversibles en codigo no critico.
- Ajustes de documentacion normativa cuando el usuario lo pida.
- Correcciones de warnings no funcionales si el diff es minimo.

Condiciones:

- Debe existir rollback razonable.
- Debe ejecutarse `bash scripts/validate_harness.sh`.
- Debe ejecutarse smoke flow relevante si existe.
- Debe reportarse exactamente que no se toco fuera de alcance.

## Requiere Aprobacion Humana

Codex debe pedir aprobacion antes de:

- Leer, tocar o migrar DB real.
- Hacer migraciones destructivas o borrar columnas.
- Leer o modificar secretos.
- Cambiar deploy, Caddy, DuckDNS, tuneles, puertos o scripts remotos.
- Enviar emails reales.
- Tocar Verifactu real, numeracion, emision, anulacion o rectificativas.
- Borrar archivos.
- Hacer `include_router()` de routers legacy/no incluidos.
- Hacer refactors grandes o mover rutas publicas.
- Cambiar autenticacion, sesiones, cookies o usuarios.
- Cambiar pagos, fiscalidad, calculos fiscales o exportaciones.
- Usar backups reales o restore real.

## Prohibido Por Defecto

Codex no debe:

- Leer `.env` ni mostrar valores completos de secretos.
- Leer DB real, backups, uploads, informes, fotos o logs.
- Tocar la carpeta anidada `sistema_pericial/`.
- Ejecutar comandos destructivos.
- Instalar dependencias sin orden explicita.
- Ejecutar servidor persistente si no es necesario para la tarea.
- Usar red real salvo orden explicita.
- Encadenar varias tareas criticas sin confirmacion humana entre ellas.

## Politica De Parada

Codex debe parar si:

- Fallan smoke tests o `validate_harness.sh`.
- Detecta un riesgo no documentado.
- Aparece ambiguedad estructural.
- Hay datos reales en el camino de ejecucion.
- Hay conflicto entre `docs/SOURCE_OF_TRUTH.md` y otra documentacion.
- No existe rollback razonable.
- El cambio requiere aprobacion y no fue concedida.
- El diff crece fuera del alcance inicial.

Al parar, debe explicar:

- Que bloqueo encontro.
- Que archivos estan implicados.
- Que validacion fallo o que riesgo se detecto.
- Que decision humana necesita.
- Cual seria el rollback.

## Politica Backlog

- Priorizar `critical` > `high` > `medium` > `low`.
- Preferir tareas pequenas, reversibles y validables.
- No ejecutar backlog completo sin orden humana.
- No encadenar tareas criticas automaticamente.
- Convertir una tarea de backlog en plan activo solo cuando haya objetivo,
  alcance, task pack y validaciones.
- Toda fase relevante con cambios debe empezar con
  `bash scripts/start_harness_task.sh SLUG TASK_PACK` antes de tocar archivos.
  No se debe depender del prompt ni cerrar la fase solo con episodio, backlog o
  resumen de chat.
- Si la fase termina OK, el plan debe quedar en
  `docs/harness/PLANS/completed/`.
- Si la fase queda bloqueada, mover el plan a `docs/harness/PLANS/blocked/`
  solo si existe; si no existe, dejarlo en `docs/harness/PLANS/active/` con
  estado bloqueado y siguiente decision humana.
- Si una tarea revela deuda nueva, registrar backlog en la prioridad adecuada,
  no resolverla por impulso.

## Politica Legacy

- No activar routers legacy/no incluidos con `include_router()` sin plan,
  smoke tests y aprobacion humana.
- Consultar `docs/harness/AGENT_MAPS/main_vs_routers_map.md` antes de tocar
  expedientes, visitas, estancias o patologias.
- No tocar la carpeta anidada `sistema_pericial/`.
- No tocar scripts remotos, Telegram, deploy o DuckDNS sin playbook y
  aprobacion humana.
- No borrar parciales legacy hasta confirmar referencias, uso real y rollback.

## Politica De Validacion

- `bash scripts/validate_harness.sh` es obligatorio antes de cerrar tareas
  relevantes.
- `bash scripts/finish_harness_task.sh` es el cierre recomendado cuando hay un
  plan activo en `docs/harness/STATE/current_plan.txt`.
- El runner admite `--smoke-scope docs|app|valoracion|full`; `full` es el
  comportamiento por defecto y debe usarse ante duda, fases criticas o cambios
  transversales.
- El runner calcula `required_scope` por paths modificados y eleva
  automaticamente scopes insuficientes. `--allow-unsafe-scope` solo puede usarse
  si el plan documenta por que la heuristica sobredimensiona la validacion.
- `validate_harness.sh` debe fallar si detecta cambios sin plan activo
  cerrable; no debe autocrear planes silenciosamente.
- El smoke flow relevante es obligatorio cuando exista.
- `python3 scripts/audit_docs.py` es el primer check documental.
- `git diff --check` debe pasar.
- Si se modifica JS, ejecutar `node --check` del archivo afectado o el runner.
- Si se modifica Python, ejecutar `python3 -m compileall` del area afectada o
  el runner.
- Crear episodio si hubo cambio real con valor historico.

## Politica De Aprendizaje

Codex no debe depender solo del chat.

La memoria reutilizable vive en:

- `docs/SOURCE_OF_TRUTH.md` para jerarquia normativa.
- `docs/harness/FAILURES/` para fallos y riesgos reutilizables.
- `docs/harness/PATTERNS/` para patrones de implementacion.
- `docs/harness/BACKLOG/` para trabajo pendiente.
- `docs/harness/EPISODES/` para trazas de tareas reales.
- `docs/harness/STATE/` para estado operativo rapido.

Si aparece una regla nueva:

- Proponerla o registrarla en la fuente normativa adecuada.
- Enlazarla desde harness si afecta a operacion de Codex.
- Evitar crear una capa nueva si basta con actualizar una existente.
