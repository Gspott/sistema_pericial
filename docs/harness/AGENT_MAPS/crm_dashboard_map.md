# CRM Dashboard Map

Mapa de reutilizacion para evolucionar el dashboard desktop como centro
operativo del despacho.

## Rutas Y Modulos Existentes

| Area | Ubicacion | Uso CRM potencial |
|---|---|---|
| Dashboard | `app/routers/dashboard.py`, `templates/dashboard.html` | Cockpit operativo desktop. |
| Leads | `app/routers/leads.py`, `templates/leads/` | Captacion, tareas y contactos comerciales existentes. |
| Clientes | `app/routers/clientes.py`, `templates/clientes/` | Destino de conversion y facturacion. |
| Propuestas | `app/routers/propuestas.py`, `templates/propuestas/` | Pipeline comercial, envio email y conversion a expediente. |
| Emails | `app/routers/emails.py`, `templates/emails/` | Registro de comunicaciones enviadas y contactos por email. |
| Expedientes | `app/main.py` | Produccion pericial tras conversion. No tocar routers legacy. |
| Facturacion | `app/routers/facturacion.py` | Cobro pendiente y administracion secundaria del cockpit. |

## Tablas Existentes Reutilizables

- `leads`: entrada comercial/inbound actual.
- `lead_contactos`: interacciones basicas ligadas a lead.
- `lead_tareas`: seguimientos pendientes y agenda ligera.
- `clientes`: clientes facturables.
- `propuestas`: estado comercial, envio y conversion a expediente.
- `emails_enviados`: log unico de emails corporativos.
- `expedientes`: trabajos periciales activos.

## Flujo Recomendado

```text
contacto profesional -> oportunidad -> interaccion/email -> propuesta -> expediente
                    \-> tarea/seguimiento -> campana
```

El flujo real debe reutilizar `leads`, `lead_tareas`, `lead_contactos`,
`emails_enviados`, `propuestas`, `clientes` y `expedientes` antes de crear
entidades nuevas.

## Huecos Detectados

- No existe contacto profesional reutilizable independiente de lead/cliente.
- No existe oportunidad CRM independiente.
- No existe campana CRM.
- No existe timeline general que una contacto, oportunidad, expediente, campana
  y email.
- No existe lectura de respuestas de email.
- No existe analitica web, CalDAV ni WhatsApp Business integrado.

## Reglas Para Futuras Fases

- No crear CRM generico.
- No usar SMTP real en smokes.
- No tocar datos reales ni secretos.
- No crear APIs de negocio paralelas.
- No activar routers legacy de expedientes/visitas/estancias/patologias.
- Mantener mobile-first; las mejoras intensivas pertenecen al dashboard
  desktop.
- Usar DB temporal en cualquier fase de esquema.
