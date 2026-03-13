import os
import re
from datetime import datetime

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from app.config import INFORMES_DIR, UPLOAD_DIR
from app.database import get_connection


def limpiar_nombre_archivo(texto: str) -> str:
    texto = (texto or "").strip().replace(" ", "_")
    texto = re.sub(r"[^A-Za-z0-9_\-]", "", texto)
    return texto or "expediente"


def valor_o_guion(valor):
    if valor is None:
        return "-"
    texto = str(valor).strip()
    return texto if texto else "-"


def configurar_documento(doc: Document) -> None:
    seccion = doc.sections[0]
    seccion.top_margin = Cm(2.5)
    seccion.bottom_margin = Cm(2.5)
    seccion.left_margin = Cm(2.5)
    seccion.right_margin = Cm(2.5)

    estilos = doc.styles

    estilos["Normal"].font.name = "Arial"
    estilos["Normal"].font.size = Pt(10)

    estilos["Title"].font.name = "Arial"
    estilos["Title"].font.size = Pt(22)
    estilos["Title"].font.bold = True

    estilos["Heading 1"].font.name = "Arial"
    estilos["Heading 1"].font.size = Pt(16)
    estilos["Heading 1"].font.bold = True

    estilos["Heading 2"].font.name = "Arial"
    estilos["Heading 2"].font.size = Pt(13)
    estilos["Heading 2"].font.bold = True

    estilos["Heading 3"].font.name = "Arial"
    estilos["Heading 3"].font.size = Pt(11)
    estilos["Heading 3"].font.bold = True


def add_parrafo(
    doc: Document,
    texto: str,
    bold: bool = False,
    centrado: bool = False,
    espacio_despues: int = 6,
):
    p = doc.add_paragraph()
    if centrado:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(texto)
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(espacio_despues)
    return p


def add_etiqueta_valor(doc: Document, etiqueta: str, valor) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)

    r1 = p.add_run(f"{etiqueta}: ")
    r1.bold = True
    r1.font.name = "Arial"
    r1.font.size = Pt(10)

    r2 = p.add_run(valor_o_guion(valor))
    r2.font.name = "Arial"
    r2.font.size = Pt(10)


def add_titulo(doc: Document, texto: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)

    run = p.add_run(texto)
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(20)


def add_subtitulo(doc: Document, texto: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)

    run = p.add_run(texto)
    run.italic = True
    run.font.name = "Arial"
    run.font.size = Pt(11)


def add_salto_pagina(doc: Document) -> None:
    doc.add_page_break()


def add_tabla_datos_expediente(doc: Document, expediente) -> None:
    tabla = doc.add_table(rows=0, cols=2)
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"

    filas = [
        ("Número de expediente", expediente["numero_expediente"]),
        ("Cliente", expediente["cliente"]),
        ("Dirección", expediente["direccion"]),
        ("Código postal", expediente["codigo_postal"]),
        ("Ciudad", expediente["ciudad"]),
        ("Provincia", expediente["provincia"]),
        ("Tipo de inmueble", expediente["tipo_inmueble"]),
        ("Orientación", expediente["orientacion_inmueble"]),
        ("Año de construcción", expediente["anio_construccion"]),
        ("Uso del inmueble", expediente["uso_inmueble"]),
        ("Superficie", expediente["superficie"]),
    ]

    for etiqueta, valor in filas:
        row = tabla.add_row().cells
        row[0].text = etiqueta
        row[1].text = valor_o_guion(valor)

    for fila in tabla.rows:
        for i, celda in enumerate(fila.cells):
            celda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for parrafo in celda.paragraphs:
                for run in parrafo.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(10)
                    if i == 0:
                        run.bold = True


