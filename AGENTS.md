# AGENTS.md

Indice operativo para Codex en Sistema Pericial.

AGENTS.md es indice, no enciclopedia. El detalle normativo vive en `docs/` y, para trabajo autonomo con Codex, en `docs/harness/`.

Ultima consolidacion normativa: 2026-05
Documento canonico: AGENTS.md
Alias sincronizado: agents.md si existe.

## Lectura obligatoria

Antes de tocar archivos, leer en este orden:

1. [docs/harness/PROJECT_RULES.md](docs/harness/PROJECT_RULES.md)
2. [docs/harness/PERMISSIONS.md](docs/harness/PERMISSIONS.md)
3. [docs/harness/CONTEXT_STRATEGY.md](docs/harness/CONTEXT_STRATEGY.md)
4. [docs/harness/RISK_MAP.md](docs/harness/RISK_MAP.md)
5. [docs/harness/CODEX_OPERATING_MANUAL.md](docs/harness/CODEX_OPERATING_MANUAL.md)
6. [docs/harness/VALIDATION/minimal_checks.md](docs/harness/VALIDATION/minimal_checks.md)
7. [docs/harness/GOLDEN_PRINCIPLES.md](docs/harness/GOLDEN_PRINCIPLES.md)
8. Playbook aplicable en `docs/harness/PLAYBOOKS/`.
9. Documento tematico afectado en `docs/`.

## Reglas criticas

- Sistema Pericial es una aplicacion local privada, no SaaS.
- Stack real: FastAPI, SQLite, Jinja2, HTML/CSS mobile-first y JavaScript minimo.
- No introducir SPA, React, Vue, Angular, PostgreSQL ni arquitectura SaaS.
- No tocar datos reales, secretos completos, bases SQLite, backups, uploads, informes, fotos ni logs salvo autorizacion explicita.
- No modificar la carpeta anidada `sistema_pericial/` sin decision humana.
- No crear APIs de negocio paralelas.
- Reutilizar flujos existentes antes de crear nuevos.
- No hacer refactors grandes sin plan previo.
- No cambiar facturacion, autenticacion, backups/restore, deploy, rutas publicas o service worker sin revisar riesgo y aprobacion humana cuando aplique.
- No hardcodear versiones fijas u obsoletas de service worker/PWA.
- Validar cualquier JS modificado con `node --check <archivo.js>`.
- Mantener `AGENTS.md` y `agents.md` sincronizados si ambos existen.

## Canon funcional resumido

- Navegacion principal activa: hamburguesa izquierda + drawer.
- `_top_nav.html` es patron secundario/legacy.
- Drawer `+` para altas globales.
- CTA contextual solo si aporta contexto real, pre-relleno o reduce pasos.
- Mobile first y compatibilidad Safari iOS/macOS.
- La visita no debe bloquearse por campos tecnicos secundarios.
- Separar "completo para continuar visita" de "completo tecnicamente para informe".
- Revision probatoria: climatologia, cuadrantes, estancias, fotos, patologias e informe pendiente.
- Informe manual disponible aunque no sea CTA recomendada si faltan datos.
- Formula canonica: `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.
- Soft delete solo para biblioteca/catalogos mediante `activo`.
- Registros de caso/visita pueden tener borrado fisico si el flujo lo contempla.

## Documentacion tematica

- UX, navegacion y mobile: [docs/ux.md](docs/ux.md)
- PWA/service worker: [docs/pwa.md](docs/pwa.md)
- Informes/PDF/DOCX: [docs/informes.md](docs/informes.md)
- Backend/endpoints/integraciones: [docs/backend.md](docs/backend.md)
- Revision probatoria: [docs/revision_probatoria.md](docs/revision_probatoria.md)
- Modelos de datos: [docs/modelos_datos.md](docs/modelos_datos.md)
- Workflow IA: [docs/ia_workflow.md](docs/ia_workflow.md)
- Gobernanza documental: [docs/documentation_governance.md](docs/documentation_governance.md)
- Changelog: [docs/changelog.md](docs/changelog.md)
- ADRs: [docs/adr/README.md](docs/adr/README.md)

## Matriz rapida

| Si modificas | Lee primero |
|---|---|
| Navegacion, drawer, CTAs | [docs/ux.md](docs/ux.md), [docs/harness/PLAYBOOKS/jinja.md](docs/harness/PLAYBOOKS/jinja.md) |
| PWA, service worker, offline | [docs/pwa.md](docs/pwa.md), [docs/harness/PLAYBOOKS/css_mobile.md](docs/harness/PLAYBOOKS/css_mobile.md) |
| Informes, PDF, DOCX | [docs/informes.md](docs/informes.md), [docs/harness/PLAYBOOKS/informes.md](docs/harness/PLAYBOOKS/informes.md) |
| Revision probatoria | [docs/revision_probatoria.md](docs/revision_probatoria.md) |
| Datos, roles, soft delete | [docs/modelos_datos.md](docs/modelos_datos.md), [docs/harness/PLAYBOOKS/base_datos.md](docs/harness/PLAYBOOKS/base_datos.md) |
| FastAPI, endpoints, subprocess | [docs/backend.md](docs/backend.md) |
| Propuestas | [docs/harness/PLAYBOOKS/propuestas.md](docs/harness/PLAYBOOKS/propuestas.md) |
| Facturacion | [docs/harness/PLAYBOOKS/facturacion.md](docs/harness/PLAYBOOKS/facturacion.md) |
| Emails | [docs/harness/PLAYBOOKS/emails.md](docs/harness/PLAYBOOKS/emails.md) |
| Backups/restore | [docs/harness/PLAYBOOKS/backups_restore.md](docs/harness/PLAYBOOKS/backups_restore.md) |
| Secretos | [docs/harness/PLAYBOOKS/secretos.md](docs/harness/PLAYBOOKS/secretos.md) |

## Validaciones

Primer check documental obligatorio:

```bash
python3 scripts/audit_docs.py
```

Checks base:

```bash
python3 -m compileall app
node --check <archivo.js>
bash -n start_all.sh start_server.sh stop_all.sh status.sh backup.sh backup_now.sh
git diff --check
git status --short
```

Para cambios solo documentales, usar:

```bash
python3 scripts/audit_docs.py
git diff --check
git status --short
```

## Cierre esperado

Despues de cada tarea, responder con:

1. Explicacion breve.
2. Archivos modificados.
3. Cambios exactos.
4. Validaciones ejecutadas.
5. Notas de compatibilidad o riesgos.
6. Confirmacion explicita de lo que no se ha tocado.

<!-- audit sync -->
