# Gobernanza documental

## Proposito

La documentacion es una capa arquitectonica del sistema. Su funcion es mantener decisiones, limites, impactos y reglas operativas para que los cambios humanos o asistidos por IA sean pequenos, trazables y coherentes.

`AGENTS.md` es la puerta de entrada normativa. Los documentos en `/docs` contienen detalle tematico. Los ADRs registran decisiones estables.

## Estados formales de decision

- Proposed
- Active
- Experimental
- Deprecated
- Replaced
- Legacy
- Pending validation

## Ownership conceptual

Los dominios de ownership son conceptuales, no personales:

- UX
- PWA
- Datos
- Informes
- Revision probatoria
- Backend
- Operaciones
- IA workflow

## Definition of Done documental

Ver `## Definition of Done documental` en [AGENTS.md](../AGENTS.md).

Un cambio documental debe revisar impacto cruzado, documentos afectados, decisiones activas, ADRs relacionadas, anti-patrones, checklist correspondiente, changelog si cambia una decision y sincronizacion `AGENTS.md` / `agents.md` si aplica.

## Reglas de migracion documental

Ver `## Reglas de migracion documental` en [AGENTS.md](../AGENTS.md).

Toda regla nueva debe tener ubicacion normativa clara, estado de madurez, Decision ID cuando afecte arquitectura/UX/datos/informes/PWA/backend, impactos declarados y documentos tematicos actualizados.

## Gestion de decisiones

Toda decision relevante debe tener:

- Decision ID.
- Titulo.
- Estado.
- Categoria.
- Fuente normativa.
- Impacto.
- Fecha o periodo de consolidacion.
- Decision sustituida si aplica.

Las decisiones activas deben vivir en el documento tematico que sea fuente normativa. `AGENTS.md` las resume; los ADRs las fijan como registro historico.

## Reglas anti-drift

- No duplicar reglas normativas extensas.
- No crear documentos huerfanos.
- No dejar decisiones sin estado.
- No usar sinonimos ambiguos para conceptos canonicos.
- No modificar comportamiento sin actualizar documentacion.
- No dejar `AGENTS.md` y `agents.md` desincronizados.
- No crear Decision ID nuevo si solo se esta referenciando una decision existente.

## Freeze del core normativo

Estas secciones de `AGENTS.md` deben cambiar poco:

- Canon actual del proyecto.
- Reglas invariantes.
- Anti-patrones.

Cualquier cambio sobre ellas debe:

- Justificarse con ADR.
- Actualizar `docs/changelog.md`.
- Revisar impacto cruzado.
- Ejecutar `python3 scripts/audit_docs.py`.

## Documentacion operacional

- Recuperacion y restauracion: [docs/recovery.md](recovery.md).
- Despliegue y operaciones: [docs/operations.md](operations.md).