def add_imagen_si_existe(doc: Document, nombre_foto: str) -> None:
    if not nombre_foto:
        return

    ruta_foto = os.path.join(UPLOAD_DIR, nombre_foto)
    if not os.path.exists(ruta_foto):
        add_parrafo(doc, f"Fotografía no localizada: {nombre_foto}")
        return

    try:
        doc.add_picture(ruta_foto, width=Cm(12.5))
        ultimo = doc.paragraphs[-1]
        ultimo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ultimo.paragraph_format.space_after = Pt(8)
    except Exception:
        add_parrafo(doc, f"No se ha podido insertar la fotografía: {nombre_foto}")


def add_portada(doc: Document, expediente) -> None:
    add_titulo(doc, "INFORME PERICIAL")
    add_subtitulo(doc, "Inspección técnica y registro de patologías")

    for _ in range(4):
        doc.add_paragraph()

    add_parrafo(
        doc,
        f"Expediente: {valor_o_guion(expediente['numero_expediente'])}",
        bold=True,
        centrado=True,
        espacio_despues=10,
    )
    add_parrafo(
        doc,
        f"Cliente: {valor_o_guion(expediente['cliente'])}",
        centrado=True,
        espacio_despues=8,
    )
    add_parrafo(
        doc,
        f"Dirección: {valor_o_guion(expediente['direccion'])}",
        centrado=True,
        espacio_despues=8,
    )
    add_parrafo(
        doc,
        f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y')}",
        centrado=True,
        espacio_despues=8,
    )

    add_salto_pagina(doc)


def add_apartado_introduccion(doc: Document) -> None:
    doc.add_heading("1. Objeto del informe", level=1)
    add_parrafo(
        doc,
        "El presente informe tiene por objeto dejar constancia de los datos del expediente, "
        "las visitas realizadas al inmueble inspeccionado, las estancias revisadas y las "
        "patologías observadas durante la inspección técnica.",
    )


def add_apartado_datos_generales(doc: Document, expediente) -> None:
    doc.add_heading("2. Datos generales del expediente", level=1)
    add_tabla_datos_expediente(doc, expediente)
    doc.add_paragraph()

    add_etiqueta_valor(
        doc, "Observaciones generales", expediente["observaciones_generales"]
    )

    if expediente["tipo_inmueble"] == "Piso":
        doc.add_heading("2.1 Características del bloque", level=2)
        add_etiqueta_valor(
            doc, "Observaciones del bloque", expediente["observaciones_bloque"]
        )

        doc.add_heading("2.2 Características de la unidad", level=2)
        add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
        add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
        add_etiqueta_valor(
            doc, "Superficie de la unidad", expediente["superficie_unidad"]
        )
        add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
        add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
        add_etiqueta_valor(
            doc, "Observaciones de la unidad", expediente["observaciones_unidad"]
        )


def add_apartado_reforma(doc: Document, expediente) -> None:
    doc.add_heading("3. Antecedentes de reforma", level=1)
    add_etiqueta_valor(doc, "Reformado", expediente["reformado"] or "No")
    add_etiqueta_valor(doc, "Fecha de reforma", expediente["fecha_reforma"])
    add_etiqueta_valor(
        doc, "Observaciones de la reforma", expediente["observaciones_reforma"]
    )


