# Context Strategy

## Orden obligatorio de lectura

1. `AGENTS.md`.
2. `docs/harness/PROJECT_RULES.md`.
3. `docs/harness/PERMISSIONS.md`.
4. `docs/harness/RISK_MAP.md`.
5. Playbook aplicable en `docs/harness/PLAYBOOKS/`.
6. Archivos afectados, con lectura parcial y dirigida.

## Contexto prohibido por defecto

No cargar ni inspeccionar de forma amplia:

- `uploads/`.
- `backups/`.
- Informes generados.
- `fotos/`.
- `logs/`.
- `.venv/`.
- Bases SQLite reales.
- `.env` y variantes con valores.
- Carpeta `sistema_pericial/` completa.

## Estrategia de lectura

- Preferir `rg` dirigido antes que abrir archivos completos.
- Leer funciones concretas, rangos pequenos y templates afectados.
- Evitar cargar datos binarios o generados.
- Evitar exploraciones amplias en carpetas sensibles.
- Confirmar estado real antes de editar.
- No asumir que la memoria de chats previos sigue vigente.

## Contexto minimo por tarea

- Modulo afectado.
- Riesgo segun `RISK_MAP.md`.
- Playbook aplicable.
- Archivos permitidos y prohibidos.
- Validaciones necesarias.
- Plan de rollback.

