# Episode: Desktop Expediente Detalle 2

## Fecha

2026-06-20


## Tarea

Implementar `desktop-expediente-detalle-2`.

## Plan asociado

desktop-expediente-detalle-2.md


## Task Pack usado

`docs/harness/TASK_PACKS/harness_change.md`

## Objetivo

Convertir el detalle de expediente en un centro de operaciones postvisita mas
util anadiendo en desktop un panel de navegacion de estancias en la sidebar,
sin cambiar rutas, permisos, persistencia, logica de negocio ni mobile-first.

## Archivos modificados

- `app/main.py`
- `templates/detalle_expediente.html`
- `tests/smoke/test_expediente_desktop_workbench.py`
- `docs/harness/PLANS/active/desktop-expediente-detalle-2.md`
- `docs/harness/EPISODES/2026-06-20-desktop-expediente-detalle-2.md`

## Validaciones ejecutadas

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `python3 -m pytest tests/smoke/test_expediente_desktop_workbench.py` (fallo de entorno: `python3` no tiene pytest instalado)
- `.venv/bin/python -m pytest tests/smoke/test_expediente_desktop_workbench.py -q`
- `bash scripts/finish_harness_task.sh --smoke-scope docs`
- `git diff --check`
- `git status --short`

## Resultado

Se anadio `preparar_estructura_estancias_desktop()` como helper read-only para
obtener, con una unica consulta agregada, las estancias del expediente y sus
indicadores disponibles:

- estado pendiente/revisada segun `calcular_estancia_rellena()`;
- total de patologias por estancia;
- total de fotos por estancia.

`detalle_expediente.html` recibe `estructura_estancias_desktop` y renderiza un
panel "Estructura del inmueble" dentro de `.desktop-sidebar`, despues de
"Acciones rapidas". Cada estancia permite:

- abrir la estancia con `/editar-estancia/{estancia_id}`;
- registrar datos reutilizando la misma ruta;
- registrar patologias con
  `/registrar-patologias/{visita_id}?estancia_id={estancia_id}#formulario_patologia_interior`;
- revisar la estructura con `/definir-estancias/{visita_id}#estructura-interior`.

La accion rapida general "Patologias" no se cambio.

## Warnings

Warnings historicos de `audit_docs.py` no introducidos por esta fase:

- monolito `app/main.py`;
- planes completados antiguos con secciones vacias.

El comando `python3 -m pytest ...` no esta disponible en el Python del sistema;
se valido con `.venv/bin/python`.

## Rollback

Revertir helper/contexto en `app/main.py`, panel/estilos en
`templates/detalle_expediente.html`, smoke ampliado y plan/episodio. No hay
cambios de datos, rutas, permisos ni persistencia.

## Memoria actualizada

Plan activo documenta auditoria de contexto, matriz de disponibilidad,
consulta nueva justificada y fuera de alcance.

## Decisiones humanas

No se requirio aprobacion adicional porque el cambio es lectura SSR + template.

## Proximos pasos

Aplicar este patron a siguientes workbenches: paneles de navegacion contextual
en sidebar solo cuando reduzcan saltos y reutilicen rutas existentes. Para una
fase posterior, complementar con validacion visual Playwright en 1280, 1366,
1440, 1920 y 2560.
