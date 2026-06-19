# Informe V2 Find Replace 2 Fix 1

# Objetivo

Corregir la regresión de búsqueda contextual del Informe V2 Editor para que encuentre texto real guardado en todos los capítulos.

# Modulo

Informes / Editor Informe V2 / Buscar y reemplazar.

# Riesgo

Bajo. Cambio acotado al helper que decide si buscar sobre contenido enviado por el cliente o sobre contenido guardado, más tests smoke.

# Archivos permitidos

`app/main.py`, `tests/smoke/test_pericial_workbench.py`, documentación harness asociada.

# Archivos prohibidos

Bases SQLite reales, uploads, backups, logs, informes generados, PDFs externos, anexos generados, CRM, costes, facturación y carpeta anidada `sistema_pericial/`.

# Playbook aplicable

Task Pack sugerido: `docs/harness/TASK_PACKS/informe_change.md`.

# Diagnóstico

El helper `contenido_cliente_capitulo_informe_v2()` priorizaba cualquier campo `contenido_<clave>` recibido en el formulario, incluso cuando llegaba vacío. Si el frontend enviaba una copia vacía/incompleta del textarea, la búsqueda se hacía sobre cadena vacía en vez de sobre el capítulo guardado, devolviendo 0 coincidencias aunque existiera texto real.

# Implementación

- Usar el contenido enviado por el cliente cuando trae texto.
- Si el campo llega vacío y existe capítulo guardado, buscar sobre el contenido guardado.
- Mantener el comportamiento de reemplazo individual y validación `updated_at`.
- Añadir test con capítulo 1 `Anexo C` y capítulo 2 `Anexo A`, incluyendo formulario con campos vacíos para reproducir la regresión.

# Validaciones

- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "buscar_reemplazar"`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q -k "informe_v2"`
- `git diff --check`

# Rollback

Revertir cambios de los archivos permitidos. No hay migraciones ni cambios de esquema.

# Fuera de alcance

No tocar editor visual, PDF V2, anexos, datos reales ni búsqueda difusa/case-insensitive.

# Aprobacion humana requerida

No requerida.

Estado: completado
