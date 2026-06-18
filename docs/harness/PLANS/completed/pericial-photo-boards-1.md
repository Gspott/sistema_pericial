# Pericial Photo Boards 1

# Objetivo

Crear la primera version de laminas fotograficas comparativas para Informe V2,
sin modificar fotografias originales ni alterar los anexos B/C existentes.

# Modulo

- Informe V2 / editor.
- Generacion PDF del informe pericial.
- Persistencia local SQLite minima para laminas fotograficas.

# Riesgo

- Medio: añade persistencia y rutas nuevas dentro del flujo de Informe V2.
- Riesgo principal: romper render PDF o alterar el orden/canon de anexos.
- Mitigacion: insertar las laminas como bloque fotografico posterior al Anexo B,
  sin renumerar Anexo C/D/E/F y con tests de compatibilidad.

# Archivos permitidos

- app/database.py
- app/main.py
- templates/informe_v2_editor.html
- templates/informes/v2_pdf.html
- tests/smoke/test_pericial_workbench.py
- docs/harness/METRICS.md
- docs/harness/EPISODES/
- docs/harness/PLANS/

# Archivos prohibidos

- CRM/prospeccion.
- DOCX.
- Datos reales, uploads, bases SQLite, backups e informes generados.
- Carpeta anidada sistema_pericial/.

# Playbook aplicable

Task Pack sugerido: `informe_change`.

- docs/harness/PLAYBOOKS/informes.md
- docs/informes.md
- docs/modelos_datos.md

# Validaciones

- python3 scripts/audit_docs.py
- python3 -m compileall app
- .venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q
- git diff --check
- bash scripts/finish_harness_task.sh --smoke-scope app

# Rollback

Revertir las rutas/helpers de laminas, retirar el bloque de editor/PDF y dejar
las tablas sin uso. No hay modificacion de fotos originales.

# Fuera de alcance

- Edicion avanzada drag-and-drop.
- Miniaturas PDF.
- Recalculo de indice con pagina final.
- Cambios en DOCX.
- Cambios en Anexo B/C existentes.
- IA externa.

# Aprobacion humana requerida

No prevista salvo que se decida cambiar el esquema mas alla de las dos tablas
minimas de persistencia.

Estado: completado
