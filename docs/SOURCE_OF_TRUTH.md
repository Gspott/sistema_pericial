# Source Of Truth

Indice de fuentes normativas para Sistema Pericial.

## Jerarquia

Si hay conflicto:

1. ADR activa en `docs/adr/`, cuando la decision existe.
2. Documento tematico fuente en `docs/`.
3. `docs/SOURCE_OF_TRUTH.md` como indice de autoridad.
4. `AGENTS.md` como indice corto.
5. `docs/harness/` como capa operativa para Codex, permisos, playbooks y validacion.
6. Documentacion historica/checklists, solo para procedimientos concretos.

## Tabla normativa

| Area | Fuente normativa | Tipo |
|---|---|---|
| Backend/reglas generales | [docs/backend.md](backend.md) | Spec operativa + guia tecnica |
| Modelo de datos | [docs/modelos_datos.md](modelos_datos.md) | Spec operativa |
| Informes/PDF/DOCX | [docs/informes.md](informes.md) | Spec operativa + checklist |
| UX/mobile | [docs/ux.md](ux.md) | Spec operativa |
| PWA/cache/service worker | [docs/pwa.md](pwa.md) | Spec operativa |
| Restore/recuperacion | [docs/RESTORE.md](RESTORE.md), [docs/RECOVERY_CHECKLIST.md](RECOVERY_CHECKLIST.md) | Guia historica + checklist |
| ADRs | [docs/adr/](adr/README.md) | Decisiones estables |
| Harness operativo | [docs/harness/](harness/CODEX_OPERATING_MANUAL.md) | Operacion Codex |
| Facturacion | [docs/facturacion.md](facturacion.md) | Spec operativa |
| Gastos | [docs/gastos.md](gastos.md) | Spec operativa |

## Como debe usarlo Codex

- Antes de tocar un area funcional, consultar este indice.
- Leer el documento tematico fuente antes del playbook.
- Usar `docs/harness/` para permisos, riesgo, validaciones y cierre.
- No duplicar reglas en harness si ya viven en la fuente normativa.
- Si aparece una nueva invariante, proponerla en el documento fuente correspondiente.

## Relacion entre docs y harness

`docs/` define el comportamiento esperado del sistema.

`docs/harness/` define como trabaja Codex de forma segura sobre ese comportamiento.

