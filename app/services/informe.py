import os
import re
from io import BytesIO
from datetime import datetime
from collections import OrderedDict

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


def limpiar_texto(valor) -> str:
    return str(valor or "").strip()


def clave_orden_cuadrante(codigo):
    texto = limpiar_texto(codigo)
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", texto)
    if not match:
        return (1, texto.upper(), 0)
    letras, numero = match.groups()
    return (0, letras.upper(), int(numero))


ESTADO_INSPECCION_LABELS = {
    "no_necesita_reparacion": "No necesita reparación",
    "necesita_reparacion": "Necesita reparación",
    "defecto_grave": "Defecto grave",
    "no_inspeccionado": "No inspeccionado",
}

INSPECCION_GENERAL_GROUPS = [
    (
        "Información general / conjunto del inmueble",
        [
            ("puerta_entrada", "Puerta de entrada"),
            ("vestibulo", "Vestíbulo"),
            ("ventilacion_cruzada", "Ventilación cruzada"),
            ("ventilacion_general_inmueble", "Ventilación general del inmueble"),
            ("iluminacion_natural_general", "Iluminación natural general"),
            ("orientacion_general", "Orientación general"),
            ("reformado_cambio_uso", "Reformado / cambio de uso"),
        ],
    ),
    (
        "Estructura",
        [
            ("estructura_vertical", "Estructura vertical"),
            ("estructura_horizontal", "Estructura horizontal"),
            ("forjados_voladizos", "Forjados / voladizos"),
            ("cubiertas", "Cubiertas"),
            ("soleras_losas", "Soleras / losas"),
        ],
    ),
    (
        "Instalaciones generales",
        [
            ("instalacion_electrica_general", "Instalación eléctrica general"),
            ("agua_acs", "Agua / ACS"),
            ("calefaccion", "Calefacción"),
            ("climatizacion", "Climatización"),
        ],
    ),
    (
        "Carpinterías generales",
        [
            ("carpinterias_generales", "Carpinterías generales"),
            ("persianas_generales", "Persianas generales"),
            ("barandillas_generales", "Barandillas generales"),
            ("vierteaguas_generales", "Vierteaguas generales"),
        ],
    ),
]

INSPECCION_ESTANCIA_BASE_ITEMS = [
    ("puerta", "Puerta"),
    ("revestimiento", "Revestimiento"),
    ("iluminacion", "Iluminación"),
    ("mobiliario", "Mobiliario"),
    ("mecanismos_electricos", "Mecanismos eléctricos"),
    ("humedades", "Humedades"),
    ("techo", "Techo"),
    ("pavimento", "Pavimento"),
]

INSPECCION_ESTANCIA_BANO_ITEMS = [
    ("banera_ducha", "Bañera / ducha"),
    ("mampara", "Mampara"),
    ("lavabo", "Lavabo"),
    ("inodoro", "Inodoro"),
    ("bide", "Bidé"),
    ("espejo", "Espejo"),
    ("ventilacion_forzada", "Ventilación forzada"),
    ("condensacion", "Condensación"),
    ("griferia", "Grifería"),
    ("sifones", "Sifones"),
    ("desagues", "Desagües"),
    ("llaves_paso", "Llaves de paso"),
]

INSPECCION_ESTANCIA_COCINA_ITEMS = [
    ("extractor", "Extractor"),
    ("encimera", "Encimera"),
    ("zona_coccion", "Zona de cocción"),
    ("frigorifico", "Frigorífico"),
    ("horno", "Horno"),
    ("fregadero", "Fregadero"),
    ("griferia", "Grifería"),
    ("sifones", "Sifones"),
    ("desagues", "Desagües"),
    ("llaves_paso", "Llaves de paso"),
    ("conexion_lavavajillas", "Conexión lavavajillas"),
]

INSPECCION_ESTANCIA_HABITABLE_ITEMS = [
    ("persiana", "Persiana"),
    ("cajon_persiana", "Cajón persiana"),
    ("carpinteria_estancia", "Carpintería estancia"),
    ("cierre_manivela", "Cierre / manivela"),
    ("tomas_corriente", "Tomas de corriente"),
]

INSPECCION_EXTERIOR_ITEMS = [
    ("fachadas", "Fachadas"),
    ("cubiertas_exteriores", "Cubiertas exteriores"),
    ("patios_exteriores", "Patios exteriores"),
    ("terrazas_balcones", "Terrazas / balcones"),
    ("jardines", "Jardines"),
    ("entorno_inmediato", "Entorno inmediato"),
    ("carpinterias_exteriores", "Carpinterías exteriores"),
    ("barandillas_exteriores", "Barandillas exteriores"),
    ("rejas_exteriores", "Rejas exteriores"),
    ("toldos", "Toldos"),
    ("tendederos", "Tendederos"),
]

INSPECCION_ELEMENTOS_COMUNES_ITEMS = [
    ("portal_acceso", "Portal / acceso"),
    ("vestibulo_comun", "Vestíbulo común"),
    ("pasillos_comunes", "Pasillos comunes"),
    ("escaleras", "Escaleras"),
    ("ascensor", "Ascensor"),
    ("patio_luces", "Patio de luces"),
    ("patio_ventilacion", "Patio de ventilación"),
    ("fachada_comun", "Fachada común"),
    ("cubierta_comun", "Cubierta común"),
    ("cuarto_instalaciones_comunes", "Cuarto de instalaciones comunes"),
]
ESTADO_HABITABILIDAD_LABELS = {
    "cumple": "Cumple",
    "no_cumple": "No cumple",
    "no_aplica": "No aplica",
    "no_inspeccionado": "No inspeccionado",
}
CONCLUSION_HABITABILIDAD_LABELS = {
    "apto": "Apto",
    "apto_con_deficiencias": "Apto con deficiencias",
    "no_apto": "No apto",
}
HABITABILIDAD_GENERAL_ITEMS = [
    ("ventilacion_general", "Ventilación general"),
    ("iluminacion_natural_general", "Iluminación natural general"),
    ("salubridad_general", "Salubridad general"),
    ("seguridad_uso", "Seguridad de uso"),
    ("instalaciones_basicas", "Instalaciones básicas"),
    ("accesibilidad_basica", "Accesibilidad básica"),
    ("adecuacion_uso_residencial", "Adecuación al uso residencial"),
]
HABITABILIDAD_ESTANCIA_ITEMS = [
    ("ventilacion", "Ventilación"),
    ("iluminacion", "Iluminación"),
    ("humedades_condensaciones", "Humedades / condensaciones"),
    ("salubridad", "Salubridad"),
    ("seguridad_uso_estancia", "Seguridad de uso"),
]
HABITABILIDAD_EXTERIOR_ITEMS = [
    ("patio_ventilacion", "Patio de ventilación"),
    ("fachada_humedades", "Fachada / humedades"),
    ("cubierta_filtraciones", "Cubierta / filtraciones"),
]
VALORACION_ENCARGO_ITEMS = [
    ("nombre_solicitante", "Solicitante"),
    ("nif_cif_solicitante", "NIF/CIF"),
    ("domicilio_solicitante", "Domicilio"),
    ("entidad_financiera", "Entidad financiera"),
    ("finalidad_valoracion", "Finalidad de la valoración"),
    ("finalidad_valoracion_detallada", "Finalidad detallada"),
]
VALORACION_DOCUMENTACION_ITEMS = [
    ("documentacion_utilizada", "Documentación utilizada"),
    ("datos_registrales", "Datos registrales"),
]
VALORACION_IDENTIFICACION_ITEMS = [
    ("identificacion_bien", "Identificación del bien"),
    ("superficie_valoracion", "Superficie de valoración"),
    ("superficie_util", "Superficie útil"),
    ("superficie_terraza", "Superficie de terraza"),
    ("superficie_zonas_comunes", "Superficie de zonas comunes"),
    ("superficie_total", "Superficie total"),
    ("superficie_comprobada", "Superficie comprobada"),
]
VALORACION_SITUACION_LEGAL_ITEMS = [
    ("situacion_ocupacion", "Situación de ocupación"),
    ("situacion_urbanistica", "Situación urbanística"),
    ("servidumbres", "Servidumbres"),
    ("linderos", "Linderos"),
]
VALORACION_ENTORNO_ITEMS = [
    ("ubicacion_valoracion", "Ubicación"),
    ("descripcion_entorno", "Descripción del entorno"),
    ("grado_consolidacion", "Grado de consolidación"),
    ("antiguedad_entorno", "Antigüedad del entorno"),
    ("rasgos_urbanos", "Rasgos urbanos"),
    ("nivel_renta", "Nivel de renta"),
    ("uso_predominante", "Uso predominante"),
    ("equipamientos", "Equipamientos"),
    ("infraestructuras", "Infraestructuras"),
]
VALORACION_EDIFICIO_INMUEBLE_ITEMS = [
    ("tipo_edificio", "Tipo de edificio"),
    ("numero_portales", "Número de portales"),
    ("numero_escaleras", "Número de escaleras"),
    ("numero_ascensores", "Número de ascensores"),
    ("estado_conservacion", "Estado de conservación"),
    ("antiguedad", "Antigüedad"),
    ("calidades", "Calidades"),
    ("vistas", "Vistas"),
    ("uso_residencial", "Uso residencial"),
]
VALORACION_CONSTRUCTIVO_ITEMS = [
    ("estructura", "Estructura"),
    ("cubierta", "Cubierta"),
    ("cerramientos", "Cerramientos"),
    ("aislamiento", "Aislamiento"),
    ("carpinteria", "Carpintería"),
    ("acristalamiento", "Acristalamiento"),
    ("instalaciones", "Instalaciones"),
]
VALORACION_ESTADO_ITEMS = [
    ("estado_inmueble", "Estado actual del inmueble"),
    ("regimen_ocupacion", "Régimen de ocupación"),
    ("inmueble_arrendado", "Inmueble arrendado"),
    ("fecha_visita", "Fecha de visita"),
    ("fecha_emision", "Fecha de emisión"),
    ("fecha_caducidad", "Fecha de caducidad"),
]
VALORACION_METODO_ITEMS = [
    ("criterios_metodo_valoracion", "Criterios / método de valoración"),
    ("testigos_comparables", "Testigos comparables"),
    ("observaciones_testigos", "Observaciones sobre testigos"),
    ("variables_mercado", "Variables de mercado"),
    ("metodo_homogeneizacion", "Método de homogeneización"),
]
VALORACION_RESULTADO_ITEMS = [
    ("valor_unitario", "Valor unitario"),
    ("valor_resultante", "Valor resultante"),
    ("valor_tasacion_final", "Valor de tasación final"),
]
VALORACION_LIMITACIONES_ITEMS = [
    (
        "condicionantes_limitaciones_valoracion",
        "Condicionantes y limitaciones",
    ),
    ("observaciones_valoracion", "Observaciones"),
]
COMPARABLES_COLUMNAS = [
    ("direccion_testigo", "Dirección"),
    ("fuente_testigo", "Fuente"),
    ("fecha_testigo", "Fecha"),
    ("precio_oferta", "Precio oferta"),
    ("valor_unitario", "Valor unitario"),
    ("superficie_construida", "Sup. constr."),
    ("superficie_util", "Sup. útil"),
    ("tipologia", "Tipología"),
    ("planta", "Planta"),
    ("dormitorios", "Dorm."),
    ("banos", "Baños"),
    ("estado_conservacion", "Estado"),
    ("antiguedad", "Antigüedad"),
    ("calidad_constructiva", "Calidad"),
    ("visitado", "Visitado"),
    ("observaciones", "Observaciones"),
]
GRAVEDAD_CUADRANTE_LABELS = {
    "leve": "Leve",
    "media": "Media",
    "grave": "Grave",
}


