# ADR-007 - Generacion manual de informe

Decision ID: INF-001
Estado: Active
Categoria: Informes
Fecha/periodo: 2026-05
Fuente normativa: [docs/informes.md](../informes.md)

## Contexto

La revision probatoria orienta la captura de evidencia, pero el informe debe poder generarse manualmente de forma tolerante a datos faltantes.

## Decision

La generacion de informe es manual y debe seguir disponible, aunque no sea CTA recomendada cuando falten datos probatorios.

## Consecuencias

- No usar generacion de informe como siguiente accion automatica durante visita si faltan datos.
- Mantener checklist de PDF/DOCX cuando se toque informe.
- La revision puede advertir sin bloquear.

## Impacta a

- [docs/informes.md](../informes.md)
- [docs/revision_probatoria.md](../revision_probatoria.md)
- [docs/ux.md](../ux.md)

## Sustituye / relacionado con

- Relacionado con ADR-003 revision probatoria.
