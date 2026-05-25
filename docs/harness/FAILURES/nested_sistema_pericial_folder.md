# Nested Sistema Pericial Folder

## Que se detecto

Existe una carpeta anidada `sistema_pericial/` dentro del repositorio principal.
La auditoria solo lectura observo estructura de aplicacion completa, entorno
virtual, `data/pericial.db` y carpetas de datos/generados como uploads, fotos,
informes y logs.

## Por que es peligroso

- Puede contener datos reales o sensibles fuera del flujo normal del repo.
- Puede confundirse con el proyecto principal y provocar cambios en la copia
  equivocada.
- Puede duplicar scripts, configuracion y codigo funcional.
- Puede ocultar drift entre versiones del sistema.
- Puede aumentar riesgo de commits accidentales si cambia `.gitignore` o se
  fuerzan adds.

## Que NO hacer

- No leer bases de datos, uploads, fotos, informes, logs ni secretos dentro de
  `sistema_pericial/`.
- No ejecutar scripts desde la carpeta anidada.
- No sincronizar, borrar, mover ni limpiar la carpeta sin aprobacion humana.
- No usarla como fuente normativa del estado real del proyecto.
- No comparar datos reales entre la carpeta anidada y el repo principal.

## Deteccion

Auditoria Fase 5A Legacy & Dead Code Audit.

## Impacto

Riesgo alto para seguridad operativa, privacidad y continuidad de trabajo si
Codex o una persona modifica la carpeta equivocada.

## Mitigacion

- Mantenerla como zona no tocable por defecto.
- Registrar decision humana antes de cualquier accion.
- Si se decide archivar o eliminar, hacer backup verificado fuera del flujo de
  Codex y validar que no quedan referencias operativas.

## Como evitar regresion

Mantener `docs/harness/CONTEXT_STRATEGY.md` y `AGENTS.md` indicando que la
carpeta anidada no debe cargarse ni modificarse sin decision humana.

## Smoke tests relacionados

No aplica directamente. La mitigacion es documental y de permisos.

## Decision humana requerida

Si debe conservarse como copia historica, moverse fuera del repo, archivarse,
ignorarse explicitamente o eliminarse tras backup verificado.
