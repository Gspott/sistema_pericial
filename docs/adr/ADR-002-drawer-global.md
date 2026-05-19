# ADR-002 - Drawer global

Decision ID: UX-002
Estado: Active
Categoria: UX
Fecha/periodo: 2026-05
Fuente normativa: [docs/ux.md](../ux.md)

## Contexto

El sistema elimina ruido visual y evita duplicar CTAs globales en dashboard, home y listados.

## Decision

El drawer global `+` se reserva para altas globales. Los CTAs contextuales solo se mantienen si aportan pre-relleno, dependen del registro actual o reducen pasos reales.

## Consecuencias

- No anadir acciones globales duplicadas en listados.
- Mantener CTAs contextuales cuando aporten contexto real.
- El drawer no convierte facturacion, IVA, gastos o backups en acciones principales de visita.

## Impacta a

- [docs/ux.md](../ux.md)
- [docs/pwa.md](../pwa.md)

## Sustituye / relacionado con

- Relacionado con ADR-001 navegacion principal.