def add_apartado_visita(
    doc: Document, numero_apartado: int, visita, climatologia, estancias, patologias
) -> None:
    doc.add_heading(
        f"{numero_apartado}. Visita de inspección - {valor_o_guion(visita['fecha'])}",
        level=1,
    )

    add_etiqueta_valor(doc, "Técnico", visita["tecnico"])
    add_etiqueta_valor(doc, "Observaciones de visita", visita["observaciones_visita"])

    if climatologia:
        doc.add_heading(f"{numero_apartado}.1 Condiciones climatológicas", level=2)
        add_parrafo(doc, valor_o_guion(climatologia["resumen"]))
    else:
        doc.add_heading(f"{numero_apartado}.1 Condiciones climatológicas", level=2)
        add_parrafo(doc, "No consta climatología registrada para esta visita.")

    doc.add_heading(f"{numero_apartado}.2 Estancias inspeccionadas", level=2)

    if estancias:
        for estancia in estancias:
            add_parrafo(
                doc,
                f"- {valor_o_guion(estancia['nombre'])} | Tipo: {valor_o_guion(estancia['tipo_estancia'])} | "
                f"Planta: {valor_o_guion(estancia['planta'])}",
            )
    else:
        add_parrafo(doc, "No constan estancias registradas en esta visita.")

    doc.add_heading(f"{numero_apartado}.3 Patologías observadas", level=2)

    if not patologias:
        add_parrafo(doc, "No constan patologías registradas en esta visita.")
        return

    indice_patologia = 1
    for patologia in patologias:
        doc.add_heading(
            f"{numero_apartado}.3.{indice_patologia} {valor_o_guion(patologia['estancia_nombre'])}",
            level=3,
        )
        add_etiqueta_valor(doc, "Elemento afectado", patologia["elemento"])
        add_etiqueta_valor(doc, "Patología", patologia["patologia"])
        add_etiqueta_valor(doc, "Observaciones", patologia["observaciones"])

        if patologia["foto"]:
            add_parrafo(doc, "Fotografía asociada:", bold=True)
            add_imagen_si_existe(doc, patologia["foto"])

        indice_patologia += 1


def add_apartado_conclusion(doc: Document) -> None:
    doc.add_heading("Conclusión", level=1)
    add_parrafo(
        doc,
        "El presente documento recopila de forma ordenada la información disponible en el expediente, "
        "las visitas realizadas, las estancias inspeccionadas y las patologías registradas, sirviendo "
        "como base documental para su posterior análisis técnico pericial.",
    )


def generar_informe(expediente_id: int) -> tuple[str, str]:
    os.makedirs(INFORMES_DIR, exist_ok=True)

    conn = get_connection()
    cur = conn.cursor()

    expediente = cur.execute(
        """
        SELECT *
        FROM expedientes
        WHERE id = ?
        """,
        (expediente_id,),
    ).fetchone()

    if not expediente:
        conn.close()
        raise ValueError("Expediente no encontrado")

    visitas = cur.execute(
        """
        SELECT *
        FROM visitas
        WHERE expediente_id = ?
        ORDER BY id ASC
        """,
        (expediente_id,),
    ).fetchall()

    doc = Document()
    configurar_documento(doc)

    add_portada(doc, expediente)
    add_apartado_introduccion(doc)
    add_apartado_datos_generales(doc, expediente)
    add_apartado_reforma(doc, expediente)

    numero_apartado = 4

    for visita in visitas:
        climatologia = cur.execute(
            """
            SELECT *
            FROM climatologia_visitas
            WHERE visita_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (visita["id"],),
        ).fetchone()

        estancias = cur.execute(
            """
            SELECT *
            FROM estancias
            WHERE visita_id = ?
            ORDER BY id ASC
            """,
            (visita["id"],),
        ).fetchall()

        patologias = cur.execute(
            """
            SELECT rp.*, e.nombre AS estancia_nombre
            FROM registros_patologias rp
            INNER JOIN estancias e ON rp.estancia_id = e.id
            WHERE rp.visita_id = ?
            ORDER BY e.nombre ASC, rp.id ASC
            """,
            (visita["id"],),
        ).fetchall()

        doc.add_section(WD_SECTION.NEW_PAGE)
        configurar_documento(doc)

        add_apartado_visita(
            doc,
            numero_apartado,
            visita,
            climatologia,
            estancias,
            patologias,
        )

        numero_apartado += 1

    doc.add_section(WD_SECTION.NEW_PAGE)
    configurar_documento(doc)
    add_apartado_conclusion(doc)

    base_nombre = limpiar_nombre_archivo(
        f"{expediente['numero_expediente']}_{expediente['cliente']}"
    )
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"informe_{base_nombre}_{marca_tiempo}.docx"
    ruta_archivo = os.path.join(INFORMES_DIR, nombre_archivo)

    doc.save(ruta_archivo)
    conn.close()

    return ruta_archivo, nombre_archivo
