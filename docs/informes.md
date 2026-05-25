# Informes periciales, PDF y DOCX editable

Documento tematico de informes. La normativa resumida esta en `AGENTS.md`.

## Fuente normativa

Fuente normativa: este documento.

Las reglas oficiales de generacion de informes, PDF/DOCX editable, completitud tecnica y checklist de informe viven aqui.

## Dependencias

Depende de:

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/revision_probatoria.md](revision_probatoria.md)
- [docs/backend.md](backend.md)

Puede impactar:

- Generacion PDF.
- DOCX editable.
- Revision probatoria.
- Modelos de datos de patologias y estancias.
- Propuestas imprimibles y PDFs comerciales.

## Decisiones

Decision ID: INF-001
Estado: Active
Categoria: Informes

La generacion de informe es manual y debe seguir disponible, aunque no sea CTA recomendada cuando falten datos probatorios.

## Madurez

- Generacion HTML/PDF: Activo.
- DOCX editable Apple Pages: Activo.
- DOCX legacy: Legacy / respaldo temporal si sigue existiendo.
- Checklist de informe: Activo.

## Flujo principal

- El HTML/PDF es la version visual principal del informe.
- El DOCX editable es una version secundaria pensada para rematar redaccion en Apple Pages/macOS.
- El DOCX antiguo/legacy se mantiene como respaldo temporal si sigue existiendo.
- No convertir PDF a DOCX.
- No convertir HTML a DOCX de forma directa si compromete compatibilidad.
- Usar `build_informe_context()` como fuente unica de datos para PDF y DOCX editable.

Flujo recomendado:

- Datos expediente -> `build_informe_context()` -> HTML/PDF profesional.
- Datos expediente -> `build_informe_context()` -> DOCX editable Pages.

## Invariantes

- PDF y DOCX deben compartir fuente de datos.
- `build_informe_context()` es la fuente principal de composicion.
- No duplicar logica de informe en plantillas o rutas.
- Un informe sin visita/fotos debe degradar de forma controlada, no romper.
- La generacion manual debe seguir disponible aunque existan advertencias.

## Rutas

- `/informes/{expediente_id}/imprimir`: vista HTML imprimible del informe.
- `/generar-informe-pdf/{expediente_id}`: genera PDF profesional desde HTML/Playwright.
- `/generar-informe-docx-editable/{expediente_id}`: genera DOCX editable compatible con Apple Pages desde `build_informe_context()`.
- `/generar-informe/{expediente_id}`: DOCX antiguo/legacy; mantener como respaldo si existe.

## HTML/PDF como estandar visual

`templates/informes/imprimir.html` es la referencia visual principal del informe pericial.

Debe mantener:

- Formato DIN A4.
- Portada profesional.
- Indice despues de portada.
- Numeracion de paginas en PDF.
- Secciones claras.
- Estancias tipo card.
- Patologias tipo card.
- Observaciones tecnicas destacadas.
- Fotografias homogeneas.
- Pies de foto automaticos.
- Conclusiones destacadas.
- Diseno apto para impresion.

## Indice, portada y paginacion

- El indice debe aparecer tras la portada.
- El indice debe incluir numeros de pagina si esta implementada la doble pasada.
- La numeracion real de paginas se genera con Playwright/Chromium en PDF.
- La vista HTML directa puede no mostrar paginas definitivas si dependen del layout final.
- Evitar soluciones fragiles si el calculo de paginas requiere layout real.
- La portada debe ocupar una sola pagina A4.
- No usar `height: 100vh` para portada en PDF A4.
- Evitar que el bloque inferior salte a la pagina siguiente.

## Impresion y consumo de tinta

- Debe predominar fondo blanco.
- Evitar fondos grises grandes.
- Evitar bloques con mucho color.
- Evitar lineas verticales oscuras gruesas.
- Evitar sombras pesadas.
- Usar bordes finos gris claro.
- Usar sombreados muy suaves solo en zonas pequenas.
- Priorizar legibilidad y bajo consumo de tinta.

## Fotografias y figuras

- Todas las fotografias deben tener pie.
- La numeracion de figuras debe ser global, secuencial y seguir el orden visual real.
- Fotos generales de estancia en grid de 2 columnas cuando sea posible.
- Fotos de patologias con tamano uniforme.
- Usar `object-fit: contain` o equivalente para no recortar informacion tecnica si se prioriza inspeccion.
- Evitar imagenes gigantes que ocupen una pagina completa salvo necesidad.
- Evitar separar foto y pie de foto.

