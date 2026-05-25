# Playbook: Informes

## Que leer primero

- `docs/informes.md`.
- `docs/revision_probatoria.md`.
- `app/services/informe.py`.
- `templates/informes/imprimir.html`.

## Archivos sensibles

- `app/services/informe.py`.
- `templates/informes/imprimir.html`.
- Informes generados reales.
- Fotos reales.

## Acciones permitidas

- Usar `build_informe_context()` como fuente unica.
- Ajustar PDF/DOCX con datos de prueba.
- Mejorar tolerancia a datos faltantes.

## Acciones prohibidas

- Leer informes reales generados.
- Duplicar logica de contexto.
- Cambiar conclusiones tecnicas sin revision.
- Bloquear generacion manual por datos secundarios.

## Validaciones

- `python3 -m compileall app`.
- Smoke `build_informe_context()`.
- Generacion PDF/DOCX en datos de prueba.

## Senales de alarma

- Cambios simultaneos en PDF y DOCX sin contexto comun.
- Cambios en `rol_final`.
- Accesos directos a fotos reales.

## Rollback

- Revertir diff.
- Descartar documentos generados de prueba.

