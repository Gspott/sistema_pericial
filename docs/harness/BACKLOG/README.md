# Backlog Operativo

Memoria persistente de tareas pendientes para Codex. No sustituye issues externos ni planes activos; sirve para priorizar trabajo entre sesiones.

## Prioridades

- [critical.md](critical.md): riesgo de perdida de datos, seguridad, facturacion fiscal, autenticacion o backups.
- [high.md](high.md): regresiones operativas relevantes o deuda que bloquea cambios seguros.
- [medium.md](medium.md): mejoras importantes sin bloqueo inmediato.
- [low.md](low.md): limpieza, ergonomia o documentacion no urgente.
- [icebox.md](icebox.md): ideas aparcadas sin compromiso.

## Como Mover Tareas

- Subir prioridad si bloquea una fase, una validacion o un flujo operativo real.
- Bajar prioridad si hay mitigacion suficiente o no afecta al foco actual.
- Mover a plan activo cuando exista objetivo, alcance y validaciones.
- Archivar o eliminar solo si queda justificado en el diff o en plan completado.

## Formato Recomendado

```md
## Titulo

- Impacto:
- Modulos:
- Riesgo:
- Task Pack recomendado:
- Validaciones minimas:
- Bloqueo/no bloqueo:
- Dependencias:
```
