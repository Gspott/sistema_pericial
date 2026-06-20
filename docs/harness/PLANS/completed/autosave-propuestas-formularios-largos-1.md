# Autosave Propuestas Formularios Largos 1

# Objetivo

Extender el estandar transversal `AUTOSAVE-STANDARD-1` al formulario largo principal de propuestas, como ultimo paquete funcional del despliegue `AUTOSAVE-ROLLOUT-1`, sin reimplementar autosave ni mezclar acciones fiscales, generacion documental o procesos irreversibles.

El alcance seguro detectado para esta fase es la edicion de propuestas persistidas en `templates/propuestas/form.html`, especialmente:

- alcance;
- condiciones;
- observaciones/textos largos equivalentes dentro del formulario principal;
- campos descriptivos editados durante preparacion de propuesta.

La creacion de propuesta queda fuera porque todavia no existe entidad persistida ni `updated_at`.

# Modulo

Propuestas.

Inventario previo:

- `GET/POST /propuestas/{propuesta_id}/editar`: formulario principal con `alcance`, `condiciones`, datos descriptivos y honorarios base. Apto para autosave porque la tabla `propuestas` dispone de `updated_at`.
- `GET/POST /propuestas/nueva`: no apto en esta fase por no tener registro persistido.
- Lineas de propuesta (`/propuestas/{id}/lineas/...`): contienen `descripcion`, `incluye`, `no_incluye` y `condiciones`, pero mezclan edicion textual con cantidades, precios, IVA, recalculo de totales y acciones estructurales. Pendiente de plan separado si se decide separar edicion textual de economia.
- Facturacion asistida, creacion de factura, estados, PDFs, emails y creacion de expediente: fuera de alcance por ser acciones fiscales/documentales o irreversibles.

# Riesgo

Medio-bajo.

Riesgos principales:

- Sobrescritura entre pestanas durante edicion prolongada de textos de propuesta.
- Divergencia entre guardado manual y autosave si no comparten validaciones y campos.
- Autosave accidental sobre formularios de creacion o acciones economicas.

Mitigaciones:

- Usar `updated_at` real de `propuestas`.
- Conservar boton manual como fallback y protegerlo tambien con `updated_at`.
- Aplicar autosave solo cuando `propuesta.id` existe.
- No tocar lineas, facturacion, PDFs, emails ni generacion documental.

# Archivos permitidos

- `app/routers/propuestas.py`
- `templates/propuestas/form.html`
- `tests/smoke/test_autosave_propuestas_formularios_largos.py`
- `docs/harness/PLANS/completed/autosave-propuestas-formularios-largos-1.md`
- `docs/harness/EPISODES/*autosave-propuestas-formularios-largos-1*.md`

# Archivos prohibidos

- Bases SQLite reales, backups, uploads, informes, fotos y logs.
- Facturacion fiscal o emision de facturas.
- Generacion PDF/DOCX.
- Envio de emails.
- Service worker/PWA.
- Arquitectura general, migraciones de esquema o refactors amplios.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

Patrones aplicables:

- `docs/harness/PATTERNS/autosave_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- Smoke especifico de autosave en propuestas.
- Smoke/regresion de propuestas y facturacion vinculada.
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los cambios de los archivos permitidos. Al no introducir migraciones ni tocar datos reales, el rollback es de codigo/template/test/documentacion.

# Fuera de alcance

- Autosave en lineas de propuesta con importes.
- Facturacion, impuestos, facturas emitidas o asistentes fiscales.
- Generacion o descarga de PDFs.
- Envio de emails.
- Propuestas nuevas sin registro persistido.
- Formularios que requieran separar previamente edicion textual de acciones irreversibles.

# Aprobacion humana requerida

No requerida para este paquete porque no toca datos reales, esquema, fiscalidad, PDFs, emails ni acciones irreversibles.

Estado: completado
