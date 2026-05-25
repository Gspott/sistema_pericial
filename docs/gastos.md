# Gastos

Spec operativa de gastos para Sistema Pericial.

## Fuente normativa

Fuente normativa: este documento.

## Dependencias

Depende de:

- [docs/backend.md](backend.md)
- [docs/facturacion.md](facturacion.md)
- [docs/modelos_datos.md](modelos_datos.md)

Puede impactar:

- Resumen IVA.
- Exportaciones.
- Adjuntos.
- Importaciones.
- Revision asistida.

## Alcance

Gastos cubre alta manual, edicion, adjuntos, importacion, deduplicado, categorias, deducibilidad e impacto en resumen/exportacion fiscal.

## Importacion

- La importacion debe reutilizar scripts existentes.
- No mover OCR pesado al frontend.
- Importacion parcial debe conservar errores y permitir revision.
- No usar recibos reales en tests.

## Adjuntos

- Adjuntos permitidos: PDF e imagenes soportadas por el flujo existente.
- No aceptar rutas arbitrarias.
- Borrar gasto puede borrar adjunto asociado solo dentro del flujo documentado.
- Tests deben usar archivos temporales.

## Deduplicado

- Debe evitar duplicados probables por proveedor, fecha, importe, numero factura o archivo original cuando exista.
- Un duplicado sospechoso debe poder quedar en revision, no romper toda la importacion.

## Categorias

- Categorias ayudan al resumen fiscal.
- Categoria desconocida debe degradar a revision o valor neutro, no romper.
- No inventar categorias fiscales sin decision humana.

## IVA y deducibilidad

- `base_imponible`, `iva_porcentaje`, `iva_importe` y `total` deben ser coherentes.
- `deducible` controla si entra en resumen/exportacion.
- IVA no deducible debe poder registrarse sin forzar deducibilidad.

## IA opcional o revision asistida

- OpenAI/OCR/IA son ayudas opcionales.
- Si IA no esta disponible, el flujo debe degradar a reglas locales o revision manual.
- No llamar IA/red en tests salvo orden explicita.

## Invariantes

- No tocar recibos reales en tests.
- No leer adjuntos reales salvo orden explicita.
- No usar red ni OpenAI por defecto.
- Importacion parcial no debe bloquear gestion manual de gastos.
- Los calculos fiscales de gastos se validan en backend.

## Edge cases

- Gasto duplicado: marcar o saltar sin romper importacion completa.
- Adjunto ausente: permitir registro si los campos minimos existen.
- OCR/IA no disponible: degradar a revision.
- Categoria desconocida: no romper resumen.
- IVA no deducible: no incluir como deducible.
- Importacion parcial: registrar importados, duplicados y errores.

## Criterios Done

- `bash scripts/validate_harness.sh` pasa.
- Tests usan temporales, no recibos reales.
- No hay red ni IA real.
- Los importes siguen coherentes.

## Enlaces

- [docs/backend.md](backend.md)
- [docs/facturacion.md](facturacion.md)
- [docs/harness/TASK_PACKS/bugfix.md](harness/TASK_PACKS/bugfix.md)
- [docs/harness/PLAYBOOKS/base_datos.md](harness/PLAYBOOKS/base_datos.md)
