# CRM Dashboard Operativo

Documento de auditoria y diseno incremental para convertir el dashboard desktop
en centro operativo del despacho sin crear un CRM generico ni romper los flujos
mobile-first.

Situacion: auditoria CRM-0, sin implementacion funcional.

## Objetivo

El dashboard desktop debe responder: que necesita hacer hoy el despacho.

Uso previsto:

- Captacion de abogados, administradores de fincas y otros prescriptores.
- Seguimiento comercial ligero.
- Campanas de email corporativo.
- Conversion a propuesta, cliente y expediente.
- Agenda operativa y radar de oportunidades.

No es objetivo replicar HubSpot, Google Analytics, un ERP ni un gestor de agenda
completo.

## Estado Actual Auditado

### Dashboard

Piezas actuales:

- Router: `app/routers/dashboard.py`.
- Ruta: `GET /dashboard`.
- Template: `templates/dashboard.html`.
- Navegacion: app shell/drawer existente.

El dashboard ya agrega informacion de leads, tareas, propuestas, expedientes,
facturacion, IVA, gastos y backups. Es una buena base tecnica, pero la jerarquia
todavia es de resumen general por modulos. Para desktop operativo necesita
priorizar acciones del dia, seguimiento comercial y conversion.

Fortalezas:

- Ya respeta `owner_user_id`.
- Usa consultas defensivas con `fetchone_safe`, `fetchall_safe` y `scalar_safe`.
- Ya muestra tareas vencidas o de hoy desde `lead_tareas`.
- Ya conecta propuesta aceptada sin expediente, expediente sin factura y
  propuesta enviada.

Carencias:

- Los bloques son tarjetas de modulo, no una mesa de trabajo densa.
- Las acciones administrativas de backup/IVA compiten con captacion.
- No hay pipeline visual comercial.
- No hay lectura de campanas, respuestas ni oportunidades profesionales.
- No existe aun estructura para analitica web o agenda externa.

### Leads, Contactos y Tareas

Piezas actuales:

- Router: `app/routers/leads.py`.
- Tablas: `leads`, `lead_contactos`, `lead_tareas`.
- Estados de lead actuales: `nuevo`, `contactado`, `pendiente_respuesta`,
  `propuesta_enviada`, `aceptado`, `rechazado`, `cerrado`.
- Tipos de contacto actuales: `llamada`, `email`, `whatsapp`, `reunion`, `nota`.

Estas tablas son el nucleo reutilizable para CRM ligero. Cubren captacion
inbound y seguimiento basico, pero no modelan bien una relacion profesional
reutilizable con abogados, administradores de fincas, inmobiliarias o
aseguradoras.

Recomendacion:

- Mantener `leads` como entrada comercial y oportunidad simple existente.
- No convertir `leads` en agenda profesional completa por acumulacion de
  columnas.
- Crear modelo CRM defensivo solo cuando haga falta separar contactos
  profesionales y oportunidades recurrentes.

### Clientes y Conversion

Piezas actuales:

- Router: `app/routers/clientes.py`.
- Tabla: `clientes`.
- Flujo documentado: lead puede convertirse a cliente y conservar `cliente_id`.

Recomendacion:

- Reutilizar `clientes` como destino de conversion y facturacion.
- No mezclar cliente facturable con contacto profesional prescriptor cuando no
  sean la misma persona.
- Mantener la regla actual: no inventar `expedientes.cliente_id` sin migracion
  planificada.

### Propuestas y Expedientes

Piezas actuales:

- Router: `app/routers/propuestas.py`.
- Tablas: `propuestas`, `propuesta_lineas`.
- Relaciones actuales: `lead_id`, `cliente_id`, `expediente_id`.
- Flujo: propuesta puede enviarse por email y crear/enlazar expediente.

Recomendacion:

- Usar propuestas como etapa de pipeline: propuesta enviada, aceptada y
  convertida a expediente.
- No duplicar importes ni logica de propuesta en CRM.
- Las oportunidades futuras deben poder apuntar a propuesta y expediente, pero
  la propuesta sigue siendo fuente economica.

### Emails Corporativos

Piezas actuales:

- Router: `app/routers/emails.py`.
- Servicios: `app/services/email_sender.py`, `email_templates.py`,
  `email_log.py`.
- Tabla: `emails_enviados`.
- `emails_enviados` guarda metadatos, estado y referencia de entidad.

Fortalezas:

