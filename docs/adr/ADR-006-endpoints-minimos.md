# ADR-006 - Endpoints minimos

Decision ID: API-001
Estado: Active
Categoria: Backend
Fecha/periodo: 2026-05
Fuente normativa: [docs/backend.md](../backend.md)

## Contexto

El backend actua como coordinador ligero y convive con automatizaciones externas ya funcionales.

## Decision

Se permiten endpoints FastAPI minimos para disparar flujos existentes. No crear APIs de negocio paralelas ni endpoints que reimplementen logica ya existente.

## Consecuencias

- Priorizar integraciones desacopladas y flujos existentes.
- Evitar workers, colas o microservicios salvo peticion explicita.
- Revisar seguridad, ownership y validacion de rutas.

## Impacta a

- [docs/backend.md](../backend.md)
- [docs/pwa.md](../pwa.md)
- [docs/modelos_datos.md](../modelos_datos.md)

## Sustituye / relacionado con

- Relacionado con patrones de automatizacion externa documentados en backend.
