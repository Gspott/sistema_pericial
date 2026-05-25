# Permissions

| Accion | Permiso | Condicion |
|---|---|---|
| Leer `docs/` | Permitido | Priorizar `AGENTS.md` y `docs/harness/`. |
| Leer codigo en `app/`, `templates/`, `static/` | Permitido | Solo contexto necesario y lectura parcial. |
| Leer secretos | Restringido | Solo nombres de variables; nunca valores completos. |
| Editar `docs/harness/` | Permitido | Mantener cambios pequenos y reversibles. |
| Editar documentacion fuera de `docs/harness/` | Requiere aprobacion | Debe justificarse impacto documental. |
| Editar facturacion | Requiere aprobacion humana | Incluye calculos, estados, numeracion, Verifactu y exportaciones. |
| Editar autenticacion | Requiere aprobacion humana | Incluye login, cookies, sesiones y usuarios. |
| Editar backups/restore | Requiere aprobacion humana | Incluye creacion, borrado, descarga y restauracion. |
| Editar deploy/acceso remoto | Requiere aprobacion humana | Incluye DuckDNS, Caddy, tuneles, puertos y scripts de arranque. |
| Tocar DB real | Prohibido | Usar copia temporal si se autoriza validar persistencia. |
| Leer DB real | Prohibido por defecto | Requiere orden explicita y modo solo lectura. |
| Borrar archivos | Prohibido | No usar `rm`, `git clean` ni equivalentes. |
| Shell destructivo | Prohibido | No ejecutar comandos que eliminen, sobrescriban o migren datos reales. |
| `git reset`, `git rebase`, `git clean` | Prohibido | Salvo instruccion humana explicita y concreta. |
| Enviar emails reales | Prohibido por defecto | Requiere orden explicita. |

