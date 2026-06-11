# Pericial Wb 2

# Objetivo

Evolucionar el Workbench pericial SSR hacia una herramienta de redaccion asistida
de solo lectura, generando un borrador temporal del informe V2 con datos ya
existentes del expediente.

# Modulo

Pericial / expedientes / workbench SSR.

# Riesgo

Medio-alto por tocar `app/main.py` y plantilla de expediente, mitigado porque no
se persiste informacion, no se modifica PDF y no se crean rutas nuevas.

# Archivos permitidos

- `app/main.py`
- `templates/pericial_workbench.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-wb-2.md`
- `docs/harness/EPISODES/*pericial-wb-2*.md`

# Archivos prohibidos

- Bases SQLite reales.
- Informes generados, PDF/DOCX y uploads.
- Plantillas de informes PDF.
- Modulos de facturacion, CRM, emails, costes, patologias y valoracion.

# Playbook aplicable

Task Pack sugerido: `app_change`.

Playbook: `docs/harness/PLAYBOOKS/informes.md` como referencia por su relacion
con salida pericial, sin modificar generacion de informes.


# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`

# Rollback

Revertir los cambios en helper, plantilla, test y documentacion harness.

# Fuera de alcance

- Persistir borradores.
- Crear campos, tablas o migraciones.
- Modificar PDF/DOCX.
- Introducir IA, LLM o servicios externos.
- Cambiar rutas o logica de captura mobile-first.

# Aprobacion humana requerida

No prevista si el cambio se mantiene en diagnostico SSR de solo lectura.

Estado: completado
