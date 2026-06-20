# AUTOSAVE-STANDARD-1

## Objetivo

Estandarizar el autoguardado en formularios largos o críticos sin sustituir el guardado manual existente.

## Infraestructura común

- Frontend común: `static/js/autosave.js`.
- Estado visual reusable: `templates/components/autosave_status.html`.
- Inicialización por atributos en el formulario:
  - `data-autosave-form`
  - `data-autosave-url`
  - `data-autosave-status`
  - `data-autosave-updated-at`
  - `data-autosave-debounce`

## Estados visuales

- `ready`: Listo para editar.
- `dirty`: Cambios pendientes.
- `saving`: Guardando...
- `saved`: Guardado HH:MM.
- `error`: Error al guardar.
- `conflict`: conflicto detectado por `updated_at`.

## Eventos

El cliente escucha `input`, `change` y `blur`. El debounce recomendado es 1000-1500 ms; el piloto de Valoración Workbench usa 1200 ms.

## Contrato JSON

Exito:

```json
{
  "ok": true,
  "updated_at": "...",
  "saved_at": "...",
  "message": "Guardado correctamente"
}
```

Conflicto:

```json
{
  "ok": false,
  "conflict": true,
  "message": "Otro proceso ha modificado el registro."
}
```

## Concurrencia

Cada formulario debe enviar el `updated_at` conocido. El endpoint compara ese valor con el registro actual y responde `409` con `conflict: true` si otro proceso o pestaña modificó el registro.

Los registros sin `updated_at` histórico no deben bloquearse por compatibilidad. El primer guardado debe rellenar el token.

## Errores y fallback

El cliente muestra error de red, hace un reintento simple y mantiene el submit manual como respaldo. El submit manual no debe eliminarse y, si recibe `updated_at`, debe aplicar la misma protección de conflicto.

## Piloto implantado

Valoración Workbench: microedición de testigos vinculados al expediente.

## Extensión posterior

Prioridad alta: patologías y visitas.

Prioridad media: CRM y costes.

Prioridad baja: propuestas y otros formularios largos.
