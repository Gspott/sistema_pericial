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
- Los servicios rapidos son endpoints POST clasicos que crean lineas normales en `propuesta_lineas` y redirigen con 303.
- Ratificacion judicial, desplazamientos/dietas, recargo por urgencia y suplemento por complejidad no son tablas ni catalogos independientes.
- Urgencia y complejidad calculan siempre sobre `base_imponible` sin IVA; no deben calcular sobre total con IVA.
- El recalculo de totales se centraliza en `recalcular_totales_propuesta()`.
- La validacion de importes no negativos es server-side para alta/edicion manual y servicios rapidos.
- El borrado de lineas exige `confirmar_eliminar` en servidor antes de borrar y recalcular.
- Los endpoints deben conservar validacion por `owner_user_id` mediante helpers `get_owned_*`.

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
