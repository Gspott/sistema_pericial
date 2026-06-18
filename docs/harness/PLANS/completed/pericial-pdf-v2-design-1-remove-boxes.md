# Pericial Pdf V2 Design 1 Remove Boxes

# Objetivo

Eliminar el tratamiento visual tipo caja del cuerpo principal del PDF V2
manteniendo el resto de mejoras editoriales de `PERICIAL-PDF-V2-DESIGN-1`.

# Modulo

Informes / PDF V2 principal.

# Riesgo

Critico por pertenecer a informes. Cambio limitado a CSS/HTML de presentacion
y smoke tests, sin modificar contenido ni logica pericial.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- Anexos aportados/fusionados, mediciones, CRM, valoracion, costes y editor V2.
- Cambios de contenido, orden de capitulos o paginacion final.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `git diff --check`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.

# Rollback

Revertir cambios en plantilla, test y documentacion harness de esta tarea.

# Fuera de alcance

- Modificar contenido tecnico/juridico o estructura de datos.
- Tocar anexos, fotos, mediciones, CRM, valoracion o costes.
- Cambiar cabecera/pie, indice, tipografia o jerarquia ya aprobada salvo lo
  imprescindible para retirar las cajas.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, datos, anexos,
conclusiones, generacion real de documentos o flujos fuera del PDF V2 principal.

Estado: completado
