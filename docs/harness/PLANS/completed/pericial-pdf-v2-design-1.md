# Pericial Pdf V2 Design 1

# Objetivo

Mejora exclusivamente visual del PDF principal del Informe V2 para aumentar
legibilidad, jerarquia y consulta profesional sin cambiar contenido, datos,
logica pericial ni anexos aportados/fusionados.

# Modulo

Informes / PDF V2 principal.

# Riesgo

Critico por pertenecer a informes. Alcance limitado a estilos, layout de
plantilla y cabecera/pie del PDF principal.

# Archivos permitidos

- `templates/informes/v2_pdf.html`.
- `app/services/informe.py` solo para cabecera/pie Playwright del PDF V2.
- `tests/smoke/test_pericial_workbench.py`.
- Documentacion de cierre en `docs/harness/EPISODES/` y este plan.

# Archivos prohibidos

- Datos reales, bases SQLite, uploads, fotos, informes generados, backups y logs.
- Anexos aportados/fusionados y flujos de fotos, CRM, valoracion, costes o mediciones.
- Editor Informe V2 salvo impacto imprescindible.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.
Playbook: `docs/harness/PLAYBOOKS/informes.md`.


# Validaciones

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app`.
- `pytest tests/smoke/test_pericial_workbench.py -q -k "pdf_v2"`.
- `bash scripts/finish_harness_task.sh --smoke-scope app`.
- `git diff --check`.

# Rollback

Revertir cambios en plantilla, servicio y test. No hay migraciones ni artefactos
generados versionados.

# Fuera de alcance

- Cambiar contenido tecnico/juridico, orden de capitulos o campos.
- Modificar anexos, fusion de PDFs externos, mediciones, fotos o valoracion.
- Introducir dependencias nuevas.
- Cambiar la paginacion final con anexos.

# Aprobacion humana requerida

Solo si aparece necesidad de cambiar estructura pericial, datos, anexos,
conclusiones, generacion real de documentos o flujos fuera del PDF V2 principal.

Estado: completado
