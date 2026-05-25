# Decision Log

Registro de decisiones operativas del harness. No sustituye ADRs.

## 2026-05-25 - Creacion de harness documental

Estado: Active

Decision:

- Crear `docs/harness/` como capa operativa para controlar contexto, permisos, memoria, playbooks, workflows, subagentes y validaciones de Codex.
- Mantener el harness separado de la logica de aplicacion.
- Tratar datos reales, secretos, backups, informes, uploads, logs y carpeta anidada `sistema_pericial/` como fuera de alcance por defecto.

Motivo:

- Aumentar autonomia de Codex sin reducir seguridad en un sistema local real con informacion sensible y modulos fiscales/documentales criticos.

