# Valoracion Qa Visual

# Objetivo

Ejecutar QA visual completa de valoracion sobre biblioteca de testigos,
detalle, seleccion por expediente, informe HTML/PDF, mobile y tablas/listados de
comparables. Detectar densidad excesiva, jerarquia, narrativa, legibilidad,
scroll y acciones confusas.

# Modulo

Valoracion inmobiliaria, UX, informe y harness.

# Riesgo

Medio. QA visual y documentacion. Se usa DB sandbox temporal con casos demo.
No hay cambios funcionales ni escritura sobre DB real.

# Archivos permitidos

- `docs/harness/EPISODES/2026-05-26-valoracion-qa-visual.md`
- `docs/harness/BACKLOG/high.md`
- Este plan activo/completed.

# Archivos prohibidos

- `app/`
- `templates/`
- `static/`
- DB real, datos reales, uploads reales, informes reales, backups y secretos.
- Routers legacy y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/valoracion_change.md`.

# Ejecucion

- Generada DB sandbox temporal en `/private/tmp/valoracion-qa-visual.DQSaE7/valoracion_qa.sqlite`.
- Levantada app temporal en `http://127.0.0.1:8765` con entorno `APP_ENV=test`.
- Revisadas pantallas en mobile 390x844 y desktop 1366x900.
- Generado PDF demo temporal en `/private/tmp/valoracion-qa-visual.DQSaE7/informe-demo.pdf`.
- Capturas temporales guardadas fuera del repo en `/private/tmp/valoracion-qa-visual.DQSaE7/screenshots`.

# Findings

- Sin overflow horizontal.
- Biblioteca demasiado larga: 31 cards y 63 acciones con 30 testigos demo.
- Seleccion por expediente no escala: select unico con todos los testigos.
- Comparables del informe y vinculados muestran numeros sin formato ni unidad.
- Narrativa del informe aun pobre: ficha estructurada mas que lectura profesional.
- Acciones de vinculados poco jerarquizadas; `Quitar del expediente` no destaca como secundaria/destructiva.

# Validaciones

- Pendientes al cierre: `python3 scripts/audit_docs.py`,
  `bash scripts/finish_harness_task.sh`, `git diff --check`,
  `git status --short`.

# Rollback

Revertir docs de harness. Borrar temporales de `/private/tmp/valoracion-qa-visual.DQSaE7` si se desea.

# Fuera de alcance

- Implementar quick wins.
- Scraping/OCR/descarga remota.
- Calculo definitivo o metodo de coste.
- Cambios de esquema, formularios o outputs.

# Aprobacion humana requerida

No requerida para QA/documentacion. Requerida para fases futuras de scraping,
OCR, calculo definitivo o migracion real.

Estado: completado
