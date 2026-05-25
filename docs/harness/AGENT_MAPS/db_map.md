# DB Map

SQLite es una superficie critica del proyecto.

## Reglas

- No leer DB real por defecto.
- No ejecutar migraciones sobre DB real.
- Usar copia temporal para cualquier prueba de persistencia.
- No borrar columnas.
- No recrear tablas salvo decision humana explicita.
- Preferir `asegurar_columna()` para evolucion defensiva.

## Areas de datos conocidas

| Area | Tablas aproximadas | Riesgo |
|---|---|---|
| Usuarios/auth | `usuarios` | Critico |
| CRM | `leads`, `lead_contactos`, `lead_tareas`, `clientes` | Alto |
| Propuestas | `propuestas`, `propuesta_lineas` | Alto |
| Facturacion | `configuracion_fiscal`, `facturas_emitidas`, `factura_lineas`, `factura_eventos`, `cobros` | Critico |
| Gastos | `gastos` | Alto |
| Expedientes/visitas | `expedientes`, `visitas`, `estancias`, fotos relacionadas | Alto |
| Patologias | biblioteca, registros interiores/exteriores, mapas/cuadrantes | Alto |
| Informes | Datos derivados desde expedientes/visitas/patologias | Critico |

## Validacion segura

- Crear DB temporal.
- Ejecutar `init_db()` sobre la copia/temporal.
- Probar solo datos sinteticos.

