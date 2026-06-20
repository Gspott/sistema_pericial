# AUTOSAVE-ROLLOUT-1 Cierre

## Estado

`AUTOSAVE-ROLLOUT-1` queda documentalmente cerrado tras completar:

- `TIMEZONE-STANDARD-1`
- `AUTOSAVE-STANDARD-1`
- `PROJECT-STANDARDS-GUARD-1`
- `autosave-patologias-visitas-1`
- `autosave-patologias-registros-1`
- `autosave-estancias-cuadrantes-1`
- `autosave-crm-costes-1`
- `autosave-propuestas-formularios-largos-1`

El estandar de autoguardado queda desplegado sobre los formularios largos,
tecnicos o de edicion prolongada que eran seguros dentro de este rollout. Las
exclusiones se mantienen fuera por falta de entidad persistida, mezcla con
acciones estructurales, fiscalidad, generacion documental, importaciones o
operaciones irreversibles.

## Infraestructura comun

Toda implantacion del rollout reutiliza:

- `static/js/autosave.js`;
- `templates/components/autosave_status.html`;
- contrato JSON estandar;
- estados visuales `ready`, `dirty`, `saving`, `saved`, `error` y `conflict`;
- `updated_at` real o token equivalente;
- conflicto `409`;
- proteccion `beforeunload`;
- reintento simple;
- guardado manual como fallback.

No se introdujo una segunda infraestructura de autosave.

## Alcance final

### Cubierto

- Valoracion Workbench.
- Visitas.
- Observaciones de visita/valoracion.
- Patologias interiores.
- Patologias exteriores.
- Estancias.
- Cuadrantes de mapa de patologias con edicion textual segura.
- CRM, notas del lead seleccionado.
- Costes, edicion de partida existente.
- Propuestas existentes.

### Parcialmente cubierto

- Inspeccion queda cubierta en pantallas persistidas de visita, observaciones,
  patologias, estancias y cuadrantes; quedan fuera altas sin entidad persistida
  y editores estructurales.
- Propuestas queda cubierta en el formulario principal de propuestas existentes;
  quedan fuera propuesta nueva y lineas con importes/IVA.
- Costes queda cubierto en partida existente; quedan fuera OCR, capturas,
  importaciones BC3, descompuestos, validacion y altas.
- CRM queda cubierto en notas persistidas del lead; quedan fuera envio,
  programacion, agenda y acciones comerciales estructurales.

### Excluido

Quedan excluidas acciones fiscales, documentales, irreversibles, importaciones,
uploads/OCR y pantallas que mezclan edicion textual con cambios estructurales.

## Matriz de cobertura

| Modulo | Pantalla o entidad | Estado | Mecanismo | Smoke tests asociados |
|---|---|---|---|---|
| Valoracion | Workbench, microedicion de testigos | cubierto | `updated_at` | `tests/smoke/test_valoracion_workbench.py` |
| Inspeccion | Visitas persistidas | cubierto | token equivalente | `tests/smoke/test_valoracion_nueva_visita_ux.py` |
| Inspeccion | Observaciones de visita/valoracion | cubierto | `updated_at` o token segun entidad | `tests/smoke/test_valoracion_nueva_visita_ux.py` |
| Inspeccion | Patologias interiores | cubierto | token equivalente | `tests/smoke/test_autosave_patologias_registros.py` |
| Inspeccion | Patologias exteriores | cubierto | token equivalente | `tests/smoke/test_autosave_patologias_registros.py` |
| Inspeccion | Estancias | cubierto | token equivalente | `tests/smoke/test_autosave_estancias_cuadrantes.py` |
| Inspeccion | Cuadrantes de mapa de patologias | cubierto | token equivalente | `tests/smoke/test_autosave_estancias_cuadrantes.py` |
| CRM | Notas del lead seleccionado | cubierto | `updated_at` | `tests/smoke/test_autosave_crm_costes.py` |
| Costes | Edicion de partida existente | cubierto | `updated_at` | `tests/smoke/test_autosave_crm_costes.py` |
| Propuestas | Formulario principal de propuesta existente | cubierto | `updated_at` | `tests/smoke/test_autosave_propuestas_formularios_largos.py` |
| Propuestas | Propuesta nueva | excluido | no aplicable | cubierto indirectamente por ausencia de `data-autosave-form` en `tests/smoke/test_autosave_propuestas_formularios_largos.py` |
| Propuestas | Lineas con importes/IVA | pendiente | no aplicable | no aplica |
| Inspeccion | `editar_mapa_patologia.html` | pendiente | no aplicable | exclusion documentada en `autosave-estancias-cuadrantes-1` |
| CRM | Emails, programacion y agenda | excluido | no aplicable | no aplica |
| Costes | OCR, capturas e importaciones BC3 | excluido | no aplicable | no aplica |
| Facturacion | Facturas y acciones fiscales | excluido | no aplicable | no aplica |
| Informes | Generacion PDF/DOCX | excluido | no aplicable | no aplica |
| Sistema | Acciones irreversibles u operaciones estructurales complejas | excluido | no aplicable | no aplica |

