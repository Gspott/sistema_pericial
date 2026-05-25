# Risk Map

| Modulo | Riesgo | Archivos principales | Dependencias | Validacion minima | Pedir aprobacion humana cuando |
|---|---|---|---|---|---|
| Propuestas | Alto | `app/routers/propuestas.py`, `templates/propuestas/*`, `static/propuestas_*.js`, `app/services/propuestas_catalogo.py` | Leads, clientes, facturacion, SMTP, Playwright | `compileall`, `node --check` si JS, prueba de PDF/email mock | Cambian importes, estados, creacion de factura, PDF comercial o envio real. |
| Facturacion | Critico | `app/routers/facturacion.py`, `app/services/verifactu.py`, `templates/facturacion/*`, `app/services/exportaciones.py` | Clientes, propuestas, gastos, configuracion fiscal | Tests de calculo, emision, rectificativa, IVA y `compileall` | Cambian numeracion, emision, anulacion, rectificativas, hash, exportacion o fiscalidad. |
| Informes | Critico | `app/services/informe.py`, `templates/informes/imprimir.html` | Expedientes, visitas, patologias, fotos, Playwright, DOCX | Generar contexto/PDF/DOCX con datos de prueba | Cambia `build_informe_context()`, estructura PDF/DOCX o conclusiones tecnicas. |
| Emails | Alto | `app/routers/emails.py`, `app/services/email_sender.py`, `app/services/email_templates.py`, `app/services/email_log.py` | SMTP, propuestas, adjuntos, logs | Mock SMTP, validacion adjunto, `compileall` | Hay envio real, cambios SMTP, adjuntos o plantillas corporativas criticas. |
| Expedientes | Alto | `app/main.py`, `app/routers/expedientes.py`, templates de expedientes | Visitas, informes, Catastro, clientes/propuestas | CRUD smoke sobre DB temporal, `compileall` | Cambian borrados, rutas, ownership o relaciones con informes. |
| Gastos | Alto | `app/routers/gastos.py`, `scripts/importar_gastos_icloud.py`, extractores de factura | Uploads, OpenAI opcional, OCR, facturacion | Import mock, no datos reales, `compileall` | Cambia importacion, deducibilidad, borrado de adjuntos o llamadas IA. |
| Backups | Critico | `app/services/backups.py`, `app/routers/backups.py`, `backup*.sh`, templates backups | DB, uploads, informes, fotos, logs | Backup en copia/sandbox, `bash -n` | Crear/restaurar/borrar backups reales o cambiar alcance del zip. |
| Autenticacion | Critico | `app/main.py`, `app/config.py`, `templates/login.html` | Usuarios, cookies, sesiones | Login/logout smoke, cookie flags | Cambian sesiones, hash, alta usuario, rutas publicas o middleware. |
| Base de datos | Critico | `app/database.py` | Todo el sistema | Migracion sobre copia, `compileall` | Cambian tablas, columnas, defaults, constraints o borrados. |
| PWA/mobile | Medio-alto | `static/mobile.css`, `static/app_shell.js`, `static/pwa.js`, `static/sw.js`, partials nav | Safari iOS, cache, drawer | `node --check`, revision mobile, cache control | Cambia service worker, cache, navegacion principal o shell. |
| Integraciones externas | Alto | Catastro, clima, DuckDNS, Telegram, SMTP, OpenAI, Caddy scripts | Red, secretos, procesos externos | Mocks/timeouts, no network salvo orden | Se usa red real, tokens, tuneles, deploy o servicios externos. |

