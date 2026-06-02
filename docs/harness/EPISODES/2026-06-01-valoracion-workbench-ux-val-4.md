# 2026-06-01 - Valoracion workbench UX-VAL-4

## Resumen

Se anade microedicion SSR segura desde el panel lateral del workbench de valoracion.

## Cambios

- Nueva ruta `POST /expediente/{expediente_id}/valoracion/workbench/testigo/{testigo_id}`.
- Formulario pequeno en el panel para inclusion en calculo, peso, representatividad, motivo de ponderacion, motivo de exclusion y observacion tecnica breve.
- Reutiliza campos existentes de `valoracion_expediente_testigos`.
- Redirige de vuelta al workbench conservando filtro, orden, direccion y testigo seleccionado.
- Valida expediente de valoracion, ownership, testigo vinculado, peso 0-100 y representatividad permitida.
- Advierte de forma no bloqueante si un testigo queda excluido sin motivo.

## Invariantes

- Sin entidades nuevas.
- Sin JS obligatorio ni SPA.
- Sin edicion inline masiva ni spreadsheet.
- Sin cambios en patologias, inspecciones o informes.
- Sin adopcion automatica del valor final.

## Pendiente

- QA visual manual de la microedicion en iPhone y escritorio.
- Evaluar en fase futura si conviene registrar historial de cambios de ponderacion.
