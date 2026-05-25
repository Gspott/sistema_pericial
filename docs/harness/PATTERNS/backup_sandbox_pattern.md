# Backup Sandbox Pattern

## Cuando Usarlo

Pruebas o cambios en backup/restore que necesitan verificar ZIP/TAR o rutas de salida sin tocar datos reales.

## Cuando NO Usarlo

- Restaurar backups reales.
- Mover, borrar o sobrescribir backups existentes.
- Probar sobre DB real.

## Estructura Recomendada

- Crear directorio temporal.
- Crear archivos demo sin datos sensibles.
- Forzar rutas mediante monkeypatch/env.
- Verificar estructura del backup, no contenido real.
- Eliminar solo temporales creados por el test.

## Riesgos

- Sobrescribir backup real.
- Filtrar datos sensibles.
- Confundir restore real con prueba sandbox.

## Validaciones

- `pytest tests/smoke/test_backup_zip.py -q`
- `pytest tests/smoke -q`
- `bash scripts/validate_harness.sh`

## Anti-Patrones

- Usar `backups/` real en tests.
- Leer uploads, informes o fotos reales.
- Ejecutar restore sin aprobacion humana.
