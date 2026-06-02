# Valoracion Workbench Ux Val 8 Comparativa Tecnica

# Objetivo

Mostrar en el Workbench de Valoracion atributos tecnicos de testigos reutilizables
para comparar superficies, planta, ascensor, exterior/interior, equipamiento y
estado sin alterar calculos, ponderacion ni flujos moviles.

# Modulo

Valoracion inmobiliaria / Workbench SSR / contexto de comparables.

# Riesgo

Bajo-medio. Vista de escritorio y contexto defensivo; no hay cambios de DB,
calculo, informes ni biblioteca.

# Archivos permitidos

- `app/services/informe.py`
- `templates/valoracion_workbench.html`
- `tests/smoke/test_valoracion_workbench.py`
- `docs/ux.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/EPISODES/`

# Archivos prohibidos

- DB real, datos reales, backups, uploads, informes generados y secretos.
- Carpeta anidada `sistema_pericial/`.
- Informes HTML/PDF/DOCX.
- Biblioteca de testigos y formularios de testigos.
- Calculos persistidos, homogeneizacion y ponderacion.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.


# Validaciones

- `python3 -m compileall app`
- `python3 scripts/audit_docs.py`
- `.venv/bin/python -m pytest`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir cambios en servicio de informe, template del workbench, smoke y
documentacion de harness/UX. No requiere restaurar DB.

# Fuera de alcance

- Cambiar calculos.
- Cambiar DB/esquema.
- Modificar Biblioteca de Testigos.
- Tocar informes.
- Adoptar valor final automatico.
- SPA/JS obligatorio.

# Aprobacion humana requerida

No prevista salvo aparicion de necesidad de esquema, datos reales o cambio de
calculo.

Estado: completado
