# Sistema Pericial

Aplicación web local para la gestión integral de actividad pericial en España. Está pensada para uso diario desde iPhone/Mac y cubre el flujo comercial, técnico y administrativo: leads, clientes, propuestas, expedientes, facturación, gastos, IVA interno, exportaciones para asesoría y backups.

## Stack

- Python + FastAPI
- Jinja2 templates
- SQLite local en `data/pericial.db`
- HTML/CSS mobile-first
- JavaScript mínimo
- Sin framework frontend

## Arquitectura

```text
app/main.py                Arranque FastAPI, routers y lógica histórica de expedientes
app/database.py            init_db(), creación de tablas y migración suave con asegurar_columna()
app/config.py              Rutas y carpetas de trabajo
app/routers/               Módulos nuevos separados
app/services/              Servicios auxiliares
templates/                 Pantallas Jinja2
templates/partials/        Shell común, navegación y partials reutilizables
static/mobile.css          Estilos principales mobile-first
static/app_shell.js        Drawer móvil/sidebar escritorio
data/pericial.db           Base de datos SQLite local
uploads/                   Adjuntos e imágenes
informes/                  Informes generados
fotos/                     Fotografías
backups/                   Backups ZIP manuales
exports/                   Exportaciones trimestrales para asesoría
```

Routers actuales:

- `dashboard.py`: panel operativo.
- `leads.py`: leads, contactos y tareas comerciales.
- `clientes.py`: clientes.
- `propuestas.py`: propuestas de encargo.
- `facturacion.py`: facturas, cobros, configuración fiscal, IVA y exportación.
- `gastos.py`: gastos deducibles.
- `backups.py`: backups manuales.

## Flujo Principal

```text
Lead
→ Propuesta
→ Aceptación
→ Cliente
→ Expediente
→ Factura
→ Cobro
→ Gastos
→ IVA trimestral
→ Exportación asesoría
→ Backup
```

## Módulos

### Dashboard

Ruta principal: `/dashboard`

Muestra leads pendientes, propuestas, expedientes recientes, facturas pendientes de cobro, IVA del trimestre actual, últimos gastos, backups recientes y acciones rápidas.

### Leads

Rutas principales:

- `/leads`
- `/leads/nuevo`
- `/leads/{lead_id}`

Funciones:

- Registro de contactos entrantes.
- Historial de llamadas, emails, WhatsApp, reuniones y notas.
- Tareas y próximas acciones.
- Base para vinculación posterior con clientes y propuestas.

Tablas: `leads`, `lead_contactos`, `lead_tareas`.

### Clientes

Rutas principales:

- `/clientes`
- `/clientes/nuevo`
- `/clientes/{cliente_id}`

Funciones:

- Datos fiscales y de contacto.
- Tipos de cliente: `particular`, `empresa`, `autonomo`, `entidad`, `extranjero`.
- Relación con propuestas y facturas.

Tabla: `clientes`.

### Propuestas

Rutas principales:

- `/propuestas`
- `/propuestas/nueva`
- `/propuestas/{propuesta_id}`
- `/propuestas/{propuesta_id}/crear-expediente`

Funciones:

- Propuestas vinculables a lead o cliente.
- Estados: `borrador`, `enviada`, `aceptada`, `rechazada`, `caducada`.
- Líneas de propuesta, base imponible, IVA y total.
- Vista imprimible.
- Conversión manual de propuesta aceptada a expediente.

### 🧠 Mejoras recientes en propuestas

- Mejora del flujo inicial desde lead → propuesta.
- Mayor coherencia en la conversión a expediente.
- Mejora en renderizado y estructura visual de la propuesta.
- Base preparada para automatización futura del flujo comercial.
- Mejor alineación con el módulo de facturación.

Tablas: `propuestas`, `propuesta_lineas`.

### Expedientes Periciales

Parte histórica del proyecto, principalmente en `app/main.py` y plantillas raíz.

Funciones:

- Alta, edición y consulta de expedientes.
- Visitas, estancias y patologías interiores/exteriores.
- Fotografías y mapas de patología.
- Inspección, habitabilidad y valoración.
- Generación de informes.
- Integraciones auxiliares de clima, catastro y direcciones.

Tablas principales: `expedientes`, `visitas`, `estancias`, `registros_patologias`, `registros_patologias_exteriores` y múltiples tablas auxiliares de inspección, habitabilidad, valoración y mapas.