def configurar_documento(doc: Document) -> None:
    seccion = doc.sections[-1]
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


def add_etiqueta_valor_si_hay(doc: Document, etiqueta: str, valor) -> None:
    if limpiar_texto(valor):
        add_etiqueta_valor(doc, etiqueta, valor)


def add_bloque_campos_si_hay(doc: Document, campos, datos, vacio: str | None = None) -> bool:
    hay_datos = False
    for campo, etiqueta in campos:
        if limpiar_texto(datos[campo]):
            add_etiqueta_valor(doc, etiqueta, datos[campo])
            hay_datos = True
    if not hay_datos and vacio:
        add_parrafo(doc, vacio)
    return hay_datos


def estado_inspeccion_legible(valor) -> str:
    estado = limpiar_texto(valor)
    if not estado:
        estado = "no_inspeccionado"
    return ESTADO_INSPECCION_LABELS.get(estado, valor_o_guion(estado))


def estado_habitabilidad_legible(valor) -> str:
    estado = limpiar_texto(valor)
    if not estado:
        estado = "no_inspeccionado"
    return ESTADO_HABITABILIDAD_LABELS.get(estado, valor_o_guion(estado))


def conclusion_habitabilidad_legible(valor) -> str:
    conclusion = limpiar_texto(valor)
    return CONCLUSION_HABITABILIDAD_LABELS.get(conclusion, valor_o_guion(conclusion))


def obtener_items_inspeccion_estancia(tipo_estancia: str):
    tipo = limpiar_texto(tipo_estancia).lower()
    items = list(INSPECCION_ESTANCIA_BASE_ITEMS)

    if tipo in {"baño", "aseo"}:
        items.extend(INSPECCION_ESTANCIA_BANO_ITEMS)
    elif tipo == "cocina":
        items.extend(INSPECCION_ESTANCIA_COCINA_ITEMS)
    elif tipo in {"salón", "salon", "dormitorio", "comedor", "recibidor", "pasillo"}:
        items.extend(INSPECCION_ESTANCIA_HABITABLE_ITEMS)

    return items


def add_estado_checklist(doc: Document, items, datos) -> None:
    for campo, etiqueta in items:
        add_etiqueta_valor(doc, etiqueta, estado_inspeccion_legible(datos[campo]))


def add_estado_checklist_habitabilidad(doc: Document, items, datos) -> None:
    for campo, etiqueta in items:
        add_etiqueta_valor(doc, etiqueta, estado_habitabilidad_legible(datos[campo]))


def recoger_incidencias_checklist(items, datos):
    incidencias = []
    for campo, etiqueta in items:
        estado = limpiar_texto(datos[campo])
        if estado in {"necesita_reparacion", "defecto_grave"}:
            incidencias.append((etiqueta, estado_inspeccion_legible(estado)))
    return incidencias


def fila_o_dict_vacio(fila, campos):
    if fila is None:
        return {campo: "" for campo in campos}
    return {campo: fila[campo] for campo in campos}


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


def indice_a_letras_cuadrante(indice: int) -> str:
    letras = ""
    valor = indice + 1
    while valor > 0:
        valor, resto = divmod(valor - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def generar_overlay_cuadrantes_mapa(
    ruta_imagen, filas, columnas, cuadrantes_con_incidencia
):
    from PIL import Image, ImageDraw, ImageFont

    if not ruta_imagen or not os.path.exists(ruta_imagen):
        raise FileNotFoundError("Imagen base no localizada")
    if not filas or not columnas or int(filas) <= 0 or int(columnas) <= 0:
        raise ValueError("Filas o columnas no válidas")

    imagen = Image.open(ruta_imagen).convert("RGBA")
    ancho, alto = imagen.size
    ancho_celda = ancho / int(columnas)
    alto_celda = alto / int(filas)
    draw = ImageDraw.Draw(imagen, "RGBA")
    font = ImageFont.load_default()
    incidencias = {limpiar_texto(codigo).upper() for codigo in cuadrantes_con_incidencia if limpiar_texto(codigo)}

    for fila_idx in range(int(filas)):
        for columna_idx in range(int(columnas)):
            x0 = int(round(columna_idx * ancho_celda))
            y0 = int(round(fila_idx * alto_celda))
            x1 = int(round((columna_idx + 1) * ancho_celda))
            y1 = int(round((fila_idx + 1) * alto_celda))
            codigo = f"{indice_a_letras_cuadrante(fila_idx)}{columna_idx + 1}"

            if codigo.upper() in incidencias:
                draw.rectangle(
                    [(x0, y0), (x1, y1)],
                    fill=(255, 0, 0, 28),
                    outline=(200, 0, 0, 255),
                    width=4,
                )

            draw.rectangle(
                [(x0, y0), (x1, y1)],
                outline=(0, 0, 0, 170),
                width=1,
            )

            bbox = draw.textbbox((0, 0), codigo, font=font)
            texto_ancho = bbox[2] - bbox[0]
            texto_alto = bbox[3] - bbox[1]
            texto_x = x0 + 6
            texto_y = y0 + 4
            draw.rectangle(
                [
                    (texto_x - 3, texto_y - 2),
                    (texto_x + texto_ancho + 3, texto_y + texto_alto + 2),
                ],
                fill=(255, 255, 255, 190),
            )
            draw.text((texto_x, texto_y), codigo, fill=(0, 0, 0, 255), font=font)

    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def add_imagen_mapa_con_overlay(doc: Document, mapa) -> None:
    nombre_foto = limpiar_texto(mapa.get("imagen_base"))
    if not nombre_foto:
        return

    ruta_foto = os.path.join(UPLOAD_DIR, nombre_foto)
    cuadrantes_con_incidencia = [
        cuadrante["codigo_cuadrante"] for cuadrante in mapa.get("cuadrantes", [])
    ]

    try:
        overlay = generar_overlay_cuadrantes_mapa(
            ruta_foto,
            mapa.get("filas"),
            mapa.get("columnas"),
            cuadrantes_con_incidencia,
        )
        doc.add_picture(overlay, width=Cm(12.5))
        ultimo = doc.paragraphs[-1]
        ultimo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ultimo.paragraph_format.space_after = Pt(8)
    except Exception:
        add_imagen_si_existe(doc, nombre_foto)


def add_tabla_comparables(doc: Document, comparables) -> None:
    if not comparables:
        add_parrafo(doc, "No constan comparables registrados.")
        return

    tabla = doc.add_table(rows=1, cols=len(COMPARABLES_COLUMNAS))
    tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabla.style = "Table Grid"

    encabezado = tabla.rows[0].cells
    for indice, (_, titulo) in enumerate(COMPARABLES_COLUMNAS):
        encabezado[indice].text = titulo

    for comparable in comparables:
        fila = tabla.add_row().cells
        for indice, (campo, _) in enumerate(COMPARABLES_COLUMNAS):
            fila[indice].text = valor_o_guion(comparable[campo])

    for fila in tabla.rows:
        es_encabezado = fila is tabla.rows[0]
        for celda in fila.cells:
            celda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for parrafo in celda.paragraphs:
                for run in parrafo.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(8)
                    run.bold = es_encabezado


def add_valor_destacado(doc: Document, etiqueta: str, valor) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)

    r1 = p.add_run(f"{etiqueta}: ")
    r1.bold = True
    r1.font.name = "Arial"
    r1.font.size = Pt(13)

    r2 = p.add_run(valor_o_guion(valor))
    r2.bold = True
    r2.font.name = "Arial"
    r2.font.size = Pt(14)


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

    numero_unidad = "2.1"

    if expediente["observaciones_bloque"]:
        doc.add_heading("2.1 Características del bloque", level=2)
        add_etiqueta_valor(
            doc, "Observaciones del bloque", expediente["observaciones_bloque"]
        )
        numero_unidad = "2.2"

    doc.add_heading(f"{numero_unidad} Características de la unidad", level=2)
    add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
    add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
    add_etiqueta_valor(
        doc, "Superficie construida", expediente["superficie_construida"]
    )
    add_etiqueta_valor(doc, "Superficie útil", expediente["superficie_util"])
    add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
    add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
    add_etiqueta_valor(
        doc, "Observaciones de la unidad", expediente["observaciones_unidad"]
    )


def add_apartado_bloque_judicial(doc: Document, numero_apartado: int, expediente) -> None:
    if limpiar_texto(expediente["destinatario"]) != "judicial":
        return

    doc.add_heading(f"{numero_apartado}. Encargo judicial", level=1)
    add_etiqueta_valor_si_hay(
        doc, "Procedimiento judicial", expediente["procedimiento_judicial"]
    )
    add_etiqueta_valor_si_hay(doc, "Juzgado", expediente["juzgado"])
    add_etiqueta_valor_si_hay(doc, "Auto judicial", expediente["auto_judicial"])
    add_etiqueta_valor_si_hay(
        doc, "Parte solicitante", expediente["parte_solicitante"]
    )
    add_etiqueta_valor_si_hay(doc, "Objeto de la pericia", expediente["objeto_pericia"])
    add_etiqueta_valor_si_hay(
        doc, "Alcance y limitaciones", expediente["alcance_limitaciones"]
    )
    add_etiqueta_valor_si_hay(
        doc, "Metodología pericial", expediente["metodologia_pericial"]
    )


