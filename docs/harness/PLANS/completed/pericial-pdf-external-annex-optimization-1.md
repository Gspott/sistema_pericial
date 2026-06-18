# Pericial Pdf External Annex Optimization 1

# Objetivo

Diagnosticar y reducir, cuando sea posible, el peso añadido por PDFs externos
fusionados al Informe V2, especialmente Anexo A documental y Anexo F de
mediciones.

# Modulo

Informe V2. Fusión de anexos PDF externos, perfiles de exportación y editor del
informe.

# Riesgo

Bajo-medio. La generación histórica se conserva para `master`,
`informe_anexos` y ausencia de perfil. `email` y `judicial` intentan optimizar
copias temporales antes de fusionar.

# Archivos permitidos

- `app/main.py`
- `app/services/pdf_annex_optimizer.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-external-annex-optimization-1.md`
- Documentación harness generada al cierre.

# Archivos prohibidos

- DOCX.
- CRM/prospección.
- Esquema de base de datos y migraciones.
- PDFs originales subidos, uploads reales fuera de fixtures de test, backups e
  informes generados.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

Diagnóstico:

- La fusión principal vive en `fusionar_pdf_informe_v2_con_anexos_integrados`.
- Anexo A se lee desde `documento["archivo_ruta"]`; Anexo F desde
  `pdf_mediciones["archivo_ruta"]`.
- La fusión ocurre después del render del PDF principal, por lo que
  `PERICIAL-PDF-IMAGE-OPTIMIZATION-1` no reduce PDFs externos escaneados o
  pesados.
- Ghostscript no está instalado en el entorno local; V1 debe funcionar con
  fallback `pypdf` o solo diagnóstico si no hay reducción real.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir el servicio nuevo, los cambios de fusión/diagnóstico/UI y los tests.
No hay migraciones ni datos persistentes nuevos.

# Fuera de alcance

- Recompresión profunda garantizada de PDFs escaneados con imágenes internas.
- Añadir dependencias obligatorias.
- Modificar PDFs originales.
- Cambios en DOCX o contenido técnico.

# Aprobacion humana requerida

No prevista.

Estado: completado
