# Deuda documental

## Aceptada

| Descripcion | Estado | Impacto | Accion recomendada |
|---|---|---|---|
| Documentos historicos no movidos para evitar romper referencias. | Aceptada | Mantiene compatibilidad de enlaces existentes. | Mantener indices `docs/recovery.md` y `docs/operations.md`; mover solo con redirecciones o revision completa de referencias. |

## Temporal

| Descripcion | Estado | Impacto | Accion recomendada |
|---|---|---|---|
| Duplicado/eliminacion exterior condicionado. | Temporal | Puede generar ambiguedad si se asume soporte completo. | Marcar como Active solo si existe endpoint/implementacion especifica documentada. |
| README de ADRs mantenido manualmente. | Temporal | Puede desincronizarse al crear nuevas ADRs. | Automatizar generacion o ampliar auditoria para validar metadatos contra README. |

## Critica

| Descripcion | Estado | Impacto | Accion recomendada |
|---|---|---|---|
| Ninguna deuda critica documentada en esta consolidacion. | Revisar | Sin impacto actual. | Revaluar en cada consolidacion normativa. |

## IA/documental

| Descripcion | Estado | Impacto | Accion recomendada |
|---|---|---|---|
| Necesidad futura de ampliar auditoria semantica. | IA/documental | El auditor detecta patrones conocidos, pero no interpreta toda contradiccion conceptual. | Anadir reglas gradualmente cuando aparezcan derivas reales. |
| Posible dashboard documental. | IA/documental | La trazabilidad existe en Markdown, pero no hay vista agregada. | Evaluar solo si el mantenimiento manual deja de ser suficiente. |
