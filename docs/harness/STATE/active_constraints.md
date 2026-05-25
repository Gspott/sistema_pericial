# Active Constraints

- No tocar DB real, backups, uploads, informes, fotos, logs ni secretos.
- No introducir SPA, React, Vue, Angular, PostgreSQL ni SaaS.
- No usar red, SMTP real ni integraciones externas sin orden explicita.
- No cambiar rutas publicas, service worker, facturacion fiscal, auth, deploy o restore sin aprobacion cuando aplique.
- Cambios funcionales deben usar Task Pack, playbook y validaciones.
- Cambios documentales deben pasar `python3 scripts/audit_docs.py`.
