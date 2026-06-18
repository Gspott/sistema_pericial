# Pericial Pdf Annex Diagnostics 1

# Objetivo

Mostrar en el editor Informe V2 un diagnostico claro del peso estimado del PDF
final, desglosando cuerpo principal, Anexo A, Anexo F y otros anexos.

# Modulo

Informe V2 / editor / diagnostico de peso de anexos PDF externos.

# Riesgo

Bajo-medio. Es una mejora informativa no bloqueante. No modifica generacion PDF,
DOCX, CRM ni esquema de base de datos.

# Archivos permitidos

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-pdf-annex-diagnostics-1.md`
- Episodio harness de cierre

# Archivos prohibidos

- DOCX
- CRM
- Esquema DB
- PDFs, uploads o informes reales
- Contenido tecnico del informe

# Playbook aplicable

Task Pack sugerido: `informe_change`.

# Diagnostico

El helper `diagnosticar_peso_anexos_pdf_v2()` ya calculaba los pesos base y los
anexos detectados. El editor solo mostraba un aviso minimo de Anexo A/Anexo F,
insuficiente para explicar casos reales como `019-26`, donde el cuerpo del
informe pesa poco y el peso procede de anexos externos.

# Alcance

- Enriquecer el helper con:
  - `nivel` verde/amarillo/rojo;
  - `anexos_pesados`;
  - `avisos`;
  - deteccion de total > 20 MB;
  - anexo individual > 10 MB;
  - Anexo A > 70 % del total.
- Mostrar en `templates/informe_v2_editor.html` el bloque `Peso estimado del PDF`.
- Mostrar desglose de informe principal, Anexo A, Anexo F, otros anexos y total.
- Mostrar texto orientativo sobre Email/Judicial, Ghostscript y escaneos pesados.
- Mantener exportacion no bloqueante.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir cambios en helper, plantilla y tests. No hay migraciones ni datos
persistentes nuevos.

# Fuera de alcance

- Comprimir Anexo A.
- Cambiar generacion PDF/DOCX.
- Validar expediente real `019-26` sin autorizacion explicita.
- Bloquear exportaciones por peso.

# Aprobacion humana requerida

Solo para validar contra DB/uploads reales.

Estado: completado