def add_apartado_datos_patologias(doc: Document, numero_apartado: int, expediente) -> None:
    doc.add_heading(
        f"{numero_apartado}. Datos específicos del informe de patologías", level=1
    )

    ambitos = {
        "interior": "Interior",
        "exterior": "Exterior",
        "interior_exterior": "Interior y exterior",
    }
    add_etiqueta_valor(
        doc,
        "Ámbito de patologías",
        ambitos.get(limpiar_texto(expediente["ambito_patologias"]), expediente["ambito_patologias"]),
    )
    add_etiqueta_valor_si_hay(doc, "Descripción del daño", expediente["descripcion_dano"])
    add_etiqueta_valor_si_hay(doc, "Causa probable", expediente["causa_probable"])
    add_etiqueta_valor_si_hay(doc, "Pruebas e indicios", expediente["pruebas_indicios"])
    add_etiqueta_valor_si_hay(
        doc, "Evolución / preexistencia", expediente["evolucion_preexistencia"]
    )
    add_etiqueta_valor_si_hay(
        doc, "Propuesta de reparación", expediente["propuesta_reparacion"]
    )
    add_etiqueta_valor_si_hay(doc, "Urgencia / gravedad", expediente["urgencia_gravedad"])


def add_apartado_inspeccion_visita(doc: Document, numero_apartado: int, visitas, climatologias) -> None:
    doc.add_heading(f"{numero_apartado}. Inspección y visita", level=1)

    if not visitas:
        add_parrafo(doc, "No constan visitas registradas en el expediente.")
        return

    for indice, visita in enumerate(visitas, start=1):
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_etiqueta_valor(doc, "Técnico", visita["tecnico"])
        add_etiqueta_valor(doc, "Observaciones de visita", visita["observaciones_visita"])
        climatologia = climatologias.get(visita["id"])
        if climatologia:
            add_etiqueta_valor(doc, "Climatología", climatologia["resumen"])
        else:
            add_etiqueta_valor(doc, "Climatología", "No consta climatología registrada")


def agrupar_patologias_interiores(patologias):
    grupos = OrderedDict()
    for patologia in patologias:
        nivel = limpiar_texto(patologia["nivel_nombre"])
        unidad = limpiar_texto(patologia["unidad_identificador"])
        estancia = limpiar_texto(patologia["estancia_nombre"]) or "Sin estancia"
        clave = (nivel, unidad, estancia)
        grupos.setdefault(
            clave,
            {
                "nivel": nivel,
                "unidad": unidad,
                "estancia": estancia,
                "items": [],
            },
        )
        grupos[clave]["items"].append(patologia)
    return grupos


def agrupar_patologias_exteriores(registros):
    grupos = OrderedDict()
    for registro in registros:
        zona = limpiar_texto(registro["zona_exterior"]) or "Sin zona exterior"
        grupos.setdefault(zona, []).append(registro)
    return grupos


def deduplicar_textos(valores) -> list[str]:
    resultado = []
    vistos = set()
    for valor in valores:
        texto = limpiar_texto(valor)
        if not texto:
            continue
        clave = texto.lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(texto)
    return resultado


def unir_lista_natural(valores) -> str:
    items = deduplicar_textos(valores)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} y {items[1]}"
    return f"{', '.join(items[:-1])} y {items[-1]}"


def obtener_rol_final_patologia(registro) -> str:
    rol_patologia_observado = (
        registro["rol_patologia_observado"]
        if "rol_patologia_observado" in registro.keys()
        else ""
    )
    rol_patologia_biblioteca = (
        registro["rol_patologia_biblioteca"]
        if "rol_patologia_biblioteca" in registro.keys()
        else ""
    )
    return limpiar_texto(
        rol_patologia_observado or rol_patologia_biblioteca
    ).lower()


def construir_resumen_patologias(prefijo: str, registros) -> str:
    causas = []
    efectos = []
    mixtas = []
    observaciones = []

    for registro in registros:
        rol = obtener_rol_final_patologia(registro)
        nombre_patologia = limpiar_texto(registro["patologia"])
        if rol == "causa":
            causas.append(nombre_patologia)
        elif rol == "efecto":
            efectos.append(nombre_patologia)
        elif rol == "mixta":
            mixtas.append(nombre_patologia)
        obs = limpiar_texto(registro["observaciones"])
        if obs:
            observaciones.append(obs)

    causas = deduplicar_textos(causas)
    efectos = deduplicar_textos(efectos)
    mixtas = deduplicar_textos(mixtas)
    observaciones = deduplicar_textos(observaciones)

    frases = []
    efectos_principales = list(efectos)
    if causas:
        efectos_principales = deduplicar_textos(efectos_principales + mixtas)
    descripcion_causas = (
        f"se observan procesos patológicos consistentes en {unir_lista_natural(causas)}"
        if len(causas) > 1
        else f"se observa {unir_lista_natural(causas)}"
    )

    if causas and efectos_principales:
        frases.append(
            f"{prefijo} {descripcion_causas}, "
            f"con efectos derivados consistentes en {unir_lista_natural(efectos_principales)}."
        )
    elif causas:
        frases.append(f"{prefijo} {descripcion_causas}.")
        if mixtas:
            frases.append(f"Asimismo, se aprecian {unir_lista_natural(mixtas)}.")
    elif efectos:
        frases.append(
            f"{prefijo} se observan daños consistentes en {unir_lista_natural(efectos)}, "
            "sin poder determinar con certeza su origen."
        )
        if mixtas:
            frases.append(f"Asimismo, se aprecian {unir_lista_natural(mixtas)}.")
    elif mixtas:
        frases.append(f"{prefijo} se observa {unir_lista_natural(mixtas)}.")

    if observaciones:
        frases.append(f"Asimismo, se aprecian {unir_lista_natural(observaciones)}.")

    return " ".join(frases)


def construir_titulo_grupo_interior(grupo) -> str:
    partes = []
    if grupo["nivel"]:
        partes.append(f"Nivel: {grupo['nivel']}")
    if grupo["unidad"]:
        partes.append(f"Unidad: {grupo['unidad']}")
    partes.append(f"Estancia: {grupo['estancia']}")
    return " · ".join(partes)


def detectar_incoherencias(registros) -> list[str]:
    causas = 0
    efectos = 0
    mixtas_sin_definir = 0

    for registro in registros:
        rol_observado = limpiar_texto(
            registro["rol_patologia_observado"]
            if "rol_patologia_observado" in registro.keys()
            else ""
        ).lower()
        rol_final = obtener_rol_final_patologia(registro)
        if rol_final == "causa":
            causas += 1
        elif rol_final == "efecto":
            efectos += 1
        elif rol_final == "mixta" and not rol_observado:
            mixtas_sin_definir += 1

    incoherencias = []
    if efectos and not causas:
        incoherencias.append(
            "Se han identificado efectos sin una causa claramente asociada. Se recomienda revisar el origen del daño."
        )
    if causas and not efectos:
        incoherencias.append(
            "Se han identificado causas sin manifestaciones visibles asociadas en el momento de la inspección."
        )
    if mixtas_sin_definir:
        incoherencias.append(
            "Existen patologías de carácter mixto cuya función no ha sido especificada (causa o efecto)."
        )
    return incoherencias


def construir_conclusion_tecnica_global(patologias_interiores, patologias_exteriores) -> str:
    registros = list(patologias_interiores) + list(patologias_exteriores)
    if not registros:
        return "No constan patologías registradas en el expediente."

    causas = []
    efectos = []
    mixtas = []
    incoherencias = []

    for registro in registros:
        rol = obtener_rol_final_patologia(registro)
        nombre_patologia = limpiar_texto(registro["patologia"])
        if rol == "causa":
            causas.append(nombre_patologia)
        elif rol == "efecto":
            efectos.append(nombre_patologia)
        elif rol == "mixta":
            mixtas.append(nombre_patologia)

    causas = deduplicar_textos(causas)
    efectos = deduplicar_textos(efectos)
    mixtas = deduplicar_textos(mixtas)
    incoherencias = deduplicar_textos(detectar_incoherencias(registros))

    afecta_interior = bool(patologias_interiores)
    afecta_exterior = bool(patologias_exteriores)
    if afecta_interior and afecta_exterior:
        alcance = "interior y exterior"
    elif afecta_interior:
        alcance = "interior"
    elif afecta_exterior:
        alcance = "exterior"
    else:
        alcance = ""

    frases = []
    causas_principales = deduplicar_textos(causas + mixtas)

    if causas_principales:
        frases.append(
            f"Del análisis realizado se concluye que existen procesos patológicos asociados a {unir_lista_natural(causas_principales)}."
        )
        if efectos:
            frases.append(
                f"Estos han generado efectos consistentes en {unir_lista_natural(efectos)}, afectando a {alcance}."
            )
        else:
            frases.append("Se han identificado causas sin manifestaciones visibles claras.")
    elif efectos:
        frases.append("Se han identificado daños sin una causa claramente definida.")

    if incoherencias:
        frases.append(
            "Asimismo, se recomienda revisar determinadas situaciones detectadas durante el análisis."
        )

    return " ".join(frases)


def construir_conclusion_pericial(patologias_interiores, patologias_exteriores) -> str:
    registros = list(patologias_interiores) + list(patologias_exteriores)
    if not registros:
        return "No se observan daños significativos que permitan establecer una conclusión pericial."

    incoherencias = detectar_incoherencias(registros)
    causas = []
    efectos = []

    for registro in registros:
        rol = obtener_rol_final_patologia(registro)
        nombre_patologia = limpiar_texto(registro["patologia"])
        if rol == "causa":
            causas.append(nombre_patologia)
        elif rol == "efecto":
            efectos.append(nombre_patologia)

    causas = deduplicar_textos(causas)
    causa_dominante = causas[0] if causas else ""
    efectos = deduplicar_textos(efectos)
    hay_causas = bool(causas)
    hay_efectos = bool(efectos)
    hay_incoherencias = bool(incoherencias)

    frases = []
    if hay_causas and hay_efectos and not hay_incoherencias:
        frases.append(
            f"Del análisis realizado se desprende que los daños observados tienen su origen en procesos asociados a {causa_dominante}."
        )
        frases.append(
            f"Las manifestaciones detectadas, consistentes en {unir_lista_natural(efectos)}, presentan coherencia con dicho origen."
        )
        frases.append(
            "La distribución de las lesiones en el inmueble resulta compatible con el mecanismo descrito."
        )
    elif hay_incoherencias:
        frases.append(
            "No puede determinarse con certeza el origen de los daños observados a partir de la información disponible."
        )
    elif hay_efectos:
        frases.append(
            f"Los daños observados resultan compatibles con procesos asociados a {causa_dominante or 'diversos mecanismos patológicos'}."
        )
    elif hay_causas:
        frases.append(
            "Se identifican procesos patológicos sin manifestaciones visibles suficientemente definidas en el momento de la inspección."
        )
    else:
        frases.append(
            "No se observan daños significativos que permitan establecer una conclusión pericial."
        )

    if patologias_interiores and patologias_exteriores:
        frases.append(
            "Los daños afectan tanto a zonas interiores como exteriores del inmueble."
        )

    return " ".join(frases)


