# Pericial Annex A Profile 1

# Objetivo

Convertir el Anexo A documental del Informe V2 en un bloque profesional,
navegable y estructurado mediante indice documental y ficha previa para cada PDF
externo incorporado.

# Modulo

Informe V2 / fusion PDF / Anexo A documental.

# Riesgo

Medio-alto. Afecta al orden de paginas fusionadas en el PDF final, aunque no
modifica PDFs originales ni contenido tecnico. La paginacion final sigue
aplicandose despues de la fusion completa.

# Archivos permitidos

- `app/main.py`
- `templates/informe_v2_editor.html`
- `tests/smoke/test_pericial_workbench.py`
- `docs/harness/PLANS/active/pericial-annex-a-profile-1.md`
- Episodio harness de cierre

# Archivos prohibidos

- DOCX
- CRM
- Esquema DB
- PDFs, uploads o informes reales
- Contenido tecnico del informe

# Playbook aplicable

Task Pack sugerido: `informe_change`.

# Diagnostico

La fusion existente ya insertaba una portadilla por documento externo del Anexo
A, pero no generaba un indice documental previo y la numeracion empezaba en
`A.2`, reservando implicitamente `A.1` para la relacion documental del HTML.

En expedientes con muchos documentos externos esta estructura era insuficiente:
el usuario recibia una secuencia larga de PDFs con pocas ayudas para navegar el
bloque documental.

# Alcance

- Generar indice documental del Anexo A antes de los PDFs externos.
- Numerar documentos externos como `A.1`, `A.2`, etc. segun el orden actual.
- Generar ficha previa para cada documento con:
  - identificador documental;
  - nombre;
  - tipo/categoria;
  - paginas;
  - tamano;
  - fecha, descripcion y observaciones si existen.
- Mantener compatibilidad si un PDF no puede leerse: ficha incluida y paginas
  como `No disponible`.
- Mantener estructura preparada con `pagina_inicio_final` y `pagina_fin_final`
  en metadatos, sin calcularlas todavia.
- Mostrar resumen no bloqueante del Anexo A documental en el diagnostico de peso
  del editor.

# Validaciones

- `python3 scripts/audit_docs.py`
- `python3 -m compileall app`
- `.venv/bin/python -m pytest tests/smoke/test_pericial_workbench.py -q`
- `git diff --check`
- `bash scripts/finish_harness_task.sh --smoke-scope app`

# Rollback

Revertir generacion de indice/fichas del Anexo A y tests asociados. No hay
migraciones ni cambios sobre uploads originales.

# Fuera de alcance

- Recalcular paginas finales del indice.
- Crear miniaturas.
- Optimizar peso de PDFs externos.
- Leer/generar expediente real `019-26` sin autorizacion explicita.

# Aprobacion humana requerida

Solo para validar contra DB/uploads reales.

Estado: completado
