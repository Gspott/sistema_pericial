# Diagnostico Demo Val 005

# Objetivo

Diagnosticar por que `DEMO-VAL-005` no parece aparecer en el listado de
expedientes, sin modificar datos.

# Modulo

Expedientes / demo data local / listado.

# Riesgo

Bajo: diagnostico de solo lectura sobre DB local autorizada por el usuario.

# Archivos permitidos

Solo este plan activo del harness.

# Archivos prohibidos

App, templates, static, DB writes, uploads, informes reales, backups, secretos,
routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/debug.md`.

# Hallazgo

DB activa: `/Users/carlosblanco/sistema_pericial/data/pericial.db`.

`DEMO-VAL-005` existe en `expedientes`:

- `id=20`
- `owner_user_id=1`
- `tipo_informe='valoracion'`
- `cliente='DEMO Inversiones Levante SL'`
- `direccion='Passeig Marítim 18'`

Comparacion:

- `DEMO-VAL-001`: `id=35`, `owner_user_id=1`
- `DEMO-VAL-002`: `id=36`, `owner_user_id=1`
- `DEMO-VAL-003`: `id=37`, `owner_user_id=1`
- `DEMO-VAL-004`: `id=38`, `owner_user_id=1`
- `DEMO-VAL-005`: `id=20`, `owner_user_id=1`

La consulta real de `/expedientes` es:

```sql
SELECT *
FROM expedientes
WHERE owner_user_id=?
ORDER BY id DESC;
```

Por tanto `DEMO-VAL-005` aparece mas abajo, entre expedientes antiguos, no junto
a `DEMO-VAL-001..004`.

El HTML servido confirma:

- `/expedientes` contiene `DEMO-VAL-005`.
- `/?q=DEMO-VAL-005` devuelve el expediente directamente.


# Validaciones

- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

No aplica a datos; no se ejecutaron escrituras.

# Fuera de alcance

Cambiar orden del listado, renumerar expedientes, actualizar DB o modificar UI.

# Aprobacion humana requerida

No requerida para diagnostico de solo lectura autorizado.

Estado: completado
