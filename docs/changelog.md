# Changelog documental

Registro de decisiones documentales y consolidaciones normativas. No sustituye a Git; sirve para trazabilidad de reglas del proyecto.

## Dependencias

Depende de:

- [AGENTS.md](../AGENTS.md)
- [docs/ia_workflow.md](ia_workflow.md)
- Documentos tematicos que declaran decisiones con Decision ID.

Puede impactar:

- Trazabilidad documental.
- Auditoria de decisiones.
- Coordinacion de futuras sesiones IA/humanas.

## 2026-05

### DOC-001

Cambio: Consolidacion normativa de `AGENTS.md` como puerta de entrada canonica.
Motivo: Reducir contradicciones y separar reglas activas de contenido historico.
Impacto: `AGENTS.md` resume canon, estado, invariantes, patrones y anti-patrones.

### DOC-002

Cambio: Separacion modular de documentacion en `/docs`.
Motivo: Evitar un unico documento acumulativo dificil de mantener.
Impacto: UX, PWA, informes, backend, revision probatoria y modelos de datos tienen documentos tematicos.

### DOC-003

Cambio: Incorporacion de contratos documentales, dependencias, impactos y madurez.
Motivo: Mejorar trazabilidad y coordinacion en cambios asistidos por IA.
Impacto: Cada documento tematico declara dependencias, posibles impactos y estado de decisiones.

### REV-001

Cambio: Canon de revision probatoria.
Motivo: Unificar detecciones y prioridad de siguiente accion.
Impacto: La revision detecta climatologia, cuadrantes, estancias, fotos, patologias e informe pendiente sin bloquear generacion manual.

### DATA-001

Cambio: Formula canonica de `rol_final`.
Motivo: Evitar formulas parciales o ambiguas en informes y helpers.
Impacto: Usar siempre `rol_final = registro.rol_patologia_observado or registro.rol_patologia_biblioteca`.

### DATA-002

Cambio: Separacion entre soft delete de biblioteca y borrado fisico de registros de caso.
Motivo: Evitar aplicar soft delete global donde el flujo operativo permite borrado real.
Impacto: Biblioteca/catalogos usan `activo`; registros de visita/caso pueden borrarse fisicamente si el flujo lo requiere.

### API-001

Cambio: Normalizacion de reglas de APIs y endpoints.
Motivo: Aclarar que se permiten endpoints minimos para disparar flujos existentes.
Impacto: No crear APIs de negocio paralelas ni endpoints que reimplementen logica ya existente.

### PWA-001

Cambio: Normalizacion de validacion JS.
Motivo: Evitar validar solo un archivo cuando se modifican otros scripts.
Impacto: Usar `node --check <archivo.js>` para cada JS modificado.

### PWA-002

Cambio: Normalizacion de versionado PWA.
Motivo: Evitar versiones fijas obsoletas de service worker.
Impacto: Usar `/sw.js?v=<version>` o incremento explicito cuando cambien assets criticos.

### DOC-004

Cambio: Consolidacion de anti-patrones.
Motivo: Hacer visibles las acciones que suelen generar regresiones.
Impacto: Se refuerza evitar navegacion paralela, CTAs duplicados, APIs paralelas, formulas alternativas de `rol_final` y hardcodes PWA.

### DOC-005

Cambio: Gobernanza documental continua.
Motivo: Evitar divergencias, referencias rotas, decisiones duplicadas y degradacion futura de la documentacion.
Impacto: Se anaden Definition of Done documental, reglas de migracion documental, indice semantico para IA y documento de gobernanza.

### DOC-006

Cambio: ADRs iniciales y onboarding IA.
Motivo: Dar trazabilidad estable a decisiones activas y orientar futuras sesiones asistidas por IA.
Impacto: Se crean ADRs para navegacion principal, drawer global, revision probatoria, `rol_final`, soft delete, endpoints minimos y generacion manual de informe; se crea `docs/onboarding_ia.md`.

### DOC-007

Cambio: Auditoria documental auxiliar.
Motivo: Automatizar deteccion de derivas conocidas.
Impacto: `scripts/audit_docs.py` verifica Decision ID duplicados, enlaces Markdown rotos, documentos vacios, hardcodes PWA, formulas alternativas de `rol_final`, reglas API ambiguas y sincronizacion `AGENTS.md` / `agents.md`.

### DOC-008

Cambio: Automatizacion y estabilidad operativa documental.
Motivo: Reducir drift, referencias rotas, decisiones duplicadas, inconsistencias semanticas y crecimiento desordenado.
Impacto: Se amplia `scripts/audit_docs.py` con validacion de estados, categorias, ADRs, contratos tematicos, titulos, README de ADRs y validaciones JS obsoletas.

### DOC-009

Cambio: Plantillas oficiales, grafo documental y deuda documental.
Motivo: Facilitar creacion consistente de ADRs, documentos, checklist, decisiones y entradas de changelog.
Impacto: Se crean `docs/templates/`, `docs/document_graph.md` y `docs/documentation_debt.md`.

### DOC-010

Cambio: Freeze del core normativo y CI documental.
Motivo: Proteger `AGENTS.md` como capa normativa compacta.
Impacto: Cambios en canon, invariantes o anti-patrones requieren ADR, changelog, impacto cruzado y auditoria; CI ejecuta `python3 scripts/audit_docs.py`.

### PROP-001

Cambio: Documentacion de propuestas con lineas de servicio estructuradas.
Motivo: Reflejar las Fases 1, 2 y 3 del generador de propuestas ya implementadas.
Impacto: Las lineas de `propuesta_lineas` son fuente economica de verdad cuando existen; se documentan categorias, servicios rapidos, PDF/imprimible, redondeo, validaciones no negativas, compatibilidad con propuestas antiguas y confirmacion server-side de borrado.

### EMAIL-001

Cambio: Documentacion de correo corporativo y envio HTML de propuestas.
Motivo: Reflejar el SMTP corporativo con SSL en puerto 465 y el email de propuestas con texto plano, HTML profesional y PDF adjunto.
Impacto: `.env.example`, despliegue, backend e informes documentan `contacto@carlosblancoperito.es`, `623 829 228`, `SMTP_SSL` para puerto 465 y `SMTP` + `STARTTLS` para otros puertos.

### EMAIL-002

Cambio: Modulo de email corporativo manual.
Motivo: Permitir envio desde `/emails/nuevo` con estilo HTML corporativo, fallback texto plano y adjunto opcional.
Impacto: El envio SMTP y la plantilla corporativa quedan centralizados en servicios reutilizables; propuestas reutiliza el helper comun sin cambiar su flujo.

### EMAIL-003

Cambio: Registro interno de emails enviados.
Motivo: Trazar emails manuales, propuestas y futuros emails corporativos enviados desde el sistema sin implementar bandeja IMAP.
Impacto: Se crea `emails_enviados`, se registra estado `enviado`/`error`, metadatos, resumen limitado y referencia opcional, sin almacenar adjuntos binarios ni MIME completo.