## Inventario de exclusiones justificadas

| Exclusion | Motivo tecnico | Riesgo si se autosalva sin separar | Posible plan futuro |
|---|---|---|---|
| Propuesta nueva sin entidad persistida | No existe registro ni `updated_at` hasta el primer submit | Guardados huerfanos, borradores incompletos o duplicados | `autosave-propuestas-borradores-1` si se define modelo de borrador |
| Lineas de propuesta con importes/IVA | Mezclan texto, cantidades, precios, IVA y recalculo de totales | Divergencia economica o cambios parciales de honorarios | `autosave-propuesta-lineas-texto-1` separando texto de economia |
| `editar_mapa_patologia.html` | Mezcla texto con filas, columnas e imagen base | Persistir estructura intermedia incoherente | `autosave-mapa-patologia-textual-1` tras separar edicion textual y estructural |
| Emails y programacion | Envio/programacion son acciones externas o semirreversibles | Enviar/programar contenido parcial o cancelar estados por error | `crm-email-drafts-autosave-1` solo si hay borrador persistido explicito |
| OCR | Flujo dependiente de upload/procesamiento y creacion derivada | Crear datos parciales o duplicar resultados de extraccion | `costes-ocr-draft-review-1` con borrador revisable |
| Importaciones BC3 | Operacion masiva y estructural | Importaciones parciales o inconsistentes | `costes-bc3-preview-draft-1` con staging separado |
| Facturacion | Fiscalidad, estados y documentos economicos | Cambios fiscales silenciosos o documentos inconsistentes | `facturacion-draft-autosave-audit-1` solo para borradores textuales |
| Generacion de PDF | Accion documental derivada, no editor primario | Generar documentos con contenido parcial o no validado | No aplicar autosave; mejorar validaciones previas |
| Acciones irreversibles y operaciones estructurales complejas | No son edicion textual prolongada | Efectos no recuperables o estados intermedios invalidos | Plan especifico por flujo con confirmacion y rollback |

## Reglas permanentes

Todo nuevo formulario largo, tecnico, susceptible de perdida de datos o de
edicion prolongada debe evaluar autosave antes de cerrarse. Si aplica, es
obligatorio:

- reutilizar `static/js/autosave.js`;
- incluir `templates/components/autosave_status.html`;
- mostrar estado visual estandar;
- enviar `updated_at` real o token equivalente;
- devolver el token actualizado bajo el campo `updated_at`;
- responder `409` con `conflict: true` ante conflicto;
- conservar guardado manual como fallback;
- proteger tambien el guardado manual cuando reciba `updated_at`;
- anadir smoke proporcional de render, persistencia, conflicto y fallback;
- documentar exclusiones cuando no sea seguro aplicar autosave.

No se debe:

- duplicar JavaScript de autosave;
- crear contratos JSON alternativos;
- introducir migraciones solo para autosave si existe token equivalente viable;
- autosalvar acciones fiscales, envios, PDFs, importaciones, OCR o cambios
  estructurales sin separar primero un borrador textual seguro.

Estas reglas forman parte de `PROJECT-STANDARDS-GUARD-1`.

## Metricas finales

- Superficies cubiertas: 10.
- Ficheros smoke/autosave especificos: 6.
- Funciones smoke/autosave identificadas: 16.
- Pantallas o grupos excluidos: 9.
- Deuda tecnica pendiente agrupada: 4 lineas principales.

Deuda tecnica pendiente:

- Borradores persistidos para formularios de alta sin entidad previa.
- Separacion texto/economia en lineas de propuesta.
- Separacion texto/estructura en mapa de patologia.
- Borradores seguros para OCR, BC3, emails, facturacion y otras acciones
  externas o irreversibles.

## Decisiones adoptadas

- Priorizar formularios persistidos y reversibles.
- Usar `updated_at` real cuando exista.
- Usar token equivalente cuando no se debe migrar esquema.
- Mantener siempre el guardado manual.
- No tocar bases SQLite reales ni migrar historicos.
- Cerrar el rollout como estandar desplegado, no como una invitacion a
  autosalvar cualquier accion.

## Referencias

- `docs/harness/PATTERNS/autosave_standard.md`
- `docs/harness/PATTERNS/project_standards_guard.md`
- `docs/harness/PLANS/completed/autosave-standard-1.md`
- `docs/harness/PLANS/completed/autosave-patologias-visitas-1.md`
- `docs/harness/PLANS/completed/autosave-patologias-registros-1.md`
- `docs/harness/PLANS/completed/autosave-estancias-cuadrantes-1.md`
- `docs/harness/PLANS/completed/autosave-crm-costes-1.md`
- `docs/harness/PLANS/completed/autosave-propuestas-formularios-largos-1.md`
