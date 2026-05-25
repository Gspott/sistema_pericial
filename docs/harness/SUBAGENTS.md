# Subagents

## Coordinador / arquitecto

- Mision: clasificar riesgo, elegir playbook, mantener coherencia del harness.
- Permisos: docs y planes; lectura dirigida de codigo.
- Limites: no tocar logica critica sin aprobacion.
- Puede tocar: `docs/harness/`.
- Debe evitar: datos reales, secretos, DB, backups.
- Validaciones: auditoria documental y `git status --short`.

## Facturacion

- Mision: cambios controlados en facturacion.
- Permisos: lectura dirigida; edicion solo con aprobacion humana.
- Limites: no cambiar numeracion, emision, anulacion, rectificativas o Verifactu sin checklist.
- Puede tocar: modulo facturacion si se autoriza.
- Debe evitar: DB real y datos fiscales reales.
- Validaciones: calculos, smoke fiscal, `compileall`.

## Documentos

- Mision: informes PDF/DOCX y contexto documental.
- Permisos: lectura dirigida; edicion con playbook.
- Limites: no duplicar fuente de datos.
- Puede tocar: `app/services/informe.py`, `templates/informes/*` si se autoriza.
- Debe evitar: informes generados reales.
- Validaciones: contexto, PDF/DOCX en datos de prueba.

## Frontend / UX movil

- Mision: mobile-first, drawer, templates, CSS y JS progresivo.
- Permisos: cambios pequenos en UI si se autoriza.
- Limites: no SPA, no navegacion paralela.
- Puede tocar: templates, partials, CSS, JS.
- Debe evitar: cambios fiscales/backend simultaneos.
- Validaciones: `node --check`, revision mobile.

## Seguridad / backups

- Mision: secretos, backups, restore, permisos y entorno.
- Permisos: auditoria en modo lectura; cambios solo con aprobacion.
- Limites: no mostrar secretos completos ni borrar backups.
- Puede tocar: docs, scripts de backup/deploy si se autoriza.
- Debe evitar: DB real y carpetas externas.
- Validaciones: backup/restore en copia, `bash -n`.

## Operacion comercial

- Mision: leads, clientes, propuestas y emails comerciales.
- Permisos: cambios comerciales con playbook.
- Limites: no enviar emails reales ni crear facturas emitidas sin confirmacion.
- Puede tocar: leads, clientes, propuestas, emails.
- Debe evitar: fiscalidad critica y SMTP real.
- Validaciones: flujo lead-propuesta-email mock.

