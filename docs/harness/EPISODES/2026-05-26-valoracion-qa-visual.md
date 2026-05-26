# 2026-05-26 - Valoracion QA Visual

## Contexto

QA visual de valoracion ejecutado contra una DB sandbox temporal con casos demo
ficticios. No se uso DB real ni uploads/informes reales.

Pantallas revisadas:

- `/valoracion/testigos`
- `/valoracion/testigos/1`
- `/expedientes/1/valoracion/testigos`
- `/informes/1/imprimir`
- `/generar-informe-pdf/1`

Viewports:

- Mobile: 390 x 844.
- Desktop: 1366 x 900.

## Resultado tecnico

- Biblioteca de testigos carga correctamente.
- Detalle de testigo carga correctamente.
- Seleccion de testigos por expediente carga correctamente.
- HTML imprimible de valoracion carga correctamente.
- PDF aislado de demo se genera correctamente: 8 paginas, `application/pdf`.
- No se detecto overflow horizontal en las pantallas revisadas.
- No aparecen bloques de patologias en el informe de valoracion revisado.

## Metricas observadas

- Biblioteca mobile: `scrollHeight` 19549, 31 cards, 63 acciones.
- Biblioteca desktop: `scrollHeight` 18078, 31 cards, 63 acciones.
- Detalle de testigo mobile: `scrollHeight` 2507, 6 cards, 4 acciones.
- Seleccion por expediente mobile: `scrollHeight` 5841, 8 cards, 22 acciones.
- Informe HTML mobile: `scrollHeight` 12754, 15 cards.
- Informe HTML desktop: `scrollHeight` 12618, 15 cards.

## Findings

### Alta prioridad

- La biblioteca de testigos es funcional, pero demasiado larga para uso real:
  30 testigos demo generan mas de 23 pantallas moviles y 63 acciones. Falta una
  vista compacta, paginacion simple o filtros fuertes por municipio, tipologia,
  validacion y reutilizable.
- La seleccion por expediente ofrece todos los testigos disponibles en un unico
  select. Con biblioteca creciente, sera dificil encontrar los 6 testigos
  adecuados. Debe filtrarse o buscarse por contexto del expediente.
- En informe y seleccion de vinculados aparecen valores numericos sin formato ni
  unidad: `200655.0`, `2388.75`, `84.0`, `1.0`. Esto degrada la lectura
  profesional de comparables, ajustes y valores unitarios.
- La seccion de comparables del informe es una ficha repetida por testigo, no una
  tabla de mercado ni un resumen comparativo. Es legible en mobile, pero poco
  eficiente para comparar seis testigos.

### Media prioridad

- La narrativa del informe sigue siendo pobre: los bloques muestran datos
  estructurados, pero falta una introduccion breve al mercado, criterio de
  seleccion de testigos, sintesis de homogeneizacion y lectura del resultado.
- En el metodo de valoracion aparece `Testigos comparables: -` aunque hay
  comparables en la seccion siguiente. El campo vacio crea ruido y parece
  contradiccion.
- En testigos vinculados, las acciones `Guardar vinculo`, `Ajustes` y `Quitar
  del expediente` tienen peso visual parecido. `Quitar` deberia verse como
  accion destructiva/secundaria.
- El detalle de testigo es claro, pero aun muy vertical. En desktop desaprovecha
  espacio disponible; podria usar grid de datos principales/caracteristicas.

### Baja prioridad

- El informe HTML tiene una portada con mucho espacio vertical en desktop. Para
  PDF puede ser correcto, pero como preview web exige demasiado scroll antes de
  llegar al contenido util.
- La biblioteca no muestra miniaturas/fotos en las cards aunque el detalle ya
  admite fotos manuales.
- Los textos demo mantienen `anos` por ASCII; en UI final convendria normalizar
  si el dataset de usuario usa `años`.

## Quick Wins Recomendados

1. Aplicar helpers de formato a comparables del informe y vinculados:
   importes con euro, superficies con m2, valores unitarios con euro/m2 y
   coeficientes como porcentaje o multiplicador consistente.
2. Anadir filtros simples en biblioteca: tipologia, municipio, estado de
   validacion y reutilizable, manteniendo busqueda libre.
3. En seleccion por expediente, permitir busqueda/filtro de testigos antes de
   vincular y priorizar testigos compatibles con municipio/tipologia.
4. Convertir la seccion de comparables del informe en resumen compacto:
   direccion, fuente, superficie, precio, euro/m2 base, coeficiente y euro/m2
   ajustado; dejar ficha completa como detalle secundario.
5. Ocultar campos vacios del metodo de valoracion cuando no aportan informacion,
   especialmente `Testigos comparables: -`.
6. Diferenciar visualmente `Quitar del expediente` como accion destructiva
   secundaria.
7. Mostrar miniatura de la primera foto del testigo en biblioteca cuando exista.

## Cambios Estructurales Recomendados

- Crear una vista de mercado por expediente con los 6 testigos en una tabla
  comparativa responsive y una narrativa corta de seleccion.
- Crear helper comun de presentacion de comparables para UI e informe para no
  duplicar formato.
- Disenar una pantalla/fase de captura asistida desde URL/captura, sin scraping
  ni OCR automatico hasta aprobacion especifica.
- Preparar QA visual recurrente con snapshots mobile/desktop sobre casos demo.

## Fuera De Alcance

- No se implementaron cambios de UI.
- No se implemento scraping, OCR ni descarga remota.
- No se toco calculo definitivo ni metodo de coste.
- No se migro legacy.
