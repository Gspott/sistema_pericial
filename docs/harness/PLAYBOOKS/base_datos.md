# Playbook: Base De Datos

## Que leer primero

- `docs/modelos_datos.md`.
- `docs/backend.md`.
- `app/database.py`.
- Modulo funcional afectado.

## Archivos sensibles

- `app/database.py`.
- Bases SQLite reales.
- Scripts de importacion.

## Acciones permitidas

- Anadir columnas con `asegurar_columna()` si esta justificado.
- Probar migraciones en copia temporal.
- Mantener compatibilidad con bases existentes.

## Acciones prohibidas

- Borrar columnas.
- Recrear tablas salvo decision explicita.
- Ejecutar migraciones sobre DB real.
- Cambiar tipos fiscales sin plan.

## Validaciones

- `python3 -m compileall app`.
- Inicializar DB temporal.
- Smoke del modulo afectado.

## Senales de alarma

- `DROP TABLE`.
- `DELETE FROM` amplio.
- Cambios en tablas fiscales, usuarios o backups.

## Rollback

- Revertir diff.
- Descartar DB temporal.
- Restaurar desde backup solo con aprobacion humana.