### Facturación

Rutas principales:

- `/facturacion`
- `/facturacion/configuracion`
- `/facturacion/facturas`
- `/facturacion/facturas/nueva`
- `/facturacion/facturas/{factura_id}`
- `/facturacion/facturas/{factura_id}/imprimir`
- `/facturacion/iva`
- `/facturacion/exportar-trimestre`

Funciones:

- Facturas emitidas, líneas de factura y cobros parciales/totales.
- Configuración fiscal del emisor.
- Numeración definitiva al emitir: `F-YYYY-0001`.
- Estados: `borrador`, `emitida`, `cobrada`, `anulada`.
- Bloqueo fiscal tras emisión.
- Historial de eventos.
- Anulación controlada.
- Rectificativas básicas.
- Vista imprimible.

Tablas: `configuracion_fiscal`, `facturas_emitidas`, `factura_lineas`, `cobros`, `factura_eventos`.

Regla práctica de IRPF:

- Sociedad: IRPF sugerido 0.
- Autónomo nuevo: sugerencia 7%.
- Autónomo general: sugerencia 15%.
- Cliente particular o extranjero: IRPF 0.
- Cliente empresa/autónomo/entidad española: aplica sugerencia según configuración.
- Siempre editable manualmente mientras la factura está en borrador.

### Registro Técnico Tipo VeriFactu

Preparación técnica interna para futura compatibilidad VeriFactu/QR tributario.

Importante:

- No hay envío real a AEAT.
- No hay QR oficial definitivo.
- No hay firma electrónica ni certificados.
- Cobrar, imprimir o anular no debe regenerar el hash.

Servicio: `app/services/verifactu.py`

Funciones:

- Construir cadena estable de factura.
- Calcular hash SHA256.
- Obtener hash anterior.
- Generar `qr_payload` interno.
- Preparar registro técnico al emitir.

Columnas relevantes en `facturas_emitidas`:

- `hash_factura`
- `hash_anterior`
- `cadena_hash`
- `qr_payload`
- `qr_path`
- `verifactu_estado`
- `verifactu_fecha_generacion`
- `verifactu_fecha_envio`
- `verifactu_respuesta`

Las facturas antiguas pueden generar registro técnico una sola vez mediante ruta de backfill. Las rectificativas también generan hash al emitirse.

### Gastos Deducibles

Rutas principales:

- `/gastos`
- `/gastos/nuevo`
- `/gastos/{gasto_id}`

Funciones:

- Registro de facturas/tickets de gasto.
- Base imponible, IVA soportado y total.
- Marcado deducible sí/no.
- Adjunto PDF/imagen.
- Filtros por año, trimestre y deducible.

Tabla: `gastos`.

### Importación automática de tickets y facturas

Flujo general:

```text
iPhone / email / PDF / imagen
→ iCloud Drive
→ carpeta Pendientes
→ scripts/importar_gastos_icloud.py
→ OCR local en Mac
→ extracción local por reglas
→ inserción en tabla gastos
→ revisión en /gastos
```

Ruta de trabajo:

```text
/Users/carlosblanco/Library/Mobile Documents/com~apple~CloudDocs/Casa/Trabajo Arquitecto Técnico/Facturas/Pendientes
```

Carpetas usadas:

- `Pendientes`: entrada de imágenes, PDFs y JSON de Shortcuts.
- `Procesadas`: archivos importados correctamente.
- `Error`: duplicados, errores o entradas no importables.

Entrada desde iPhone/Mac:

- El Atajo captura foto o documento.
- Genera un JSON asociado.
- Incluye OCR inicial de Shortcuts.
- Guarda imagen + JSON en `Pendientes`.
- Separa ámbito `trabajo` / `casa`.

Ejemplo de JSON:

```json
{
  "fecha_captura": "2026-05-05_125556",
  "origen": "shortcut_mac",
  "ambito": "trabajo",
  "estado": "pendiente",
  "archivo_imagen": "2026-05-05_125556_factura.jpg",
  "ocr_text": "...",
  "proveedor": "",
  "nif_proveedor": "",
  "numero_factura": "",
  "concepto": "",
  "base_imponible": "",
  "iva_porcentaje": "",
  "iva_importe": "",
  "total": "",
  "deducible": true,
  "es_factura_probable": ""
}
```

