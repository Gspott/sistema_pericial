# Pericial Pdf V2 Document Order 1

# Objetivo

Reordenar el PDF V2 master para que los anexos técnicos sigan al informe
principal y la documentación aportada por terceros pase a un bloque final
independiente, sin pertenecer a la numeración de anexos técnicos.

# Modulo

Informes / PDF V2 / índice, portadillas, anexos y fusión master.

# Riesgo

Crítico por afectar la estructura documental del informe PDF V2. El cambio se
limita a renderizado, nomenclatura automática y orden de fusión; no debe tocar
datos, contenido técnico, documentos externos ni workflows ajenos.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `app/main.py` en funciones de PDF V2, anexos y fusión.
- `tests/smoke/test_pericial_workbench.py`.
- Documentación harness de esta tarea.

# Archivos prohibidos

- Bases SQLite, datos reales, uploads, fotos, informes generados, backups y logs.
- PDFs externos aportados por terceros.
- Editor V2 salvo tests existentes que verifiquen que no queda roto.
- CRM, costes, valoración hipotecaria, facturación y workflows ajenos.

# Playbook aplicable

Task Pack: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app`.
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.
- `git diff --check`.

# Rollback

Revertir cambios en plantilla PDF V2, funciones de fusión/renderizado, tests y
documentación harness de esta tarea.

# Fuera de alcance

- Modificar contenido técnico, textos manuales del usuario, datos, modelos o
  lógica pericial.
- Modificar PDFs externos fusionados.
- Cambiar editor V2, CRM, costes, valoración hipotecaria, facturación u otros
  módulos no relacionados.

# Aprobacion humana requerida

Si el cambio exige reescribir contenido manual guardado por el usuario,
renumerar datos persistidos o alterar la fusión de PDFs externos más allá del
orden de inserción.

Estado: completado