- El envio corporativo manual y el envio de propuestas ya registran emails.
- `/emails/contactos` ya consulta emails desde emails enviados, clientes, leads
  y propuestas.

Carencias:

- No hay lectura de respuestas.
- No hay asociacion a campana.
- No hay asociacion automatica a contacto profesional.
- No hay timeline CRM unificado.

Recomendacion:

- CRM-2 debe partir de `emails_enviados`, no crear otro log de email.
- Las respuestas deben disenar primero como integracion separada; no asumir IMAP
  ni automatizacion sin fase propia.

## Mapa De Reutilizacion

| Necesidad CRM | Reutilizar ahora | Brecha | Fase sugerida |
|---|---|---|---|
| Seguimientos de hoy | `lead_tareas` | Solo ligado a lead | CRM-3 read-only inicial |
| Contacto comercial inbound | `leads` | No es contacto profesional recurrente | CRM-1 |
| Interacciones basicas | `lead_contactos` | Solo lead, no campana/oportunidad/expediente | CRM-1/2 |
| Email enviado | `emails_enviados` | Falta campana/respuesta/contacto | CRM-2 |
| Pipeline a propuesta | `propuestas.lead_id`, `estado` | Falta oportunidad profesional previa | CRM-1 |
| Conversion a expediente | `propuestas.expediente_id` | No hay vista cockpit | CRM-3 |
| Cliente facturable | `clientes` | No siempre es prescriptor | CRM-1 |
| Agenda futura | `lead_tareas.calendar_event_id` | No hay CalDAV activo | CRM-5 |
| WhatsApp manual | `lead_contactos.tipo=whatsapp` | No hay timeline general | CRM-6 |
| Analitica web | Ninguna tabla especifica | Integraciones futuras | CRM-4 |

## Arquitectura Minima Propuesta

### Principios

- SQLite defensivo y server-side rendering.
- Consultas por `owner_user_id` en toda pantalla CRM.
- No crear APIs de negocio paralelas.
- No enviar emails reales en smokes.
- No leer ni modificar datos reales durante pruebas.
- Desktop puede ser denso; mobile existente no debe cambiar.

### Modelo Futuro Candidato

CRM-1 deberia evaluar tablas nuevas defensivas:

- `contactos_profesionales`
- `crm_oportunidades`
- `crm_interacciones`
- `crm_campanas`

Motivo para prefijo parcial `crm_`:

- `contactos_profesionales` es un concepto propio claro.
- `interacciones`, `oportunidades` y `campanas` son terminos mas genericos y
  pueden chocar con usos futuros; el prefijo reduce ambiguedad.

Campos candidatos para `contactos_profesionales`:

- tipo: abogado, administrador_fincas, inmobiliaria, arquitecto, aseguradora,
  empresa, procurador, cliente.
- nombre, empresa_despacho, especialidad, zona, email, telefono, linkedin,
  origen, potencial, estado_relacion, ultima_interaccion, notas.

Campos candidatos para `crm_oportunidades`:

- contacto_id, lead_id, cliente_id, propuesta_id, expediente_id.
- estado: pendiente_contacto, contactado, respondio, reunion, colaboracion,
  dormido, perdido.
- titulo, servicio_objetivo, valor_estimado, proxima_accion, fecha_proxima,
  notas.

Campos candidatos para `crm_interacciones`:

- contacto_id, oportunidad_id, expediente_id, campana_id, email_enviado_id.
- tipo: email, llamada, reunion, whatsapp, visita, seguimiento.
- fecha, resumen, resultado, siguiente_accion, visible_en_timeline.

Campos candidatos para `crm_campanas`:

- nombre, objetivo, estado, fecha_inicio, fecha_fin, canal, notas.
- Metricas derivadas desde emails/interacciones; no duplicar si se pueden
  calcular.

### Primera Arquitectura Sin Esquema

Antes de crear tablas, hay un paso de bajo riesgo:

- Reordenar el dashboard como cockpit read-only usando datos ya existentes.
- Bloques: Hoy, Captacion, Comunicacion, Pipeline, Administracion secundaria.
- Usar `lead_tareas`, `leads`, `propuestas`, `emails_enviados` y expedientes.
- Anadir smokes de render y ownership.

Esto entrega valor rapido y reduce incertidumbre antes de abrir CRM-1 con DB.

## Riesgos

