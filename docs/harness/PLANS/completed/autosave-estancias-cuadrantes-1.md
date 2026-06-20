# Autosave Estancias Cuadrantes 1

# Objetivo

Extender `AUTOSAVE-STANDARD-1` a estancias y a editores textuales de
mapas/cuadrantes de patologias, sin reimplementar infraestructura y manteniendo
el guardado manual como fallback.

El paquete debe permanecer pequeno, reversible y autocontenido dentro de
`AUTOSAVE-ROLLOUT-1`.

# Modulo

Inventario afectado:

- `templates/editar_estancia.html`: edicion de estancia ya persistida.
  Campos: nombre, tipo, ventilacion, planta cuando aplica, acabados y
  observaciones.
- `templates/editar_cuadrante_mapa_patologia.html`: edicion de cuadrante ya
  persistido. Campos: descripcion, patologia detectada, vinculo a patologia,
  gravedad y observaciones. Fotos quedan fuera del autosave.

Pantallas revisadas y fuera de esta fase:

- `templates/definir_estancias.html`: altas, generacion y navegacion/listado de
  estancias; no hay editor largo persistido por fila.
- `templates/editar_mapa_patologia.html`: combina texto con filas/columnas e
  imagen base; el autosave podria persistir cambios estructurales a mitad de
  edicion. Queda pendiente de plan especifico si se decide separar su edicion
  textual de la estructural.
- Formularios de creacion de mapas o estancias sin entidad previa.

# Riesgo

Medio. Son flujos de inspeccion mobile-first con informacion susceptible de
perdida. El riesgo se contiene usando endpoints especificos, tokens
equivalentes sin migracion y manteniendo el submit manual existente.

Las tablas `estancias`, `mapas_patologia` y `cuadrantes_mapa_patologia` no
disponen de `updated_at` util para estas rutas; se usara token calculado sobre
campos editables y devuelto bajo el contrato estandar `updated_at`.

# Archivos permitidos

- `app/main.py`
- `templates/editar_estancia.html`
- `templates/editar_cuadrante_mapa_patologia.html`
- `tests/smoke/test_autosave_estancias_cuadrantes.py`
- `docs/harness/PLANS/active/autosave-estancias-cuadrantes-1.md`
- Episodio harness correspondiente.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos y logs.
- Migraciones o cambios de esquema.
- CRM, costes, propuestas, facturacion y refactors generales.
- Reimplementacion de `static/js/autosave.js`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- Smoke especifico de estancias/mapas/cuadrantes.
- Smoke de regresion proporcional para autosave de visitas/patologias si el
  scope lo requiere.
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Retirar atributos `data-autosave-*`, hidden `updated_at`, includes del
componente visual y scripts comunes de las dos plantillas; retirar endpoints y
helpers de token especificos; retirar el smoke nuevo. El guardado manual queda
intacto.

# Fuera de alcance

- Creacion de estancias y mapas sin entidad persistida.
- Editor estructural de mapa de patologias (`editar_mapa_patologia.html`).
- Fotos, borrado de fotos e imagen base mediante autosave.
- CRM, costes, propuestas y facturacion.
- Migraciones de datos historicos.
- Cambios visuales no necesarios.

# Aprobacion humana requerida

No prevista si se mantiene el alcance. Si aparece necesidad de migracion,
datos reales, cambios de uploads/fotos o reestructuracion de mapas, abrir plan
independiente y solicitar decision humana.

Estado: completado
