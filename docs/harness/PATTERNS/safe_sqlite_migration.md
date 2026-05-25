# Safe SQLite Migration

## Cuando Usarlo

Cambios pequenos de esquema compatibles hacia atras.

## Cuando NO Usarlo

- Borrado de columnas.
- Migraciones destructivas.
- Cambios sobre DB real.
- Cambios fiscales sin aprobacion.

## Estructura Recomendada

- Revisar `docs/modelos_datos.md`.
- Usar patron existente tipo `asegurar_columna()` si aplica.
- Probar solo sobre DB temporal o copia sandbox.
- Mantener compatibilidad con datos antiguos.

## Riesgos

- Perdida de datos.
- Esquema divergente entre entornos.
- Tests que pasan con DB vacia pero fallan con datos historicos.

## Validaciones

- `python3 -m compileall app`
- `pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`

## Anti-Patrones

- `DROP COLUMN` automatico.
- Migracion implicita sin plan.
- Leer o modificar DB real durante pruebas.
