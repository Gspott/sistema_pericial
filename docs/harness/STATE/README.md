# Operational State

Snapshot corto para que Codex entienda el estado operativo sin depender del chat.

## Archivos

- [current_focus.md](current_focus.md): prioridad actual.
- [current_plan.txt](current_plan.txt): nombre del plan activo creado mas recientemente por `scripts/harness_new_plan.py`.
- [known_risks.md](known_risks.md): riesgos abiertos.
- [recent_changes.md](recent_changes.md): cambios relevantes recientes.
- [active_constraints.md](active_constraints.md): restricciones activas.

## Uso

- Leer antes de tareas grandes o ambiguas.
- Mantener breve: si requiere detalle, enlazar a la fuente normativa.
- Actualizar cuando cambie foco, riesgo o restriccion operativa.
- `current_plan.txt` lo actualizan scripts del harness; si queda vacio, el runner no cierra planes automaticamente.