- Duplicar `leads` y `contactos_profesionales`: riesgo alto de doble fuente de
  verdad si no se define conversion/enlace.
- Emails reales: cualquier fase de CRM-2 debe mockear o aislar SMTP.
- Ownership: todas las consultas CRM deben filtrar por usuario.
- Dashboard pesado: demasiadas consultas en `/dashboard` pueden hacerlo lento;
  mantener limites y queries simples.
- CSS global: mejoras desktop no deben cambiar tarjetas o formularios mobile.
- Analitica web/CalDAV/WhatsApp: integraciones externas deben ser fases de
  diseno antes de conectar.
- Task pack documental: no existe `docs/harness/TASK_PACKS/docs_change.md`; las
  fases documentales deben usar `README.md`, `bugfix.md` con scope docs o crear
  un pack especifico en fase harness.

## Roadmap Incremental

### CRM-0 Auditoria

Situacion: completado en documentacion. No cambia app, DB ni templates.

### CRM-1A Dashboard Read-Only Con Datos Existentes

Objetivo: transformar `/dashboard` en cockpit desktop sin cambiar esquema.

Cambios sugeridos:

- Seccion Hoy: tareas de lead vencidas/hoy, propuestas aceptadas sin expediente,
  facturas emitidas pendientes, visitas si se detecta fuente segura.
- Seccion Captacion: leads nuevos/contactados/pendientes, propuestas enviadas,
  ultimos emails enviados.
- Seccion Pipeline: nuevo, contactado, propuesta, expediente, cerrado.
- Administracion pasa a banda secundaria.

Smokes:

- Dashboard renderiza con usuario demo.
- No muestra datos de otro usuario.
- Bloques principales aparecen aunque no haya datos.

### CRM-1B Modelo Minimo Defensivo

Objetivo: crear tablas CRM sin migrar leads ni clientes.

Cambios sugeridos:

- Crear `contactos_profesionales`, `crm_oportunidades`, `crm_interacciones`,
  `crm_campanas`.
- Usar `asegurar_columna()` y DB temporal en tests.
- No migrar datos existentes.

Smokes:

- Crear contacto profesional ficticio.
- Crear oportunidad vinculada a contacto.
- Crear interaccion.
- Crear campana.
- Ownership obligatorio.

### CRM-2 Emails

Objetivo: asociar `emails_enviados` a contacto/campana/oportunidad.

Cambios sugeridos:

- Asociacion manual inicial.
- Matching por email como sugerencia no bloqueante.
- Sin IMAP ni respuesta automatica.

Smokes:

- Email log se asocia a contacto.
- Campana calcula enviados/respuestas manuales.
- No se envia SMTP real.

### CRM-3 Dashboard Desktop Operativo

Objetivo: tablero denso de productividad.

Bloques:

- Hoy.
- Captacion.
- Comunicacion.
- Web.
- Pipeline.
- KPIs utiles.

Reglas:

- Desktop wide, tablas densas y filtros rapidos.
- Mobile se degrada o mantiene vista actual sin sustituir workflows.

### CRM-4 Captacion Web

Objetivo: preparar Plausible, Matomo y Google Business Profile.

Regla: no replicar Google Analytics. Guardar solo metricas utiles para
conversion: visitas, formularios, paginas y tendencias.

### CRM-5 Agenda

Objetivo: disenar integracion Apple Calendar/CalDAV.

Regla: empezar por lectura/manual y `calendar_event_id` existente en tareas.

### CRM-6 WhatsApp

Objetivo: registro manual y enlaces rapidos.

Regla: no automatizacion compleja ni APIs externas sin fase propia.

## Quick Wins

- Reordenar `/dashboard` por prioridad operativa: Hoy primero.
- Mover backups/IVA/exportaciones a zona secundaria.
- Mostrar emails recientes desde `emails_enviados`.
- Mostrar pipeline simple con datos actuales de leads/propuestas/expedientes.
- Anadir enlaces rapidos a `/leads`, `/emails`, `/propuestas` y contactos
  existentes sin duplicar CTAs del drawer.

## Pendientes Para Harness

- Crear task pack especifico `crm_change.md` o documentar uso de `bugfix.md` y
  `db_change.md` para fases CRM.
- Crear pattern de dashboard desktop SSR cuando CRM-1A implemente la primera
  version.
- Crear smokes de dashboard con fixtures temporales.
- Documentar integraciones externas como diseno antes de tocar red o secretos.
