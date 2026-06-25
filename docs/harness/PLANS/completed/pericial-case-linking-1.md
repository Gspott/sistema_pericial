# Pericial Case Linking 1

# Objetivo

Implementar soporte inicial para expedientes derivados o relacionados entre si,
permitiendo crear un expediente nuevo desde otro sin duplicar hechos periciales,
evidencias, informes, documentos ni valoraciones. El derivado debe heredar solo
el marco fisico permanente del inmueble y mantener independencia tecnica y
documental.

# Modulo

Expedientes, persistencia SQLite, detalle de expediente, workbench pericial SSR
y smoke tests.

# Riesgo

Critico por cambio de esquema y alto por tocar expedientes. Mitigacion:
migracion idempotente, sin borrado de columnas/datos, sin tocar bases reales,
tests con DB temporal y copia estrictamente acotada.

# Archivos permitidos

- `app/database.py`
- `app/main.py`
- `templates/detalle_expediente.html`
- `templates/pericial_workbench.html`
- `templates/crear_expediente_derivado.html`
- `tests/smoke/test_pericial_workbench.py`
- Este plan activo del harness.

# Archivos prohibidos

- Bases SQLite reales.
- `uploads/`, fotos reales, informes generados, backups, logs y secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes ya generados.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/db_change.md`.

Playbooks aplicados:

- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/css_mobile.md`

# Diagnostico inicial

El modelo actual se organiza alrededor de `expedientes` y tablas dependientes
por visita, patologias, fotos, documentos aportados, capitulos de informe,
actuaciones y valoracion. Copiar un expediente completo duplicaria evidencia
probatoria y contenido documental. La mejora debe crear una relacion entre
expedientes y un expediente limpio que solo comparta el marco fisico del
inmueble.

# Decision de modelo de datos

Se elige tabla nueva `expediente_relaciones`, no columna en `expedientes`,
porque permite evolucionar a multiples relaciones.

Campos:

- `id`
- `expediente_origen_id`
- `expediente_derivado_id`
- `tipo_relacion`
- `descripcion`
- `created_at`

Incluye indice unico idempotente por origen, derivado y tipo. Tipos iniciales:
`derivado`, `complementario`, `seguimiento`.

# Que se copia

- `cliente`
- `direccion`
- `codigo_postal`
- `ciudad`
- `provincia`
- `referencia_catastral`
- `tipo_inmueble`
- `anio_construccion`
- `uso_inmueble`
- `orientacion_inmueble`
- `superficie_construida`
- `superficie_util`
- Datos generales de bloque/unidad: planta, puerta, dormitorios, banos,
  plantas bajo rasante/sobre baja, reforma y superficies.
- Estructura base multiunidad (`niveles_edificio` y `unidades_expediente`) sin
  observaciones libres.

# Que no se copia

- `visitas`
- `estancias` creadas dentro de visita
- patologias interiores/exteriores
- fotografias
- documentos aportados
- capitulos de informe V2
- informes/PDF/DOCX generados
- valoracion inmobiliaria
- actuaciones de reparacion, partidas o PEM
- observaciones tecnicas del informe
- anexos/documentos internos/presupuestos
- observaciones libres de niveles/unidades si podrian mezclar hechos tecnicos.

# Validaciones

- `python3 scripts/audit_docs.py` inicial: OK con warnings historicos
  preexistentes de planes completados vacios y monolito informativo.
- `python3 -m compileall app`: OK.
- `.venv/bin/pytest tests/smoke/test_pericial_workbench.py -q -k "expediente_derivado"`:
  OK, 1 passed.
- `.venv/bin/pytest tests/smoke/test_pericial_workbench.py -q`: OK, 87 passed.
- `.venv/bin/pytest -q`: OK, 299 passed.
- `python3 scripts/audit_docs.py`: OK con warnings historicos preexistentes.
- `git diff --check`: OK.
- Pendiente de cierre: `bash scripts/finish_harness_task.sh`.

# Rollback

Revertir cambios en los archivos permitidos. La tabla nueva no borra ni migra
datos existentes; en DB temporal se descarta la base. En base existente, el
rollback funcional consiste en dejar de usar la tabla/rutas sin tocar datos
reales.

# Fuera de alcance

- Modificar informes ya generados.
- Fusionar PDFs o anexos entre expedientes.
- Insertar automaticamente antecedentes en el PDF.
- Duplicar o mover evidencias.
- Cambiar flujo mobile-first de visita.
- Crear APIs paralelas o frontend SPA.
- Leer o modificar datos reales.

# Aprobacion humana requerida

No requerida para esta fase: no hay migracion destructiva, facturacion,
autenticacion, backups/restore, secretos, deploy ni datos reales.

# Limitaciones

- La mencion textual del expediente origen en futuros informes queda preparada
  como contexto relacional, pero no se inserta automaticamente.
- El tipo de informe del derivado se elige en el formulario; por defecto se
  sugiere `inspeccion`.
- La estructura copiada es la estructura base multiunidad, no las estancias
  observadas en visitas.

Estado: completado
