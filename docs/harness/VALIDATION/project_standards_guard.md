# Project Standards Guard Checklist

## Cuando usarlo

Usar esta checklist en tareas que toquen formularios largos, fechas, templates, PDF/documentos, CRM, valoracion, visitas, patologias, costes, propuestas, dashboard o harness.

## Checklist

### Zona Horaria

- Las fechas nuevas usan `app/utils/timezone.py`.
- No se introduce `datetime.now()` ni `datetime.utcnow()` sin justificacion.
- Las fechas visibles en templates usan `datetime_madrid`, `date_madrid` o helper equivalente.
- Si se usa `CURRENT_TIMESTAMP`, se documenta si es persistencia SQLite y se convierte al mostrar.
- Tests cubren al menos un caso de hora local cuando hay riesgo de desfase.

### Autosave

- El formulario es corto y no critico, o se justifica por que no requiere autosave.
- Si es largo/critico, usa `static/js/autosave.js`.
- Existe estado visual de guardado.
- Se conserva guardado manual como fallback.
- Hay `updated_at` o token equivalente para detectar conflictos.
- Hay smoke de persistencia y conflicto cuando aplique.

### Seleccion Reactiva

- Selectores que cambian plantilla, filtro, contexto o vista reaccionan en `change`.
- No hay botones `Aplicar`, `Aceptar`, `Cargar` o `Continuar` para cambios simples.
- Si existe boton, la razon es operacion costosa, irreversible, con perdida potencial de datos o confirmacion explicita.

### Estado Visual

- Las operaciones lentas o criticas muestran pendiente/procesando/completado/error.
- Los errores recuperables conservan contexto y explican la siguiente accion.

### Concurrencia

- Los editores largos no sobrescriben silenciosamente cambios de otra pestana o proceso.
- Los endpoints AJAX devuelven conflicto claro cuando detectan `updated_at` obsoleto.

### Mobile-First + Desktop

- El flujo movil existente sigue disponible.
- La mejora desktop es una capa adicional, no un reemplazo opaco.
- No se introducen dependencias SPA ni patrones incompatibles con Safari iOS/macOS.

### Documental y PDF

- La salida documental usa fuentes canonicas.
- Si toca PDF V2, respeta bookmarks, anexos, perfiles y portadas existentes.
- No se duplica logica de informe fuera de servicios canonicos.

### Harness

- Hay plan activo antes de editar.
- Se ejecuta `python3 scripts/audit_docs.py`.
- Se ejecuta smoke scope adecuado.
- Se ejecuta `git diff --check`.
- Se registra episodio si la tarea consolida un estandar o una decision reutilizable.

## Validacion automatica

`scripts/audit_docs.py` avisa sobre posibles usos nuevos de `datetime.now()` o `datetime.utcnow()` en archivos Python modificados respecto a `HEAD`, excluyendo `app/utils/timezone.py` y tests. El aviso es informativo para no bloquear deuda historica, pero debe revisarse antes de cerrar una tarea.
