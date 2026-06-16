# Plan Quality

## Decision

Los planes completados son memoria historica, no simples marcadores de ejecucion.
Un plan creado con la plantilla actual solo puede cerrarse si contiene contenido
real en estas secciones:

- Objetivo.
- Modulo.
- Riesgo.
- Validaciones.
- Rollback.
- Fuera de alcance.
- Aprobacion humana requerida.

## Regla operativa

`scripts/harness_close_plan.py` valida el plan activo antes de moverlo a
`docs/harness/PLANS/completed/`. Si el plan sigue siendo una plantilla vacia,
el cierre falla con un mensaje que indica las secciones pendientes.

`scripts/audit_docs.py` revisa planes completados. Los artefactos sospechosos
con sufijos como `duplicate-plan` o `revalidation` fallan la auditoria si no
tienen contenido real. Los planes legacy incompletos se reportan como warning
para no romper compatibilidad historica.

## Rollback

Revertir `scripts/harness_plan_guard.py` y las integraciones en
`scripts/harness_close_plan.py` y `scripts/audit_docs.py`.
