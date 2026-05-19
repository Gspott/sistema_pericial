# Flujo de trabajo IA

Documento operativo para coordinar futuros chats IA/humanos. `AGENTS.md` sigue siendo la puerta de entrada normativa.

## Dependencias

Depende de:

- [AGENTS.md](../AGENTS.md)
- [docs/changelog.md](changelog.md)
- Documentos tematicos afectados por cada cambio.

Puede impactar:

- Gobernanza documental.
- Trazabilidad de decisiones.
- Calidad de cambios asistidos por IA.

## Flujo recomendado para futuros chats IA

1. Leer `AGENTS.md`.
2. Leer los documentos relacionados antes de modificar.
3. Revisar decisiones activas.
4. Revisar anti-patrones.
5. Verificar impactos cruzados en la matriz de impacto.
6. No crear reglas paralelas.
7. No duplicar navegacion ni logica.
8. Actualizar documentacion si cambia el comportamiento.
9. Mantener trazabilidad con Decision ID cuando haya una decision estable.
10. Ejecutar `python3 scripts/audit_docs.py`.
11. Verificar checklist antes de cerrar cambios.

Si existe CI documental, el workflow de auditoria documental debe quedar en verde antes de cerrar el cambio.

## Errores comunes

- Editar una zona funcional sin consultar su documento tematico.
- Resolver un caso puntual creando una regla global no consensuada.
- Repetir en `AGENTS.md` detalles que deben vivir en `/docs`.
- Confundir estado activo, legacy, experimental y pendiente.
- Duplicar CTAs, navegacion o endpoints ya existentes.

## Anti-patrones IA

- Proponer re-arquitecturas amplias para cambios locales.
- Crear APIs de negocio paralelas.
- Sustituir automatizaciones externas ya funcionales.
- Convertir flujos server-side en SPA.
- Reescribir documentos completos sin necesidad.
- Anadir reglas nuevas sin Decision ID, estado y documento fuente.

## Como proponer cambios

- Identificar el documento fuente afectado.
- Explicar el cambio en terminos de impacto operativo.
- Indicar si modifica una decision activa o crea una nueva.
- Marcar riesgos y compatibilidad con datos existentes.
- Mantener diffs pequenos y verificables.

## Como marcar experimental o legacy

- Experimental: existe como propuesta o implementacion condicionada, requiere verificacion o depende de endpoint documentado.
- Legacy: existe por compatibilidad, no debe ampliarse salvo necesidad explicita.
- Activo: patron vigente y recomendado.
- Pendiente de validar: depende de codigo no verificado o de una decision humana posterior.

## Como documentar nuevas decisiones

Usar este formato:

```md
Decision ID: PREFIJO-000
Estado: Active | Experimental | Legacy | Pending validation
Categoria: UX | Datos | PWA | Backend | Informes | Revisión probatoria | Documentación
```

La decision debe vivir en el documento tematico que sea fuente normativa. `AGENTS.md` solo debe resumirla o enlazarla.
