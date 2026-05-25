# Tech Debt Tracker

| Deuda | Riesgo | Estado | Siguiente accion recomendada |
|---|---|---|---|
| `app/main.py` monolitico | Alto | Conocida | No refactorizar de golpe; extraer por flujo solo con tests/smoke. |
| `app/main.py` monolitico como riesgo estructural persistente | Alto | Warning automatizado | Mantener warning en auditoria; cualquier extraccion debe ir con plan y smoke tests. |
| Ausencia de `pytest`/smoke tests | Alto | Pendiente | Crear smoke tests minimos antes de cambios criticos. |
| Drift PWA entre `pwa.js` y `sw.js` | Medio-alto | Pendiente | Revisar con playbook CSS/mobile antes de tocar service worker. |
| Warning Starlette `TemplateResponse` deprecated | Medio | Detectado por smoke tests | Revisar llamadas `TemplateResponse` en una fase especifica sin mezclar con cambios funcionales. |
| Carpeta anidada `sistema_pericial/` pendiente de decision | Alto | Pendiente | Clasificar como copia historica, deploy local o residuo antes de tocar. |
| Datos locales sensibles presentes pero no trackeados | Critico | Vigilado | Mantener fuera de alcance; comprobar tracking sin mostrar valores. |
