# Valoracion Eco Inspired Fase 1 Ajuste Final

# Objetivo

Registrar el ajuste final de numeracion/TOC tras la fase ECO-inspired y validar que los cambios quedan cubiertos por plan activo.

# Modulo

Valoracion inmobiliaria e informes.

# Riesgo

Bajo: ajuste documental/harness y numeracion de secciones; sin cambios funcionales nuevos.

# Archivos permitidos

Archivos ya tocados por la fase ECO-inspired, plan/harness y tests.

# Archivos prohibidos

DB real, uploads, informes generados reales, backups, secretos, routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

`bash scripts/finish_harness_task.sh`, `python3 scripts/audit_docs.py`, `.venv/bin/python -m pytest`, `git diff --check`, `git status`.

# Rollback

Revertir ajuste final junto con la fase principal si fuese necesario.

# Fuera de alcance

Nuevos cambios de modelo, calculo, UX o migraciones.

# Aprobacion humana requerida

No.

Estado: completado
