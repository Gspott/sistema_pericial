# Project Rules

## Reglas permanentes

- No convertir Sistema Pericial en SaaS.
- No introducir SPA, React, Vue, Angular ni framework frontend.
- No migrar SQLite a PostgreSQL u otra base sin decision humana formal.
- No tocar datos reales.
- No leer, mostrar ni copiar secretos completos.
- No modificar facturacion sin tests, smoke test o validacion equivalente sobre datos de prueba.
- No cambiar rutas publicas sin justificar impacto y rollback.
- No reintroducir navegacion paralela que compita con drawer/hamburguesa.
- No hacer cambios fiscales sin checklist humano.
- No crear APIs de negocio paralelas.
- No reescribir flujos existentes si pueden reutilizarse.
- No hacer refactors grandes sin plan previo y aprobacion.
- No borrar archivos generados, backups, bases de datos, informes, fotos ni uploads sin confirmacion explicita.
- No usar red, SMTP real o integraciones externas salvo orden explicita.

## Principio operativo

El modelo puede escribir codigo, pero el harness decide contexto, memoria, permisos, validaciones y puntos de aprobacion humana.

## Prioridades actuales

1. Activacion comercial.
2. Estabilidad operativa.
3. Seguridad de datos.
4. Facturacion segura.
5. Velocidad de uso mobile-first.

