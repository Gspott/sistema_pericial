# Autosave Standard 1

# Objetivo

Implantar el estándar transversal `AUTOSAVE-STANDARD-1` con cambios pequeños:

- extraer un patrón reutilizable desde Informe V2;
- crear infraestructura común de autosave para formularios largos;
- aplicar un piloto acotado en Valoración Workbench, sin retirar el guardado manual.

# Modulo

Infraestructura compartida de frontend y piloto en `Valoración Workbench`.

# Riesgo

Medio-bajo. El riesgo principal es una sobrescritura silenciosa entre pestañas o un guardado AJAX parcial incorrecto. Se limita el alcance a la microedición de testigos del Workbench y se mantiene el submit manual como fallback.

# Archivos permitidos

- `static/js/autosave.js`
- `templates/components/autosave_status.html`
- `templates/valoracion_workbench.html`
- `app/main.py`
- `app/services/informe.py`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/harness/PATTERNS/autosave_standard.md`
- episodio harness asociado.

# Archivos prohibidos

- Bases SQLite, backups, uploads, informes generados, fotos, logs y secretos.
- Carpeta anidada `sistema_pericial/`.
- Refactors amplios de valoración, informes o arquitectura frontend.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/bugfix.md`.

- `docs/harness/PLAYBOOKS/jinja.md`
- `docs/harness/PLAYBOOKS/base_datos.md`
- `docs/harness/PLAYBOOKS/informes.md` solo como referencia por Informe V2 autosave.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `node --check static/js/autosave.js`
- smoke scope de Valoración Workbench/autosave
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir el endpoint `/autosave`, retirar los atributos `data-autosave-*` del formulario de microedición, dejar el submit manual existente intacto y eliminar el JS común si no queda ningún consumidor.

# Fuera de alcance

- Extender autosave a patologías, visitas, CRM, costes, propuestas u otros formularios.
- Migrar datos históricos.
- Cambiar el modelo de navegación mobile-first.
- Sustituir el guardado manual.

# Aprobacion humana requerida

Solo si se detecta necesidad de migración de datos, tocar módulos no listados o rediseñar workflows fuera del piloto.

Estado: completado
