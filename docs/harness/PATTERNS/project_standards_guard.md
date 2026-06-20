# PROJECT-STANDARDS-GUARD-1

## Proposito

Convertir los estandares transversales maduros de Sistema Pericial en reglas permanentes para nuevas tareas. Este documento no cambia comportamiento de negocio: define que debe preservarse cuando se toque codigo, templates o flujos afectados.

## Estandares Oficiales

### TIMEZONE-STANDARD-1

Todo manejo nuevo de fechas y horas debe pasar por `app/utils/timezone.py` o helper equivalente ya registrado.

Evitar en nuevas implementaciones:

- `datetime.now()` sin zona horaria.
- `datetime.utcnow()`.
- `date.today()` cuando represente fecha operativa del sistema.
- `CURRENT_TIMESTAMP` mostrado al usuario sin conversion.
- Fechas crudas en templates.

Toda fecha visible para usuario debe presentarse mediante `datetime_madrid`, `date_madrid` o helpers equivalentes. `CURRENT_TIMESTAMP` puede seguir usandose para compatibilidad SQLite, pero debe interpretarse como UTC cuando se muestra.

### AUTOSAVE-STANDARD-1

Todo formulario largo, tecnico, de inspeccion, valoracion o susceptible de perdida de informacion debe evaluar autosave.

Cuando aplique, debe usar:

- `static/js/autosave.js`;
- `templates/components/autosave_status.html`;
- estado visual estandar;
- `updated_at` o mecanismo equivalente de concurrencia;
- guardado manual como fallback.

Referencia detallada: [autosave_standard.md](autosave_standard.md).

### Seleccion Reactiva

Cuando un selector cambie plantilla, filtro, contexto, vista o contenido mostrado, el cambio debe ejecutarse en `change`.

No anadir botones `Aplicar`, `Aceptar`, `Cargar` o `Continuar` para cambios de contexto simples salvo que exista:

- operacion costosa;
- riesgo de perdida de datos;
- accion irreversible;
- confirmacion explicita necesaria.

Referencia de proyecto: plantillas de prospeccion CRM con cambio reactivo.

### Estado Visual

Toda operacion critica, lenta o recuperable debe mostrar al menos:

- pendiente;
- procesando;
- completado;
- error recuperable.

Evitar pantallas silenciosas tras acciones de guardado, generacion, envio o importacion.

### Concurrencia

Editores con autosave o formularios largos deben usar `updated_at` o un token equivalente. No se aceptan sobrescrituras silenciosas entre pestanas, sesiones o procesos.

### Tests

Toda mejora transversal debe incluir smoke tests o prueba antirregresion proporcional, y documentar que cubre y que no cubre.

### Mobile-First + Desktop

Las mejoras desktop son capas adicionales. No deben romper flujos moviles, Safari iOS/macOS ni inspeccion en campo.

### Documental y PDF

Las mejoras documentales deben respetar, cuando aplique:

- estructura PDF V2;
- bookmarks;
- anexos;
- perfiles;
- portadas;
- criterios visuales consolidados.

No duplicar logica de datos de informe fuera de `build_informe_context()` o fuentes canonicas equivalentes.

### Harness

Toda mejora relevante debe tener:

- plan;
- validaciones;
- cierre documentado;
- episodio cuando tenga valor historico.

Evitar desarrollos huerfanos sin trazabilidad.

## Reglas Maduras Detectadas

Tambien deben considerarse estandares operativos ya consolidados:

- navegacion principal mediante drawer/hamburguesa; no crear navegacion paralela;
- FastAPI, SQLite, Jinja2 y JavaScript minimo; no introducir SPA ni SaaS;
- soft delete solo donde el canon funcional lo permite;
- datos reales, backups, uploads, informes, fotos, logs y secretos fuera de alcance salvo orden explicita;
- PDF/DOCX comparten fuente de datos.

## Uso

Antes de cerrar una tarea transversal, revisar [project_standards_guard.md](../VALIDATION/project_standards_guard.md) y ejecutar `python3 scripts/audit_docs.py`.
