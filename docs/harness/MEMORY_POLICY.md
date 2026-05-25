# Memory Policy

## Tipos de memoria

| Tipo | Donde vive | Uso |
|---|---|---|
| Decision permanente | ADR en `docs/adr/` | Arquitectura, UX, datos, informes, PWA, backend o fiscalidad. |
| Decision operativa | `docs/harness/DECISION_LOG.md` | Reglas de trabajo, restricciones de agente y criterios de operacion. |
| Bug temporal | Goal o playbook aplicable | Incidencias pendientes, smoke tests y pasos de reproduccion. |
| Observacion puntual | Respuesta de cierre | No convertir en regla sin validacion. |

## Reglas

- No asumir contexto antiguo.
- Verificar estado real antes de editar.
- No convertir preferencias temporales en reglas permanentes.
- Si una decision afecta arquitectura, UX, datos, informes, PWA, backend o fiscalidad, proponer ADR.
- Si una decision afecta solo al modo de trabajo de Codex, registrar en `DECISION_LOG.md`.
- No almacenar secretos, rutas privadas sensibles ni datos personales innecesarios.

