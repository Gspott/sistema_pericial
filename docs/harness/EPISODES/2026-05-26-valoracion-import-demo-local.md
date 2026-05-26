# Valoracion Import Demo Local

Fecha: 2026-05-26

## Objetivo

Importar los cinco casos demo ficticios de valoracion en la DB local de
desarrollo para poder verlos en el listado de expedientes.

## DB Detectada

`/Users/carlosblanco/sistema_pericial/data/pericial.db`

## Backup Previo

`/Users/carlosblanco/sistema_pericial/data/before_valoracion_demo_import_20260526_095549.sqlite`

## Comando Ejecutado

```bash
python3 scripts/create_valoracion_demo_cases.py --db /Users/carlosblanco/sistema_pericial/data/pericial.db --append --allow-project-db
```

El script se ejecuto dos veces:

- Primera ejecucion: creo 4 casos nuevos y detecto `DEMO-VAL-005` existente.
- Segunda ejecucion: completo `DEMO-VAL-005` porque era demo existente sin
  testigos vinculados.

## Verificacion

- Expedientes totales tras importacion: 36.
- Expedientes demo `DEMO-VAL-*`: 5.
- Expedientes no demo: 31.
- Todos los demo tienen `tipo_informe='valoracion'`.
- Todos tienen `valoracion_expediente`.
- Todos tienen 1 visita.
- Todos tienen 6 testigos vinculados.
- Todos tienen 6 ajustes.
- `DEMO-VAL-003` mantiene 0 resultados por ser el caso incompleto/problematico.
- Los otros cuatro casos tienen resultado borrador.

## Reversion

Con la app parada, restaurar la copia previa:

```bash
cp /Users/carlosblanco/sistema_pericial/data/before_valoracion_demo_import_20260526_095549.sqlite /Users/carlosblanco/sistema_pericial/data/pericial.db
```

## Seguridad

- No se borraron datos.
- No se tocaron uploads, informes, backups existentes ni secretos.
- Solo se creo un backup nuevo y se insertaron/completaron casos
  `DEMO-VAL-*`.
