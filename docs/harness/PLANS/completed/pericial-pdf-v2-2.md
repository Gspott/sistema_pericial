# Pericial Pdf V2 2

# Objetivo

Evolucionar exclusivamente los anexos del PDF Pericial V2 para el caso piloto
019-26, fusionando la salida PDF de conclusiones técnicas/periciales en un
único capítulo y sustituyendo los anexos placeholder por anexos útiles derivados
de datos existentes.

# Modulo

Informes / PDF V2.

# Riesgo

Crítico, por tocar salida de informe. Alcance limitado a contexto y plantilla de
PDF V2; sin modificar PDF clásico, editor V2, Workbench, patologías, costes,
captura móvil ni almacenamiento.

# Archivos permitidos

- `app/main.py`
- `templates/informes/v2_pdf.html`
- `tests/smoke/test_pericial_workbench.py`

# Archivos prohibidos

- PDF clásico y `templates/informes/imprimir.html`
- Editor V2 y Workbench salvo lectura
- Patologías, costes, captura móvil y persistencia
- Bases SQLite, uploads, informes generados, backups, logs y secretos

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Datos reutilizados

- Capítulos guardados en `informe_v2_capitulos`.
- Contexto común de informe para estancias, patologías, fotos y actuaciones.
- Fuentes económicas ya existentes si constan.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest`
- `git diff --check`
- `bash scripts/finish_harness_task.sh`

# Rollback

Revertir los cambios acotados en contexto/plantilla/test de PDF V2 y descartar
documentos temporales de prueba si se generan.

# Fuera de alcance

- Cambiar el cuerpo principal del PDF V2.
- Cambiar el PDF clásico.
- Modificar contenido redactado por el técnico.
- Cambiar editor V2, Workbench, patologías, costes o captura móvil.
- Crear tablas, migraciones o almacenamiento nuevo.

# Aprobacion humana requerida

No prevista si se mantiene el alcance anterior. Cualquier cambio de criterio
pericial, persistencia o PDF clásico requiere revisión humana.

Estado: completado
