# Valoracion Mover Campos Diseno

# Objetivo

Disenar, sin implementar, la evolucion del modelo de valoracion inmobiliaria
para mover datos estables desde visita hacia expediente y preparar testigos
reutilizables, ajustes y calculo futuro por metodo de comparacion.

# Modulo

Datos / valoracion inmobiliaria / harness / diseno tecnico.

# Riesgo

Critico por tratar evolucion de modelo de datos, acotado a documentacion y
auditoria solo lectura. No se cambia esquema ni se migra nada.

# Archivos permitidos

- `docs/harness/GOALS/valoracion_modelo_comparacion.md`
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`
- `docs/harness/EPISODES/2026-05-25-valoracion-modelo-comparacion-diseno.md`
- `docs/harness/BACKLOG/high.md`
- `docs/harness/STATE/known_risks.md`
- `docs/harness/PLANS/active/valoracion-mover-campos-diseno.md`
- `docs/harness/METRICS.md` por cierre automatico

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- DB real, datos reales, secretos, uploads, informes reales y backups
- Cambios de esquema, migraciones, borrado de columnas
- Calculo/homogeneizacion real
- Routers legacy
- Carpeta anidada `sistema_pericial/`

# Playbook aplicable

Task Pack sugerido: `TASK_PACKS/db_change.md`.

Task pack real leido: `docs/harness/TASK_PACKS/db_change.md`.
Playbook: `docs/harness/PLAYBOOKS/base_datos.md`.

# Validaciones

- `python3 scripts/audit_docs.py`
- `bash scripts/finish_harness_task.sh`
- `git diff --check`
- `git status --short`

# Rollback

Revertir documentos de diseno/harness anadidos o actualizados.

# Fuera de alcance

- Implementar tablas, columnas o migraciones.
- Leer DB real o PDFs de `uploads/`.
- Crear calculo final, homogeneizacion o imports de testigos.
- Cambiar formularios o salidas de informe.

# Aprobacion humana requerida

Requerida para cualquier fase posterior que implemente esquema o migre datos.
No requerida para este diseno documental.

Estado: completado
