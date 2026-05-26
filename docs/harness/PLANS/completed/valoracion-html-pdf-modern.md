# Valoracion Html Pdf Modern

# Objetivo

Adaptar el HTML/PDF moderno de informes para que `tipo_informe='valoracion'`
renderice secciones propias de valoracion inmobiliaria desde
`build_informe_context()`, sin tocar calculo, homogeneizacion, DB ni DOCX.

# Modulo

Informes / plantilla imprimible / smoke tests.

# Riesgo

Critico por afectar salida de informe, acotado a plantilla moderna y smoke con
datos temporales.

# Archivos permitidos

- `templates/informes/imprimir.html`
- `app/services/informe.py` solo para indice/toc derivado del contexto
- `tests/smoke/test_informe_context.py`
- `docs/harness/PLANS/active/valoracion-html-pdf-modern.md`
- `docs/harness/METRICS.md` por cierre automatico

# Archivos prohibidos

- DB real, datos reales, secretos, uploads, fotos reales, informes generados y backups
- DOCX moderno o legacy
- Calculo/homogeneizacion
- Migraciones o cambios de esquema
- Routers legacy
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/informe_change.md`.

Playbook: `docs/harness/PLAYBOOKS/informes.md`.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_informe_context.py -q`
- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh`
- `python3 -m compileall app`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en plantilla, toc de contexto y smoke HTML.

# Fuera de alcance

- Adaptar DOCX editable moderno.
- Crear calculo u homogeneizacion.
- Mover campos entre tablas.
- Generar PDF real con datos reales.

# Aprobacion humana requerida

No adicional: el usuario ha autorizado esta fase funcional acotada. Parar si
aparece cambio de esquema, calculo, rediseño mayor o fallo de validacion.

Estado: completado