def add_apartado_patologias_interiores(
    doc: Document, numero_apartado: int, patologias, conn
) -> None:
    doc.add_heading(f"{numero_apartado}. Patologías interiores", level=1)

    if not patologias:
        add_parrafo(doc, "No constan patologías interiores registradas.")
        return

    grupos = agrupar_patologias_interiores(patologias)
    indice_estancia = 1
    for grupo in grupos.values():
        doc.add_heading(
            f"{numero_apartado}.{indice_estancia} {construir_titulo_grupo_interior(grupo)}",
            level=2,
        )
        resumen = construir_resumen_patologias(
            f"En la estancia {grupo['estancia']}",
            grupo["items"],
        )
        if resumen:
            add_parrafo(doc, resumen)
        incoherencias = detectar_incoherencias(grupo["items"])
        if incoherencias:
            add_parrafo(doc, "Observaciones técnicas:", bold=True)
            for item in incoherencias:
                add_parrafo(doc, f"- {item}")
        for indice_item, item in enumerate(grupo["items"], start=1):
            doc.add_heading(
                f"{numero_apartado}.{indice_estancia}.{indice_item} {valor_o_guion(item['patologia'])}",
                level=3,
            )
            referencias_cuadrantes = obtener_referencias_cuadrantes_patologia(
                conn, item["id"]
            )
            if referencias_cuadrantes:
                add_etiqueta_valor(
                    doc,
                    "Cuadrantes",
                    formatear_referencias_cuadrantes_patologia(referencias_cuadrantes),
                )
            add_etiqueta_valor(doc, "Localización del daño", item["localizacion_dano"])
            add_etiqueta_valor(doc, "Elemento", item["elemento"])
            add_etiqueta_valor(doc, "Patología", item["patologia"])
            add_etiqueta_valor(doc, "Observaciones", item["observaciones"])
            if item["foto"]:
                add_parrafo(doc, "Fotografía asociada:", bold=True)
                add_imagen_si_existe(doc, item["foto"])
        indice_estancia += 1


def add_apartado_patologias_exteriores(
    doc: Document, numero_apartado: int, registros, conn
) -> None:
    doc.add_heading(f"{numero_apartado}. Patologías exteriores", level=1)

    if not registros:
        add_parrafo(doc, "No constan patologías exteriores registradas.")
        return

    zonas = {
        "fachada": "Fachada",
        "cubierta": "Cubierta",
        "medianera": "Medianera",
        "patio": "Patio",
        "terraza": "Terraza",
        "exterior_general": "Exterior general",
    }
    elementos = {
        "revestimiento": "Revestimiento",
        "cerramiento": "Cerramiento",
        "cornisa": "Cornisa",
        "alero": "Alero",
        "peto": "Peto",
        "impermeabilizacion": "Impermeabilizacion",
        "carpinteria_exterior": "Carpinteria exterior",
        "barandilla": "Barandilla",
        "bajante": "Bajante",
        "canalon": "Canalon",
        "forjado": "Forjado",
        "otro": "Otro",
    }
    localizaciones = {
        "horizontal": "Horizontal",
        "vertical": "Vertical",
        "encuentro": "Encuentro",
        "puntual": "Puntual",
    }

    grupos = agrupar_patologias_exteriores(registros)
    indice_zona = 1
    for zona, items in grupos.items():
        doc.add_heading(
            f"{numero_apartado}.{indice_zona} {zonas.get(zona, zona)}",
            level=2,
        )
        resumen = construir_resumen_patologias(
            "En el exterior del inmueble",
            items,
        )
        if resumen:
            add_parrafo(doc, resumen)
        incoherencias = detectar_incoherencias(items)
        if incoherencias:
            add_parrafo(doc, "Observaciones técnicas:", bold=True)
            for item in incoherencias:
                add_parrafo(doc, f"- {item}")
        for indice_item, item in enumerate(items, start=1):
            doc.add_heading(
                f"{numero_apartado}.{indice_zona}.{indice_item} {valor_o_guion(item['patologia'])}",
                level=3,
            )
            referencias_cuadrantes = obtener_referencias_cuadrantes_patologia(
                conn, item["id"]
            )
            if referencias_cuadrantes:
                add_etiqueta_valor(
                    doc,
                    "Cuadrantes",
                    formatear_referencias_cuadrantes_patologia(referencias_cuadrantes),
                )
            add_etiqueta_valor(
                doc,
                "Elemento exterior",
                elementos.get(limpiar_texto(item["elemento_exterior"]), item["elemento_exterior"]),
            )
            add_etiqueta_valor(
                doc,
                "Localización del daño exterior",
                localizaciones.get(
                    limpiar_texto(item["localizacion_dano_exterior"]),
                    item["localizacion_dano_exterior"],
                ),
            )
            add_etiqueta_valor(doc, "Patología", item["patologia"])
            add_etiqueta_valor(doc, "Observaciones", item["observaciones"])
            if item["foto"]:
                add_parrafo(doc, "Fotografía asociada:", bold=True)
                add_imagen_si_existe(doc, item["foto"])
        indice_zona += 1


def describir_objeto_visita_informe(cur, visita) -> str:
    ambito = limpiar_texto(visita["ambito_visita"]) or "edificio_completo"
    if ambito == "edificio_completo":
        return "Edificio completo"
    if ambito == "nivel" and visita["nivel_id"]:
        nivel = cur.execute(
            "SELECT nombre_nivel FROM niveles_edificio WHERE id=?",
            (visita["nivel_id"],),
        ).fetchone()
        if nivel and limpiar_texto(nivel["nombre_nivel"]):
            return f"Nivel: {nivel['nombre_nivel']}"
    if visita["unidad_id"]:
        unidad = cur.execute(
            "SELECT identificador FROM unidades_expediente WHERE id=?",
            (visita["unidad_id"],),
        ).fetchone()
        identificador = limpiar_texto(unidad["identificador"]) if unidad else ""
        if identificador:
            if ambito == "zona_comun":
                return f"Zona común: {identificador}"
            if ambito == "exterior":
                return f"Exterior: {identificador}"
            return f"Unidad: {identificador}"
    etiquetas = {
        "nivel": "Nivel",
        "unidad": "Unidad",
        "zona_comun": "Zona común",
        "exterior": "Exterior",
    }
    return etiquetas.get(ambito, valor_o_guion(ambito))


def resumen_patologia_vinculada_mapa(cur, visita_id: int, patologia_id, patologia_detectada) -> str:
    if patologia_id:
        interior = cur.execute(
            """
            SELECT rp.patologia, e.nombre AS estancia_nombre
            FROM registros_patologias rp
            JOIN estancias e ON rp.estancia_id = e.id
            WHERE rp.id=? AND rp.visita_id=?
            """,
            (patologia_id, visita_id),
        ).fetchone()
        exterior = cur.execute(
            """
            SELECT patologia, zona_exterior
            FROM registros_patologias_exteriores
            WHERE id=? AND visita_id=?
            """,
            (patologia_id, visita_id),
        ).fetchone()

        texto_referencia = limpiar_texto(patologia_detectada).lower()
        if interior and exterior and texto_referencia:
            if limpiar_texto(interior["patologia"]).lower() == texto_referencia:
                exterior = None
            elif limpiar_texto(exterior["patologia"]).lower() == texto_referencia:
                interior = None

        if interior:
            estancia = limpiar_texto(interior["estancia_nombre"])
            if estancia:
                return f"{interior['patologia']} ({estancia})"
            return valor_o_guion(interior["patologia"])
        if exterior:
            zona = limpiar_texto(exterior["zona_exterior"])
            if zona:
                return f"{exterior['patologia']} ({zona})"
            return valor_o_guion(exterior["patologia"])

    return limpiar_texto(patologia_detectada)


def obtener_referencias_cuadrantes_patologia(conn, patologia_id):
    if not patologia_id:
        return []

    filas = conn.execute(
        """
        SELECT mp.titulo AS mapa_titulo, qmp.codigo_cuadrante
        FROM cuadrantes_mapa_patologia qmp
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        WHERE qmp.patologia_id = ?
        ORDER BY mp.id ASC, qmp.id ASC
        """,
        (patologia_id,),
    ).fetchall()

    if not filas:
        return []

    agrupado = OrderedDict()
    for fila in filas:
        mapa_titulo = limpiar_texto(fila["mapa_titulo"]) or "Mapa sin título"
        agrupado.setdefault(mapa_titulo, [])
        codigo = limpiar_texto(fila["codigo_cuadrante"])
        if codigo and codigo not in agrupado[mapa_titulo]:
            agrupado[mapa_titulo].append(codigo)

    return [
        {
            "mapa_titulo": "" if mapa_titulo == "Mapa sin título" else mapa_titulo,
            "cuadrantes": sorted(cuadrantes, key=clave_orden_cuadrante),
        }
        for mapa_titulo, cuadrantes in agrupado.items()
    ]


def formatear_referencias_cuadrantes_patologia(referencias) -> str:
    if not referencias:
        return ""

    if len(referencias) == 1:
        referencia = referencias[0]
        cuadrantes = ", ".join(referencia["cuadrantes"])
        mapa_titulo = limpiar_texto(referencia["mapa_titulo"])
        if mapa_titulo:
            return f"{cuadrantes} (Mapa: {mapa_titulo})"
        return cuadrantes

    partes = []
    for referencia in referencias:
        cuadrantes = ", ".join(referencia["cuadrantes"])
        mapa_titulo = limpiar_texto(referencia["mapa_titulo"])
        if mapa_titulo:
            partes.append(f"{cuadrantes} ({mapa_titulo})")
        else:
            partes.append(cuadrantes)
    return " | ".join(partes)


