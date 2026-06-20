# Autosave Patologias Registros 1

# Objetivo

Extender el estandar AUTOSAVE-STANDARD-1 a las pantallas de edicion de
registros de patologias interiores y exteriores, reutilizando la
infraestructura comun existente y manteniendo el guardado manual como
fallback.

El paquete debe ser pequeno, reversible y autocontenido dentro del rollout
AUTOSAVE-ROLLOUT-1.

# Modulo

Patologias / registros ya persistidos:

- Edicion de registros interiores: `templates/editar_registro.html`.
- Edicion de registros exteriores: `templates/editar_registro_exterior.html`.

Inventario afectado:

- Interiores: estancia, patologia, rol observado, elemento, localizacion,
  detalle de localizacion y observaciones.
- Exteriores: zona exterior, elemento exterior, localizacion exterior,
  patologia y observaciones.

Los formularios de alta de patologias no se incluyen porque todavia no existe
registro persistido sobre el que aplicar autosave seguro.

# Riesgo

Medio. Son pantallas de inspeccion con campos largos y uso en campo, pero el
cambio se limita a autosave sobre entidades existentes. No se introducen
migraciones ni se modifica el flujo manual de guardado.

Las tablas no disponen de `updated_at`; la concurrencia se resolvera con un
token equivalente calculado sobre los campos editables y devuelto bajo el
contrato estandar `updated_at`.

# Archivos permitidos

- `app/main.py`
- `templates/editar_registro.html`
- `templates/editar_registro_exterior.html`
- `tests/smoke/test_autosave_patologias_registros.py`
- `docs/harness/PLANS/active/autosave-patologias-registros-1.md`
- Episodio harness correspondiente.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos y logs.
- Migraciones o cambios de esquema.
- CRM, costes, propuestas, estancias, cuadrantes/mapas y refactors generales.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- Smoke especifico de patologias/registros.
- `bash scripts/finish_harness_task.sh` o `bash scripts/validate_harness.sh`
- `git diff --check`

# Rollback

Retirar los atributos `data-autosave-*`, el include del estado visual y el
script comun de las dos plantillas; retirar los endpoints de autosave y helpers
de token especificos; retirar el smoke especifico. El guardado manual queda
intacto en todo momento.

# Fuera de alcance

- Altas de nuevas patologias sin registro persistido.
- Fotos y borrado de fotos.
- Estancias.
- Cuadrantes/mapas.
- CRM, costes, propuestas y otros formularios largos.
- Migraciones de datos historicos.

# Aprobacion humana requerida

No prevista para este paquete si se mantiene el alcance anterior. Si aparece
necesidad de migracion, cambios de estancias, mapas/cuadrantes o bases reales,
abrir plan independiente y solicitar decision humana.

Estado: completado
