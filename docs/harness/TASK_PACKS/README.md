# Task Packs

Los Task Packs son paquetes operativos para elegir rapidamente como trabajar una tarea real sin repetir prompts largos.

## Como elegir pack

1. Identificar modulo y riesgo en `docs/harness/RISK_MAP.md`.
2. Elegir el pack mas especifico que aplique.
3. Si varios aplican, gana el de mayor riesgo.
4. Rellenar mentalmente o por escrito `docs/harness/templates/TASK_ENVELOPE.md`.
5. Leer el playbook relacionado.
6. Ejecutar validaciones; el pack no sustituye validaciones.

## Prioridad si varios aplican

1. `facturacion_change.md`
2. `backup_restore_change.md`
3. `db_change.md`
4. `email_change.md`
5. `informe_change.md`
6. `mobile_ui.md`
7. `safe_refactor.md`
8. `bugfix.md`

## Relacion con TASK_ENVELOPE

Cada pack incluye una mini plantilla especifica. Para tareas medianas o criticas, crear plan activo en `docs/harness/PLANS/active/` usando `TASK_ENVELOPE.md`.

## Relacion con playbooks

El pack decide el tipo de tarea y el nivel de riesgo. El playbook explica el procedimiento concreto por modulo.

## Regla

Antes de planificar una tarea real, elegir un Task Pack o justificar por que no aplica.