## Saltos de pagina

- Evitar paginas con solo un titulo, especialmente "Patologias interiores".
- No separar titulo de patologia de su tabla.
- No separar foto de pie.
- Usar `break-inside` / `page-break-inside: avoid` con cuidado.
- Evitar `break-before` excesivos que generen paginas vacias.
- Anadir salto antes de conclusiones si mejora el cierre visual.
- Revisar manualmente PDF final si se cambia CSS de impresion.

## Estancias y patologias

- Cada estancia debe mostrarse como bloque claro.
- Cada patologia debe estar diferenciada dentro de la estancia.
- Estancias sin patologias: "No constan patologias interiores registradas en esta estancia."
- Mantener datos tecnicos: tipo de estancia, planta, ventilacion, acabados, observaciones, cuadrantes, localizacion, elemento, patologia, rol tecnico y fotos.

## Completitud

- Completa para continuar visita: nombre, tipo de estancia y al menos una foto pueden bastar.
- Completa tecnicamente para informe: ventilacion, acabados, observaciones y otros campos tecnicos enriquecen el informe y deben conservarse cuando existan.
- El informe debe poder generarse manualmente, aunque no sea CTA recomendada si faltan datos.

## DOCX editable para Apple Pages

- Se genera desde `build_informe_context()`.
- Debe ser estable y facil de editar.
- No debe buscar pixel-perfect con HTML/PDF, pero si mantener la misma linea visual.
- Usar fuentes compatibles: Arial, Helvetica o Times New Roman si aplica.
- Evitar tablas anidadas complejas, cuadros flotantes, formas, layouts fragiles y estilos no compatibles.
- Usar titulos jerarquicos, tablas simples, imagenes centradas, pies de figura como parrafos normales, sombreados suaves y bloques tipo card simulados con tablas simples.

## Checklist recomendado

- `python3 -m compileall app`
- `node --check <archivo.js>` para cada JS tocado.
- Probar `/informes/{id}/imprimir`.
- Probar `/generar-informe-pdf/{id}`.
- Probar `/generar-informe-docx-editable/{id}`.
- Verificar que el PDF valido empieza por `%PDF`.
- Verificar que el DOCX valido empieza por `PK` si se toca DOCX.
- Verificar figuras secuenciales.
- Verificar que no hay paginas vacias.
- Verificar que la portada cabe en una pagina.
- Revisar visualmente un PDF real, especialmente si se toca CSS de impresion.

## Propuestas imprimibles y PDF comercial

`templates/propuestas/imprimir.html` es la referencia visual para el documento final de propuesta y para el PDF adjunto por email.

Reglas activas:

- El imprimible separa objeto del encargo, alcance de servicios, honorarios, condiciones economicas, exclusiones generales, limitaciones del encargo y validez.
- Si existen lineas, el PDF muestra tabla de honorarios con categoria, concepto, descripcion, cantidad, precio, IVA y total.
- Si una linea tiene `incluye`, `no_incluye` o `condiciones`, esos campos se muestran dentro del bloque de la linea.
- Si no existen lineas, el documento mantiene fallback de importe global para propuestas antiguas.
- Los totales mostrados deben venir de `propuestas`; no recalcular importes dentro de Jinja.
- El PDF descargado y el PDF enviado por email deben usar la misma plantilla imprimible actualizada.
- El email de envio de propuesta incluye texto plano, version HTML profesional con estilos inline y el PDF como adjunto.
- El HTML del email debe ser compatible con clientes moviles y Gmail, sin imagenes remotas, scripts ni CSS externo.

Checklist especifico:

- Probar `/propuestas/{id}/imprimir` con propuesta antigua sin lineas.
- Probar `/propuestas/{id}/imprimir` con lineas categorizadas y servicios rapidos.
- Generar `/propuestas/{id}/pdf` y verificar que el desglose coincide con el detalle.
- Enviar email solo si el PDF adjunto usa la misma plantilla actualizada.
- Verificar que el email recibido contiene version HTML, fallback texto plano y adjunto PDF.

## Criterios Done

- `bash scripts/validate_harness.sh` pasa.
- Smoke de `build_informe_context()` pasa si se toca contexto.
- PDF y DOCX siguen compartiendo fuente de datos.
- No se han leido informes/fotos reales salvo orden explicita.
- Si se toca impresion/PDF, queda documentada revision visual necesaria.
