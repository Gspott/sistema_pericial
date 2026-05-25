# Episode: Legacy Dead Code Audit

## Fecha

2026-05-25

## Tarea

Auditoria solo lectura de legacy, codigo muerto, duplicados y elementos
sospechosos.

## Plan asociado

No se creo plan activo porque la auditoria se solicito en modo solo lectura y
sin modificar archivos.

## Task Pack usado

bugfix, como referencia de tarea segura y reversible.

## Objetivo

Persistir hallazgos de auditoria para futuras sesiones de Codex sin borrar ni
modificar codigo, datos reales, secretos, backups, uploads, informes, fotos o
logs.

## Archivos modificados

- `docs/harness/EPISODES/2026-05-25-legacy-dead-code-audit.md`
- `docs/harness/FAILURES/nested_sistema_pericial_folder.md`
- `docs/harness/BACKLOG/critical.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/BACKLOG/medium.md`
- `docs/harness/BACKLOG/low.md`
- `docs/harness/STATE/known_risks.md`
- `docs/harness/METRICS.md`

## Validaciones ejecutadas

- Pendiente de cierre: `python3 scripts/audit_docs.py`
- Pendiente de cierre: `bash scripts/validate_harness.sh`
- Pendiente de cierre: `git diff --check`
- Pendiente de cierre: `git status --short`

## Resultado

La auditoria detecto carpeta anidada sensible, posible archivo de backup SMTP,
routers no incluidos que solapan `app/main.py`, parciales legacy y artefactos
locales/generados.

## Warnings

- No leer `.env.backup.smtp`; puede contener secretos.
- No tocar `sistema_pericial/`; contiene estructura de app, `.venv`, DB y
  carpetas de datos/generados.
- No asumir que routers no incluidos estan muertos; pueden ser extracciones
  parciales.

## Rollback

Revertir solo las entradas documentales de harness creadas en este episodio.

## Memoria actualizada

- Backlog por prioridad.
- Known risks.
- Failure dedicado a carpeta anidada.
- Metricas manuales.

## Decisiones humanas

Pendiente decidir destino de `sistema_pericial/`, tratamiento de
`.env.backup.smtp` y estrategia de routers no incluidos.

## Proximos pasos

Crear fases separadas para secretos, carpeta anidada y mapa `app/main.py` vs
routers.
