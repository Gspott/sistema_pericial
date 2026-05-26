# Valoracion Completitud

# Objetivo

Crear una comprobacion ligera y no bloqueante de completitud para valoracion
inmobiliaria, visible como advertencias cuando falten datos, sin cambiar DB ni
impedir la generacion manual.

# Modulo

Informes / contexto / HTML-PDF / DOCX editable / smoke tests.

# Riesgo

Medio-alto por afectar salidas documentales, acotado a advertencias derivadas
del contexto existente y sin cambios de persistencia.

# Archivos permitidos

- `app/services/informe.py`
- `templates/informes/imprimir.html`
- `tests/smoke/test_informe_context.py`
- `docs/harness/PLANS/active/valoracion-completitud.md`
- `docs/harness/METRICS.md` por cierre automatico

# Archivos prohibidos

- DB real, datos reales, secretos, uploads, fotos reales, informes generados y backups
- Cambios de esquema o migraciones
- Calculo/homogeneizacion
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

Revertir helper de completitud, advertencias en HTML/DOCX y smoke asociado.

# Fuera de alcance

- Bloquear generacion de informes.
- Cambiar DB/esquema.
- Crear calculo u homogeneizacion.
- Mover campos entre visita y expediente.

# Aprobacion humana requerida

No adicional mientras sea no bloqueante y sin esquema. Parar si se convierte en
regla pericial/cuantitativa o bloqueo de generacion.

Estado: completado
