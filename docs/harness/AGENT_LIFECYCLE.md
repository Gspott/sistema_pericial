# Agent Lifecycle

## Ciclo obligatorio

1. Clasificar tarea.
2. Identificar riesgo.
3. Leer playbook.
4. Hacer inspeccion minima.
5. Proponer plan corto si el riesgo es alto o critico.
6. Aplicar cambio minimo.
7. Ejecutar validacion.
8. Tener rollback plan.
9. Cerrar con archivos, validaciones y riesgos.

## Criterios de parada

Pedir aprobacion humana si:

- El cambio toca modulo critico.
- Hay datos reales.
- Hay secretos.
- Hay fiscalidad.
- Hay envio externo.
- Hay borrado o restore.
- Hay cambio de ruta publica.
- Hay service worker o deploy.

## Rollback

Todo cambio debe poder revertirse con:

- Revert del diff documental o funcional.
- Restauracion de copia temporal si se valido DB.
- Desactivacion del cambio sin migraciones destructivas.

