# Backend, endpoints e integraciones

Documento tematico de backend. La normativa resumida esta en `AGENTS.md`.

## Dependencias

Depende de:

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/revision_probatoria.md](revision_probatoria.md)
- [docs/pwa.md](pwa.md)

Puede impactar:

- Persistencia SQLite.
- Integraciones externas.
- Informes.
- PWA y autenticacion.
- Propuestas, PDFs comerciales y calculo de honorarios.

## Decisiones

Decision ID: API-001
Estado: Active
Categoria: Backend

Se permiten endpoints FastAPI minimos para disparar flujos existentes. No crear APIs de negocio paralelas ni endpoints que reimplementen logica ya existente.

## Madurez

- Backend FastAPI server-side: Activo.
- Endpoints auxiliares para flujos existentes: Experimental / condicionado a no crear logica de negocio paralela.
- `subprocess` para procesos existentes: Experimental / condicionado a justificacion clara.

## Principios

- FastAPI + Jinja server-side rendering.
- SQLite con `sqlite3.Row`.
- Preparar datos en backend y mantener templates simples.
- No crear APIs de negocio paralelas.
- Si se necesitan integraciones, se permiten endpoints minimos para disparar flujos existentes.
- Reutilizar flujos existentes antes de crear nuevos.
- Mantener consultas compactas y legibles.
- Usar funciones auxiliares existentes antes de crear nuevas.
- Respetar `owner_user_id` y helpers `get_owned_*` para control de acceso.

## Invariantes

- Los POST criticos deben seguir funcionando sin depender exclusivamente de JavaScript.
- SMTP/email no debe bloquear la operacion principal salvo decision explicita.
- No introducir APIs paralelas de negocio sin justificar.
- No cambiar rutas publicas sin actualizar navegacion, tests y docs.
- Mantener logica critica en backend, no en plantillas ni navegador.

## Integraciones externas

- El backend actua como coordinador ligero, interfaz web y gestor documental.
- Puede disparar automatizaciones externas mediante endpoints minimos.
- Se permite `subprocess` para lanzar procesos ya existentes cuando este justificado.
- No mover OCR pesado al frontend ni al servidor principal salvo peticion explicita.
- No reescribir pipelines funcionales.

Patron aprobado:

- Boton web.
- Endpoint FastAPI ligero.
- `subprocess` o script externo.
- Importador existente.
- Incorporacion documental al modulo correspondiente.

## Correo y SMTP

El contacto corporativo oficial es `contacto@carlosblancoperito.es` y el telefono visible profesional es `623 829 228`.

Configuracion SMTP recomendada en `.env`:

```env
SMTP_HOST=mail.carlosblancoperito.es
SMTP_PORT=465
SMTP_USER=contacto@carlosblancoperito.es
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=contacto@carlosblancoperito.es
```

Reglas activas:

- `.env` no debe commitearse.
- Usar credenciales reales del buzon configurado en `SMTP_USER`.
- Reiniciar FastAPI tras cambiar variables SMTP.
- `SMTP_PORT=465` usa `smtplib.SMTP_SSL`.
- Otros puertos usan `smtplib.SMTP` con `starttls()`.
- El envio SMTP comun vive en `app/services/email_sender.py`.
- La base visual corporativa vive en `app/services/email_templates.py`.
- Si falla el envio, probar primero una conexion manual con `smtplib.SMTP_SSL(...).login(...)` o `SMTP(...).starttls().login(...)` segun puerto.

Troubleshooting rapido:

- `WRONG_VERSION_NUMBER` suele indicar mezcla de STARTTLS con puerto 465; usar `SMTP_SSL`.
- Puerto 587 suele requerir `SMTP` + `STARTTLS`.
- Variables de entorno cargadas en terminal pueden quedar cacheadas; reiniciar el proceso FastAPI y revisar `.env`.
- Revisar logs del router de propuestas para el error SMTP real, sin exponer contrasenas.

## SQLite

- No modificar la base de datos salvo necesidad real.
- No borrar columnas SQLite.
- No recrear tablas para cambios menores.
- Usar `asegurar_columna()` cuando haga falta anadir columnas.
- Mantener compatibilidad con bases existentes.
- Evitar accesos directos a claves opcionales en `sqlite3.Row`; comprobar existencia o normalizar queries.

## Seguridad

- Usar rutas POST para acciones destructivas o duplicacion.
- Mantener ownership/validacion del usuario en acciones de registros, patologias y biblioteca.
- No tocar autenticacion salvo peticion expresa.
- No permitir open redirects: solo rutas internas que empiezan por `/` y no por `//`.

## Propuestas

El router `app/routers/propuestas.py` mantiene flujos server-side con formularios Jinja. No hay API JSON paralela para el generador de propuestas.

Reglas activas:

- `/propuestas/{id}/imprimir`, `/pdf` y `/enviar-email` usan la plantilla imprimible con el desglose de lineas cuando existe.
- `generar_pdf_propuesta_bytes()` acepta lineas y renderiza el mismo HTML actualizado que la vista imprimible.
- El email de propuesta se envia con texto plano, alternativa HTML con estilos inline y PDF adjunto.
- El envio por email debe conservar compatibilidad con clientes moviles y Gmail; no usar imagenes externas, scripts ni CSS remoto.
- Los servicios rapidos son endpoints POST clasicos que crean lineas normales en `propuesta_lineas` y redirigen con 303.
- Ratificacion judicial, desplazamientos/dietas, recargo por urgencia y suplemento por complejidad no son tablas ni catalogos independientes.
- Urgencia y complejidad calculan siempre sobre `base_imponible` sin IVA; no deben calcular sobre total con IVA.
- El recalculo de totales se centraliza en `recalcular_totales_propuesta()`.
- La validacion de importes no negativos es server-side para alta/edicion manual y servicios rapidos.
- El borrado de lineas exige `confirmar_eliminar` en servidor antes de borrar y recalcular.
- Los endpoints deben conservar validacion por `owner_user_id` mediante helpers `get_owned_*`.

## Emails corporativos manuales

El router `app/routers/emails.py` expone `/emails/nuevo` para enviar emails corporativos manuales desde la app y `/emails` como registro interno de envios.

Reglas activas:

- Mantener version texto plano y alternativa HTML corporativa.
- Escapar el cuerpo escrito por el usuario antes de insertarlo en HTML.
- Permitir solo adjuntos subidos desde el formulario, sin rutas arbitrarias.
- Limitar adjuntos a 10 MB.
- Reutilizar `app/services/email_sender.py` y `app/services/email_templates.py`.
- Registrar emails manuales, propuestas y futuros emails corporativos en `emails_enviados`.
- No guardar contrasenas, adjuntos binarios ni MIME completo; solo metadatos, resumen limitado, nombre de adjunto y estado.

Anti-patrones especificos:

- Crear un catalogo editable o motor avanzado de calculo sin fase planificada.
- Duplicar calculos entre formulario, PDF y backend.
- Calcular recargos sobre importes con IVA y volver a aplicar IVA.
- Recalcular totales si una validacion de linea falla.

## Anti-patrones

- Crear APIs de negocio paralelas.
- Crear endpoints que reimplementen logica ya existente.
- Introducir colas, workers, microservicios o arquitectura enterprise sin necesidad explicita.
- Mover reglas de negocio criticas al navegador.

## Criterios Done

- `bash scripts/validate_harness.sh` pasa.
- Rutas publicas afectadas estan documentadas.
- No se han creado APIs de negocio paralelas.
- Si se toca JS, cada archivo modificado pasa `node --check`.
- No se han usado datos reales ni integraciones externas sin orden explicita.
