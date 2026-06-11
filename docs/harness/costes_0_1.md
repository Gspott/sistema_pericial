# Costes 0-1

Diseno inicial para la base propia de costes de reparacion. Fase limitada a
arquitectura y modelo de datos; no conecta costes con patologias ni implementa
OCR, importador BC3 o interfaz de workbench.

## Contexto

- Proyecto local privado, SQLite-first, FastAPI/Jinja.
- El proyecto no usa migraciones separadas; el patron activo vive en
  `app/database.py` mediante `init_db()`, `CREATE TABLE IF NOT EXISTS`,
  columnas defensivas cuando aplica e indices idempotentes.
- Los tests de persistencia usan DB temporal mediante `tests/conftest.py` y no
  deben leer ni escribir `data/pericial.db`.
- La navegacion principal vive en drawer/hamburguesa. COSTES-1 no requiere ruta
  ni entrada de navegacion.

## Modelo

La base de costes queda inspirada en una estructura BC3/FIEBDC, pero como
modelo propio y editable en fases posteriores:

- `costes_bases`: cabecera de base, ambito territorial, origen, version y fecha.
- `costes_capitulos`: capitulos jerarquicos por base mediante `parent_id`.
- `costes_conceptos`: partidas y conceptos simples con codigo, tipo, unidad,
  resumen, descripcion, precio, moneda, estado y ambito temporal/territorial.
- `costes_descompuestos`: lineas de descomposicion de una partida, con hijo
  opcional, rendimiento, precio unitario, importe y orden.
- `costes_fuentes`: trazabilidad de origen/captura por base o concepto.
- `costes_capturas`: evidencias graficas futuras y JSON extraido, sin OCR en
  esta fase.

## Indices

Indices idempotentes sobre:

- `base_id` en capitulos, conceptos y fuentes.
- `codigo` en capitulos, conceptos y descompuestos.
- `resumen` y `estado` en conceptos.
- `concepto_padre_id` en descompuestos.
- `concepto_id` en fuentes/capturas y `estado` en capturas.

## Compatibilidad

- No se borran ni renombran tablas existentes.
- No se modifican patologias, expedientes, inspecciones, valoraciones, CRM,
  emails ni facturacion.
- No hay rutas nuevas, APIs de negocio ni navegacion nueva.
- La idempotencia se valida ejecutando `init_db()` dos veces sobre SQLite
  temporal.

## Fuera De Alcance

- OCR.
- Importador BC3/FIEBDC.
- Conexion con patologias o informes.
- Calculo productivo de reparaciones.
- Workbench escritorio.

## Siguiente Fase

COSTES-2: workbench escritorio para alta, busqueda y edicion controlada de
bases/capitulos/conceptos, manteniendo la desconexion con patologias hasta una
fase posterior aprobada.