Entrada por email/PDF:

- Si se deja un PDF o imagen en `Pendientes` sin JSON, el script autocrea un JSON mínimo.
- Esto permite importar adjuntos de email sin crear metadatos manualmente.

OCR local:

El sistema combina:

- OCR de Shortcuts.
- OCR local en Mac con Tesseract, pytesseract y Pillow.
- Texto extraído de PDFs con pdfplumber.

Dependencias Python:

```bash
pip install pytesseract pillow pdfplumber
```

Dependencias Homebrew:

```bash
brew install tesseract
brew install tesseract-lang
```

Extracción local sin IA:

- No usa OpenAI.
- No usa Ollama.
- El extractor está en `app/services/rule_based_invoice_extractor.py`.

Detecta:

- Proveedor.
- CIF/NIF.
- Fecha fiscal.
- Número de factura, ticket o pedido.
- Concepto.
- Categoría.
- Base imponible.
- Porcentaje IVA.
- Cuota IVA.
- Total.
- Tipo documental.

Patrones soportados:

- Factura completa.
- Factura simplificada.
- Tickets de gasolinera.
- Supermercados.
- Recibos tipo plataforma/pago online.
- PDFs con texto embebido.
- Imágenes con OCR parcial.
- Patrones `Subtotal / IVA / Total`.
- Tablas `BASE / % / CUOTA`.
- Tickets donde se reconstruye IVA con base + tipo.
- Tickets con total cerca de etiquetas como `IMPORTE` o `TOTAL EUROS`.

Categorías automáticas:

- `combustible`
- `suscripciones`
- `material_oficina`
- `informatica`
- `telefonia_internet`
- `transporte`
- `alojamiento`
- `comidas`
- `suministros`
- `herramientas`
- `parking_peajes`
- `otros`

La categoría se infiere por proveedor, concepto y texto OCR.

Duplicados:

- Se calcula SHA256 del archivo original.
- Se evita reimportar el mismo justificante.
- También se usan pistas como proveedor + número de factura cuando existen.

Estados de revisión en `/gastos`:

- `OK`
- `Revisar`
- `Rechazar`
- `Sin estado`

Criterios habituales:

- Validación matemática `base + IVA ≈ total`.
- Datos incompletos.
- OCR poco fiable.
- Documento no fiscal.
- Error de importación.

Importación manual desde interfaz:

- En `/gastos` existe el botón `Importar recibos`.
- Ejecuta manualmente `scripts/importar_gastos_icloud.py`.
- Muestra resumen de importados, duplicados y errores.

Previsualización:

- En la edición del gasto se muestra previsualización del justificante.
- Soporta imagen, PDF y enlace de apertura en nueva pestaña.

Comando manual:

```bash
cd /Users/carlosblanco/sistema_pericial
./.venv/bin/python scripts/importar_gastos_icloud.py
```

Filosofía del sistema:

- Local.
- Privado.
- Sin APIs de pago.
- Auditable.
- Pensado para revisión humana.
- No sustituye asesoramiento fiscal.
- Ante duda marca `REVISAR`.

### Resumen IVA

Ruta: `/facturacion/iva`

Calcula:

- IVA repercutido de facturas `emitida` o `cobrada`.
- IVA soportado de gastos deducibles.
- Resultado estimado.
- Detalle de facturas y gastos incluidos.

Notas:

- Usa `fecha` de factura/gasto, no `created_at`.
- Excluye facturas en borrador y anuladas.
- Excluye gastos no deducibles.
- Es una ayuda interna, no una presentación oficial del Modelo 303.

### Exportación Trimestral Para Asesoría

Ruta: `/facturacion/exportar-trimestre`

Servicio: `app/services/exportaciones.py`

Genera ZIP con:

- `resumen_iva.csv`
- `facturas_emitidas.csv`
- `gastos_deducibles.csv`
- `gastos_adjuntos/`
- `facturas_pdf/` si existen PDFs locales seguros

Seguridad:

- Filtra por `owner_user_id`.
- No incluye rutas absolutas.
- Adjuntos solo desde `uploads/`.

### Backups

Rutas:

- `/backups`
- `/backups/crear`
- `/backups/descargar/{filename}`
- `/backups/eliminar/{filename}`

