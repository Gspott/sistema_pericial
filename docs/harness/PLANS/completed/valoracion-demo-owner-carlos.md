# Valoracion Demo Owner Carlos

# Objetivo

Hacer visibles en la DB local de desarrollo los casos `DEMO-VAL-001` a
`DEMO-VAL-004` para el usuario real Carlos (`owner_user_id=1`).

# Modulo

Valoracion inmobiliaria / demo data local / SQLite local de desarrollo.

# Riesgo

Bajo-medio: escritura acotada en DB local autorizada por el usuario, con backup
previo y sin borrados.

# Archivos permitidos

`docs/harness/PLANS/active/valoracion-demo-owner-carlos.md`.

# Archivos prohibidos

App, templates, static, uploads, informes reales, secretos, routers legacy y
carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/demo_data.md`.

# Ejecucion

DB activa confirmada:

`/Users/carlosblanco/sistema_pericial/data/pericial.db`

Backup creado:

`/Users/carlosblanco/sistema_pericial/data/before_demo_owner_fix_20260526_100723.sqlite`

SQL equivalente ejecutado:

```sql
BEGIN;

UPDATE expedientes
SET owner_user_id = 1
WHERE numero_expediente IN (
    'DEMO-VAL-001', 'DEMO-VAL-002', 'DEMO-VAL-003', 'DEMO-VAL-004'
)
  AND owner_user_id = 2;

UPDATE testigos_valoracion
SET owner_user_id = 1
WHERE owner_user_id = 2
  AND id IN (
      SELECT vet.testigo_id
      FROM valoracion_expediente_testigos vet
      JOIN expedientes e ON e.id = vet.expediente_id
      WHERE e.numero_expediente IN (
          'DEMO-VAL-001', 'DEMO-VAL-002', 'DEMO-VAL-003', 'DEMO-VAL-004'
      )
  );

COMMIT;
```

Resultado:

- Expedientes actualizados: 4.
- Testigos actualizados: 24.
- Demos visibles para Carlos: 5.
- Expedientes no demo tras la fase: 31.


# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Con la app parada:

```bash
cp /Users/carlosblanco/sistema_pericial/data/before_demo_owner_fix_20260526_100723.sqlite /Users/carlosblanco/sistema_pericial/data/pericial.db
```

# Fuera de alcance

Cambios de logica, migraciones, borrados, uploads, informes reales, secretos,
routers legacy y carpeta anidada `sistema_pericial/`.

# Aprobacion humana requerida

Ya concedida en el prompt para esta DB local de desarrollo, con backup previo.

Estado: completado
