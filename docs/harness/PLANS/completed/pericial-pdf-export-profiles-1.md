# Pericial Pdf Export Profiles 1

# Objetivo

Añadir perfiles informativos de exportación PDF para Informe V2 sin sustituir el
exportador actual ni modificar el contenido técnico del informe.

# Modulo

Informe V2. Endpoint `/generar-informe-v2-pdf/{expediente_id}` y editor
`templates/informe_v2_editor.html`.

# Riesgo

Bajo-medio. La generación PDF actual se conserva como comportamiento por
defecto; el cambio introduce una rama para omitir fusión de anexos en
`solo_informe` y una validación explícita de perfiles.

# Archivos permitidos

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-export-profiles-1.md`
- Documentación harness generada al cierre.

# Archivos prohibidos

- Generación DOCX.
- CRM/prospección.
- Esquema de base de datos y migraciones.
- Carpetas de datos reales, uploads, backups, informes generados y logs.
- Carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Playbook revisado: `docs/harness/PLAYBOOKS/informes.md`.

Diagnóstico:

- La ruta PDF V2 genera primero el cuerpo del informe y después fusiona PDFs
  externos de anexos integrados.
- La separación permite implementar `solo_informe` sin tocar plantillas PDF.
- No se ha localizado una generación separada del anexo fotográfico que permita
  implementarla sin refactor; se deja como perfil preparado con respuesta 501.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_consistency.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir los cambios en `app/main.py`, `templates/informe_v2_editor.html` y
`tests/smoke/test_pericial_workbench.py`. La ruta sin parámetro debe volver al
comportamiento anterior.

# Fuera de alcance

- Compresión profunda de imágenes o reducción real de tamaño.
- Cambios en PDF/DOCX generados por contenido.
- Bloqueo de exportación.
- Histórico de perfiles o persistencia en base de datos.
- Implementación separada del anexo fotográfico si requiere refactor.

# Aprobacion humana requerida

No prevista para este alcance. Requerida si se decide modificar generación PDF
interna, DOCX, esquema de base de datos o datos reales.

Estado: completado
