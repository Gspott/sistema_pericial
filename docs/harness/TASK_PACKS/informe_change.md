# Task Pack: Informe Change

## Cuando usarlo

Para contexto de informe, PDF, DOCX y plantillas de impresion.

## Cuando NO usarlo

No usar para cambios de estancias/patologias que modifiquen persistencia; combinar con `db_change.md` si hay esquema.

## Riesgo base

Critico.

## Archivos normalmente permitidos

- `app/services/informe.py` si esta aprobado.
- `templates/informes/imprimir.html` si esta aprobado.
- Tests de contexto.

## Archivos normalmente prohibidos

- Informes reales generados.
- Fotos reales.
- DB real.
- Playwright real salvo orden explicita.

## Lectura previa obligatoria

- `docs/informes.md`.
- `docs/revision_probatoria.md`.
- `docs/harness/PLAYBOOKS/informes.md`.

## Playbook relacionado

`docs/harness/PLAYBOOKS/informes.md`.

## Fuente normativa

- [docs/informes.md](../../informes.md)

## Checklist antes de editar

- Verificar fuente de datos.
- Confirmar si PDF y DOCX comparten contexto.
- Usar datos de prueba.
- No bloquear generacion manual por datos secundarios.

## Validaciones obligatorias

- `bash scripts/validate_harness.sh`.
- Smoke de `build_informe_context()`.

## Validaciones recomendadas

- Generacion PDF/DOCX aislada solo si es trivial y autorizada.

## Senales de alarma

- Logica duplicada entre PDF y DOCX.
- Cambio de conclusiones tecnicas.
- Acceso a fotos/informes reales.

## Cuando pedir aprobacion humana

Si cambia estructura de informe, conclusiones, criterios periciales o generacion real de documentos.

## Rollback

Revertir diff y descartar documentos temporales.

## Criterios Done

- Contexto minimo valido.
- PDF y DOCX no divergen.
- No se han leido informes reales.

## Mini TASK_ENVELOPE

- Tipo de informe:
- Fuente de datos:
- PDF/DOCX afectado:
- Datos de prueba:
- Validaciones:
- Rollback:
