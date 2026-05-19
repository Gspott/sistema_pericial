# ADR-004 - Rol final

Decision ID: DATA-001
Estado: Active
Categoria: Datos
Fecha/periodo: 2026-05
Fuente normativa: [docs/modelos_datos.md](../modelos_datos.md)

## Contexto

El informe y los helpers deben resolver de forma consistente el rol tecnico de patologias, respetando ajustes puntuales del registro.

## Decision

La formula canonica es:

```python
rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca
```

## Consecuencias

- No usar formulas alternativas.
- En exteriores, normalizar queries o usar acceso defensivo si no existe `rol_patologia_observado`.
- Informes y revision probatoria deben usar el mismo criterio.

## Impacta a

- [docs/modelos_datos.md](../modelos_datos.md)
- [docs/informes.md](../informes.md)
- [docs/revision_probatoria.md](../revision_probatoria.md)

## Sustituye / relacionado con

- Relacionado con ADR-005 soft delete por compartir dominio de datos.