def cargar_mapas_patologia_utiles_visita(cur, visita):
    mapas = cur.execute(
        """
        SELECT *
        FROM mapas_patologia
        WHERE visita_id=?
        ORDER BY id ASC
        """,
        (visita["id"],),
    ).fetchall()

    resultado = []
    for mapa in mapas:
        cuadrantes = cur.execute(
            """
            SELECT *
            FROM cuadrantes_mapa_patologia
            WHERE mapa_id=?
            ORDER BY id ASC
            """,
            (mapa["id"],),
        ).fetchall()
        cuadrantes_utiles = []
        for cuadrante in cuadrantes:
            tiene_datos = any(
                [
                    limpiar_texto(cuadrante["descripcion"]),
                    limpiar_texto(cuadrante["gravedad"]),
                    cuadrante["patologia_id"],
                    limpiar_texto(cuadrante["foto_detalle"]),
                ]
            )
            if not tiene_datos:
                continue
            cuadrantes_utiles.append(
                {
                    "codigo_cuadrante": cuadrante["codigo_cuadrante"],
                    "descripcion": cuadrante["descripcion"],
                    "gravedad_label": GRAVEDAD_CUADRANTE_LABELS.get(
                        limpiar_texto(cuadrante["gravedad"]), valor_o_guion(cuadrante["gravedad"])
                    ),
                    "patologia_vinculada_resumen": resumen_patologia_vinculada_mapa(
                        cur,
                        visita["id"],
                        cuadrante["patologia_id"],
                        cuadrante["patologia_detectada"],
                    ),
                    "foto_detalle": cuadrante["foto_detalle"],
                }
            )

        if not cuadrantes_utiles:
            continue

        resultado.append(
            {
                "titulo": mapa["titulo"],
                "descripcion": mapa["descripcion"],
                "imagen_base": mapa["imagen_base"],
                "filas": mapa["filas"],
                "columnas": mapa["columnas"],
                "objeto_visita_label": describir_objeto_visita_informe(cur, visita),
                "cuadrantes": cuadrantes_utiles,
            }
        )

    return resultado


def add_apartado_mapas_patologia(
    doc: Document, numero_apartado: int, bloques_mapas
) -> bool:
    bloques_utiles = [bloque for bloque in bloques_mapas if bloque["mapas"]]
    if not bloques_utiles:
        return False

    doc.add_heading(f"{numero_apartado}. Mapas de localización de daños", level=1)

    multiple_visitas = len(bloques_utiles) > 1
    for indice_visita, bloque in enumerate(bloques_utiles, start=1):
        visita = bloque["visita"]
        mapas = bloque["mapas"]
        prefijo_visita = f"{numero_apartado}.{indice_visita}"

        if multiple_visitas:
            doc.add_heading(
                f"{prefijo_visita} Visita de fecha {valor_o_guion(visita['fecha'])}",
                level=2,
            )

        for indice_mapa, mapa in enumerate(mapas, start=1):
            prefijo_mapa = (
                f"{prefijo_visita}.{indice_mapa}" if multiple_visitas else f"{numero_apartado}.{indice_mapa}"
            )
            doc.add_heading(f"{prefijo_mapa} {valor_o_guion(mapa['titulo'])}", level=2 if not multiple_visitas else 3)
            add_etiqueta_valor_si_hay(doc, "Descripción", mapa["descripcion"])
            add_etiqueta_valor_si_hay(doc, "Contexto", mapa["objeto_visita_label"])
            if mapa["imagen_base"]:
                add_parrafo(doc, "Imagen base con cuadrícula:", bold=True)
                add_imagen_mapa_con_overlay(doc, mapa)

            for indice_cuadrante, cuadrante in enumerate(mapa["cuadrantes"], start=1):
                prefijo_cuadrante = f"{prefijo_mapa}.{indice_cuadrante}"
                doc.add_heading(
                    f"{prefijo_cuadrante} Cuadrante {valor_o_guion(cuadrante['codigo_cuadrante'])}",
                    level=3,
                )
                add_etiqueta_valor_si_hay(doc, "Descripción", cuadrante["descripcion"])
                if limpiar_texto(cuadrante["gravedad_label"]) and cuadrante["gravedad_label"] != "-":
                    add_etiqueta_valor(doc, "Gravedad", cuadrante["gravedad_label"])
                add_etiqueta_valor_si_hay(
                    doc,
                    "Patología vinculada",
                    cuadrante["patologia_vinculada_resumen"],
                )
                if cuadrante["foto_detalle"]:
                    add_parrafo(doc, "Foto detalle:", bold=True)
                    add_imagen_si_existe(doc, cuadrante["foto_detalle"])

    return True


def add_apartado_analisis_tecnico(doc: Document, numero_apartado: int, expediente) -> None:
    doc.add_heading(f"{numero_apartado}. Análisis técnico", level=1)
    campos = [
        ("Descripción del daño", expediente["descripcion_dano"]),
        ("Causa probable", expediente["causa_probable"]),
        ("Pruebas e indicios", expediente["pruebas_indicios"]),
        ("Evolución / preexistencia", expediente["evolucion_preexistencia"]),
        ("Urgencia / gravedad", expediente["urgencia_gravedad"]),
    ]
    hay_datos = False
    for etiqueta, valor in campos:
        if limpiar_texto(valor):
            add_etiqueta_valor(doc, etiqueta, valor)
            hay_datos = True
    if not hay_datos:
        add_parrafo(doc, "No constan observaciones globales adicionales de análisis técnico.")


def add_apartado_propuesta_reparacion(doc: Document, numero_apartado: int, expediente) -> None:
    doc.add_heading(f"{numero_apartado}. Propuesta de reparación", level=1)
    if limpiar_texto(expediente["propuesta_reparacion"]):
        add_parrafo(doc, expediente["propuesta_reparacion"])
    else:
        add_parrafo(doc, "No consta propuesta de reparación registrada.")


def add_apartado_conclusion_patologias(
    doc: Document, numero_apartado: int, patologias_interiores, patologias_exteriores
) -> None:
    doc.add_heading(f"{numero_apartado}. Conclusiones técnicas", level=1)
    add_parrafo(
        doc,
        construir_conclusion_tecnica_global(
            patologias_interiores,
            patologias_exteriores,
        ),
    )


def add_apartado_conclusion_pericial(
    doc: Document, numero_apartado: int, patologias_interiores, patologias_exteriores
) -> None:
    doc.add_heading(f"{numero_apartado}. Conclusiones periciales", level=1)
    add_parrafo(
        doc,
        construir_conclusion_pericial(
            patologias_interiores,
            patologias_exteriores,
        ),
    )


