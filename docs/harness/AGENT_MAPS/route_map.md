# Route Map

Indice manual inicial de areas de rutas conocidas. No inventar endpoints si no se inspeccionan.

## Areas conocidas

| Area | Ubicacion principal | Notas |
|---|---|---|
| Dashboard | `app/routers/dashboard.py` | Vista operativa general. |
| Leads | `app/routers/leads.py` | Captacion y seguimiento comercial. |
| Clientes | `app/routers/clientes.py` | Base de clientes. |
| Propuestas | `app/routers/propuestas.py` | Propuestas, lineas, PDF y email. |
| Emails | `app/routers/emails.py` | Email corporativo manual y registro. |
| Facturacion | `app/routers/facturacion.py` | Facturas, IVA, cobros, rectificativas y configuracion fiscal. |
| Gastos | `app/routers/gastos.py` | Gastos, adjuntos e importacion. |
| Backups | `app/routers/backups.py` | Crear, listar, descargar y eliminar backups. |
| Expedientes | `app/main.py`, `app/routers/expedientes.py` | Flujo historico y modular parcial. |
| Visitas | `app/main.py`, `app/routers/visitas.py` | Visitas y datos asociados. |
| Estancias | `app/main.py`, `app/routers/estancias.py` | Estancias, fotos y registros relacionados. |
| Patologias | `app/main.py`, `app/routers/patologias.py` | Registros interiores/exteriores y biblioteca. |
| Informes | `app/main.py`, `app/services/informe.py` | PDF, DOCX y contexto de informe. |
| Autenticacion | `app/main.py` | Login, logout, cookie y middleware. |
| PWA | `app/main.py`, `static/pwa.js`, `static/sw.js` | Manifest, service worker y assets moviles. |

## Uso

- Consultar este mapa antes de buscar rutas.
- Verificar con `rg` dirigido antes de editar.
- Si se confirma una ruta nueva, actualizar este mapa en un cambio documental.

## Nota Sobre Routers Legacy No Incluidos

`app/routers/expedientes.py`, `app/routers/visitas.py`,
`app/routers/estancias.py` y `app/routers/patologias.py` existen, pero no estan
incluidos en `app/main.py`.

Tratarlos como extraccion parcial/legacy. No hacer `include_router()` de estos
routers sin plan, mapa ruta a ruta, smoke tests y aprobacion humana.

Mapa detallado: [main_vs_routers_map.md](main_vs_routers_map.md).
