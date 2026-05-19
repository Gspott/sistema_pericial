# ADR-001 - Navegacion principal

Decision ID: UX-001
Estado: Active
Categoria: UX
Fecha/periodo: 2026-05
Fuente normativa: [docs/ux.md](../ux.md)

## Contexto

El proyecto usa una experiencia mobile first orientada a iPhone durante visitas reales. La navegacion debe ser clara y no competir con acciones duplicadas.

## Decision

La navegacion principal activa es hamburguesa izquierda + drawer. `_top_nav.html` queda como patron secundario/legacy.

## Consecuencias

- No reintroducir navegacion paralela que compita con el drawer.
- Usar `_top_nav.html` solo donde ya exista o se indique expresamente.
- Revisar UX y PWA si se modifica navegacion.

## Impacta a

- [docs/ux.md](../ux.md)
- [docs/pwa.md](../pwa.md)

## Sustituye / relacionado con

- Relacionado con ADR-002 drawer global.