def cargar_habitabilidad_visita(cur, visita_id: int) -> dict:
    general_campos = [campo for campo, _ in HABITABILIDAD_GENERAL_ITEMS] + [
        "conclusion_habitabilidad",
        "observaciones_generales_habitabilidad",
    ]
    exterior_campos = [campo for campo, _ in HABITABILIDAD_EXTERIOR_ITEMS] + [
        "observaciones_exterior_habitabilidad"
    ]

    general = fila_o_dict_vacio(
        cur.execute(
            """
            SELECT *
            FROM habitabilidad_general_visita
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone(),
        general_campos,
    )
    exterior = fila_o_dict_vacio(
        cur.execute(
            """
            SELECT *
            FROM habitabilidad_exterior
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone(),
        exterior_campos,
    )
    estancias = cur.execute(
        """
        SELECT e.id AS estancia_id,
               e.nombre AS estancia_nombre,
               e.tipo_estancia,
               e.planta,
               e.acabado_pavimento,
               e.acabado_paramento,
               e.acabado_techo,
               he.*
        FROM estancias e
        LEFT JOIN habitabilidad_estancias he
               ON he.estancia_id = e.id
              AND he.visita_id = e.visita_id
        WHERE e.visita_id = ?
        ORDER BY e.id ASC
        """,
        (visita_id,),
    ).fetchall()

    return {
        "general": general,
        "exterior": exterior,
        "estancias": estancias,
    }


def add_apartado_condiciones_habitabilidad(
    doc: Document, numero_apartado: int, visitas_habitabilidad
) -> None:
    doc.add_heading(f"{numero_apartado}. Condiciones generales de habitabilidad", level=1)

    if not visitas_habitabilidad:
        add_parrafo(doc, "No constan comprobaciones generales de habitabilidad registradas.")
        return

    for indice, bloque in enumerate(visitas_habitabilidad, start=1):
        visita = bloque["visita"]
        general = bloque["habitabilidad"]["general"]
        climatologia = bloque["climatologia"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_etiqueta_valor(doc, "Técnico", visita["tecnico"])
        if climatologia:
            add_etiqueta_valor(doc, "Climatología", climatologia["resumen"])
        for campo, etiqueta in HABITABILIDAD_GENERAL_ITEMS:
            add_etiqueta_valor(doc, etiqueta, estado_habitabilidad_legible(general[campo]))
        if limpiar_texto(general["observaciones_generales_habitabilidad"]):
            add_etiqueta_valor(
                doc,
                "Observaciones generales de habitabilidad",
                general["observaciones_generales_habitabilidad"],
            )


def add_apartado_evaluacion_estancias_habitabilidad(
    doc: Document, numero_apartado: int, visitas_habitabilidad
) -> None:
    doc.add_heading(f"{numero_apartado}. Evaluación por estancias", level=1)

    if not visitas_habitabilidad:
        add_parrafo(doc, "No constan estancias evaluadas.")
        return

    for indice_visita, bloque in enumerate(visitas_habitabilidad, start=1):
        visita = bloque["visita"]
        estancias = bloque["habitabilidad"]["estancias"]
        doc.add_heading(
            f"{numero_apartado}.{indice_visita} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        if not estancias:
            add_parrafo(doc, "No constan estancias registradas en esta visita.")
            continue

        for indice_estancia, estancia in enumerate(estancias, start=1):
            doc.add_heading(
                f"{numero_apartado}.{indice_visita}.{indice_estancia} {valor_o_guion(estancia['estancia_nombre'])}",
                level=3,
            )
            add_etiqueta_valor(doc, "Tipo de estancia", estancia["tipo_estancia"])
            add_etiqueta_valor(doc, "Planta", estancia["planta"])
            add_etiqueta_valor(doc, "Acabado de pavimento", estancia["acabado_pavimento"])
            add_etiqueta_valor(doc, "Acabado de paramento", estancia["acabado_paramento"])
            add_etiqueta_valor(doc, "Acabado de techo", estancia["acabado_techo"])
            add_estado_checklist_habitabilidad(doc, HABITABILIDAD_ESTANCIA_ITEMS, estancia)
            if limpiar_texto(estancia["observaciones_estancia_habitabilidad"]):
                add_etiqueta_valor(
                    doc,
                    "Observaciones de habitabilidad",
                    estancia["observaciones_estancia_habitabilidad"],
                )


def add_apartado_exterior_habitabilidad(
    doc: Document, numero_apartado: int, visitas_habitabilidad
) -> None:
    doc.add_heading(
        f"{numero_apartado}. Factores exteriores que afectan a la habitabilidad",
        level=1,
    )

    hay_datos = False
    for indice, bloque in enumerate(visitas_habitabilidad, start=1):
        exterior = bloque["habitabilidad"]["exterior"]
        if not any(limpiar_texto(exterior[campo]) for campo, _ in HABITABILIDAD_EXTERIOR_ITEMS) and not limpiar_texto(
            exterior["observaciones_exterior_habitabilidad"]
        ):
            continue

        hay_datos = True
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_estado_checklist_habitabilidad(doc, HABITABILIDAD_EXTERIOR_ITEMS, exterior)
        if limpiar_texto(exterior["observaciones_exterior_habitabilidad"]):
            add_etiqueta_valor(
                doc,
                "Observaciones exteriores",
                exterior["observaciones_exterior_habitabilidad"],
            )

    if not hay_datos:
        add_parrafo(doc, "No constan factores exteriores registrados que afecten a la habitabilidad.")


def add_apartado_conclusion_habitabilidad(
    doc: Document, numero_apartado: int, visitas_habitabilidad
) -> None:
    doc.add_heading(f"{numero_apartado}. Conclusión global de habitabilidad", level=1)

    if not visitas_habitabilidad:
        add_parrafo(doc, "No consta conclusión global de habitabilidad registrada.")
        return

    for indice, bloque in enumerate(visitas_habitabilidad, start=1):
        visita = bloque["visita"]
        general = bloque["habitabilidad"]["general"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_etiqueta_valor(
            doc,
            "Conclusión global",
            conclusion_habitabilidad_legible(general["conclusion_habitabilidad"]),
        )
        if limpiar_texto(general["observaciones_generales_habitabilidad"]):
            add_etiqueta_valor(
                doc,
                "Observaciones complementarias",
                general["observaciones_generales_habitabilidad"],
            )


def cargar_valoracion_visita(cur, visita_id: int) -> dict:
    campos = (
        [campo for campo, _ in VALORACION_ENCARGO_ITEMS]
        + [campo for campo, _ in VALORACION_DOCUMENTACION_ITEMS]
        + [campo for campo, _ in VALORACION_IDENTIFICACION_ITEMS]
        + [campo for campo, _ in VALORACION_SITUACION_LEGAL_ITEMS]
        + [campo for campo, _ in VALORACION_ENTORNO_ITEMS]
        + [campo for campo, _ in VALORACION_EDIFICIO_INMUEBLE_ITEMS]
        + [campo for campo, _ in VALORACION_CONSTRUCTIVO_ITEMS]
        + [campo for campo, _ in VALORACION_ESTADO_ITEMS]
        + [campo for campo, _ in VALORACION_METODO_ITEMS]
        + [campo for campo, _ in VALORACION_RESULTADO_ITEMS]
        + [campo for campo, _ in VALORACION_LIMITACIONES_ITEMS]
    )
    return fila_o_dict_vacio(
        cur.execute(
            """
            SELECT *
            FROM valoracion_visita
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone(),
        campos,
    )


def add_apartado_valoracion_por_visitas(
    doc: Document, numero_apartado: int, titulo: str, visitas_valoracion, campos
) -> None:
    doc.add_heading(f"{numero_apartado}. {titulo}", level=1)

    hay_datos = False
    for indice, bloque in enumerate(visitas_valoracion, start=1):
        valoracion = bloque["valoracion"]
        if not any(limpiar_texto(valoracion[campo]) for campo, _ in campos):
            continue
        hay_datos = True
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_bloque_campos_si_hay(doc, campos, valoracion)

    if not hay_datos:
        add_parrafo(doc, "No constan datos registrados en este apartado.")


def add_apartado_comparables_valoracion(
    doc: Document, numero_apartado: int, visitas_valoracion
) -> None:
    doc.add_heading(f"{numero_apartado}. Testigos o comparables", level=1)

    hay_datos = False
    for indice, bloque in enumerate(visitas_valoracion, start=1):
        comparables = bloque["comparables"]
        if not comparables:
            continue
        hay_datos = True
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_tabla_comparables(doc, comparables)

    if not hay_datos:
        add_parrafo(doc, "No constan comparables registrados.")


def add_apartado_resultado_valoracion(
    doc: Document, numero_apartado: int, visitas_valoracion
) -> None:
    doc.add_heading(f"{numero_apartado}. Resultado de la valoración", level=1)

    if not visitas_valoracion:
        add_parrafo(doc, "No constan resultados de valoración registrados.")
        return

    hay_datos = False
    for indice, bloque in enumerate(visitas_valoracion, start=1):
        valoracion = bloque["valoracion"]
        if not any(
            limpiar_texto(valoracion[campo]) for campo, _ in VALORACION_RESULTADO_ITEMS
        ):
            continue
        hay_datos = True
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_valor_destacado(doc, "Valor unitario", valoracion["valor_unitario"])
        add_etiqueta_valor(doc, "Valor resultante", valoracion["valor_resultante"])
        add_valor_destacado(
            doc, "Valor de tasación final", valoracion["valor_tasacion_final"]
        )

    if not hay_datos:
        add_parrafo(doc, "No constan resultados de valoración registrados.")


def add_apartado_limitaciones_valoracion(
    doc: Document, numero_apartado: int, visitas_valoracion
) -> None:
    doc.add_heading(f"{numero_apartado}. Condicionantes y limitaciones", level=1)

    hay_datos = False
    for indice, bloque in enumerate(visitas_valoracion, start=1):
        valoracion = bloque["valoracion"]
        if not any(
            limpiar_texto(valoracion[campo]) for campo, _ in VALORACION_LIMITACIONES_ITEMS
        ):
            continue
        hay_datos = True
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_bloque_campos_si_hay(doc, VALORACION_LIMITACIONES_ITEMS, valoracion)

    if not hay_datos:
        add_parrafo(doc, "No constan condicionantes, limitaciones u observaciones adicionales.")


def cargar_inspeccion_visita(cur, visita_id: int) -> dict:
    general_campos = [
        campo for _, grupo in INSPECCION_GENERAL_GROUPS for campo, _ in grupo
    ] + ["observaciones_generales_inspeccion"]
    exterior_campos = [campo for campo, _ in INSPECCION_EXTERIOR_ITEMS] + [
        "observaciones_exteriores"
    ]
    comunes_campos = [campo for campo, _ in INSPECCION_ELEMENTOS_COMUNES_ITEMS] + [
        "observaciones_elementos_comunes"
    ]

    general = fila_o_dict_vacio(
        cur.execute(
        """
        SELECT *
        FROM inspeccion_general_visita
        WHERE visita_id = ?
        """,
        (visita_id,),
        ).fetchone(),
        general_campos,
    )
    exterior = fila_o_dict_vacio(
        cur.execute(
        """
        SELECT *
        FROM inspeccion_exterior
        WHERE visita_id = ?
        """,
        (visita_id,),
        ).fetchone(),
        exterior_campos,
    )
    comunes = fila_o_dict_vacio(
        cur.execute(
        """
        SELECT *
        FROM inspeccion_elementos_comunes
        WHERE visita_id = ?
        """,
        (visita_id,),
        ).fetchone(),
        comunes_campos,
    )
    estancias = cur.execute(
        """
        SELECT e.id AS estancia_id,
               e.nombre AS estancia_nombre,
               e.tipo_estancia,
               e.planta,
               e.acabado_pavimento,
               e.acabado_paramento,
               e.acabado_techo,
               ie.*
        FROM estancias e
        LEFT JOIN inspeccion_estancias ie
               ON ie.estancia_id = e.id
              AND ie.visita_id = e.visita_id
        WHERE e.visita_id = ?
        ORDER BY e.id ASC
        """,
        (visita_id,),
    ).fetchall()

    return {
        "general": general,
        "exterior": exterior,
        "comunes": comunes,
        "estancias": estancias,
    }


def add_apartado_condiciones_visita_inspeccion(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Condiciones de la visita / inspección", level=1)

    if not visitas_inspeccion:
        add_parrafo(doc, "No constan visitas registradas en el expediente.")
        return

    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        visita = bloque["visita"]
        climatologia = bloque["climatologia"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_etiqueta_valor(doc, "Técnico", visita["tecnico"])
        add_etiqueta_valor(doc, "Observaciones de visita", visita["observaciones_visita"])
        if climatologia:
            add_etiqueta_valor(doc, "Climatología", climatologia["resumen"])
        else:
            add_etiqueta_valor(doc, "Climatología", "No consta climatología registrada")


def add_apartado_comprobaciones_generales(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Comprobaciones generales", level=1)

    if not visitas_inspeccion:
        add_parrafo(doc, "No constan comprobaciones generales registradas.")
        return

    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        general = bloque["inspeccion"]["general"]
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        for subindice, (titulo, items) in enumerate(INSPECCION_GENERAL_GROUPS, start=1):
            doc.add_heading(f"{numero_apartado}.{indice}.{subindice} {titulo}", level=3)
            add_estado_checklist(doc, items, general)
        if limpiar_texto(general["observaciones_generales_inspeccion"]):
            add_etiqueta_valor(
                doc,
                "Observaciones generales de inspección",
                general["observaciones_generales_inspeccion"],
            )


def add_apartado_inspeccion_estancias(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Inspección por estancias", level=1)

    if not visitas_inspeccion:
        add_parrafo(doc, "No constan estancias inspeccionadas.")
        return

    for indice_visita, bloque in enumerate(visitas_inspeccion, start=1):
        visita = bloque["visita"]
        estancias = bloque["inspeccion"]["estancias"]
        doc.add_heading(
            f"{numero_apartado}.{indice_visita} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        if not estancias:
            add_parrafo(doc, "No constan estancias registradas en esta visita.")
            continue

        for indice_estancia, estancia in enumerate(estancias, start=1):
            doc.add_heading(
                f"{numero_apartado}.{indice_visita}.{indice_estancia} {valor_o_guion(estancia['estancia_nombre'])}",
                level=3,
            )
            add_etiqueta_valor(doc, "Tipo de estancia", estancia["tipo_estancia"])
            add_etiqueta_valor(doc, "Planta", estancia["planta"])
            add_etiqueta_valor(doc, "Acabado de pavimento", estancia["acabado_pavimento"])
            add_etiqueta_valor(doc, "Acabado de paramento", estancia["acabado_paramento"])
            add_etiqueta_valor(doc, "Acabado de techo", estancia["acabado_techo"])
            add_estado_checklist(
                doc,
                obtener_items_inspeccion_estancia(estancia["tipo_estancia"]),
                estancia,
            )
            if limpiar_texto(estancia["observaciones_estancia_inspeccion"]):
                add_etiqueta_valor(
                    doc,
                    "Observaciones de inspección",
                    estancia["observaciones_estancia_inspeccion"],
                )


def add_apartado_inspeccion_exterior(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Inspección exterior", level=1)

    if not visitas_inspeccion:
        add_parrafo(doc, "No constan comprobaciones exteriores registradas.")
        return

    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        exterior = bloque["inspeccion"]["exterior"]
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_estado_checklist(doc, INSPECCION_EXTERIOR_ITEMS, exterior)
        if limpiar_texto(exterior["observaciones_exteriores"]):
            add_etiqueta_valor(
                doc,
                "Observaciones exteriores",
                exterior["observaciones_exteriores"],
            )


def add_apartado_elementos_comunes(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Elementos comunes", level=1)

    if not visitas_inspeccion:
        add_parrafo(doc, "No constan elementos comunes inspeccionados.")
        return

    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        comunes = bloque["inspeccion"]["comunes"]
        visita = bloque["visita"]
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_estado_checklist(doc, INSPECCION_ELEMENTOS_COMUNES_ITEMS, comunes)
        if limpiar_texto(comunes["observaciones_elementos_comunes"]):
            add_etiqueta_valor(
                doc,
                "Observaciones de elementos comunes",
                comunes["observaciones_elementos_comunes"],
            )


def add_apartado_observaciones_tecnicas(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Observaciones técnicas", level=1)

    hay_observaciones = False
    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        visita = bloque["visita"]
        general = bloque["inspeccion"]["general"]
        exterior = bloque["inspeccion"]["exterior"]
        comunes = bloque["inspeccion"]["comunes"]
        estancias = bloque["inspeccion"]["estancias"]
        lineas = []

        if limpiar_texto(visita["observaciones_visita"]):
            lineas.append(("Observaciones de visita", visita["observaciones_visita"]))
        if limpiar_texto(general["observaciones_generales_inspeccion"]):
            lineas.append(
                (
                    "Observaciones generales de inspección",
                    general["observaciones_generales_inspeccion"],
                )
            )
        if limpiar_texto(exterior["observaciones_exteriores"]):
            lineas.append(("Observaciones exteriores", exterior["observaciones_exteriores"]))
        if limpiar_texto(comunes["observaciones_elementos_comunes"]):
            lineas.append(
                (
                    "Observaciones de elementos comunes",
                    comunes["observaciones_elementos_comunes"],
                )
            )

        for estancia in estancias:
            if limpiar_texto(estancia["observaciones_estancia_inspeccion"]):
                lineas.append(
                    (
                        f"Observaciones de {valor_o_guion(estancia['estancia_nombre'])}",
                        estancia["observaciones_estancia_inspeccion"],
                    )
                )

        if not lineas:
            continue

        hay_observaciones = True
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        for etiqueta, valor in lineas:
            add_etiqueta_valor(doc, etiqueta, valor)

    if not hay_observaciones:
        add_parrafo(doc, "No constan observaciones técnicas adicionales registradas.")


def add_apartado_recomendaciones_inspeccion(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Recomendaciones", level=1)

    hay_recomendaciones = False
    for indice, bloque in enumerate(visitas_inspeccion, start=1):
        visita = bloque["visita"]
        general = bloque["inspeccion"]["general"]
        exterior = bloque["inspeccion"]["exterior"]
        comunes = bloque["inspeccion"]["comunes"]
        estancias = bloque["inspeccion"]["estancias"]
        incidencias = []

        for titulo, items in INSPECCION_GENERAL_GROUPS:
            for etiqueta, estado in recoger_incidencias_checklist(items, general):
                incidencias.append((f"General - {etiqueta}", estado))
        for etiqueta, estado in recoger_incidencias_checklist(
            INSPECCION_EXTERIOR_ITEMS, exterior
        ):
            incidencias.append((f"Exterior - {etiqueta}", estado))
        for etiqueta, estado in recoger_incidencias_checklist(
            INSPECCION_ELEMENTOS_COMUNES_ITEMS, comunes
        ):
            incidencias.append((f"Elementos comunes - {etiqueta}", estado))
        for estancia in estancias:
            for etiqueta, estado in recoger_incidencias_checklist(
                obtener_items_inspeccion_estancia(estancia["tipo_estancia"]),
                estancia,
            ):
                incidencias.append(
                    (
                        f"{valor_o_guion(estancia['estancia_nombre'])} - {etiqueta}",
                        estado,
                    )
                )

        if not incidencias:
            continue

        hay_recomendaciones = True
        doc.add_heading(
            f"{numero_apartado}.{indice} Visita de fecha {valor_o_guion(visita['fecha'])}",
            level=2,
        )
        add_parrafo(
            doc,
            "Se recomienda revisar y, en su caso, actuar sobre los siguientes elementos marcados en la inspección:",
        )
        for elemento, estado in incidencias:
            add_parrafo(doc, f"- {elemento}: {estado}")

    if not hay_recomendaciones:
        add_parrafo(
            doc,
            "No constan elementos marcados como necesitados de reparación o defecto grave en los checklists registrados.",
        )


def add_apartado_conclusion_inspeccion(
    doc: Document, numero_apartado: int, visitas_inspeccion
) -> None:
    doc.add_heading(f"{numero_apartado}. Conclusión general", level=1)

    total_reparacion = 0
    total_graves = 0
    total_no_inspeccionado = 0

    for bloque in visitas_inspeccion:
        general = bloque["inspeccion"]["general"]
        exterior = bloque["inspeccion"]["exterior"]
        comunes = bloque["inspeccion"]["comunes"]
        estancias = bloque["inspeccion"]["estancias"]
        conjuntos = [
            [campo for _, grupo in INSPECCION_GENERAL_GROUPS for campo, _ in grupo],
            [campo for campo, _ in INSPECCION_EXTERIOR_ITEMS],
            [campo for campo, _ in INSPECCION_ELEMENTOS_COMUNES_ITEMS],
        ]
        fuentes = [general, exterior, comunes]

        for fuente, campos in zip(fuentes, conjuntos):
            for campo in campos:
                estado = limpiar_texto(fuente[campo])
                if estado == "necesita_reparacion":
                    total_reparacion += 1
                elif estado == "defecto_grave":
                    total_graves += 1
                elif estado in {"", "no_inspeccionado"}:
                    total_no_inspeccionado += 1

        for estancia in estancias:
            for campo, _ in obtener_items_inspeccion_estancia(estancia["tipo_estancia"]):
                estado = limpiar_texto(estancia[campo])
                if estado == "necesita_reparacion":
                    total_reparacion += 1
                elif estado == "defecto_grave":
                    total_graves += 1
                elif estado in {"", "no_inspeccionado"}:
                    total_no_inspeccionado += 1

    if total_graves or total_reparacion:
        add_parrafo(
            doc,
            "La inspección incorpora elementos consignados con necesidad de reparación y/o defecto grave. "
            f"Se han registrado {total_reparacion} ítems como 'Necesita reparación' y {total_graves} como 'Defecto grave'.",
        )
    else:
        add_parrafo(
            doc,
            "De acuerdo con los checklists registrados, no constan elementos marcados como necesitados de reparación o defecto grave.",
        )

    if total_no_inspeccionado:
        add_parrafo(
            doc,
            f"Asimismo, constan {total_no_inspeccionado} ítems marcados como 'No inspeccionado', por lo que la valoración debe entenderse limitada a los elementos efectivamente revisados.",
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


def generar_informe_patologias(cur, expediente, visitas, doc: Document) -> None:
    add_portada(doc, expediente)

    doc.add_heading("1. Identificación del expediente", level=1)
    add_tabla_datos_expediente(doc, expediente)

    doc.add_heading("2. Objeto del informe", level=1)
    add_parrafo(
        doc,
        "El presente informe pericial documenta las patologías observadas en el inmueble objeto del expediente, "
        "incorporando los antecedentes disponibles, las visitas realizadas y los registros técnicos interiores "
        "y/o exteriores existentes en el sistema.",
    )

    doc.add_heading("3. Descripción del inmueble", level=1)
    add_etiqueta_valor(
        doc, "Referencia catastral", expediente["referencia_catastral"]
    )
    add_etiqueta_valor(
        doc, "Observaciones generales", expediente["observaciones_generales"]
    )
    add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
    add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
    add_etiqueta_valor(
        doc, "Superficie construida", expediente["superficie_construida"]
    )
    add_etiqueta_valor(doc, "Superficie útil", expediente["superficie_util"])
    add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
    add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
    add_etiqueta_valor(
        doc, "Observaciones de la unidad", expediente["observaciones_unidad"]
    )

    numero_apartado = 4
    add_apartado_datos_patologias(doc, numero_apartado, expediente)
    numero_apartado += 1

    add_apartado_bloque_judicial(doc, numero_apartado, expediente)
    if limpiar_texto(expediente["destinatario"]) == "judicial":
        numero_apartado += 1

    climatologias = {}
    patologias_interiores = []
    patologias_exteriores = []
    bloques_mapas = []

    for visita in visitas:
        climatologias[visita["id"]] = cur.execute(
            """
            SELECT *
            FROM climatologia_visitas
            WHERE visita_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (visita["id"],),
        ).fetchone()

        patologias_interiores.extend(
            cur.execute(
                """
                SELECT rp.*,
                       e.nombre AS estancia_nombre,
                       ue.identificador AS unidad_identificador,
                       ne.nombre_nivel AS nivel_nombre,
                       bp.rol_patologia AS rol_patologia_biblioteca
                FROM registros_patologias rp
                INNER JOIN estancias e ON rp.estancia_id = e.id
                LEFT JOIN unidades_expediente ue ON e.unidad_id = ue.id
                LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
                LEFT JOIN biblioteca_patologias bp
                       ON lower(trim(bp.nombre)) = lower(trim(rp.patologia))
                WHERE rp.visita_id = ?
                ORDER BY ne.nombre_nivel ASC, ue.identificador ASC, e.nombre ASC, rp.id ASC
                """,
                (visita["id"],),
            ).fetchall()
        )
        patologias_exteriores.extend(
            cur.execute(
                """
                SELECT rpe.*,
                       '' AS rol_patologia_observado,
                       bp.rol_patologia AS rol_patologia_biblioteca
                FROM registros_patologias_exteriores rpe
                LEFT JOIN biblioteca_patologias bp
                       ON lower(trim(bp.nombre)) = lower(trim(rpe.patologia))
                WHERE rpe.visita_id = ?
                ORDER BY rpe.zona_exterior ASC, rpe.id ASC
                """,
                (visita["id"],),
            ).fetchall()
        )
        bloques_mapas.append(
            {
                "visita": visita,
                "mapas": cargar_mapas_patologia_utiles_visita(cur, visita),
            }
        )

    add_apartado_inspeccion_visita(doc, numero_apartado, visitas, climatologias)
    numero_apartado += 1

    ambito = limpiar_texto(expediente["ambito_patologias"])
    if ambito in ("", "interior", "interior_exterior"):
        add_apartado_patologias_interiores(
            doc, numero_apartado, patologias_interiores, cur.connection
        )
        numero_apartado += 1

    if ambito in ("exterior", "interior_exterior"):
        add_apartado_patologias_exteriores(
            doc, numero_apartado, patologias_exteriores, cur.connection
        )
        numero_apartado += 1

    if add_apartado_mapas_patologia(doc, numero_apartado, bloques_mapas):
        numero_apartado += 1

    add_apartado_analisis_tecnico(doc, numero_apartado, expediente)
    numero_apartado += 1
    add_apartado_propuesta_reparacion(doc, numero_apartado, expediente)
    numero_apartado += 1
    add_apartado_conclusion_patologias(
        doc,
        numero_apartado,
        patologias_interiores,
        patologias_exteriores,
    )
    numero_apartado += 1
    add_apartado_conclusion_pericial(
        doc,
        numero_apartado,
        patologias_interiores,
        patologias_exteriores,
    )


def generar_informe_inspeccion(cur, expediente, visitas, doc: Document) -> None:
    add_portada(doc, expediente)

    doc.add_heading("1. Identificación del expediente", level=1)
    add_tabla_datos_expediente(doc, expediente)

    doc.add_heading("2. Objeto del informe", level=1)
    add_parrafo(
        doc,
        "El presente informe técnico recoge las comprobaciones de inspección registradas en el inmueble objeto del expediente, "
        "incluyendo las condiciones de la visita, los checklists generales, la revisión por estancias, la inspección exterior "
        "y, en su caso, los elementos comunes del edificio.",
    )

    doc.add_heading("3. Descripción del inmueble", level=1)
    add_etiqueta_valor(doc, "Referencia catastral", expediente["referencia_catastral"])
    add_etiqueta_valor(doc, "Observaciones generales", expediente["observaciones_generales"])
    add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
    add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
    add_etiqueta_valor(doc, "Superficie construida", expediente["superficie_construida"])
    add_etiqueta_valor(doc, "Superficie útil", expediente["superficie_util"])
    add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
    add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
    add_etiqueta_valor(doc, "Observaciones del bloque", expediente["observaciones_bloque"])
    add_etiqueta_valor(doc, "Observaciones de la unidad", expediente["observaciones_unidad"])

    numero_apartado = 4
    add_apartado_bloque_judicial(doc, numero_apartado, expediente)
    if limpiar_texto(expediente["destinatario"]) == "judicial":
        numero_apartado += 1

    visitas_inspeccion = []
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
        visitas_inspeccion.append(
            {
                "visita": visita,
                "climatologia": climatologia,
                "inspeccion": cargar_inspeccion_visita(cur, visita["id"]),
            }
        )

    add_apartado_condiciones_visita_inspeccion(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_comprobaciones_generales(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_inspeccion_estancias(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_inspeccion_exterior(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_elementos_comunes(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_observaciones_tecnicas(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_recomendaciones_inspeccion(doc, numero_apartado, visitas_inspeccion)
    numero_apartado += 1
    add_apartado_conclusion_inspeccion(doc, numero_apartado, visitas_inspeccion)


def generar_informe_habitabilidad(cur, expediente, visitas, doc: Document) -> None:
    add_portada(doc, expediente)

    doc.add_heading("1. Identificación del expediente", level=1)
    add_tabla_datos_expediente(doc, expediente)

    doc.add_heading("2. Objeto del informe", level=1)
    add_parrafo(
        doc,
        "El presente informe técnico recoge la evaluación de habitabilidad registrada en el inmueble objeto del expediente, "
        "incluyendo las condiciones generales, la valoración por estancias y los factores exteriores mínimos que pueden afectar al uso residencial.",
    )

    doc.add_heading("3. Descripción del inmueble", level=1)
    add_etiqueta_valor(doc, "Referencia catastral", expediente["referencia_catastral"])
    add_etiqueta_valor(doc, "Observaciones generales", expediente["observaciones_generales"])
    add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
    add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
    add_etiqueta_valor(doc, "Superficie construida", expediente["superficie_construida"])
    add_etiqueta_valor(doc, "Superficie útil", expediente["superficie_util"])
    add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
    add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
    add_etiqueta_valor(doc, "Observaciones del bloque", expediente["observaciones_bloque"])
    add_etiqueta_valor(doc, "Observaciones de la unidad", expediente["observaciones_unidad"])

    visitas_habitabilidad = []
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
        visitas_habitabilidad.append(
            {
                "visita": visita,
                "climatologia": climatologia,
                "habitabilidad": cargar_habitabilidad_visita(cur, visita["id"]),
            }
        )

    numero_apartado = 4
    add_apartado_condiciones_habitabilidad(doc, numero_apartado, visitas_habitabilidad)
    numero_apartado += 1
    add_apartado_evaluacion_estancias_habitabilidad(
        doc, numero_apartado, visitas_habitabilidad
    )
    numero_apartado += 1
    add_apartado_exterior_habitabilidad(doc, numero_apartado, visitas_habitabilidad)
    numero_apartado += 1
    add_apartado_conclusion_habitabilidad(doc, numero_apartado, visitas_habitabilidad)
    numero_apartado += 1
    add_apartado_bloque_judicial(doc, numero_apartado, expediente)


def generar_informe_valoracion(cur, expediente, visitas, doc: Document) -> None:
    add_portada(doc, expediente)

    doc.add_heading("1. Identificación del expediente", level=1)
    add_tabla_datos_expediente(doc, expediente)

    doc.add_heading("2. Objeto del informe", level=1)
    add_parrafo(
        doc,
        "El presente informe técnico recoge la información disponible para la valoración inmobiliaria del bien objeto del expediente, "
        "incluyendo la documentación consultada, las características del inmueble, los criterios de valoración y los comparables registrados.",
    )

    doc.add_heading("3. Identificación y descripción del bien", level=1)
    add_etiqueta_valor(doc, "Referencia catastral", expediente["referencia_catastral"])
    add_etiqueta_valor(doc, "Observaciones generales", expediente["observaciones_generales"])
    add_etiqueta_valor(doc, "Planta de la unidad", expediente["planta_unidad"])
    add_etiqueta_valor(doc, "Puerta / unidad", expediente["puerta_unidad"])
    add_etiqueta_valor(doc, "Superficie construida", expediente["superficie_construida"])
    add_etiqueta_valor(doc, "Superficie útil", expediente["superficie_util"])
    add_etiqueta_valor(doc, "Dormitorios", expediente["dormitorios_unidad"])
    add_etiqueta_valor(doc, "Baños", expediente["banos_unidad"])
    add_etiqueta_valor(doc, "Observaciones del bloque", expediente["observaciones_bloque"])
    add_etiqueta_valor(doc, "Observaciones de la unidad", expediente["observaciones_unidad"])

    visitas_valoracion = []
    for visita in visitas:
        comparables = cur.execute(
            """
            SELECT *
            FROM comparables_valoracion
            WHERE visita_id = ?
            ORDER BY id ASC
            """,
            (visita["id"],),
        ).fetchall()
        visitas_valoracion.append(
            {
                "visita": visita,
                "valoracion": cargar_valoracion_visita(cur, visita["id"]),
                "comparables": comparables,
            }
        )

    numero_apartado = 4
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Encargo / solicitante", visitas_valoracion, VALORACION_ENCARGO_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Documentación utilizada", visitas_valoracion, VALORACION_DOCUMENTACION_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Situación legal y urbanística", visitas_valoracion, VALORACION_SITUACION_LEGAL_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Entorno", visitas_valoracion, VALORACION_ENTORNO_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Descripción del edificio e inmueble", visitas_valoracion, VALORACION_IDENTIFICACION_ITEMS + VALORACION_EDIFICIO_INMUEBLE_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Características constructivas", visitas_valoracion, VALORACION_CONSTRUCTIVO_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Estado actual y ocupación", visitas_valoracion, VALORACION_ESTADO_ITEMS
    )
    numero_apartado += 1
    add_apartado_valoracion_por_visitas(
        doc, numero_apartado, "Método / criterios de valoración", visitas_valoracion, VALORACION_METODO_ITEMS
    )
    numero_apartado += 1
    add_apartado_comparables_valoracion(doc, numero_apartado, visitas_valoracion)
    numero_apartado += 1
    add_apartado_resultado_valoracion(doc, numero_apartado, visitas_valoracion)
    numero_apartado += 1
    add_apartado_limitaciones_valoracion(doc, numero_apartado, visitas_valoracion)
    numero_apartado += 1
    add_apartado_bloque_judicial(doc, numero_apartado, expediente)


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

    tipo_informe = limpiar_texto(expediente["tipo_informe"])

    if tipo_informe == "patologias":
        generar_informe_patologias(cur, expediente, visitas, doc)
    elif tipo_informe == "inspeccion":
        generar_informe_inspeccion(cur, expediente, visitas, doc)
    elif tipo_informe == "habitabilidad":
        generar_informe_habitabilidad(cur, expediente, visitas, doc)
    elif tipo_informe == "valoracion":
        generar_informe_valoracion(cur, expediente, visitas, doc)
    else:
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