Servicio: `app/services/backups.py`

Incluye en ZIP, si existe:

- `data/pericial.db`
- `uploads/`
- `informes/`
- `fotos/`
- `logs/`
- `.env.example`

No incluye `.git`, `.venv`, `__pycache__` ni backups anteriores.

## Navegación y UX

La app usa shell común:

- `templates/partials/_app_shell_start.html`
- `templates/partials/_app_shell_end.html`
- `templates/partials/_top_bar.html`
- `templates/partials/_drawer_nav.html`

Comportamiento:

- Móvil: top bar simple con drawer lateral.
- Escritorio: sidebar fijo.
- Estilos en `static/mobile.css`.
- JS en `static/app_shell.js`.
- Login, alta de usuario e impresión quedan fuera del shell.

## Instalación Local

```bash
git clone https://github.com/Gspott/sistema_pericial.git
cd sistema_pericial
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## ⚙️ Configuración `.env`

La aplicación utiliza un archivo `.env` para configuración local.

### ⚠️ Regla crítica

Si un valor contiene:

- espacios
- texto libre
- símbolos

👉 debe ir entre comillas.

### ✅ Correcto

````env
SMTP_FROM_NAME="Carlos Blanco"
BASE_URL="http://localhost:8000"

### ❌ Incorrecto

SMTP_FROM_NAME=Carlos Blanco

La base de datos local se crea/migra desde `app/database.py` sobre `data/pericial.db`.

## Control Manual del Servidor

El proyecto conserva scripts de operación local:

- `./disable_autostart.sh`: desactiva `LaunchAgents` antiguos.
- `./start_all.sh`: arranca FastAPI, DuckDNS, Caddy y mantiene el Mac despierto con `caffeinate`.
- `./stop_all.sh`: detiene FastAPI, Caddy y `caffeinate`.
- `./status.sh`: devuelve `RUNNING` o `STOPPED`.
- `./run_app.sh`: abre la app local `control_app.py`.

```md

### 🖥️ App local "Control Servidor"

La app `control_app.py` proporciona una interfaz gráfica para gestionar el servidor desde macOS.

Funciones:

- Iniciar / detener servidor con un clic

- Estado en tiempo real:

  - FastAPI

  - Caddy

  - caffeinate

  - DuckDNS

- Detección de errores en scripts

- Feedback visual inmediato

En Apple Silicon, ejecutar en `arm64` nativo si se reutiliza una `.venv` arm64.

## Recuperación Ante Pérdida De Equipo

El proceso de restauración completa está documentado en:

- [docs/RESTORE.md](docs/RESTORE.md)
- [docs/RECOVERY_CHECKLIST.md](docs/RECOVERY_CHECKLIST.md)

Resumen: clonar el repo, crear `.venv`, copiar `.env.example` a `.env`, restaurar `data/pericial.db` y carpetas `uploads/`, `informes/`, `fotos/` desde el último ZIP de iCloud, arrancar la app y probar un backup manual.

## Validaciones Útiles

```bash
python3 -m py_compile app/main.py app/database.py app/config.py
python3 -m py_compile app/routers/*.py app/services/*.py
python3 -c "import app.main"
````

## Estado Actual

- Sistema funcional local.
- Pensado para uso desde iPhone/Mac vía web.
- Facturación internamente robusta: bloqueo tras emisión, eventos, cobros, anulaciones y rectificativas básicas.
- Preparado técnicamente para futura compatibilidad VeriFactu, sin envío AEAT.
- Backups y exportaciones son manuales.

## Limitaciones

- No presenta oficialmente el Modelo 303.
- No comunica con AEAT.
- El QR VeriFactu es interno/no oficial.
- No hay Facturae.
- No hay OCR.
- No hay sincronización automática con Drive/iCloud/Dropbox.
- No hay restauración automática de backups.
- Conviene revisión con asesor fiscal antes de uso fiscal definitivo.

## Próximos Pasos Recomendados

- Automatizar backups con `launchd` en macOS.
- Integración de calendario para tareas y citas.
- Mejorar tests y smoke tests.
- Preparar despliegue local seguro.
- Implementar VeriFactu real cuando proceda.
- Añadir QR oficial cuando la especificación aplicable esté cerrada.
- Implementar Facturae si es necesario.
- Mejorar exportaciones avanzadas para asesoría.
