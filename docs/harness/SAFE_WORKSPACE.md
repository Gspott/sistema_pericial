# Safe Workspace

## Reglas de espacio seguro

- No ejecutar cambios sobre DB real.
- Usar copia temporal cuando haga falta validar migraciones o persistencia.
- No escribir fuera del repo.
- No tocar `$HOME`, keychain, iCloud, Desktop, Documents ni carpetas externas.
- No usar network salvo orden explicita.
- No enviar emails reales salvo orden explicita.
- No disparar DuckDNS, Caddy, tuneles ni deploy salvo autorizacion.
- No modificar `.env` ni variantes.
- No borrar ni rotar logs/backups.

## Datos generados

Quedan fuera de alcance por defecto:

- Bases SQLite.
- Backups.
- Uploads.
- Informes generados.
- Fotos.
- Logs.
- Exports.

## Validaciones seguras

Permitidas por defecto:

- Auditoria documental.
- Compilacion Python.
- `node --check` en JS tocado.
- `bash -n` en scripts sin ejecutar efectos.
- `git diff --check`.
- `git status --short`.

