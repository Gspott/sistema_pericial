# Task Pack: Valoracion Inmobiliaria Change

## Cuando usarlo

Para fases funcionales de valoracion inmobiliaria: datos estables de
expediente, observaciones de visita, testigos reutilizables, snapshots,
ajustes/homogeneizacion manual, outputs de informe, casos demo y QA visual.

Usarlo tambien cuando una tarea de valoracion parezca encajar con `db_change`,
`informe_change` o `mobile_ui`: este pack actua como capa especifica y debe
combinarse con el pack de mayor riesgo si hay esquema, informes o UX sensible.

## Cuando NO usarlo

- Facturacion, emails, backups, autenticacion, PWA o patologias sin relacion
  directa con valoracion.
- Scraping, OCR, IA de extraccion, descarga automatica de imagenes o calculo
  definitivo: requieren fase y aprobacion propias.
- Migraciones de datos reales: requieren plan especifico, backup/copia y
  aprobacion humana.

## Riesgo base

Alto.

Sube a Critico si hay:

- esquema o persistencia nueva;
- PDF/DOCX moderno;
- calculo de valor final;
- migracion o escritura sobre DB local/real;
- uploads/fotos reales.

## Reglas de seguridad

- No tocar DB real salvo autorizacion explicita, backup previo y comando
  acotado.
- No usar datos reales, uploads reales, informes reales, backups ni secretos.
- No tocar la carpeta anidada `sistema_pericial/`.
- No activar routers legacy.
- No crear APIs de negocio paralelas ni introducir SPA/React/Vue.
- Mantener cambios pequenos, reversibles y auditables.
- Si aparece necesidad de migrar datos, cambiar calculo final o tocar outputs
  reales, detener y documentar.

## Modelo canonico actual

- `valoracion_expediente`: datos estables 1:1 del expediente.
- `valoracion_visita_observaciones`: datos observados en visita.
- `testigos_valoracion`: biblioteca reusable de testigos/comparables.
- `testigos_valoracion_fotos`: fotos/capturas manuales del testigo base.
- `valoracion_expediente_testigos`: vinculo expediente-testigo con orden,
  incluido, notas y `snapshot_json`.
- `valoracion_testigo_ajustes`: ajustes manuales por vinculo, no por testigo
  base.
- `valoracion_resultados`: resultados versionados por metodo.

## Fallback legacy obligatorio

Mientras no exista migracion aprobada:

- `valoracion_visita` sigue como fallback de datos historicos.
- `comparables_valoracion` sigue como fallback de comparables ligados a visita.
- `build_informe_context()` debe priorizar modelo nuevo y degradar a legacy sin
  romper patologias, inspeccion ni habitabilidad.

## Testigos reutilizables

- El testigo base puede usarse en multiples expedientes.
- Editar el testigo base no debe reescribir valoraciones historicas.
- Al vincular a expediente, guardar `snapshot_json` con los datos usados en ese
  momento.
- Quitar un testigo del expediente elimina solo el vinculo, nunca el testigo
  base.
- La recomendacion de 6 testigos es orientativa salvo regla funcional explicita.

## Ajustes

- Los ajustes viven en `valoracion_testigo_ajustes`.
- Coeficientes individuales permitidos: -0.20 a +0.20.
- Guardar justificacion.
- Antes del calculo final solo se permite persistir ayudas preparatorias como
  `coeficiente_total = 1 + suma de ajustes` y `valor_unitario_ajustado` del
  vinculo.
- No calcular valor final, ponderacion global ni metodo de coste sin fase
  propia.

## Demo cases

Los casos demo de valoracion deben ser ficticios, plausibles y profesionales.
No usar lorem ipsum ni inmuebles reales identificables.

Casos de referencia:

- Piso urbano estandar.
- Piso reformado premium.
- Caso incompleto/problematico.
- Local comercial.
- Vivienda unifamiliar.

Usar scripts/fixtures existentes con DB temporal o DB local autorizada con
backup previo.

## Archivos normalmente permitidos

- `app/database.py` solo en fases DB defensivas.
- `app/main.py` para rutas server-side acotadas.
- `app/services/informe.py` para contexto y outputs autorizados.
- `templates/valoracion_*.html` y `templates/informes/imprimir.html` cuando
  aplique.
