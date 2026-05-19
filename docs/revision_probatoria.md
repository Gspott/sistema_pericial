# Revision probatoria

Documento tematico de revision probatoria. La normativa resumida esta en `AGENTS.md`.

## Fuente normativa

Fuente normativa: este documento.

Las reglas oficiales de revision probatoria, detecciones y prioridad de siguiente accion viven aqui.

## Dependencias

Depende de:

- [docs/modelos_datos.md](modelos_datos.md)
- [docs/ux.md](ux.md)
- [docs/informes.md](informes.md)

Puede impactar:

- UX de visita.
- CTAs de expediente/resumen.
- Generacion manual de informe.
- Completitud tecnica de datos.

## Decisiones

Decision ID: REV-001
Estado: Active
Categoria: Revisión probatoria

La revision probatoria detecta y prioriza con el mismo criterio; no bloquea el informe, pero orienta el siguiente paso.

## Madurez

- Revision probatoria: Activo.
- CTA de informe desde revision: Activo, solo recomendado cuando la visita este suficientemente documentada.

## Ruta y objetivo

- Ruta: `/resumen-registro/{expediente_id}`.
- Template principal: `templates/resumen_registro.html`.
- La revision probatoria es operativa: detecta pendientes y recomienda el siguiente paso.
- No bloquea la generacion de informe; advierte y orienta.

## Detecciones activas

- Visita sin climatologia.
- Cuadrantes obligatorios/incompletos si aplica.
- Estancias sin foto o datos minimos.
- Patologias sin foto/documentacion.
- Otros datos tecnicos opcionales.
- Informe pendiente.

## Prioridad de siguiente accion

1. Climatologia de la visita.
2. Cuadrantes obligatorios/incompletos si aplica.
3. Estancias sin foto o datos minimos.
4. Patologias sin foto/documentacion.
5. Otros datos tecnicos opcionales.
6. Generar informe, solo cuando la visita este suficientemente documentada.

## Reglas

- Deteccion y prioridad deben usar el mismo criterio.
- Si hay varias estancias pendientes, recomendar "Completar estructura interior" y enlazar a `/definir-estancias/{visita_id}#estructura-interior`.
- No recomendar patologias si todavia hay estancias pendientes.
- No recomendar generar informe como CTA automatica durante visita si aun hay pendientes probatorios.
- La generacion manual de informe sigue disponible.

## UX

- Mantener lectura rapida: estado, pendiente, editar, foto.
- Usar tarjetas compactas y badges.
- Evitar tablas complejas.
- Mantener jerarquia Nivel > Unidad > Estancia > Patologia.
