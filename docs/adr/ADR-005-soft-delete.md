# ADR-005 - Soft delete

Decision ID: DATA-002
Estado: Active
Categoria: Datos
Fecha/periodo: 2026-05
Fuente normativa: [docs/modelos_datos.md](../modelos_datos.md)

## Contexto

La biblioteca describe patologias genericas y debe conservar historico sin mostrar elementos inactivos como seleccionables.

## Decision

El soft delete aplica a biblioteca/catalogos mediante `activo`. Los registros de caso/visita pueden borrarse fisicamente si el flujo lo requiere.

## Consecuencias

- No aplicar soft delete global a registros de caso sin decision explicita.
- Las patologias inactivas no deben mostrarse como seleccionables.
- Mantener compatibilidad con datos antiguos.

## Impacta a

- [docs/modelos_datos.md](../modelos_datos.md)
- [docs/backend.md](../backend.md)
- [docs/ux.md](../ux.md)

## Sustituye / relacionado con

- Relacionado con ADR-004 rol final.