- `tests/smoke/test_valoracion_*.py`.
- `tests/fixtures/valoracion_demo_cases.py`.
- `scripts/create_valoracion_demo_cases.py` si la fase es demo.
- `docs/modelos_datos.md`, `docs/ux.md`, `docs/informes.md`.
- Harness: backlog, episodes, patterns, plans y agent maps.

## Archivos normalmente prohibidos

- DB real, backups reales, uploads reales, informes generados reales, secretos
  y logs.
- Carpeta anidada `sistema_pericial/`.
- Routers legacy no incluidos.
- Facturacion, autenticacion, backups/restore, deploy y service worker salvo
  objetivo explicito.

## Lectura previa obligatoria

- `AGENTS.md`.
- `docs/SOURCE_OF_TRUTH.md`.
- `docs/modelos_datos.md`.
- `docs/informes.md`.
- `docs/ux.md`.
- `docs/backend.md`.
- `docs/harness/CODEX_OPERATING_MANUAL.md`.
- `docs/harness/EXECUTION_POLICY.md`.
- `docs/harness/PATTERNS/valoracion_comparables_reutilizables.md`.
- Planes completed recientes de valoracion que afecten a la fase.

## Playbooks relacionados

- `docs/harness/PLAYBOOKS/base_datos.md` para esquema/persistencia.
- `docs/harness/PLAYBOOKS/informes.md` para contexto/PDF/DOCX.
- `docs/harness/PLAYBOOKS/jinja.md` para templates server-side.

## Smokes obligatorios

Elegir los especificos de la fase, pero toda fase funcional de valoracion debe
cubrir al menos:

- DB temporal, nunca DB real.
- Expediente `tipo_informe='valoracion'`.
- Compatibilidad con no valoracion.
- Fallback legacy si se toca lectura/contexto.
- Ownership si hay rutas o biblioteca.
- Snapshot si hay testigos vinculados.
- Ajustes y rango -0.20/+0.20 si se toca homogeneizacion.
- No modificacion de legacy cuando el modelo nuevo escribe aparte.
- No ruptura de `build_informe_context()`.
- HTML/PDF/DOCX aislados solo si la fase toca outputs.
- Demo cases solo con datos ficticios.

## QA visual recomendado

Cuando la fase toque UX o informes:

- Revisar mobile-first en listado, detalle y formularios.
- Verificar que no aparezcan patologias/climatologia en valoracion donde no
  proceda.
- Usar casos demo ficticios para inspeccionar HTML/PDF/DOCX.
- Si se usa navegador/Playwright, hacerlo sobre entorno local/test, no sobre
  datos reales.

## Cosas prohibidas sin fase propia

- Scraping de portales inmobiliarios.
- OCR o IA de extraccion desde capturas.
- Descarga automatica de imagenes desde URLs externas.
- Calculo definitivo de valoracion, ponderacion final o metodo de coste.
- Migracion de `valoracion_visita` o `comparables_valoracion` a modelo nuevo.
- Borrado destructivo de testigos, comparables o datos historicos.

## Validaciones obligatorias

- `python3 scripts/audit_docs.py`.
- `python3 -m compileall app` si se toca app.
- `bash scripts/finish_harness_task.sh --smoke-scope valoracion` para fases
  acotadas de valoracion. Si se pide un scope menor y hay paths de valoracion,
  el runner lo eleva automaticamente a `valoracion`.
- `bash scripts/finish_harness_task.sh` sin scope, equivalente a `full`, para
  fases criticas: esquema, migracion, PDF/DOCX moderno, calculo, uploads reales
  autorizados o cambios transversales.
- `git diff --check`.
- `git status --short`.

## Rollback

Revertir el diff de la fase. Si se autorizo escritura local, restaurar backup
documentado. Descartar DB temporales y uploads temporales de test.

## Criterios Done

- Plan activo creado y cerrado.
- Fallback legacy conservado.
- Smokes aplicables pasan.
- Riesgos/pedidos futuros quedan documentados en harness.
- Confirmado que no se tocaron datos reales ni artefactos reales.

## Mini TASK_ENVELOPE

- Subfase de valoracion:
- Modelo afectado:
- Legacy/fallback:
- Testigos/snapshot:
- Ajustes/calculo:
- Outputs afectados:
- Demo/QA:
- Smokes:
- Fuera de alcance:
- Rollback:
