import binascii
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import shutil
import sqlite3
import unicodedata
from urllib.parse import parse_qs, quote_plus, urlparse
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
except ImportError:  # pragma: no cover - fallback defensivo si falta Pillow
    Image = None
    ImageDraw = None
    ImageFont = None
    ImageOps = None
    UnidentifiedImageError = None

try:  # pragma: no cover - soporte opcional para HEIC/HEIF
    from pillow_heif import register_heif_opener
except ImportError:  # pragma: no cover - dependencia opcional
    register_heif_opener = None

from app.config import (
    SESSION_COOKIE_SECURE,
    APP_HOST,
    APP_PORT,
    BASE_URL,
    DB_PATH,
    INFORMES_DIR,
    SESSION_SECRET_KEY,
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOAD_DIR,
    ensure_directories,
)
from app.database import init_db
from app.routers import backups as backups_router
from app.routers import clientes as clientes_router
from app.routers import costes as costes_router
from app.routers import crm as crm_router
from app.routers import dashboard as dashboard_router
from app.routers import emails as emails_router
from app.routers import facturacion as facturacion_router
from app.routers import gastos as gastos_router
from app.routers import leads as leads_router
from app.routers import propuestas as propuestas_router
from app.services.catastro import consultar_catastro_por_referencia
from app.services.clima import geocodificar, obtener_climatologia
from app.services.direccion import autocompletar_direccion, sugerir_direcciones
from app.services.economia import construir_timeline_economico_expediente
from app.services.informe import (
    build_informe_context,
    generar_informe,
    generar_informe_docx_editable_bytes,
    generar_informe_pdf_bytes,
    generar_informe_v2_pdf_bytes,
    nombre_archivo_docx_editable_informe,
    nombre_archivo_pdf_informe,
    limpiar_nombre_archivo,
)
from app.services.pericial_consistency import analizar_consistencia_expediente
from app.services.pdf_annex_optimizer import (
    analizar_peso_pdf,
    bytes_a_mb,
    crear_sesion_optimizacion_anexos_pdf,
)
from app.services.pdf_image_optimizer import (
    crear_sesion_optimizacion_pdf,
    optimizar_contexto_imagenes_pdf,
)
from app.services.valoracion_comparacion import (
    preparar_resumen_comparacion,
    preparar_matriz_homogeneizacion,
    preparar_testigo_comparacion,
)
from app.utils.helpers import formatear_plantas

app = FastAPI()

STATIC_PATH = Path(STATIC_DIR)
TEMPLATES_PATH = Path(TEMPLATES_DIR)
UPLOAD_PATH = Path(UPLOAD_DIR)
DOCUMENTOS_EXPEDIENTE_UPLOAD_DIR = UPLOAD_PATH / "expediente_documentos"
DB_FILE = Path(DB_PATH)
TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES = "informe_v2_anexo_f_mediciones"
INFORME_V2_TITULO_PORTADA_DEFAULT = (
    "DAÑOS POR ENTRADA DE AGUA DE LLUVIA Y\n"
    "AFECCIONES CONSTRUCTIVAS DERIVADAS"
)
INFORME_V2_SUBTITULO_PORTADA_DEFAULT = (
    "Análisis técnico de los daños observados, su distribución en el inmueble "
    "y valoración económica de las actuaciones de reparación necesarias."
)
INFORME_V2_CAMPOS_METADATOS = {"titulo_portada", "subtitulo_portada"}

ensure_directories()
init_db()

app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_PATH)), name="uploads")

templates = Jinja2Templates(directory=str(TEMPLATES_PATH))
app.state.templates = templates
app.state.base_url = BASE_URL
app.state.app_host = APP_HOST
app.state.app_port = APP_PORT

logger = logging.getLogger(__name__)

if Image is not None and register_heif_opener is not None:  # pragma: no branch
    register_heif_opener()

PUBLIC_PATHS = {
    "/login",
    "/crear-usuario",
    "/logout",
    "/ping",
    "/manifest.json",
    "/sw.js",
    "/favicon.ico",
    "/apple-touch-icon.png",
}
PUBLIC_PREFIXES = ("/static/", "/uploads/")
AUTH_PAGES = {"/login", "/crear-usuario"}
SESSION_COOKIE_NAME = "sistema_pericial_session"
# SESSION_COOKIE_SECURE = BASE_URL.startswith("https://")
TIPO_INFORME_LABELS = {
    "patologias": "Patologías",
    "inspeccion": "Inspección del inmueble",
    "valoracion": "Valoración inmobiliaria",
    "habitabilidad": "Habitabilidad",
}
DESTINATARIO_LABELS = {
    "particular": "Cliente particular / empresa",
    "judicial": "Encargo judicial",
}
AMBITO_PATOLOGIAS_LABELS = {
    "interior": "Interior",
    "exterior": "Exterior",
    "interior_exterior": "Interior y exterior",
}
ZONA_EXTERIOR_LABELS = {
    "fachada": "Fachada",
    "cubierta": "Cubierta",
    "medianera": "Medianera",
    "patio": "Patio",
    "terraza": "Terraza",
    "exterior_general": "Exterior general",
}
ELEMENTO_EXTERIOR_LABELS = {
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
LOCALIZACION_EXTERIOR_LABELS = {
    "horizontal": "Horizontal",
    "vertical": "Vertical",
    "encuentro": "Encuentro",
    "puntual": "Puntual",
}
BIBLIOTECA_CATEGORIA_OPTIONS = [
    ("", "Sin clasificar"),
    ("humedades", "Humedades"),
    ("acabados", "Acabados"),
    ("pavimentos", "Pavimentos"),
    ("carpinterias", "Carpinterías"),
    ("fachada", "Fachada"),
    ("estructura", "Estructura"),
    ("instalaciones", "Instalaciones"),
    ("biologicas", "Biológicas"),
    ("roturas", "Roturas"),
    ("desprendimientos", "Desprendimientos"),
]
BIBLIOTECA_CATEGORIA_LABELS = dict(BIBLIOTECA_CATEGORIA_OPTIONS)
BIBLIOTECA_ELEMENTO_AFECTADO_OPTIONS = [
    ("", "Sin definir"),
    ("cubierta", "Cubierta"),
    ("techo", "Techo"),
    ("falso_techo", "Falso techo"),
    ("paramento_vertical", "Paramento vertical"),
    ("pavimento", "Pavimento"),
    ("forjado", "Forjado"),
    ("fachada", "Fachada"),
    ("cornisa", "Cornisa"),
    ("carpinteria", "Carpintería"),
    ("ventana", "Ventana"),
    ("puerta", "Puerta"),
    ("revestimiento_interior", "Revestimiento interior"),
    ("instalacion_electrica", "Instalación eléctrica"),
]
BIBLIOTECA_ELEMENTO_AFECTADO_LABELS = dict(BIBLIOTECA_ELEMENTO_AFECTADO_OPTIONS)
BIBLIOTECA_MECANISMO_OPTIONS = [
    ("", "Sin definir"),
    ("infiltracion", "Infiltración"),
    ("condensacion", "Condensación"),
    ("capilaridad", "Capilaridad"),
    ("impacto", "Impacto"),
    ("desprendimiento", "Desprendimiento"),
    ("deformacion", "Deformación"),
    ("corrosion", "Corrosión"),
    ("perdida_adherencia", "Pérdida de adherencia"),
    ("saturacion", "Saturación"),
    ("colonizacion_biologica", "Colonización biológica"),
    ("rotura", "Rotura"),
]
BIBLIOTECA_MECANISMO_LABELS = dict(BIBLIOTECA_MECANISMO_OPTIONS)
AMBITO_MAPA_OPTIONS = [
    ("edificio_completo", "Edificio completo"),
    ("nivel", "Nivel"),
    ("unidad", "Unidad"),
    ("zona_comun", "Zona común"),
    ("exterior", "Exterior"),
]
AMBITO_MAPA_LABELS = dict(AMBITO_MAPA_OPTIONS)
GRAVEDAD_CUADRANTE_OPTIONS = [
    ("leve", "Leve"),
    ("media", "Media"),
    ("grave", "Grave"),
]
GRAVEDAD_CUADRANTE_LABELS = dict(GRAVEDAD_CUADRANTE_OPTIONS)
ESTADO_INSPECCION_OPTIONS = [
    ("no_necesita_reparacion", "No necesita reparación"),
    ("necesita_reparacion", "Necesita reparación"),
    ("defecto_grave", "Defecto grave"),
    ("no_inspeccionado", "No inspeccionado"),
]
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
    ("cubiertas_exteriores", "Cubiertas"),
    ("patios_exteriores", "Patios"),
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
    ("portal_acceso", "Portal acceso"),
    ("vestibulo_comun", "Vestíbulo común"),
    ("pasillos_comunes", "Pasillos comunes"),
    ("escaleras", "Escaleras"),
    ("ascensor", "Ascensor"),
    ("patio_luces", "Patio de luces"),
    ("patio_ventilacion", "Patio de ventilación"),
    ("fachada_comun", "Fachada común"),
    ("cubierta_comun", "Cubierta común"),
    ("cuarto_instalaciones_comunes", "Cuarto instalaciones comunes"),
]
ESTADO_HABITABILIDAD_OPTIONS = [
    ("cumple", "Cumple"),
    ("no_cumple", "No cumple"),
    ("no_aplica", "No aplica"),
    ("no_inspeccionado", "No inspeccionado"),
]
CONCLUSION_HABITABILIDAD_OPTIONS = [
    ("apto", "Apto"),
    ("apto_con_deficiencias", "Apto con deficiencias"),
    ("no_apto", "No apto"),
]
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
VALORACION_DATOS_GENERALES_ITEMS = [
    ("finalidad_valoracion", "Finalidad de la valoración"),
    ("identificacion_bien", "Identificación del bien"),
    ("superficie_valoracion", "Superficie"),
    ("estado_conservacion", "Estado de conservación"),
    ("antiguedad", "Antigüedad"),
    ("calidades", "Calidades"),
    ("ubicacion_valoracion", "Ubicación"),
]
VALORACION_ENCARGO_ITEMS = [
    ("nombre_solicitante", "Solicitante"),
    ("nif_cif_solicitante", "NIF/CIF"),
    ("domicilio_solicitante", "Domicilio"),
    ("entidad_financiera", "Entidad financiera"),
    ("finalidad_valoracion_detallada", "Finalidad detallada"),
]
VALORACION_DOCUMENTACION_ITEMS = [
    ("documentacion_utilizada", "Documentación utilizada"),
    ("datos_registrales", "Datos registrales"),
]
VALORACION_SUPERFICIES_ITEMS = [
    ("superficie_util", "Útil"),
    ("superficie_terraza", "Terraza"),
    ("superficie_zonas_comunes", "Zonas comunes"),
    ("superficie_total", "Total"),
    ("superficie_comprobada", "Superficie comprobada"),
]
VALORACION_SITUACION_LEGAL_ITEMS = [
    ("situacion_ocupacion", "Ocupación"),
    ("situacion_urbanistica", "Urbanística"),
    ("servidumbres", "Servidumbres"),
    ("linderos", "Linderos"),
]
VALORACION_ENTORNO_ITEMS = [
    ("descripcion_entorno", "Descripción"),
    ("grado_consolidacion", "Consolidación"),
    ("antiguedad_entorno", "Antigüedad entorno"),
    ("rasgos_urbanos", "Rasgos urbanos"),
    ("nivel_renta", "Nivel renta"),
    ("uso_predominante", "Uso predominante"),
    ("equipamientos", "Equipamientos"),
    ("infraestructuras", "Infraestructuras"),
]
VALORACION_EDIFICIO_ITEMS = [
    ("tipo_edificio", "Tipo edificio"),
    ("numero_portales", "Portales"),
    ("numero_escaleras", "Escaleras"),
    ("numero_ascensores", "Ascensores"),
]
VALORACION_INMUEBLE_ITEMS = [
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
    ("estado_inmueble", "Estado inmueble"),
    ("regimen_ocupacion", "Régimen de ocupación"),
    ("inmueble_arrendado", "Inmueble arrendado"),
]
VALORACION_FECHAS_ITEMS = [
    ("fecha_visita", "Fecha visita"),
    ("fecha_emision", "Fecha emisión"),
    ("fecha_caducidad", "Fecha caducidad"),
]
VALORACION_METODO_ITEMS = [
    ("criterios_metodo_valoracion", "Criterios / método de valoración"),
    ("testigos_comparables", "Testigos comparables"),
    ("observaciones_testigos", "Observaciones testigos"),
    ("variables_mercado", "Variables de mercado"),
    ("metodo_homogeneizacion", "Método de homogeneización"),
]
VALORACION_RESULTADO_ITEMS = [
    ("valor_unitario", "Valor unitario"),
    ("valor_resultante", "Valor resultante"),
    ("valor_tasacion_final", "Valor de tasación final"),
    (
        "condicionantes_limitaciones_valoracion",
        "Condicionantes / limitaciones",
    ),
    ("observaciones_valoracion", "Observaciones"),
]
VALORACION_EXPEDIENTE_FORM_GROUPS = [
    (
        "Encargo",
        [
            ("finalidad_valoracion", "Finalidad de la valoración"),
            ("finalidad_otro", "Finalidad: otro / matiz"),
            ("alcance_valoracion", "Alcance de la valoración"),
            ("fecha_valoracion", "Fecha de valoración"),
            ("finalidad_valoracion_detallada", "Finalidad detallada"),
            ("nombre_solicitante", "Solicitante"),
            ("nif_cif_solicitante", "NIF/CIF"),
            ("domicilio_solicitante", "Domicilio"),
            ("entidad_financiera", "Entidad financiera"),
        ],
    ),
    (
        "Documentación",
        [
            ("documentacion_utilizada", "Documentación utilizada"),
            ("datos_registrales", "Datos registrales"),
        ],
    ),
    (
        "Identificación y superficies",
        [
            ("identificacion_bien", "Identificación del bien"),
            ("superficie_valoracion", "Superficie de valoración"),
            ("superficie_construida", "Superficie construida"),
            ("superficie_util", "Superficie útil"),
            ("superficie_registral", "Superficie registral"),
            ("superficie_catastral", "Superficie catastral"),
            ("superficie_terraza", "Superficie de terraza"),
            ("superficie_zonas_comunes", "Superficie de zonas comunes"),
            ("superficie_total", "Superficie total"),
            ("superficie_comprobada", "Superficie comprobada"),
            ("superficie_computable", "Superficie computable"),
            ("superficie_adoptada_calculo", "Superficie adoptada para cálculo"),
            (
                "criterio_superficie_adoptada",
                "Criterio de superficie adoptada",
            ),
        ],
    ),
    (
        "Base de valor",
        [
            ("base_valor", "Base de valor"),
            ("base_valor_otro", "Base de valor: otro"),
            ("definicion_base_valor", "Definición de la base de valor"),
        ],
    ),
    (
        "Situación legal",
        [
            ("situacion_ocupacion", "Situación de ocupación"),
            ("situacion_urbanistica", "Situación urbanística"),
            ("servidumbres", "Servidumbres"),
            ("linderos", "Linderos"),
        ],
    ),
    (
        "Entorno",
        [
            ("ubicacion_valoracion", "Ubicación"),
            ("descripcion_entorno", "Descripción del entorno"),
            ("grado_consolidacion", "Grado de consolidación"),
            ("antiguedad_entorno", "Antigüedad del entorno"),
            ("rasgos_urbanos", "Rasgos urbanos"),
            ("nivel_renta", "Nivel de renta"),
            ("uso_predominante", "Uso predominante"),
            ("equipamientos", "Equipamientos"),
            ("infraestructuras", "Infraestructuras"),
        ],
    ),
    (
        "Edificio/inmueble",
        [
            ("tipo_edificio", "Tipo de edificio"),
            ("numero_portales", "Número de portales"),
            ("numero_escaleras", "Número de escaleras"),
            ("numero_ascensores", "Número de ascensores"),
            ("estado_conservacion", "Estado de conservación"),
            ("antiguedad", "Antigüedad"),
            ("calidades", "Calidades"),
            ("vistas", "Vistas"),
            ("uso_residencial", "Uso residencial"),
        ],
    ),
    (
        "Características constructivas",
        [
            ("estructura", "Estructura"),
            ("cubierta", "Cubierta"),
            ("cerramientos", "Cerramientos"),
            ("aislamiento", "Aislamiento"),
            ("carpinteria", "Carpintería"),
            ("acristalamiento", "Acristalamiento"),
            ("instalaciones", "Instalaciones"),
        ],
    ),
    (
        "Métodos",
        [
            ("metodo_comparacion_activo", "Método de comparación activo"),
            ("metodo_coste_activo", "Método de coste activo"),
            ("criterios_metodo_valoracion", "Criterios / método de valoración"),
            ("variables_mercado", "Variables de mercado"),
            ("metodo_homogeneizacion", "Método de homogeneización"),
            ("metodo_comparacion_aplicado", "Comparación aplicada"),
            ("metodo_comparacion_descartado", "Comparación descartada"),
            (
                "metodo_comparacion_justificacion",
                "Justificación comparación",
            ),
            ("metodo_comparacion_observaciones", "Observaciones comparación"),
            ("metodo_coste_aplicado", "Coste aplicado"),
            ("metodo_coste_descartado", "Coste descartado"),
            ("metodo_coste_justificacion", "Justificación coste"),
            ("metodo_coste_observaciones", "Observaciones coste"),
            (
                "metodo_actualizacion_rentas_aplicado",
                "Actualización de rentas aplicada",
            ),
            (
                "metodo_actualizacion_rentas_descartado",
                "Actualización de rentas descartada",
            ),
            (
                "metodo_actualizacion_rentas_justificacion",
                "Justificación actualización de rentas",
            ),
            (
                "metodo_actualizacion_rentas_observaciones",
                "Observaciones actualización de rentas",
            ),
            ("metodo_residual_aplicado", "Residual aplicado"),
            ("metodo_residual_descartado", "Residual descartado"),
            ("metodo_residual_justificacion", "Justificación residual"),
            ("metodo_residual_observaciones", "Observaciones residual"),
        ],
    ),
    (
        "Incidencias y limitaciones",
        [
            (
                "incidencias_automaticas_visibles",
                "Mostrar incidencias automáticas en informe",
            ),
            (
                "incidencias_manuales_visibles",
                "Mostrar incidencias manuales en informe",
            ),
            (
                "incidencias_condicionantes_manuales",
                "Condicionantes manuales",
            ),
            ("incidencias_advertencias_manuales", "Advertencias manuales"),
            ("incidencias_limitaciones_manuales", "Limitaciones manuales"),
            (
                "condicionantes_limitaciones_valoracion",
                "Condicionantes / limitaciones",
            ),
            ("observaciones_valoracion", "Observaciones"),
        ],
    ),
]
VALORACION_EXPEDIENTE_FORM_FIELDS = list(
    dict.fromkeys(
        campo
        for _, campos in VALORACION_EXPEDIENTE_FORM_GROUPS
        for campo, _ in campos
    )
)
VALORACION_EXPEDIENTE_CHECKBOX_FIELDS = {
    "metodo_comparacion_activo",
    "metodo_coste_activo",
    "metodo_comparacion_aplicado",
    "metodo_comparacion_descartado",
    "metodo_coste_aplicado",
    "metodo_coste_descartado",
    "metodo_actualizacion_rentas_aplicado",
    "metodo_actualizacion_rentas_descartado",
    "metodo_residual_aplicado",
    "metodo_residual_descartado",
    "incidencias_automaticas_visibles",
    "incidencias_manuales_visibles",
}
VALORACION_VISITA_OBSERVACIONES_GROUPS = [
    (
        "Estado observado",
        [("estado_observado", "Estado observado")],
    ),
    (
        "Reforma observada",
        [("reforma_observada", "Reforma observada")],
    ),
    (
        "Ocupación observada",
        [("ocupacion_observada", "Ocupación observada")],
    ),
    (
        "Observaciones de inspección",
        [("observaciones_inspeccion_valoracion", "Observaciones de inspección")],
    ),
    (
        "Incidencias",
        [("incidencias_valoracion", "Incidencias")],
    ),
    (
        "Comprobaciones físicas",
        [("comprobaciones_fisicas", "Comprobaciones físicas")],
    ),
    (
        "Portal y contadores",
        [
            ("observaciones_portal", "Observaciones del portal"),
            (
                "observaciones_cuadro_contadores",
                "Observaciones del cuadro de contadores",
            ),
        ],
    ),
]
VALORACION_VISITA_OBSERVACIONES_FIELDS = [
    campo
    for _, campos in VALORACION_VISITA_OBSERVACIONES_GROUPS
    for campo, _ in campos
]
VALORACION_AYUDAS_RAPIDAS = {
    "finalidad_valoracion": [
        "Compraventa",
        "Herencia",
        "Divorcio",
        "Garantía",
        "Asesoramiento",
        "Judicial",
        "Otro",
    ],
    "base_valor": [
        "valor_mercado",
        "valor_razonable_estimado",
        "valor_reposicion",
        "valor_actualizacion_rentas",
        "otro",
    ],
    "alcance_valoracion": [
        "Valoración pericial con estructura inspirada en estándares ECO/805/2003",
        "Valoración orientativa para asesoramiento",
        "Valoración para procedimiento judicial",
    ],
    "criterio_superficie_adoptada": [
        "Superficie comprobada en visita",
        "Superficie catastral contrastada",
        "Superficie registral disponible",
        "Superficie construida adoptada por prudencia",
    ],
    "situacion_ocupacion": [
        "Libre",
        "Ocupado por propietario",
        "Arrendado",
        "Desconocido",
    ],
    "estado_conservacion": [
        "Reformado",
        "Buen estado",
        "Normal",
        "A reformar",
        "Deficiente",
    ],
    "documentacion_utilizada": [
        "Catastro",
        "Nota simple",
        "Escritura",
        "IBI",
        "Planos",
        "Certificado energético",
        "Visita",
        "Otro",
    ],
    "criterios_metodo_valoracion": [
        "Comparación",
        "Coste",
        "Actualización de rentas",
        "Residual",
        "Otro",
    ],
    "condicionantes_limitaciones_valoracion": [
        "Sin nota simple",
        "Sin documentación registral",
        "Sin acceso completo",
        "Superficies no comprobadas",
        "Comparables no visitados",
        "Otro",
    ],
    "incidencias_condicionantes_manuales": [
        "Valor condicionado a comprobación documental",
        "Valor condicionado a acceso completo",
    ],
    "incidencias_advertencias_manuales": [
        "Datos sujetos a la documentación aportada",
        "Comparables no visitados individualmente",
    ],
    "incidencias_limitaciones_manuales": [
        "No se realiza comprobación urbanística exhaustiva",
        "No se verifica cargas registrales fuera de la documentación aportada",
    ],
}
COMPARABLE_VALORACION_ITEMS = [
    ("direccion_testigo", "Dirección testigo"),
    ("fuente_testigo", "Fuente"),
    ("fecha_testigo", "Fecha"),
    ("precio_oferta", "Precio oferta"),
    ("valor_unitario", "Valor unitario"),
    ("superficie_construida", "Superficie construida"),
    ("superficie_util", "Superficie útil"),
    ("tipologia", "Tipología"),
    ("planta", "Planta"),
    ("dormitorios", "Dormitorios"),
    ("banos", "Baños"),
    ("estado_conservacion", "Estado de conservación"),
    ("antiguedad", "Antigüedad"),
    ("calidad_constructiva", "Calidad constructiva"),
    ("visitado", "Visitado"),
    ("observaciones", "Observaciones"),
]
TESTIGO_VALORACION_FORM_GROUPS = [
    (
        "Identificación y fuente",
        [
            ("direccion_testigo", "Dirección"),
            ("referencia_testigo", "Referencia"),
        ],
    ),
    (
        "Datos económicos y fuente",
        [
            ("precio_oferta", "Precio ofertado"),
            ("precio_depurado", "Precio depurado"),
            ("superficie_tomada", "Superficie tomada"),
            ("tipo_superficie_tomada", "Tipo de superficie tomada"),
            ("fuente_tipo", "Tipo de fuente"),
            ("fuente_testigo", "Fuente"),
            ("fuente_detalle", "Detalle de fuente"),
            ("url_fuente", "URL o referencia de fuente"),
            ("fecha_testigo", "Fecha del testigo"),
            ("fecha_captura", "Fecha de captura"),
            ("dato_verificado", "Dato verificado"),
            ("testigo_visitado", "Testigo visitado"),
            ("fiabilidad_dato", "Fiabilidad del dato"),
            ("similitud_inmueble", "Similitud con el inmueble"),
            ("observaciones_economicas", "Observaciones económicas"),
        ],
    ),
    (
        "Ubicación",
        [
            ("codigo_postal", "Código postal"),
            ("municipio", "Municipio"),
            ("provincia", "Provincia"),
            ("ubicacion", "Ubicación"),
        ],
    ),
    (
        "Importes y superficies",
        [
            ("precio_cierre", "Precio cierre"),
            ("superficie_construida", "Superficie construida"),
            ("superficie_util", "Superficie útil"),
            ("superficie_otros_usos", "Superficie otros usos"),
            ("valor_unitario", "Valor unitario"),
        ],
    ),
    (
        "Características",
        [
            ("tipologia", "Tipología"),
            ("planta", "Planta"),
            ("dormitorios", "Dormitorios"),
            ("banos", "Baños"),
            ("aseos", "Aseos"),
            ("ascensor", "Ascensor"),
            ("es_exterior", "Exterior"),
            ("balcon", "Balcón"),
            ("garaje", "Garaje"),
            ("trastero", "Trastero"),
            ("terraza", "Terraza"),
            ("patio", "Patio"),
        ],
    ),
    (
        "Estado y validación",
        [
            ("estado_conservacion", "Estado de conservación"),
            ("antiguedad", "Antigüedad"),
            ("ano_construccion", "Año de construcción"),
            ("ano_reforma", "Año de reforma"),
            ("calidad_constructiva", "Calidad constructiva"),
            ("caracteristicas_constructivas", "Características constructivas"),
            ("aire_acondicionado", "Aire acondicionado"),
            ("tipo_calefaccion", "Tipo de calefacción"),
            ("certificacion_energetica", "Certificación energética"),
            ("visitado", "Visitado"),
            ("validacion_estado", "Estado de validación"),
            ("reutilizable", "Reutilizable"),
        ],
    ),
    (
        "Observaciones",
        [("observaciones", "Observaciones")],
    ),
]
TESTIGO_VALORACION_FORM_FIELDS = [
    campo
    for _, campos in TESTIGO_VALORACION_FORM_GROUPS
    for campo, _ in campos
]
if "precio_unitario_inicial" not in TESTIGO_VALORACION_FORM_FIELDS:
    TESTIGO_VALORACION_FORM_FIELDS.append("precio_unitario_inicial")
TESTIGO_VALORACION_NUMERIC_FIELDS = {
    "precio_oferta",
    "precio_depurado",
    "precio_unitario_inicial",
    "superficie_tomada",
    "precio_cierre",
    "superficie_construida",
    "superficie_util",
    "superficie_otros_usos",
    "valor_unitario",
}
TESTIGO_VALORACION_INTEGER_FIELDS = {
    "dormitorios",
    "banos",
    "aseos",
    "ano_construccion",
    "ano_reforma",
}
TESTIGO_VALORACION_CHECKBOX_FIELDS = {
    "ascensor",
    "es_exterior",
    "balcon",
    "garaje",
    "trastero",
    "terraza",
    "patio",
    "aire_acondicionado",
    "dato_verificado",
    "testigo_visitado",
    "visitado",
    "reutilizable",
}
TESTIGO_VALORACION_VALIDACION_OPTIONS = [
    ("pendiente", "Pendiente"),
    ("revisado", "Revisado"),
    ("validado", "Validado"),
    ("descartado", "Descartado"),
]
TESTIGO_BIBLIOTECA_FUENTE_PRESETS = [
    "Idealista",
    "Fotocasa",
    "Habitaclia",
    "Pisos.com",
    "Yaencontre",
    "Otro",
]
TESTIGO_BIBLIOTECA_BOOLEAN_FIELDS = {
    "ascensor",
    "es_exterior",
    "balcon",
    "terraza",
    "patio",
    "aire_acondicionado",
    "garaje",
    "trastero",
    "dato_verificado",
}
TESTIGO_BIBLIOTECA_NUMERIC_FIELDS = {
    "precio_oferta": "Precio oferta",
    "precio_depurado": "Precio depurado",
    "superficie_tomada": "Superficie tomada",
    "superficie_construida": "Superficie construida",
    "superficie_util": "Superficie útil",
}
TESTIGO_BIBLIOTECA_INTEGER_FIELDS = {
    "banos": "Baños",
    "ano_construccion": "Año de construcción",
    "ano_reforma": "Año de reforma",
}
VALORACION_TESTIGO_AJUSTES_ITEMS = [
    ("ajuste_superficie_construida", "Superficie construida"),
    ("ajuste_ubicacion", "Ubicación"),
    ("ajuste_antiguedad", "Antigüedad"),
    ("ajuste_calidades", "Calidades"),
    ("ajuste_caracteristicas_constructivas", "Características constructivas"),
]
HOMOGENEIZACION_VARIABLE_OPTIONS = [
    ("superficie", "Superficie"),
    ("estado_conservacion", "Estado de conservación"),
    ("antiguedad", "Antigüedad"),
    ("planta", "Planta"),
    ("ascensor", "Ascensor"),
    ("ubicacion", "Ubicación"),
    ("calidad_constructiva", "Calidad constructiva"),
    ("reformas", "Reformas"),
    ("anexos", "Anexos"),
    ("exterior_interior", "Exterior/interior"),
    ("orientacion", "Orientación"),
    ("fuente_negociacion", "Fuente/negociación"),
    ("otro", "Otro"),
]
HOMOGENEIZACION_TIPO_AJUSTE_OPTIONS = [
    ("porcentaje", "Porcentaje"),
    ("importe_m2", "Importe €/m²"),
    ("cualitativo_no_cuantificado", "Cualitativo no cuantificado"),
]
HOMOGENEIZACION_SIGNO_OPTIONS = [
    ("+", "Suma"),
    ("-", "Resta"),
]
REPRESENTATIVIDAD_VALORACION_OPTIONS = [
    ("alta", "Alta"),
    ("media_alta", "Media alta"),
    ("media", "Media"),
    ("baja", "Baja"),
    ("descartado", "Descartado"),
]
TIPO_NIVEL_OPTIONS = [
    ("bajo_rasante", "Bajo rasante"),
    ("baja", "Baja"),
    ("sobre_rasante", "Sobre rasante"),
    ("cubierta", "Cubierta"),
    ("otro", "Otro"),
]
TIPO_NIVEL_LABELS = dict(TIPO_NIVEL_OPTIONS)
TIPO_UNIDAD_OPTIONS = [
    ("vivienda", "Vivienda"),
    ("local", "Local"),
    ("oficina", "Oficina"),
    ("garaje", "Garaje"),
    ("trastero", "Trastero"),
    ("zona_comun", "Zona común"),
    ("exterior", "Exterior"),
    ("otro", "Otro"),
]
TIPO_UNIDAD_LABELS = dict(TIPO_UNIDAD_OPTIONS)
VINCULO_UNIDAD_OPTIONS = [
    ("principal", "Principal"),
    ("anejo", "Anejo"),
    ("comun", "Común"),
    ("exterior", "Exterior"),
]
VINCULO_UNIDAD_LABELS = dict(VINCULO_UNIDAD_OPTIONS)
TIPO_ANEJO_OPTIONS = [
    ("garaje", "Garaje"),
    ("trastero", "Trastero"),
    ("terraza", "Terraza"),
    ("patio", "Patio"),
    ("cuarto_anejo", "Cuarto anejo"),
    ("otro", "Otro"),
]
TIPO_ANEJO_LABELS = dict(TIPO_ANEJO_OPTIONS)
AMBITO_VISITA_OPTIONS = [
    ("edificio_completo", "Edificio completo"),
    ("nivel", "Nivel / planta"),
    ("unidad", "Unidad"),
    ("zona_comun", "Zona común"),
    ("exterior", "Exterior"),
]
AMBITO_VISITA_LABELS = dict(AMBITO_VISITA_OPTIONS)
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".heif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}
MAX_IMAGE_DIMENSION = 1600
MAX_THUMB_DIMENSION = 400
JPEG_QUALITY = 80


def get_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def es_archivo_imagen(nombre_archivo: str | None, content_type: str | None = None) -> bool:
    extension = os.path.splitext(nombre_archivo or "")[1].lower()
    if extension in IMAGE_EXTENSIONS:
        return True
    return bool(content_type and content_type.lower().startswith("image/"))


def construir_ruta_thumbnail(ruta_imagen: str | Path) -> Path:
    ruta = Path(ruta_imagen)
    return ruta.with_name(f"{ruta.stem}_thumb.jpg")


def _normalizar_imagen_para_jpeg(imagen: Image.Image) -> Image.Image:
    if imagen.mode in ("RGBA", "LA"):
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        alpha = imagen.getchannel("A")
        fondo.paste(imagen.convert("RGBA"), mask=alpha)
        return fondo
    if imagen.mode == "P":
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        alpha = imagen.getchannel("A")
        fondo.paste(imagen, mask=alpha)
        return fondo
    if imagen.mode != "RGB":
        return imagen.convert("RGB")
    return imagen


def _guardar_jpeg_sin_metadatos(imagen: Image.Image, ruta_destino: Path) -> None:
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(
        ruta_destino,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
        progressive=True,
    )


def _procesar_imagen_a_rutas(
    ruta_origen: str | Path,
    ruta_destino: str | Path,
    ruta_thumb: str | Path | None = None,
) -> dict:
    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow no está disponible para procesar imágenes.")

    ruta_origen = Path(ruta_origen)
    ruta_destino = Path(ruta_destino)
    ruta_thumb_path = Path(ruta_thumb) if ruta_thumb else construir_ruta_thumbnail(ruta_destino)

    if ruta_destino.stem.endswith("_thumb"):
        raise ValueError("No se deben reprocesar thumbnails.")

    with Image.open(ruta_origen) as imagen_original:
        imagen_original.load()
        imagen = ImageOps.exif_transpose(imagen_original)
        imagen = _normalizar_imagen_para_jpeg(imagen)

        if max(imagen.size) > MAX_IMAGE_DIMENSION:
            imagen.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

        width, height = imagen.size
        _guardar_jpeg_sin_metadatos(imagen, ruta_destino)

        thumb = imagen.copy()
        if max(thumb.size) > MAX_THUMB_DIMENSION:
            thumb.thumbnail((MAX_THUMB_DIMENSION, MAX_THUMB_DIMENSION), Image.Resampling.LANCZOS)
        _guardar_jpeg_sin_metadatos(thumb, ruta_thumb_path)

    return {
        "ruta_original": str(ruta_destino),
        "ruta_thumb": str(ruta_thumb_path),
        "width": width,
        "height": height,
    }


def procesar_imagen(ruta_imagen: str) -> dict:
    ruta = Path(ruta_imagen)
    if ruta.stem.endswith("_thumb"):
        raise ValueError("No se deben reprocesar thumbnails.")
    return _procesar_imagen_a_rutas(ruta, ruta)


def borrar_foto_si_existe(nombre_foto):
    if nombre_foto:
        ruta = UPLOAD_PATH / nombre_foto
        if ruta.exists():
            ruta.unlink()
        ruta_thumb = construir_ruta_thumbnail(ruta)
        if ruta_thumb.exists():
            ruta_thumb.unlink()


def guardar_upload_si_existe(archivo: UploadFile | None):
    if not archivo or not archivo.filename:
        return None

    extension = os.path.splitext(archivo.filename)[1].lower()
    es_imagen = es_archivo_imagen(archivo.filename, archivo.content_type)
    extension_salida = ".jpg" if es_imagen else extension
    nombre_archivo = f"{uuid4().hex}{extension_salida}"
    ruta_destino = UPLOAD_PATH / nombre_archivo

    if not es_imagen:
        with ruta_destino.open("wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        return nombre_archivo

    extension_temporal = extension or ".tmp"
    ruta_temporal = UPLOAD_PATH / f"{uuid4().hex}{extension_temporal}"

    try:
        with ruta_temporal.open("wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        procesar_imagen_temporal = _procesar_imagen_a_rutas(ruta_temporal, ruta_destino)
        logger.debug("Imagen procesada: %s", procesar_imagen_temporal)
    except Exception as exc:
        logger.warning("No se pudo procesar la imagen %s: %s", archivo.filename, exc)
        if ruta_destino.exists():
            ruta_destino.unlink()
        extension_respaldo = extension or ".bin"
        nombre_archivo = f"{uuid4().hex}{extension_respaldo}"
        ruta_destino = UPLOAD_PATH / nombre_archivo
        with ruta_destino.open("wb") as buffer:
            with ruta_temporal.open("rb") as temporal:
                shutil.copyfileobj(temporal, buffer)
    finally:
        if ruta_temporal.exists():
            ruta_temporal.unlink()

    return nombre_archivo


def guardar_uploads_si_existen(archivos: list[UploadFile] | None) -> list[str]:
    nombres: list[str] = []
    for archivo in archivos or []:
        nombre = guardar_upload_si_existe(archivo)
        if nombre:
            nombres.append(nombre)
    return nombres


def normalizar_fragmento_nombre_archivo(
    texto: str | None,
    fallback: str = "foto",
    max_len: int = 24,
) -> str:
    texto_limpio = limpiar_texto(texto or "")
    if not texto_limpio:
        return fallback

    texto_ascii = (
        unicodedata.normalize("NFKD", texto_limpio)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    texto_seguro = re.sub(r"[^a-z0-9]+", "_", texto_ascii).strip("_")
    if not texto_seguro:
        return fallback
    return texto_seguro[:max_len].strip("_") or fallback


def construir_nombre_archivo_contextual(
    extension: str,
    *fragmentos: str | None,
) -> str:
    partes = [
        normalizar_fragmento_nombre_archivo(fragmento)
        for fragmento in fragmentos
        if limpiar_texto(fragmento or "")
    ]
    if not partes:
        partes = ["foto"]
    extension_limpia = extension.lower() or ".jpg"
    return f"{'_'.join(partes[:5])}_{uuid4().hex[:8]}{extension_limpia}"


def guardar_upload_contextual(archivo: UploadFile | None, *fragmentos: str | None):
    if not archivo or not archivo.filename:
        return None

    extension = os.path.splitext(archivo.filename)[1].lower()
    es_imagen = es_archivo_imagen(archivo.filename, archivo.content_type)
    extension_salida = ".jpg" if es_imagen else extension
    nombre_archivo = construir_nombre_archivo_contextual(extension_salida, *fragmentos)
    ruta_destino = UPLOAD_PATH / nombre_archivo

    if not es_imagen:
        with ruta_destino.open("wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        return nombre_archivo

    extension_temporal = extension or ".tmp"
    ruta_temporal = UPLOAD_PATH / f"{uuid4().hex}{extension_temporal}"

    try:
        with ruta_temporal.open("wb") as buffer:
            shutil.copyfileobj(archivo.file, buffer)
        procesar_imagen_temporal = _procesar_imagen_a_rutas(ruta_temporal, ruta_destino)
        logger.debug("Imagen procesada: %s", procesar_imagen_temporal)
    except Exception as exc:
        logger.warning("No se pudo procesar la imagen %s: %s", archivo.filename, exc)
        if ruta_destino.exists():
            ruta_destino.unlink()
        extension_respaldo = extension or ".bin"
        nombre_archivo = construir_nombre_archivo_contextual(extension_respaldo, *fragmentos)
        ruta_destino = UPLOAD_PATH / nombre_archivo
        with ruta_destino.open("wb") as buffer:
            with ruta_temporal.open("rb") as temporal:
                shutil.copyfileobj(temporal, buffer)
    finally:
        if ruta_temporal.exists():
            ruta_temporal.unlink()

    return nombre_archivo


def guardar_uploads_contextuales(
    archivos: list[UploadFile] | None,
    *fragmentos: str | None,
) -> list[str]:
    nombres: list[str] = []
    for indice, archivo in enumerate(archivos or [], start=1):
        nombre = guardar_upload_contextual(
            archivo,
            *fragmentos,
            f"{indice:02d}",
        )
        if nombre:
            nombres.append(nombre)
    return nombres


def normalizar_tipo_documental_anexo_a(tipo: str | None) -> str:
    tipo_limpio = limpiar_texto(tipo)
    return tipo_limpio if tipo_limpio in TIPOS_DOCUMENTALES_ANEXO_A else "Otro"


def es_pdf_aportado_valido(archivo: UploadFile | None) -> bool:
    if not archivo or not archivo.filename:
        return False
    extension = os.path.splitext(archivo.filename)[1].lower()
    mime = limpiar_texto(archivo.content_type).lower()
    return extension == ".pdf" and mime in ("", "application/pdf", "application/x-pdf")


def guardar_documento_pdf_expediente(
    archivo: UploadFile | None,
    expediente_id: int,
) -> tuple[str, str, str]:
    if not es_pdf_aportado_valido(archivo):
        raise ValueError("Solo se admiten documentos PDF.")

    assert archivo is not None
    carpeta = DOCUMENTOS_EXPEDIENTE_UPLOAD_DIR / str(expediente_id)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre_destino = f"{uuid4().hex}.pdf"
    ruta_destino = carpeta / nombre_destino
    with ruta_destino.open("wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    ruta_relativa = f"expediente_documentos/{expediente_id}/{nombre_destino}"
    return ruta_relativa, limpiar_texto(archivo.filename), limpiar_texto(archivo.content_type)


def resolver_ruta_upload_relativa_segura(ruta_relativa: str | None) -> Path | None:
    ruta_limpia = limpiar_texto(ruta_relativa).lstrip("/")
    if not ruta_limpia:
        return None
    ruta = (UPLOAD_PATH / ruta_limpia).resolve()
    raiz_uploads = UPLOAD_PATH.resolve()
    try:
        ruta.relative_to(raiz_uploads)
    except ValueError:
        return None
    return ruta


def borrar_upload_relativo_si_existe(ruta_relativa: str | None) -> None:
    ruta = resolver_ruta_upload_relativa_segura(ruta_relativa)
    if ruta and ruta.exists() and ruta.is_file():
        ruta.unlink()


def documento_expediente_a_dict(documento) -> dict | None:
    if not documento:
        return None
    item = dict(documento)
    item["url"] = f"/uploads/{item['archivo_ruta']}"
    return item


def obtener_pdf_mediciones_anexo_f_informe_v2(cur, expediente_id: int) -> dict | None:
    documento = cur.execute(
        """
        SELECT *
        FROM expediente_documentos
        WHERE expediente_id = ? AND tipo_documento = ?
        ORDER BY updated_at DESC, created_at DESC, id DESC
        LIMIT 1
        """,
        (expediente_id, TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
    ).fetchone()
    return documento_expediente_a_dict(documento)


def eliminar_pdfs_mediciones_anexo_f_informe_v2(cur, expediente_id: int) -> int:
    documentos = cur.execute(
        """
        SELECT id, archivo_ruta
        FROM expediente_documentos
        WHERE expediente_id = ? AND tipo_documento = ?
        """,
        (expediente_id, TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
    ).fetchall()
    for documento in documentos:
        borrar_upload_relativo_si_existe(documento["archivo_ruta"])
    cur.execute(
        """
        DELETE FROM expediente_documentos
        WHERE expediente_id = ? AND tipo_documento = ?
        """,
        (expediente_id, TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
    )
    return len(documentos)


def nombre_visible_documento_desde_archivo(nombre_original: str | None) -> str:
    nombre = limpiar_texto(nombre_original)
    if not nombre:
        return "Documento aportado"
    return limpiar_texto(Path(nombre).stem) or "Documento aportado"


TESTIGO_FOTO_EXT_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TESTIGO_FOTO_MAX_BYTES = 10 * 1024 * 1024


def tamano_upload_file(archivo: UploadFile) -> int:
    posicion = archivo.file.tell()
    archivo.file.seek(0, os.SEEK_END)
    tamano = archivo.file.tell()
    archivo.file.seek(posicion)
    return tamano


def validar_fotos_testigo_valoracion(fotos: list[UploadFile] | None) -> list[str]:
    errores = []
    for foto in fotos or []:
        if not foto or not foto.filename:
            continue
        extension = os.path.splitext(foto.filename)[1].lower()
        if extension not in TESTIGO_FOTO_EXT_PERMITIDAS:
            errores.append(
                f"{foto.filename}: extensión no permitida. Usa JPG, PNG, WEBP o GIF."
            )
            continue
        if foto.content_type and not foto.content_type.startswith("image/"):
            errores.append(f"{foto.filename}: el archivo debe ser una imagen.")
            continue
        if tamano_upload_file(foto) > TESTIGO_FOTO_MAX_BYTES:
            errores.append(f"{foto.filename}: supera el tamaño máximo de 10 MB.")
    return errores


def obtener_fotos_relacionadas(cur, tabla: str, fk_columna: str, parent_id: int) -> list[dict]:
    return [
        dict(row)
        for row in cur.execute(
            f"""
            SELECT id, archivo, created_at
            FROM {tabla}
            WHERE {fk_columna}=?
            ORDER BY id ASC
            """,
            (parent_id,),
        ).fetchall()
    ]


def obtener_fotos_visita(cur, visita_id: int, categoria: str = "exterior") -> list[dict]:
    fotos = [
        dict(row)
        for row in cur.execute(
            """
            SELECT id, visita_id, categoria, ruta, descripcion, created_at
            FROM visita_fotos
            WHERE visita_id=? AND categoria=?
            ORDER BY id ASC
            """,
            (visita_id, categoria),
        ).fetchall()
    ]
    for foto in fotos:
        foto["url"] = f"/uploads/{foto['ruta']}"
    return fotos


def insertar_fotos_relacionadas(
    cur,
    tabla: str,
    fk_columna: str,
    parent_id: int,
    nombres_archivos: list[str],
):
    for nombre in nombres_archivos:
        cur.execute(
            f"INSERT INTO {tabla} ({fk_columna}, archivo) VALUES (?, ?)",
            (parent_id, nombre),
        )


def borrar_fotos_relacionadas(cur, tabla: str, fk_columna: str, parent_id: int):
    fotos = obtener_fotos_relacionadas(cur, tabla, fk_columna, parent_id)
    for foto in fotos:
        borrar_foto_si_existe(foto["archivo"])
    cur.execute(f"DELETE FROM {tabla} WHERE {fk_columna}=?", (parent_id,))


def sincronizar_foto_principal(
    cur,
    tabla_principal: str,
    id_columna: str,
    foto_columna: str,
    parent_id: int,
    tabla_fotos: str,
    fk_columna: str,
):
    primera = cur.execute(
        f"""
        SELECT archivo
        FROM {tabla_fotos}
        WHERE {fk_columna}=?
        ORDER BY id ASC
        LIMIT 1
        """,
        (parent_id,),
    ).fetchone()
    cur.execute(
        f"UPDATE {tabla_principal} SET {foto_columna}=? WHERE {id_columna}=?",
        (primera["archivo"] if primera else None, parent_id),
    )


def enriquecer_registro_con_fotos(
    cur,
    registro,
    tabla_fotos: str,
    fk_columna: str,
    foto_legacy_columna: str,
):
    registro_dict = dict(registro)
    fotos = obtener_fotos_relacionadas(cur, tabla_fotos, fk_columna, registro_dict["id"])
    if not fotos and registro_dict.get(foto_legacy_columna):
        fotos = [{"id": None, "archivo": registro_dict.get(foto_legacy_columna), "created_at": None}]
    for foto in fotos:
        foto["url"] = f"/uploads/{foto['archivo']}"
    registro_dict["fotos"] = fotos
    registro_dict["foto_url"] = fotos[0]["url"] if fotos else ""
    return registro_dict


def obtener_nombre_imagen_mapa_anotada(nombre_imagen_base: str | None) -> str:
    if not nombre_imagen_base:
        return ""
    return f"{Path(nombre_imagen_base).stem}_mapa_anotado.png"


def borrar_imagen_anotada_mapa_si_existe(nombre_imagen_base: str | None):
    nombre_anotado = obtener_nombre_imagen_mapa_anotada(nombre_imagen_base)
    if nombre_anotado:
        borrar_foto_si_existe(nombre_anotado)


def cargar_fuente_mapa_patologia(tamano: int):
    if ImageFont is None:
        return None

    for fuente in (
        "DejaVuSans-Bold.ttf",
        "Arial Bold.ttf",
        "Arial.ttf",
        "LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(fuente, tamano)
        except OSError:
            continue

    return ImageFont.load_default()


def generar_imagen_anotada_mapa_patologia(
    nombre_imagen_base: str | None,
    filas: int,
    columnas: int,
) -> str:
    if (
        not nombre_imagen_base
        or Image is None
        or ImageDraw is None
        or ImageFont is None
    ):
        return ""

    ruta_base = UPLOAD_PATH / nombre_imagen_base
    if not ruta_base.exists():
        return ""

    nombre_anotado = obtener_nombre_imagen_mapa_anotada(nombre_imagen_base)
    ruta_anotada = UPLOAD_PATH / nombre_anotado

    try:
        filas_seguras = max(int(filas or 0), 1)
        columnas_seguras = max(int(columnas or 0), 1)

        with Image.open(ruta_base) as imagen_original:
            imagen = imagen_original.convert("RGBA")

        ancho, alto = imagen.size
        celda_ancho = ancho / columnas_seguras
        celda_alto = alto / filas_seguras
        referencia = min(ancho, alto)
        trazo_base = max(1, int(referencia / 400))
        trazo_borde = trazo_base + 2
        tamano_fuente = max(16, min(120, int(min(celda_ancho, celda_alto) * 0.18)))
        padding_x = max(8, int(tamano_fuente * 0.45))
        padding_y = max(6, int(tamano_fuente * 0.28))
        margen = max(8, int(tamano_fuente * 0.5))
        trazo_texto = max(2, int(tamano_fuente * 0.12))

        dibujo = ImageDraw.Draw(imagen, "RGBA")
        fuente = cargar_fuente_mapa_patologia(tamano_fuente)

        for fila in range(1, filas_seguras):
            y = int(round(fila * celda_alto))
            dibujo.line([(0, y), (ancho, y)], fill=(0, 0, 0, 180), width=trazo_borde)
            dibujo.line([(0, y), (ancho, y)], fill=(255, 255, 255, 235), width=trazo_base)

        for columna in range(1, columnas_seguras):
            x = int(round(columna * celda_ancho))
            dibujo.line([(x, 0), (x, alto)], fill=(0, 0, 0, 180), width=trazo_borde)
            dibujo.line([(x, 0), (x, alto)], fill=(255, 255, 255, 235), width=trazo_base)

        for fila in range(filas_seguras):
            for columna in range(columnas_seguras):
                etiqueta = generar_codigo_cuadrante(fila, columna)
                caja = dibujo.textbbox(
                    (0, 0),
                    etiqueta,
                    font=fuente,
                    stroke_width=trazo_texto,
                )
                texto_ancho = caja[2] - caja[0]
                texto_alto = caja[3] - caja[1]
                x = int(columna * celda_ancho) + margen
                y = int(fila * celda_alto) + margen
                fondo = (
                    x,
                    y,
                    x + texto_ancho + (padding_x * 2),
                    y + texto_alto + (padding_y * 2),
                )
                dibujo.rounded_rectangle(
                    fondo,
                    radius=max(4, int(tamano_fuente * 0.2)),
                    fill=(0, 0, 0, 148),
                )
                dibujo.text(
                    (x + padding_x, y + padding_y),
                    etiqueta,
                    font=fuente,
                    fill=(255, 255, 255, 255),
                    stroke_width=trazo_texto,
                    stroke_fill=(0, 0, 0, 220),
                )

        imagen.convert("RGB").save(ruta_anotada, format="PNG")
        return nombre_anotado
    except Exception:
        logger.exception(
            "No se pudo generar la imagen anotada del mapa %s",
            nombre_imagen_base,
        )
        return ""


def construir_imagen_mapa_url(nombre_imagen_base: str | None) -> str:
    if not nombre_imagen_base:
        return ""

    nombre_anotado = obtener_nombre_imagen_mapa_anotada(nombre_imagen_base)
    if nombre_anotado and (UPLOAD_PATH / nombre_anotado).exists():
        return f"/uploads/{nombre_anotado}"

    if (UPLOAD_PATH / nombre_imagen_base).exists():
        return f"/uploads/{nombre_imagen_base}"

    return ""


def guardar_imagen_catastro_si_existe(contenido: bytes | None, extension: str | None):
    if not contenido or not extension:
        return ""

    nombre_archivo = f"catastro_{uuid4().hex}{extension}"
    ruta = UPLOAD_PATH / nombre_archivo
    ruta.write_bytes(contenido)
    return nombre_archivo


def require_row(row, detail: str):
    if row is None:
        raise HTTPException(status_code=404, detail=detail)
    return row


def get_table_columns(table_name: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        rows = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}
    finally:
        conn.close()


def ensure_climatologia_table():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS climatologia_visitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visita_id INTEGER NOT NULL,
                resumen TEXT,
                detalle_json TEXT,
                ubicacion TEXT,
                latitud REAL,
                longitud REAL,
                fecha_generacion TEXT,
                FOREIGN KEY (visita_id) REFERENCES visitas (id)
            )
            """
        )
        columnas = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(climatologia_visitas)").fetchall()
        }
        if "detalle_json" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN detalle_json TEXT")
        if "ubicacion" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN ubicacion TEXT")
        if "latitud" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN latitud REAL")
        if "longitud" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN longitud REAL")
        if "fecha_generacion" not in columnas:
            cur.execute(
                "ALTER TABLE climatologia_visitas ADD COLUMN fecha_generacion TEXT"
            )
        tablas = {
            row["name"]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "climatologia" in tablas:
            cur.execute(
                """
                INSERT INTO climatologia_visitas (visita_id, resumen)
                SELECT c.visita_id, c.resumen
                FROM climatologia c
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM climatologia_visitas cv
                    WHERE cv.visita_id = c.visita_id
                      AND IFNULL(cv.resumen, '') = IFNULL(c.resumen, '')
                )
                """
            )
            cur.execute("DROP TABLE climatologia")
        conn.commit()
    finally:
        conn.close()


def limpiar_texto(valor) -> str:
    return str(valor or "").strip()


def parse_optional_int(valor):
    texto = limpiar_texto(valor)
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def fila_a_dict(fila, columnas):
    if not fila:
        return {columna: "" for columna in columnas}
    return {columna: limpiar_texto(fila[columna]) for columna in columnas}


def upsert_tabla_por_visita(cur, tabla: str, visita_id: int, valores: dict):
    columnas = list(valores.keys())
    placeholders = ", ".join(["?"] * (len(columnas) + 1))
    updates = ", ".join([f"{col}=excluded.{col}" for col in columnas])
    cur.execute(
        f"""
        INSERT INTO {tabla} (visita_id, {", ".join(columnas)})
        VALUES ({placeholders})
        ON CONFLICT(visita_id) DO UPDATE SET {updates}
        """,
        [visita_id] + [valores[col] for col in columnas],
    )


def upsert_inspeccion_estancia(cur, visita_id: int, estancia_id: int, valores: dict):
    columnas = list(valores.keys())
    placeholders = ", ".join(["?"] * (len(columnas) + 2))
    updates = ", ".join([f"{col}=excluded.{col}" for col in columnas])
    cur.execute(
        f"""
        INSERT INTO inspeccion_estancias (visita_id, estancia_id, {", ".join(columnas)})
        VALUES ({placeholders})
        ON CONFLICT(visita_id, estancia_id) DO UPDATE SET {updates}
        """,
        [visita_id, estancia_id] + [valores[col] for col in columnas],
    )


def upsert_habitabilidad_estancia(cur, visita_id: int, estancia_id: int, valores: dict):
    columnas = list(valores.keys())
    placeholders = ", ".join(["?"] * (len(columnas) + 2))
    updates = ", ".join([f"{col}=excluded.{col}" for col in columnas])
    cur.execute(
        f"""
        INSERT INTO habitabilidad_estancias (visita_id, estancia_id, {", ".join(columnas)})
        VALUES ({placeholders})
        ON CONFLICT(visita_id, estancia_id) DO UPDATE SET {updates}
        """,
        [visita_id, estancia_id] + [valores[col] for col in columnas],
    )


def cargar_datos_valoracion_visita(cur, visita_id: int):
    columnas = (
        [item[0] for item in VALORACION_ENCARGO_ITEMS]
        + [item[0] for item in VALORACION_DOCUMENTACION_ITEMS]
        + [item[0] for item in VALORACION_DATOS_GENERALES_ITEMS]
        + [item[0] for item in VALORACION_SUPERFICIES_ITEMS]
        + [item[0] for item in VALORACION_SITUACION_LEGAL_ITEMS]
        + [item[0] for item in VALORACION_ENTORNO_ITEMS]
        + [item[0] for item in VALORACION_EDIFICIO_ITEMS]
        + [item[0] for item in VALORACION_INMUEBLE_ITEMS]
        + [item[0] for item in VALORACION_CONSTRUCTIVO_ITEMS]
        + [item[0] for item in VALORACION_ESTADO_ITEMS]
        + [item[0] for item in VALORACION_FECHAS_ITEMS]
        + [item[0] for item in VALORACION_METODO_ITEMS]
        + [item[0] for item in VALORACION_RESULTADO_ITEMS]
    )
    return fila_a_dict(
        cur.execute(
            "SELECT * FROM valoracion_visita WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        columnas,
    )


def comparable_valoracion_form_vacio():
    return {campo: "" for campo, _ in COMPARABLE_VALORACION_ITEMS}


def valoracion_expediente_form_vacio():
    return {campo: "" for campo in VALORACION_EXPEDIENTE_FORM_FIELDS}


def cargar_valoracion_expediente_form(cur, expediente_id: int):
    return fila_a_dict(
        cur.execute(
            "SELECT * FROM valoracion_expediente WHERE expediente_id=?",
            (expediente_id,),
        ).fetchone(),
        VALORACION_EXPEDIENTE_FORM_FIELDS,
    )


def cargar_valoracion_legacy_expediente_form(cur, expediente_id: int):
    columnas_legacy = [
        campo
        for campo in VALORACION_EXPEDIENTE_FORM_FIELDS
        if campo not in {"metodo_comparacion_activo", "metodo_coste_activo"}
    ]
    visita_legacy = cur.execute(
        """
        SELECT vv.*
        FROM valoracion_visita vv
        JOIN visitas v ON vv.visita_id = v.id
        WHERE v.expediente_id = ?
        ORDER BY vv.id DESC
        LIMIT 1
        """,
        (expediente_id,),
    ).fetchone()
    if not visita_legacy:
        return {columna: "" for columna in columnas_legacy}
    columnas_fila = set(visita_legacy.keys())
    return {
        columna: limpiar_texto(visita_legacy[columna]) if columna in columnas_fila else ""
        for columna in columnas_legacy
    }


def upsert_valoracion_expediente(cur, expediente_id: int, valores: dict):
    columnas_disponibles = get_table_columns("valoracion_expediente")
    columnas = [
        campo
        for campo in VALORACION_EXPEDIENTE_FORM_FIELDS
        if campo in columnas_disponibles
    ]
    valores_limpios = {
        campo: (
            1
            if campo in VALORACION_EXPEDIENTE_CHECKBOX_FIELDS
            and valores.get(campo) == "1"
            else 0
            if campo in VALORACION_EXPEDIENTE_CHECKBOX_FIELDS
            else limpiar_texto(valores.get(campo))
        )
        for campo in columnas
    }
    insert_columns = ["expediente_id"] + columnas
    placeholders = ", ".join(["?"] * len(insert_columns))
    updates = ", ".join(
        [f"{campo}=excluded.{campo}" for campo in columnas]
        + ["updated_at=CURRENT_TIMESTAMP"]
    )
    cur.execute(
        f"""
        INSERT INTO valoracion_expediente ({", ".join(insert_columns)})
        VALUES ({placeholders})
        ON CONFLICT(expediente_id) DO UPDATE SET {updates}
        """,
        [expediente_id] + [valores_limpios[campo] for campo in columnas],
    )


def valoracion_visita_observaciones_form_vacio():
    return {campo: "" for campo in VALORACION_VISITA_OBSERVACIONES_FIELDS}


def cargar_valoracion_visita_observaciones_form(cur, visita_id: int):
    return fila_a_dict(
        cur.execute(
            "SELECT * FROM valoracion_visita_observaciones WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        VALORACION_VISITA_OBSERVACIONES_FIELDS,
    )


def cargar_valoracion_visita_observaciones_legacy(cur, visita_id: int):
    legacy = cur.execute(
        """
        SELECT *
        FROM valoracion_visita
        WHERE visita_id = ?
        """,
        (visita_id,),
    ).fetchone()
    if not legacy:
        return valoracion_visita_observaciones_form_vacio()
    columnas = set(legacy.keys())
    return {
        "estado_observado": limpiar_texto(legacy["estado_inmueble"])
        if "estado_inmueble" in columnas
        else limpiar_texto(legacy["estado_conservacion"])
        if "estado_conservacion" in columnas
        else "",
        "reforma_observada": "",
        "ocupacion_observada": limpiar_texto(legacy["regimen_ocupacion"])
        if "regimen_ocupacion" in columnas
        else limpiar_texto(legacy["situacion_ocupacion"])
        if "situacion_ocupacion" in columnas
        else "",
        "observaciones_inspeccion_valoracion": limpiar_texto(
            legacy["observaciones_valoracion"]
        )
        if "observaciones_valoracion" in columnas
        else "",
        "incidencias_valoracion": "",
        "comprobaciones_fisicas": "",
    }


def upsert_valoracion_visita_observaciones(
    cur,
    visita_id: int,
    expediente_id: int,
    valores: dict,
):
    columnas_disponibles = get_table_columns("valoracion_visita_observaciones")
    columnas = [
        campo
        for campo in VALORACION_VISITA_OBSERVACIONES_FIELDS
        if campo in columnas_disponibles
    ]
    valores_limpios = {campo: limpiar_texto(valores.get(campo)) for campo in columnas}
    insert_columns = ["visita_id", "expediente_id"] + columnas
    placeholders = ", ".join(["?"] * len(insert_columns))
    updates = ", ".join(
        [f"{campo}=excluded.{campo}" for campo in columnas]
        + ["expediente_id=excluded.expediente_id", "updated_at=CURRENT_TIMESTAMP"]
    )
    cur.execute(
        f"""
        INSERT INTO valoracion_visita_observaciones ({", ".join(insert_columns)})
        VALUES ({placeholders})
        ON CONFLICT(visita_id) DO UPDATE SET {updates}
        """,
        [visita_id, expediente_id] + [valores_limpios[campo] for campo in columnas],
    )


def testigo_valoracion_form_vacio():
    valores = {campo: "" for campo in TESTIGO_VALORACION_FORM_FIELDS}
    valores["reutilizable"] = "1"
    valores["validacion_estado"] = "pendiente"
    return valores


def normalizar_valor_testigo(campo: str, valor):
    if campo in TESTIGO_VALORACION_CHECKBOX_FIELDS:
        return 1 if limpiar_texto(valor) == "1" else 0
    if campo in TESTIGO_VALORACION_INTEGER_FIELDS:
        return parse_optional_int(valor)
    if campo in TESTIGO_VALORACION_NUMERIC_FIELDS:
        return parsear_float(valor)
    return limpiar_texto(valor)


def formatear_numero_es(valor, decimales: int = 0) -> str:
    numero = parsear_float(valor)
    if numero is None:
        return "—"
    texto = f"{numero:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatear_moneda_es(valor) -> str:
    return f"{formatear_numero_es(valor, 0)} €" if parsear_float(valor) is not None else "—"


def formatear_precio_unitario_es(valor) -> str:
    return f"{formatear_numero_es(valor, 0)} €/m²" if parsear_float(valor) is not None else "—"


def formatear_superficie_es(valor) -> str:
    return f"{formatear_numero_es(valor, 2)} m²" if parsear_float(valor) is not None else "—"


def formatear_booleano_es(valor) -> str:
    return "Sí" if str(valor or "").strip() in {"1", "true", "True", "sí", "Sí"} else "No"


def formatear_coeficiente_es(valor) -> str:
    numero = parsear_float(valor)
    if numero is None:
        return "—"
    return f"{formatear_numero_es(numero, 2)}x"


def enriquecer_testigo_valoracion(testigo: dict) -> dict:
    item = dict(testigo)
    preparado = preparar_testigo_comparacion(item)
    if not item.get("precio_unitario_inicial"):
        item["precio_unitario_inicial"] = preparado["precio_unitario_inicial"]
    item["advertencias_calculo"] = preparado["advertencias_calculo"]
    item["precio_oferta_fmt"] = formatear_moneda_es(item.get("precio_oferta"))
    item["precio_depurado_fmt"] = formatear_moneda_es(item.get("precio_depurado"))
    item["precio_cierre_fmt"] = formatear_moneda_es(item.get("precio_cierre"))
    item["valor_unitario_fmt"] = formatear_precio_unitario_es(item.get("valor_unitario"))
    item["precio_unitario_inicial_fmt"] = formatear_precio_unitario_es(
        item.get("precio_unitario_inicial")
    )
    item["superficie_tomada_fmt"] = formatear_superficie_es(
        item.get("superficie_tomada")
    )
    item["superficie_construida_fmt"] = formatear_superficie_es(
        item.get("superficie_construida")
    )
    item["superficie_util_fmt"] = formatear_superficie_es(item.get("superficie_util"))
    item["superficie_otros_usos_fmt"] = formatear_superficie_es(
        item.get("superficie_otros_usos")
    )
    item["reutilizable_fmt"] = formatear_booleano_es(item.get("reutilizable"))
    item["visitado_fmt"] = formatear_booleano_es(item.get("visitado"))
    item["dato_verificado_fmt"] = formatear_booleano_es(item.get("dato_verificado"))
    item["testigo_visitado_fmt"] = formatear_booleano_es(item.get("testigo_visitado"))
    item["ascensor_fmt"] = formatear_booleano_es(item.get("ascensor"))
    item["garaje_fmt"] = formatear_booleano_es(item.get("garaje"))
    item["trastero_fmt"] = formatear_booleano_es(item.get("trastero"))
    item["terraza_fmt"] = formatear_booleano_es(item.get("terraza"))
    item["foto_url"] = (
        f"/uploads/{item['primera_foto']}"
        if limpiar_texto(item.get("primera_foto"))
        else ""
    )
    return item


def enriquecer_vinculo_testigo_valoracion(vinculo: dict) -> dict:
    item = dict(vinculo)
    preparado = preparar_testigo_comparacion(item)
    if not item.get("precio_unitario_inicial"):
        item["precio_unitario_inicial"] = preparado["precio_unitario_inicial"]
    item["advertencias_calculo"] = preparado["advertencias_calculo"]
    item["valor_unitario_base_fmt"] = formatear_precio_unitario_es(
        item.get("valor_unitario_base") or item.get("valor_unitario")
    )
    item["valor_unitario_ajustado_fmt"] = formatear_precio_unitario_es(
        item.get("valor_unitario_ajustado")
    )
    item["coeficiente_total_fmt"] = formatear_coeficiente_es(
        item.get("coeficiente_total")
    )
    item["precio_oferta_fmt"] = formatear_moneda_es(item.get("precio_oferta"))
    item["precio_depurado_fmt"] = formatear_moneda_es(item.get("precio_depurado"))
    item["precio_unitario_inicial_fmt"] = formatear_precio_unitario_es(
        item.get("precio_unitario_inicial")
    )
    item["superficie_tomada_fmt"] = formatear_superficie_es(
        item.get("superficie_tomada")
    )
    item["superficie_construida_fmt"] = formatear_superficie_es(
        item.get("superficie_construida")
    )
    item["superficie_util_fmt"] = formatear_superficie_es(item.get("superficie_util"))
    return item


def valores_testigo_desde_form(form) -> dict:
    valores = {
        campo: normalizar_valor_testigo(
            campo,
            form.get(campo, "1" if campo == "reutilizable" else ""),
        )
        for campo in TESTIGO_VALORACION_FORM_FIELDS
    }
    preparado = preparar_testigo_comparacion(valores)
    if "precio_unitario_inicial" in TESTIGO_VALORACION_FORM_FIELDS:
        valores["precio_unitario_inicial"] = preparado["precio_unitario_inicial"]
    return valores


def cargar_testigo_valoracion_form(cur, testigo_id: int, user_id: int):
    testigo = get_owned_testigo_valoracion(cur, testigo_id, user_id)
    require_row(testigo, "Testigo no encontrado")
    return testigo, fila_a_dict(testigo, TESTIGO_VALORACION_FORM_FIELDS)


def snapshot_testigo_valoracion(testigo) -> str:
    datos = {
        campo: limpiar_texto(testigo[campo])
        for campo in TESTIGO_VALORACION_FORM_FIELDS
        if campo in testigo.keys()
    }
    return json.dumps(datos, ensure_ascii=False, sort_keys=True)


def cargar_testigos_valoracion_usuario(cur, user_id: int, solo_reutilizables: bool = False):
    filtro_reutilizable = "AND COALESCE(reutilizable, 1) = 1" if solo_reutilizables else ""
    return cur.execute(
        f"""
        SELECT *
        FROM testigos_valoracion
        WHERE owner_user_id = ?
        {filtro_reutilizable}
        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
        """,
        (user_id,),
    ).fetchall()


def cargar_opciones_filtro_testigos_valoracion(cur, user_id: int) -> dict:
    opciones = {}
    for campo in (
        "tipologia",
        "municipio",
        "validacion_estado",
        "fuente_testigo",
        "fiabilidad_dato",
    ):
        opciones[campo] = [
            row[campo]
            for row in cur.execute(
                f"""
                SELECT DISTINCT {campo}
                FROM testigos_valoracion
                WHERE owner_user_id = ?
                  AND COALESCE({campo}, '') != ''
                ORDER BY {campo} COLLATE NOCASE ASC
                """,
                (user_id,),
            ).fetchall()
        ]
    return opciones


def biblioteca_testigos_valor_orden(testigo: dict, ordenar: str):
    if ordenar == "fecha":
        return (False, limpiar_texto(testigo.get("fecha_testigo")))
    if ordenar == "unitario":
        valor = parsear_float(testigo.get("precio_unitario_inicial"))
        return (valor is None, valor or 0)
    if ordenar == "precio":
        valor = parsear_float(testigo.get("precio_depurado") or testigo.get("precio_oferta"))
        return (valor is None, valor or 0)
    if ordenar == "superficie":
        valor = parsear_float(
            testigo.get("superficie_tomada") or testigo.get("superficie_construida")
        )
        return (valor is None, valor or 0)
    if ordenar == "fiabilidad":
        texto = limpiar_texto(testigo.get("fiabilidad_dato")).lower()
        return (False, WORKBENCH_FIABILIDAD_RANK.get(texto, 0), texto)
    return (False, limpiar_texto(testigo.get("direccion_testigo")).lower())


def ordenar_biblioteca_testigos(testigos: list[dict], ordenar: str, direccion: str) -> list[dict]:
    con_valor = []
    sin_valor = []
    for testigo in testigos:
        valor = biblioteca_testigos_valor_orden(testigo, ordenar)
        if valor[0]:
            sin_valor.append(testigo)
        else:
            con_valor.append((valor[1:], testigo))
    con_valor.sort(key=lambda item: item[0], reverse=direccion == "desc")
    return [item for _, item in con_valor] + sin_valor


def testigo_biblioteca_incompleto(testigo: dict) -> bool:
    return bool(testigo.get("advertencias_calculo")) or any(
        parsear_float(testigo.get(campo)) is None
        for campo in ("precio_oferta", "superficie_tomada", "precio_unitario_inicial")
    )


def diagnostico_biblioteca_testigos(testigos: list[dict]) -> dict:
    return {
        "total": len(testigos),
        "incompletos": sum(1 for item in testigos if testigo_biblioteca_incompleto(item)),
        "sin_fuente": sum(1 for item in testigos if not limpiar_texto(item.get("fuente_testigo"))),
        "sin_fecha": sum(1 for item in testigos if not limpiar_texto(item.get("fecha_testigo"))),
        "sin_precio_superficie": sum(
            1
            for item in testigos
            if parsear_float(item.get("precio_oferta") or item.get("precio_depurado")) is None
            or parsear_float(item.get("superficie_tomada")) is None
        ),
        "verificados": sum(1 for item in testigos if str(item.get("dato_verificado")) == "1"),
        "no_verificados": sum(
            1 for item in testigos if str(item.get("dato_verificado") or "0") != "1"
        ),
    }


def biblioteca_testigos_url(filtros: dict, ordenar: str, direccion: str, **overrides) -> str:
    params = {
        "municipio": filtros.get("municipio", ""),
        "tipologia": filtros.get("tipologia", ""),
        "fuente": filtros.get("fuente", ""),
        "fiabilidad": filtros.get("fiabilidad", ""),
        "verificacion": filtros.get("verificacion", ""),
        "incompletos": filtros.get("incompletos", ""),
        "expediente_id": filtros.get("expediente_id", ""),
        "ordenar": ordenar,
        "dir": direccion,
    }
    params.update(overrides)
    query = "&".join(
        f"{clave}={quote_plus(str(valor))}"
        for clave, valor in params.items()
        if limpiar_texto(valor)
    )
    return f"/valoracion/testigos/biblioteca?{query}" if query else "/valoracion/testigos/biblioteca"


def testigo_biblioteca_form_vacio(expediente_id: str = "") -> dict:
    return {
        "texto_anuncio_bruto": "",
        "url_fuente": "",
        "fuente_tipo": "Idealista",
        "fuente_testigo": "",
        "fecha_captura": datetime.now().date().isoformat(),
        "fecha_testigo": "",
        "referencia_testigo": "",
        "direccion_testigo": "",
        "codigo_postal": "",
        "municipio": "",
        "provincia": "",
        "tipologia": "",
        "precio_oferta": "",
        "precio_depurado": "",
        "superficie_tomada": "",
        "tipo_superficie_tomada": "construida",
        "superficie_construida": "",
        "superficie_util": "",
        "banos": "",
        "planta": "",
        "ascensor": "0",
        "es_exterior": "0",
        "balcon": "0",
        "terraza": "0",
        "patio": "0",
        "ano_construccion": "",
        "ano_reforma": "",
        "aire_acondicionado": "0",
        "tipo_calefaccion": "",
        "estado_conservacion": "",
        "certificacion_energetica": "",
        "garaje": "0",
        "trastero": "0",
        "fiabilidad_dato": "",
        "dato_verificado": "0",
        "observaciones": "",
        "expediente_id": limpiar_texto(expediente_id),
    }


def analisis_anuncio_vacio() -> dict:
    return {
        "ejecutado": False,
        "campos": {},
        "confianza": "baja",
        "advertencias": [],
    }


def _numero_texto_anuncio(valor: str):
    if not valor:
        return None
    texto = valor.replace(".", "").replace(" ", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def analizar_texto_anuncio_inmobiliario(texto: str) -> dict:
    texto_limpio = limpiar_texto(texto)
    if not texto_limpio:
        return {
            "ejecutado": True,
            "campos": {},
            "confianza": "baja",
            "advertencias": ["No se ha pegado texto suficiente para analizar."],
        }

    campos = {}
    advertencias = []
    texto_lower = texto_limpio.lower()
    for portal in TESTIGO_BIBLIOTECA_FUENTE_PRESETS:
        if portal != "Otro" and portal.lower() in texto_lower:
            campos["fuente_tipo"] = portal
            campos["fuente_testigo"] = portal
            break

    precio_match = re.search(
        r"(\d{2,3}(?:[.\s]\d{3})+|\d{5,7})(?:,\d{1,2})?\s*(?:€|eur)",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if precio_match:
        precio = _numero_texto_anuncio(precio_match.group(1))
        if precio is not None:
            campos["precio_oferta"] = str(int(precio))

    superficie_matches = list(re.finditer(
        r"(\d{2,4}(?:[,.]\d{1,2})?)\s*m(?:²|2)?\s*(construidos|útiles|utiles|registrales|catastrales)?",
        texto_limpio,
        flags=re.IGNORECASE,
    ))
    for superficie_match in superficie_matches:
        superficie = _numero_texto_anuncio(superficie_match.group(1))
        if superficie is None:
            continue
        superficie_valor = str(superficie).rstrip("0").rstrip(".")
        if "superficie_tomada" not in campos:
            campos["superficie_tomada"] = str(superficie).rstrip("0").rstrip(".")
        tipo_superficie = limpiar_texto(superficie_match.group(2)).lower()
        if "útil" in tipo_superficie or "util" in tipo_superficie:
            campos["superficie_util"] = superficie_valor
            campos["tipo_superficie_tomada"] = "util"
        elif "registral" in tipo_superficie:
            campos["tipo_superficie_tomada"] = "registral"
        elif "catastral" in tipo_superficie:
            campos["tipo_superficie_tomada"] = "catastral"
        elif tipo_superficie:
            campos["superficie_construida"] = superficie_valor
            campos["tipo_superficie_tomada"] = "construida"

    unitario_match = re.search(
        r"(\d{1,3}(?:[.\s]\d{3})+|\d{3,5})(?:,\d{1,2})?\s*(?:€\s*/\s*m(?:²|2)|€/m(?:²|2))",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if unitario_match:
        unitario = _numero_texto_anuncio(unitario_match.group(1))
        if unitario is not None:
            campos["precio_unitario_detectado"] = formatear_precio_unitario_es(unitario)

    habitaciones = re.search(
        r"(\d{1,2})\s*(?:hab\.?|habitaciones|dormitorios)",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    banos = re.search(
        r"(\d{1,2})\s*(?:baños|banos)",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    observaciones_detectadas = []
    if habitaciones:
        observaciones_detectadas.append(f"{habitaciones.group(1)} habitaciones detectadas")
    if banos:
        campos["banos"] = banos.group(1)
        observaciones_detectadas.append(f"{banos.group(1)} baños detectados")
    if observaciones_detectadas:
        campos["observaciones_detectadas"] = "; ".join(observaciones_detectadas) + "."

    planta_match = re.search(
        r"(\d{1,2})(?:ª|a|º|o)?\s*planta",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if planta_match:
        campos["planta"] = f"{planta_match.group(1)}ª"
    elif re.search(r"\bático\b|\batico\b", texto_lower):
        campos["planta"] = "ático"
    elif re.search(r"\bbajo\b", texto_lower):
        campos["planta"] = "bajo"

    if "sin ascensor" in texto_lower:
        campos["ascensor"] = "0"
    elif "con ascensor" in texto_lower or re.search(r"\bascensor\b", texto_lower):
        campos["ascensor"] = "1"
    if "exterior" in texto_lower:
        campos["es_exterior"] = "1"
    elif "interior" in texto_lower:
        campos["es_exterior"] = "0"
    if re.search(r"\bbalc[oó]n\b", texto_lower):
        campos["balcon"] = "1"
    if "terraza" in texto_lower:
        campos["terraza"] = "1"
    if re.search(r"\bpatio\b", texto_lower):
        campos["patio"] = "1"

    construido_match = re.search(
        r"construid[oa]\s+en\s+((?:19|20)\d{2})",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if construido_match:
        campos["ano_construccion"] = construido_match.group(1)
    reforma_match = re.search(
        r"reformad[oa]\s+en\s+((?:19|20)\d{2})",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if reforma_match:
        campos["ano_reforma"] = reforma_match.group(1)
    if re.search(r"\ba reformar\b", texto_lower):
        campos["estado_conservacion"] = "a reformar"
    elif "reformado" in texto_lower or "reformada" in texto_lower:
        campos["estado_conservacion"] = "reformado"
    elif "buen estado" in texto_lower:
        campos["estado_conservacion"] = "buen estado"
    if "aire acondicionado" in texto_lower:
        campos["aire_acondicionado"] = "1"
    calefaccion_match = re.search(
        r"calefacci[oó]n\s*(?:individual|central)?\s*[:\-]?\s*([A-Za-zÁÉÍÓÚÑáéíóúñ ]{3,40}?)(?=\s+(?:certificaci[oó]n|certificado|aire|precio|\d)|[.,;]|$)",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if calefaccion_match:
        campos["tipo_calefaccion"] = limpiar_texto(
            calefaccion_match.group(1)
        ).split(".")[0][:40]
    certificado_match = re.search(
        r"(?:certificaci[oó]n|certificado)\s+energ[eé]tic[ao]\s*[:\-]?\s*([A-G])\b",
        texto_limpio,
        flags=re.IGNORECASE,
    )
    if certificado_match:
        campos["certificacion_energetica"] = certificado_match.group(1).upper()

    lineas = [linea.strip() for linea in texto_limpio.splitlines() if linea.strip()]
    if lineas:
        primera_linea = lineas[0][:180]
        if not re.search(r"^\d", primera_linea):
            campos["referencia_testigo"] = primera_linea

    municipio_match = re.search(
        r"(?:municipio|localidad|en)\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\s]{2,40})",
        texto_limpio,
    )
    if municipio_match:
        municipio = limpiar_texto(municipio_match.group(1)).split(".")[0].strip()
        if 2 < len(municipio) <= 40:
            campos["municipio"] = municipio

    if "precio_oferta" not in campos:
        advertencias.append("No se ha detectado un precio claro.")
    if "superficie_tomada" not in campos:
        advertencias.append("No se ha detectado una superficie clara.")
    if "fuente_testigo" not in campos:
        advertencias.append("No se ha detectado portal/fuente de forma clara.")

    señales_fuertes = sum(
        1
        for campo in ("precio_oferta", "superficie_tomada", "fuente_testigo")
        if campo in campos
    )
    confianza = "alta" if señales_fuertes >= 3 else "media" if señales_fuertes == 2 else "baja"
    return {
        "ejecutado": True,
        "campos": campos,
        "confianza": confianza,
        "advertencias": advertencias,
    }


def aplicar_analisis_a_testigo_biblioteca(valores: dict, analisis: dict) -> dict:
    actualizados = dict(valores)
    for campo, valor in (analisis.get("campos") or {}).items():
        if campo in {"precio_unitario_detectado", "observaciones_detectadas"}:
            continue
        if campo in TESTIGO_BIBLIOTECA_BOOLEAN_FIELDS and campo in actualizados:
            if str(valor) == "1" and str(actualizados.get(campo)) != "1":
                actualizados[campo] = "1"
            elif str(valor) == "0" and not limpiar_texto(actualizados.get(campo)):
                actualizados[campo] = "0"
        elif campo in actualizados and not limpiar_texto(actualizados.get(campo)):
            actualizados[campo] = valor
    observacion_detectada = analisis.get("campos", {}).get("observaciones_detectadas")
    if observacion_detectada and not limpiar_texto(actualizados.get("observaciones")):
        actualizados["observaciones"] = observacion_detectada
    return actualizados


def normalizar_clave_duplicado(texto: str) -> str:
    texto = limpiar_texto(texto).lower()
    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def valores_cercanos(valor_a, valor_b, tolerancia: float = 0.05) -> bool:
    numero_a = parsear_float(valor_a)
    numero_b = parsear_float(valor_b)
    if numero_a is None or numero_b is None or numero_a <= 0 or numero_b <= 0:
        return False
    return abs(numero_a - numero_b) / max(numero_a, numero_b) <= tolerancia


def buscar_duplicados_testigo_biblioteca(cur, user_id: int, valores: dict) -> list[dict]:
    rows = cur.execute(
        """
        SELECT *
        FROM testigos_valoracion
        WHERE owner_user_id = ?
        ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
        """,
        (user_id,),
    ).fetchall()
    url = limpiar_texto(valores.get("url_fuente"))
    fuente = normalizar_clave_duplicado(valores.get("fuente_testigo") or valores.get("fuente_tipo"))
    referencia = normalizar_clave_duplicado(valores.get("referencia_testigo"))
    direccion = normalizar_clave_duplicado(valores.get("direccion_testigo"))
    municipio = normalizar_clave_duplicado(valores.get("municipio"))
    precio = valores.get("precio_depurado") or valores.get("precio_oferta")
    superficie = valores.get("superficie_tomada")
    candidatos = {}

    for row in rows:
        item = dict(row)
        motivos = []
        if url and limpiar_texto(item.get("url_fuente")) == url:
            motivos.append("Misma URL del anuncio.")
        item_fuente = normalizar_clave_duplicado(
            item.get("fuente_testigo") or item.get("fuente_tipo")
        )
        item_referencia = normalizar_clave_duplicado(item.get("referencia_testigo"))
        if fuente and referencia and item_fuente == fuente and item_referencia:
            if referencia == item_referencia or referencia in item_referencia or item_referencia in referencia:
                motivos.append("Misma fuente y referencia/título similar.")
        item_municipio = normalizar_clave_duplicado(item.get("municipio"))
        if (
            municipio
            and item_municipio == municipio
            and valores_cercanos(precio, item.get("precio_depurado") or item.get("precio_oferta"))
            and valores_cercanos(superficie, item.get("superficie_tomada"))
        ):
            motivos.append("Mismo municipio con precio y superficie parecidos.")
        item_direccion = normalizar_clave_duplicado(item.get("direccion_testigo"))
        if direccion and item_direccion and (
            direccion == item_direccion
            or direccion in item_direccion
            or item_direccion in direccion
        ):
            motivos.append("Dirección o zona similar.")
        if motivos:
            enriquecido = enriquecer_testigo_valoracion(item)
            candidatos[item["id"]] = {
                **enriquecido,
                "motivos_duplicado": motivos,
            }
    return list(candidatos.values())[:5]


def calcular_unitario_visual_testigo_biblioteca(valores: dict) -> str:
    precio = parsear_float(valores.get("precio_depurado") or valores.get("precio_oferta"))
    superficie = parsear_float(valores.get("superficie_tomada"))
    if precio is None or superficie is None or superficie <= 0:
        return "pendiente"
    return formatear_precio_unitario_es(precio / superficie)


def valores_testigo_biblioteca_desde_form(form) -> tuple[dict, list[str], list[str]]:
    valores = testigo_biblioteca_form_vacio(form.get("expediente_id", ""))
    for campo in valores.keys():
        if campo != "expediente_id":
            valores[campo] = limpiar_texto(form.get(campo))
    for campo in TESTIGO_BIBLIOTECA_BOOLEAN_FIELDS:
        if campo in valores:
            valores[campo] = "1" if form.get(campo) == "1" else "0"
    if not valores["fecha_captura"]:
        valores["fecha_captura"] = datetime.now().date().isoformat()
    if not valores["fecha_testigo"]:
        valores["fecha_testigo"] = valores["fecha_captura"]
    if valores["fuente_tipo"] != "Otro" and not valores["fuente_testigo"]:
        valores["fuente_testigo"] = valores["fuente_tipo"]

    errores = []
    avisos = []
    for campo, etiqueta in TESTIGO_BIBLIOTECA_NUMERIC_FIELDS.items():
        if valores[campo] and parsear_float(valores[campo]) is None:
            errores.append(f"{etiqueta} debe ser numérico.")
    for campo, etiqueta in TESTIGO_BIBLIOTECA_INTEGER_FIELDS.items():
        if valores[campo] and parse_optional_int(valores[campo]) is None:
            errores.append(f"{etiqueta} debe ser un número entero.")
    if valores["superficie_tomada"] and parsear_float(valores["superficie_tomada"]) == 0:
        errores.append("La superficie tomada debe ser mayor que cero.")
    if valores["url_fuente"]:
        parsed = urlparse(valores["url_fuente"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errores.append("La URL del anuncio debe empezar por http:// o https://.")
    if not valores["fuente_testigo"]:
        avisos.append("Fuente no informada; el testigo se guardará como dato pendiente.")
    return valores, errores, avisos


def insertar_testigo_biblioteca_rapido(cur, user_id: int, valores: dict) -> int:
    datos = {
        "owner_user_id": user_id,
        "url_fuente": valores["url_fuente"],
        "fuente_tipo": valores["fuente_tipo"],
        "fuente_testigo": valores["fuente_testigo"],
        "fecha_captura": valores["fecha_captura"],
        "fecha_testigo": valores["fecha_testigo"],
        "referencia_testigo": valores["referencia_testigo"],
        "direccion_testigo": valores["direccion_testigo"],
        "codigo_postal": valores["codigo_postal"],
        "municipio": valores["municipio"],
        "provincia": valores["provincia"],
        "tipologia": valores["tipologia"],
        "precio_oferta": parsear_float(valores["precio_oferta"]),
        "precio_depurado": parsear_float(valores["precio_depurado"]),
        "superficie_tomada": parsear_float(valores["superficie_tomada"]),
        "tipo_superficie_tomada": valores["tipo_superficie_tomada"],
        "superficie_construida": parsear_float(valores["superficie_construida"]),
        "superficie_util": parsear_float(valores["superficie_util"]),
        "banos": parse_optional_int(valores["banos"]),
        "planta": valores["planta"],
        "ascensor": 1 if valores["ascensor"] == "1" else 0,
        "es_exterior": 1 if valores["es_exterior"] == "1" else 0,
        "balcon": 1 if valores["balcon"] == "1" else 0,
        "terraza": 1 if valores["terraza"] == "1" else 0,
        "patio": 1 if valores["patio"] == "1" else 0,
        "ano_construccion": parse_optional_int(valores["ano_construccion"]),
        "ano_reforma": parse_optional_int(valores["ano_reforma"]),
        "aire_acondicionado": 1 if valores["aire_acondicionado"] == "1" else 0,
        "tipo_calefaccion": valores["tipo_calefaccion"],
        "estado_conservacion": valores["estado_conservacion"],
        "certificacion_energetica": valores["certificacion_energetica"],
        "garaje": 1 if valores["garaje"] == "1" else 0,
        "trastero": 1 if valores["trastero"] == "1" else 0,
        "fiabilidad_dato": valores["fiabilidad_dato"],
        "dato_verificado": 1 if valores["dato_verificado"] == "1" else 0,
        "observaciones": valores["observaciones"],
        "validacion_estado": "revisado" if valores["dato_verificado"] == "1" else "pendiente",
        "reutilizable": 1,
    }
    preparado = preparar_testigo_comparacion(datos)
    datos["precio_unitario_inicial"] = preparado["precio_unitario_inicial"]
    columnas_disponibles = get_table_columns("testigos_valoracion")
    datos = {
        clave: valor
        for clave, valor in datos.items()
        if clave in columnas_disponibles
    }
    columnas = list(datos.keys())
    placeholders = ", ".join(["?"] * len(columnas))
    cur.execute(
        f"""
        INSERT INTO testigos_valoracion ({", ".join(columnas)})
        VALUES ({placeholders})
        """,
        [datos[columna] for columna in columnas],
    )
    return cur.lastrowid


def primera_foto_testigo_valoracion(cur, testigo_id: int) -> str:
    foto = cur.execute(
        """
        SELECT archivo
        FROM testigos_valoracion_fotos
        WHERE testigo_id = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (testigo_id,),
    ).fetchone()
    return foto["archivo"] if foto is not None else ""


def enriquecer_testigos_con_foto(cur, testigos) -> list[dict]:
    enriquecidos = []
    for testigo in testigos:
        item = dict(testigo)
        item["primera_foto"] = primera_foto_testigo_valoracion(cur, item["id"])
        enriquecidos.append(enriquecer_testigo_valoracion(item))
    return enriquecidos


def cargar_fotos_testigo_valoracion(cur, testigo_id: int):
    fotos = [
        dict(row)
        for row in cur.execute(
            """
            SELECT id, testigo_id, archivo, descripcion, origen, created_at
            FROM testigos_valoracion_fotos
            WHERE testigo_id = ?
            ORDER BY id ASC
            """,
            (testigo_id,),
        ).fetchall()
    ]
    for foto in fotos:
        foto["url"] = f"/uploads/{foto['archivo']}"
    return fotos


def cargar_vinculos_testigo_valoracion(cur, testigo_id: int, user_id: int):
    return cur.execute(
        """
        SELECT vet.id,
               vet.expediente_id,
               vet.orden,
               vet.incluido,
               vet.notas_seleccion,
               vet.valor_unitario_base,
               vet.valor_unitario_ajustado,
               e.numero_expediente,
               e.cliente,
               e.direccion
        FROM valoracion_expediente_testigos vet
        JOIN expedientes e ON e.id = vet.expediente_id
        WHERE vet.testigo_id = ?
          AND e.owner_user_id = ?
        ORDER BY vet.created_at DESC, vet.id DESC
        """,
        (testigo_id, user_id),
    ).fetchall()


def cargar_testigos_expediente_valoracion(cur, expediente_id: int):
    return cur.execute(
        """
        SELECT vet.*,
               tv.direccion_testigo,
               tv.referencia_testigo,
               tv.fuente_testigo,
               tv.fecha_testigo,
               tv.precio_oferta,
               tv.precio_depurado,
               tv.precio_unitario_inicial,
               tv.superficie_tomada,
               tv.tipo_superficie_tomada,
               tv.valor_unitario,
               tv.superficie_construida,
               tv.superficie_util,
               tv.tipologia,
               tv.validacion_estado,
               tv.fiabilidad_dato,
               tv.similitud_inmueble,
               tv.observaciones,
               vta.ajuste_superficie_construida,
               vta.ajuste_ubicacion,
               vta.ajuste_antiguedad,
               vta.ajuste_calidades,
               vta.ajuste_caracteristicas_constructivas,
               vta.coeficiente_total,
               vta.justificacion
        FROM valoracion_expediente_testigos vet
        LEFT JOIN testigos_valoracion tv ON tv.id = vet.testigo_id
        LEFT JOIN valoracion_testigo_ajustes vta
          ON vta.expediente_testigo_id = vet.id
         AND COALESCE(vta.variable, '') = ''
        WHERE vet.expediente_id = ?
        ORDER BY COALESCE(vet.orden, 9999) ASC, vet.id ASC
        """,
        (expediente_id,),
    ).fetchall()


def siguiente_orden_testigo_expediente(cur, expediente_id: int) -> int:
    row = cur.execute(
        """
        SELECT COALESCE(MAX(orden), 0) + 1 AS siguiente
        FROM valoracion_expediente_testigos
        WHERE expediente_id = ?
        """,
        (expediente_id,),
    ).fetchone()
    return int(row["siguiente"] or 1)


def valoracion_testigo_ajustes_vacio():
    valores = {campo: "0" for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS}
    valores["coeficiente_total"] = ""
    valores["justificacion"] = ""
    return valores


def cargar_valoracion_testigo_ajustes(cur, vinculo_id: int):
    fila = cur.execute(
        """
        SELECT *
        FROM valoracion_testigo_ajustes
        WHERE expediente_testigo_id = ?
          AND COALESCE(variable, '') = ''
        """,
        (vinculo_id,),
    ).fetchone()
    if not fila:
        return valoracion_testigo_ajustes_vacio()
    valores = fila_a_dict(
        fila,
        [campo for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS]
        + ["coeficiente_total", "justificacion"],
    )
    for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS:
        valores[campo] = valores.get(campo) or "0"
    return valores


def parsear_ajuste_valoracion(campo: str, valor) -> float:
    texto = limpiar_texto(valor)
    ajuste = parsear_float(texto) if texto else 0.0
    if ajuste is None or ajuste < -0.20 or ajuste > 0.20:
        raise ValueError(f"El ajuste {campo} debe estar entre -0.20 y 0.20.")
    return ajuste


def valores_ajustes_desde_form(form) -> dict:
    valores = {
        campo: parsear_ajuste_valoracion(campo, form.get(campo))
        for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS
    }
    valores["justificacion"] = limpiar_texto(form.get("justificacion"))
    valores["coeficiente_total"] = 1 + sum(
        valores[campo] for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS
    )
    return valores


def upsert_valoracion_testigo_ajustes(cur, vinculo, valores: dict):
    columnas = [campo for campo, _ in VALORACION_TESTIGO_AJUSTES_ITEMS]
    existente = cur.execute(
        """
        SELECT id
        FROM valoracion_testigo_ajustes
        WHERE expediente_testigo_id = ?
          AND COALESCE(variable, '') = ''
        """,
        (vinculo["id"],),
    ).fetchone()
    if existente:
        assignments = ", ".join([f"{campo}=?" for campo in columnas])
        cur.execute(
            f"""
            UPDATE valoracion_testigo_ajustes
            SET {assignments}, coeficiente_total = ?, justificacion = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [valores[campo] for campo in columnas]
            + [valores["coeficiente_total"], valores["justificacion"], existente["id"]],
        )
    else:
        insert_columns = ["expediente_testigo_id"] + columnas + [
            "coeficiente_total",
            "justificacion",
        ]
        placeholders = ", ".join(["?"] * len(insert_columns))
        cur.execute(
            f"""
            INSERT INTO valoracion_testigo_ajustes ({", ".join(insert_columns)})
            VALUES ({placeholders})
            """,
            [vinculo["id"]]
            + [valores[campo] for campo in columnas]
            + [valores["coeficiente_total"], valores["justificacion"]],
        )

    valor_unitario_base = parsear_float(vinculo["valor_unitario_base"])
    valor_unitario_ajustado = (
        round(valor_unitario_base * valores["coeficiente_total"], 2)
        if valor_unitario_base is not None
        else None
    )
    cur.execute(
        """
        UPDATE valoracion_expediente_testigos
        SET valor_unitario_ajustado = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (valor_unitario_ajustado, vinculo["id"]),
    )
    return valor_unitario_ajustado


def ajuste_homogeneizacion_vacio() -> dict:
    return {
        "id": "",
        "variable": "superficie",
        "variable_otro": "",
        "valor_inmueble": "",
        "valor_testigo": "",
        "tipo_ajuste": "porcentaje",
        "ajuste_porcentaje": "",
        "ajuste_importe_m2": "",
        "signo": "+",
        "justificacion": "",
        "orden": "",
        "activo": "1",
    }


def row_ajuste_homogeneizacion(row) -> dict:
    item = dict(row)
    item["activo_fmt"] = formatear_booleano_es(item.get("activo"))
    porcentaje = parsear_float(item.get("ajuste_porcentaje"))
    item["ajuste_porcentaje_fmt"] = (
        f"{formatear_numero_es(porcentaje * 100, 2)}%" if porcentaje is not None else "—"
    )
    item["ajuste_importe_m2_fmt"] = formatear_precio_unitario_es(
        item.get("ajuste_importe_m2")
    )
    return item


def cargar_ajustes_homogeneizacion(cur, vinculo_id: int) -> list[dict]:
    return [
        row_ajuste_homogeneizacion(row)
        for row in cur.execute(
            """
            SELECT *
            FROM valoracion_testigo_ajustes
            WHERE expediente_testigo_id = ?
              AND COALESCE(variable, '') != ''
            ORDER BY COALESCE(orden, 9999) ASC, id ASC
            """,
            (vinculo_id,),
        ).fetchall()
    ]


def get_owned_ajuste_homogeneizacion(
    cur,
    ajuste_id: int,
    vinculo_id: int,
    expediente_id: int,
    user_id: int,
):
    return cur.execute(
        """
        SELECT vta.*
        FROM valoracion_testigo_ajustes vta
        JOIN valoracion_expediente_testigos vet ON vet.id = vta.expediente_testigo_id
        JOIN expedientes e ON e.id = vet.expediente_id
        WHERE vta.id = ?
          AND vta.expediente_testigo_id = ?
          AND vet.expediente_id = ?
          AND e.owner_user_id = ?
          AND COALESCE(vta.variable, '') != ''
        """,
        (ajuste_id, vinculo_id, expediente_id, user_id),
    ).fetchone()


def valores_homogeneizacion_desde_form(form) -> dict:
    tipo = limpiar_texto(form.get("tipo_ajuste")) or "porcentaje"
    signo = limpiar_texto(form.get("signo")) or "+"
    if tipo == "cualitativo_no_cuantificado":
        signo = ""
    return {
        "variable": limpiar_texto(form.get("variable")) or "otro",
        "variable_otro": limpiar_texto(form.get("variable_otro")),
        "valor_inmueble": limpiar_texto(form.get("valor_inmueble")),
        "valor_testigo": limpiar_texto(form.get("valor_testigo")),
        "tipo_ajuste": tipo,
        "ajuste_porcentaje": parsear_float(form.get("ajuste_porcentaje")),
        "ajuste_importe_m2": parsear_float(form.get("ajuste_importe_m2")),
        "signo": signo,
        "justificacion": limpiar_texto(form.get("justificacion")),
        "orden": parse_optional_int(form.get("orden")),
        "activo": 1 if form.get("activo", "1") == "1" else 0,
    }


def insertar_ajuste_homogeneizacion(cur, vinculo, valores: dict):
    cur.execute(
        """
        INSERT INTO valoracion_testigo_ajustes (
            expediente_testigo_id, expediente_id, testigo_id, variable,
            variable_otro, valor_inmueble, valor_testigo, tipo_ajuste,
            ajuste_porcentaje, ajuste_importe_m2, signo, justificacion,
            orden, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vinculo["id"],
            vinculo["expediente_id"],
            vinculo["testigo_id"],
            valores["variable"],
            valores["variable_otro"],
            valores["valor_inmueble"],
            valores["valor_testigo"],
            valores["tipo_ajuste"],
            valores["ajuste_porcentaje"],
            valores["ajuste_importe_m2"],
            valores["signo"],
            valores["justificacion"],
            valores["orden"],
            valores["activo"],
        ),
    )


def actualizar_ajuste_homogeneizacion(cur, ajuste_id: int, valores: dict):
    cur.execute(
        """
        UPDATE valoracion_testigo_ajustes
        SET variable = ?, variable_otro = ?, valor_inmueble = ?,
            valor_testigo = ?, tipo_ajuste = ?, ajuste_porcentaje = ?,
            ajuste_importe_m2 = ?, signo = ?, justificacion = ?,
            orden = ?, activo = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            valores["variable"],
            valores["variable_otro"],
            valores["valor_inmueble"],
            valores["valor_testigo"],
            valores["tipo_ajuste"],
            valores["ajuste_porcentaje"],
            valores["ajuste_importe_m2"],
            valores["signo"],
            valores["justificacion"],
            valores["orden"],
            valores["activo"],
            ajuste_id,
        ),
    )


def resumen_homogeneizacion_vinculo(vinculo, ajustes: list[dict]) -> dict:
    testigo = {
        "precio_unitario_inicial": vinculo.get("precio_unitario_inicial")
        or vinculo.get("valor_unitario_base")
        or vinculo.get("valor_unitario"),
    }
    resumen = preparar_matriz_homogeneizacion(testigo, ajustes)
    resumen["unitario_inicial_fmt"] = formatear_precio_unitario_es(
        resumen.get("unitario_inicial")
    )
    resumen["unitario_homogeneizado_fmt"] = formatear_precio_unitario_es(
        resumen.get("unitario_homogeneizado")
    )
    resumen["ajuste_total_importe_m2_fmt"] = formatear_precio_unitario_es(
        resumen.get("ajuste_total_importe_m2")
    )
    porcentaje = resumen.get("ajuste_total_porcentaje_equivalente")
    resumen["ajuste_total_porcentaje_equivalente_fmt"] = (
        f"{formatear_numero_es(porcentaje * 100, 2)}%"
        if porcentaje is not None
        else "—"
    )
    return resumen


def enriquecer_ponderacion_vinculo_valoracion(vinculo: dict, resumen: dict) -> dict:
    item = dict(vinculo)
    item["incluido_calculo"] = (
        item.get("incluido_calculo") if item.get("incluido_calculo") is not None else 1
    )
    item["unitario_homogeneizado"] = resumen.get("unitario_homogeneizado")
    item["unitario_inicial"] = resumen.get("unitario_inicial")
    item["unitario_para_resumen"] = (
        resumen.get("unitario_homogeneizado") or resumen.get("unitario_inicial")
    )
    item["unitario_homogeneizado_fmt"] = resumen.get("unitario_homogeneizado_fmt")
    item["unitario_para_resumen_fmt"] = formatear_precio_unitario_es(
        item.get("unitario_para_resumen")
    )
    item["peso_porcentaje_fmt"] = (
        f"{formatear_numero_es(item.get('peso_porcentaje'), 2)}%"
        if item.get("peso_porcentaje") is not None
        else "—"
    )
    return item


def preparar_resumen_comparacion_vinculos(cur, vinculados) -> dict:
    items = []
    for row in vinculados or []:
        vinculo = dict(row)
        ajustes = cargar_ajustes_homogeneizacion(cur, vinculo["id"])
        resumen = resumen_homogeneizacion_vinculo(vinculo, ajustes)
        items.append(enriquecer_ponderacion_vinculo_valoracion(vinculo, resumen))
    resumen_comparacion = preparar_resumen_comparacion(items)
    resumen_comparacion["unitario_minimo_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("unitario_minimo")
    )
    resumen_comparacion["unitario_maximo_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("unitario_maximo")
    )
    resumen_comparacion["unitario_medio_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("unitario_medio")
    )
    resumen_comparacion["unitario_mediana_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("unitario_mediana")
    )
    resumen_comparacion["unitario_ponderado_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("unitario_ponderado")
    )
    resumen_comparacion["propuesta_unitaria_orientativa_fmt"] = formatear_precio_unitario_es(
        resumen_comparacion.get("propuesta_unitaria_orientativa")
    )
    resumen_comparacion["suma_pesos_fmt"] = (
        f"{formatear_numero_es(resumen_comparacion.get('suma_pesos'), 2)}%"
        if resumen_comparacion.get("suma_pesos") is not None
        else "—"
    )
    return {"items": items, "resumen": resumen_comparacion}


WORKBENCH_FILTROS = {"todos", "incluidos", "excluidos", "advertencias", "incompletos"}
WORKBENCH_ORDENES = {"homogeneizado", "peso", "similitud", "fiabilidad", "fecha"}
WORKBENCH_REPRESENTATIVIDAD_VALUES = {
    valor for valor, _ in REPRESENTATIVIDAD_VALORACION_OPTIONS
}
WORKBENCH_SIMILITUD_RANK = {"alta": 4, "media_alta": 3, "media": 2, "baja": 1}
WORKBENCH_FIABILIDAD_RANK = {"alta": 4, "media_alta": 3, "media": 2, "baja": 1}


def workbench_comparable_id(comparable: dict) -> str:
    return limpiar_texto(
        comparable.get("testigo_id")
        or comparable.get("expediente_testigo_id")
        or comparable.get("id")
    )


def workbench_comparable_incluido(comparable: dict) -> bool:
    valor = comparable.get("incluido_calculo")
    if valor is None or valor == "":
        valor = 1
    return str(valor).strip().lower() not in {
        "0",
        "false",
        "no",
    }


def workbench_comparable_incompleto(comparable: dict) -> bool:
    return parsear_float(comparable.get("unitario_homogeneizado")) is None


def workbench_comparable_advertencias(comparable: dict) -> list[str]:
    return (
        list(comparable.get("advertencias_calculo") or [])
        + list(comparable.get("advertencias_homogeneizacion") or [])
        + list(comparable.get("advertencias_tecnicas") or [])
    )


def cargar_fotos_workbench_testigos(
    cur,
    testigo_ids: list[int],
    owner_user_id: int,
) -> dict[int, list[dict]]:
    ids = set()
    for testigo_id in testigo_ids:
        if not testigo_id:
            continue
        try:
            ids.add(int(testigo_id))
        except (TypeError, ValueError):
            continue
    ids = sorted(ids)
    if not ids:
        return {}
    placeholders = ", ".join(["?"] * len(ids))
    fotos_por_testigo = {testigo_id: [] for testigo_id in ids}
    filas = cur.execute(
        f"""
        SELECT f.id, f.testigo_id, f.archivo, f.descripcion, f.origen, f.created_at
        FROM testigos_valoracion_fotos f
        INNER JOIN testigos_valoracion tv ON tv.id = f.testigo_id
        WHERE f.testigo_id IN ({placeholders})
          AND tv.owner_user_id = ?
        ORDER BY f.testigo_id ASC, f.id ASC
        """,
        ids + [owner_user_id],
    ).fetchall()
    for fila in filas:
        foto = dict(fila)
        foto["url"] = f"/uploads/{foto['archivo']}"
        fotos_por_testigo.setdefault(foto["testigo_id"], []).append(foto)
    return fotos_por_testigo


def enriquecer_comparables_workbench_con_fotos(
    comparables: list[dict],
    fotos_por_testigo: dict[int, list[dict]],
) -> list[dict]:
    for comparable in comparables:
        testigo_id = comparable.get("testigo_id")
        try:
            testigo_id_int = int(testigo_id)
        except (TypeError, ValueError):
            testigo_id_int = 0
        fotos = fotos_por_testigo.get(testigo_id_int, [])
        comparable["fotos_testigo"] = fotos
        comparable["fotos_count"] = len(fotos)
        comparable["primera_foto_url"] = fotos[0]["url"] if fotos else ""
    return comparables


def workbench_trazabilidad_homogeneizacion(comparable: dict) -> dict:
    if not comparable:
        return {}

    unitario_inicial = parsear_float(
        comparable.get("unitario_inicial")
        or comparable.get("precio_unitario_inicial")
        or comparable.get("valor_unitario_base")
    )
    unitario_homogeneizado = parsear_float(comparable.get("unitario_homogeneizado"))
    pasos = list(comparable.get("pasos_homogeneizacion") or [])
    pasos_contexto = []
    subtotal_efectos = 0.0
    subtotal_calculable = unitario_inicial is not None and bool(pasos)
    avisos_incompleto = []

    if unitario_inicial is None:
        avisos_incompleto.append("Falta €/m² inicial para reconstruir la trazabilidad.")
    if unitario_homogeneizado is None:
        avisos_incompleto.append("Falta €/m² homogeneizado mostrado.")
    if not pasos:
        avisos_incompleto.append("No hay ajustes activos trazables para este testigo.")

    for paso in pasos:
        tipo = limpiar_texto(paso.get("tipo_ajuste"))
        variable = limpiar_texto(paso.get("variable")) or "ajuste"
        variable_label = variable.replace("_", " ").capitalize()
        porcentaje = parsear_float(paso.get("ajuste_porcentaje"))
        importe = parsear_float(paso.get("ajuste_importe_m2"))
        efecto = parsear_float(paso.get("efecto_importe_m2"))
        if tipo == "porcentaje" and porcentaje is None:
            subtotal_calculable = False
            avisos_incompleto.append(f"Ajuste porcentual sin porcentaje en {variable_label}.")
        if tipo == "importe_m2" and importe is None:
            subtotal_calculable = False
            avisos_incompleto.append(f"Ajuste por importe €/m² sin importe en {variable_label}.")
        if tipo in {"porcentaje", "importe_m2"} and efecto is None:
            subtotal_calculable = False
            avisos_incompleto.append(f"Ajuste cuantificado sin efecto €/m² en {variable_label}.")
        if efecto is not None:
            subtotal_efectos += efecto
        pasos_contexto.append(
            {
                "variable": variable_label,
                "tipo_ajuste": tipo,
                "tipo_label": {
                    "porcentaje": "Porcentaje",
                    "importe_m2": "Importe €/m²",
                    "cualitativo_no_cuantificado": "Cualitativo no cuantificado",
                }.get(tipo, tipo.replace("_", " ").capitalize() or "Ajuste"),
                "porcentaje_fmt": (
                    f"{formatear_numero_es(porcentaje * 100, 2)}%"
                    if porcentaje is not None
                    else "—"
                ),
                "importe_m2_fmt": formatear_precio_unitario_es(importe),
                "efecto_fmt": formatear_precio_unitario_es(efecto),
                "unitario_antes_fmt": formatear_precio_unitario_es(
                    paso.get("unitario_antes")
                ),
                "unitario_despues_fmt": formatear_precio_unitario_es(
                    paso.get("unitario_despues")
                ),
                "valor_inmueble": limpiar_texto(paso.get("valor_inmueble")),
                "valor_testigo": limpiar_texto(paso.get("valor_testigo")),
                "justificacion": limpiar_texto(paso.get("justificacion")),
                "es_cualitativo": tipo == "cualitativo_no_cuantificado",
            }
        )

    subtotal_calculado = (
        unitario_inicial + subtotal_efectos if subtotal_calculable else None
    )
    diferencia = (
        subtotal_calculado - unitario_homogeneizado
        if subtotal_calculado is not None and unitario_homogeneizado is not None
        else None
    )
    discrepancia = diferencia is not None and abs(diferencia) > 0.01
    return {
        "unitario_inicial": unitario_inicial,
        "unitario_inicial_fmt": formatear_precio_unitario_es(unitario_inicial),
        "subtotal_efectos": subtotal_efectos if pasos else None,
        "subtotal_efectos_fmt": formatear_precio_unitario_es(
            subtotal_efectos if pasos else None
        ),
        "subtotal_calculado": subtotal_calculado,
        "subtotal_calculado_fmt": formatear_precio_unitario_es(subtotal_calculado),
        "unitario_homogeneizado": unitario_homogeneizado,
        "unitario_homogeneizado_fmt": formatear_precio_unitario_es(
            unitario_homogeneizado
        ),
        "diferencia": diferencia,
        "diferencia_fmt": formatear_precio_unitario_es(diferencia),
        "discrepancia": discrepancia,
        "incompleto": bool(avisos_incompleto),
        "avisos_incompleto": avisos_incompleto,
        "pasos": pasos_contexto,
    }


def workbench_filtrar_comparables(comparables: list[dict], filtro: str) -> list[dict]:
    if filtro == "incluidos":
        return [item for item in comparables if workbench_comparable_incluido(item)]
    if filtro == "excluidos":
        return [item for item in comparables if not workbench_comparable_incluido(item)]
    if filtro == "advertencias":
        return [item for item in comparables if workbench_comparable_advertencias(item)]
    if filtro == "incompletos":
        return [item for item in comparables if workbench_comparable_incompleto(item)]
    return list(comparables)


def workbench_orden_valor(comparable: dict, ordenar: str):
    if ordenar == "homogeneizado":
        valor = parsear_float(comparable.get("unitario_homogeneizado"))
        return (valor is None, valor or 0)
    if ordenar == "peso":
        valor = parsear_float(comparable.get("peso_porcentaje"))
        return (valor is None, valor or 0)
    if ordenar == "similitud":
        texto = limpiar_texto(comparable.get("similitud_inmueble")).lower()
        return (False, WORKBENCH_SIMILITUD_RANK.get(texto, 0), texto)
    if ordenar == "fiabilidad":
        texto = limpiar_texto(comparable.get("fiabilidad_dato")).lower()
        return (False, WORKBENCH_FIABILIDAD_RANK.get(texto, 0), texto)
    if ordenar == "fecha":
        return (False, limpiar_texto(comparable.get("fecha_testigo")))
    return (False, comparable.get("orden") or 0)


def workbench_ordenar_comparables(
    comparables: list[dict],
    ordenar: str,
    direccion: str,
) -> list[dict]:
    con_valor = []
    sin_valor = []
    for comparable in comparables:
        valor = workbench_orden_valor(comparable, ordenar)
        if valor[0]:
            sin_valor.append(comparable)
        else:
            con_valor.append((valor[1:], comparable))
    con_valor.sort(key=lambda item: item[0], reverse=direccion == "desc")
    return [item for _, item in con_valor] + sin_valor


def workbench_diagnostico(comparables: list[dict]) -> dict:
    unitarios = [
        parsear_float(comparable.get("unitario_homogeneizado"))
        for comparable in comparables
    ]
    unitarios = [valor for valor in unitarios if valor is not None]
    minimo = min(unitarios) if unitarios else None
    maximo = max(unitarios) if unitarios else None
    diferencia_relativa = ((maximo - minimo) / minimo * 100) if minimo and maximo else None
    return {
        "total": len(comparables),
        "incluidos": sum(1 for item in comparables if workbench_comparable_incluido(item)),
        "excluidos": sum(
            1 for item in comparables if not workbench_comparable_incluido(item)
        ),
        "incompletos": sum(1 for item in comparables if workbench_comparable_incompleto(item)),
        "con_advertencias": sum(
            1 for item in comparables if workbench_comparable_advertencias(item)
        ),
        "unitario_minimo": minimo,
        "unitario_maximo": maximo,
        "unitario_minimo_fmt": formatear_precio_unitario_es(minimo),
        "unitario_maximo_fmt": formatear_precio_unitario_es(maximo),
        "diferencia_relativa": diferencia_relativa,
        "diferencia_relativa_fmt": (
            f"{formatear_numero_es(diferencia_relativa, 1)}%"
            if diferencia_relativa is not None
            else "—"
        ),
    }


def workbench_url(
    expediente_id: int,
    filtro: str,
    ordenar: str,
    direccion: str,
    testigo_id: str = "",
    mensaje: str = "",
    error: str = "",
) -> str:
    params = [("filtro", filtro), ("ordenar", ordenar), ("dir", direccion)]
    if limpiar_texto(testigo_id):
        params.append(("testigo_id", limpiar_texto(testigo_id)))
    if limpiar_texto(mensaje):
        params.append(("mensaje", limpiar_texto(mensaje)))
    if limpiar_texto(error):
        params.append(("error", limpiar_texto(error)))
    query = "&".join(f"{clave}={quote_plus(str(valor))}" for clave, valor in params)
    return f"/expediente/{expediente_id}/valoracion/workbench?{query}"


def valores_microedicion_workbench_desde_form(form) -> dict:
    peso = parsear_float(form.get("peso_porcentaje"))
    if peso is not None and (peso < 0 or peso > 100):
        raise ValueError("El peso debe estar entre 0 y 100.")
    representatividad = limpiar_texto(form.get("representatividad"))
    if representatividad and representatividad not in WORKBENCH_REPRESENTATIVIDAD_VALUES:
        raise ValueError("Representatividad no válida.")
    return {
        "incluido_calculo": 1 if form.get("incluido_calculo") == "1" else 0,
        "peso_porcentaje": peso,
        "representatividad": representatividad,
        "motivo_ponderacion": limpiar_texto(form.get("motivo_ponderacion")),
        "motivo_exclusion": limpiar_texto(form.get("motivo_exclusion")),
        "observaciones_ponderacion": limpiar_texto(
            form.get("observaciones_ponderacion")
        ),
    }


def actualizar_microedicion_workbench(cur, vinculo_id: int, valores: dict) -> None:
    cur.execute(
        """
        UPDATE valoracion_expediente_testigos
        SET incluido_calculo = ?, peso_porcentaje = ?, representatividad = ?,
            motivo_ponderacion = ?, motivo_exclusion = ?,
            observaciones_ponderacion = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            valores["incluido_calculo"],
            valores["peso_porcentaje"],
            valores["representatividad"],
            valores["motivo_ponderacion"],
            valores["motivo_exclusion"],
            valores["observaciones_ponderacion"],
            vinculo_id,
        ),
    )


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


def cargar_datos_inspeccion_visita(cur, visita_id: int, estancias):
    general_columnas = [item[0] for _, grupo in INSPECCION_GENERAL_GROUPS for item in grupo]
    general_columnas.append("observaciones_generales_inspeccion")
    exterior_columnas = [item[0] for item in INSPECCION_EXTERIOR_ITEMS] + [
        "observaciones_exteriores"
    ]
    comunes_columnas = [item[0] for item in INSPECCION_ELEMENTOS_COMUNES_ITEMS] + [
        "observaciones_elementos_comunes"
    ]

    general = fila_a_dict(
        cur.execute(
            "SELECT * FROM inspeccion_general_visita WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        general_columnas,
    )
    exterior = fila_a_dict(
        cur.execute(
            "SELECT * FROM inspeccion_exterior WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        exterior_columnas,
    )
    comunes = fila_a_dict(
        cur.execute(
            "SELECT * FROM inspeccion_elementos_comunes WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        comunes_columnas,
    )

    inspecciones_estancia = {
        fila["estancia_id"]: fila
        for fila in cur.execute(
            "SELECT * FROM inspeccion_estancias WHERE visita_id=?",
            (visita_id,),
        ).fetchall()
    }

    estancias_inspeccion = []
    for estancia in estancias:
        items = obtener_items_inspeccion_estancia(estancia["tipo_estancia"])
        columnas = [item[0] for item in items] + ["observaciones_estancia_inspeccion"]
        estancias_inspeccion.append(
            {
                "estancia": estancia,
                "campos": items,
                "datos": fila_a_dict(inspecciones_estancia.get(estancia["id"]), columnas),
            }
        )

    return {
        "general": general,
        "exterior": exterior,
        "comunes": comunes,
        "estancias": estancias_inspeccion,
    }


def cargar_datos_habitabilidad_visita(cur, visita_id: int, estancias):
    general_columnas = [item[0] for item in HABITABILIDAD_GENERAL_ITEMS] + [
        "conclusion_habitabilidad",
        "observaciones_generales_habitabilidad",
    ]
    exterior_columnas = [item[0] for item in HABITABILIDAD_EXTERIOR_ITEMS] + [
        "observaciones_exterior_habitabilidad"
    ]

    general = fila_a_dict(
        cur.execute(
            "SELECT * FROM habitabilidad_general_visita WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        general_columnas,
    )
    exterior = fila_a_dict(
        cur.execute(
            "SELECT * FROM habitabilidad_exterior WHERE visita_id=?",
            (visita_id,),
        ).fetchone(),
        exterior_columnas,
    )

    habitabilidad_estancias = {
        fila["estancia_id"]: fila
        for fila in cur.execute(
            "SELECT * FROM habitabilidad_estancias WHERE visita_id=?",
            (visita_id,),
        ).fetchall()
    }

    estancias_habitabilidad = []
    for estancia in estancias:
        columnas = [item[0] for item in HABITABILIDAD_ESTANCIA_ITEMS] + [
            "observaciones_estancia_habitabilidad"
        ]
        estancias_habitabilidad.append(
            {
                "estancia": estancia,
                "campos": HABITABILIDAD_ESTANCIA_ITEMS,
                "datos": fila_a_dict(
                    habitabilidad_estancias.get(estancia["id"]),
                    columnas,
                ),
            }
        )

    return {
        "general": general,
        "exterior": exterior,
        "estancias": estancias_habitabilidad,
    }


async def guardar_datos_inspeccion_desde_form(cur, visita_id: int, estancias, form):
    visita = cur.execute(
        """
        SELECT v.*, n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita
        FROM visitas v
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE v.id=?
        """,
        (visita_id,),
    ).fetchone()

    general_valores = {}
    for _, grupo in INSPECCION_GENERAL_GROUPS:
        for campo, _ in grupo:
            general_valores[campo] = (
                limpiar_texto(form.get(f"insp_general__{campo}")) or "no_inspeccionado"
            )
    general_valores["observaciones_generales_inspeccion"] = limpiar_texto(
        form.get("insp_general__observaciones_generales_inspeccion")
    )
    upsert_tabla_por_visita(cur, "inspeccion_general_visita", visita_id, general_valores)

    exterior_valores = {
        campo: limpiar_texto(form.get(f"insp_exterior__{campo}")) or "no_inspeccionado"
        for campo, _ in INSPECCION_EXTERIOR_ITEMS
    }
    exterior_valores["observaciones_exteriores"] = limpiar_texto(
        form.get("insp_exterior__observaciones_exteriores")
    )
    upsert_tabla_por_visita(cur, "inspeccion_exterior", visita_id, exterior_valores)

    comunes_valores = {
        campo: limpiar_texto(form.get(f"insp_comunes__{campo}")) or "no_inspeccionado"
        for campo, _ in INSPECCION_ELEMENTOS_COMUNES_ITEMS
    }
    comunes_valores["observaciones_elementos_comunes"] = limpiar_texto(
        form.get("insp_comunes__observaciones_elementos_comunes")
    )
    upsert_tabla_por_visita(
        cur,
        "inspeccion_elementos_comunes",
        visita_id,
        comunes_valores,
    )

    for estancia in estancias:
        if visita:
            validar_estancia_para_visita(cur, visita, estancia["id"])
        valores = {
            campo: (
                limpiar_texto(form.get(f"insp_estancia_{estancia['id']}__{campo}"))
                or "no_inspeccionado"
            )
            for campo, _ in obtener_items_inspeccion_estancia(estancia["tipo_estancia"])
        }
        valores["observaciones_estancia_inspeccion"] = limpiar_texto(
            form.get(
                f"insp_estancia_{estancia['id']}__observaciones_estancia_inspeccion"
            )
        )
        upsert_inspeccion_estancia(cur, visita_id, estancia["id"], valores)


async def guardar_datos_habitabilidad_desde_form(cur, visita_id: int, estancias, form):
    visita = cur.execute(
        """
        SELECT v.*, n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita
        FROM visitas v
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE v.id=?
        """,
        (visita_id,),
    ).fetchone()

    general_valores = {
        campo: limpiar_texto(form.get(f"hab_general__{campo}")) or "no_inspeccionado"
        for campo, _ in HABITABILIDAD_GENERAL_ITEMS
    }
    general_valores["conclusion_habitabilidad"] = limpiar_texto(
        form.get("hab_general__conclusion_habitabilidad")
    )
    general_valores["observaciones_generales_habitabilidad"] = limpiar_texto(
        form.get("hab_general__observaciones_generales_habitabilidad")
    )
    upsert_tabla_por_visita(
        cur,
        "habitabilidad_general_visita",
        visita_id,
        general_valores,
    )

    exterior_valores = {
        campo: limpiar_texto(form.get(f"hab_exterior__{campo}")) or "no_inspeccionado"
        for campo, _ in HABITABILIDAD_EXTERIOR_ITEMS
    }
    exterior_valores["observaciones_exterior_habitabilidad"] = limpiar_texto(
        form.get("hab_exterior__observaciones_exterior_habitabilidad")
    )
    upsert_tabla_por_visita(cur, "habitabilidad_exterior", visita_id, exterior_valores)

    for estancia in estancias:
        if visita:
            validar_estancia_para_visita(cur, visita, estancia["id"])
        valores = {
            campo: (
                limpiar_texto(form.get(f"hab_estancia_{estancia['id']}__{campo}"))
                or "no_inspeccionado"
            )
            for campo, _ in HABITABILIDAD_ESTANCIA_ITEMS
        }
        valores["observaciones_estancia_habitabilidad"] = limpiar_texto(
            form.get(
                f"hab_estancia_{estancia['id']}__observaciones_estancia_habitabilidad"
            )
        )
        upsert_habitabilidad_estancia(cur, visita_id, estancia["id"], valores)


async def guardar_datos_valoracion_desde_form(cur, visita_id: int, form):
    cur.execute(
        """
        SELECT v.*, n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita
        FROM visitas v
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE v.id=?
        """,
        (visita_id,),
    ).fetchone()

    columnas = (
        [item[0] for item in VALORACION_ENCARGO_ITEMS]
        + [item[0] for item in VALORACION_DOCUMENTACION_ITEMS]
        + [item[0] for item in VALORACION_DATOS_GENERALES_ITEMS]
        + [item[0] for item in VALORACION_SUPERFICIES_ITEMS]
        + [item[0] for item in VALORACION_SITUACION_LEGAL_ITEMS]
        + [item[0] for item in VALORACION_ENTORNO_ITEMS]
        + [item[0] for item in VALORACION_EDIFICIO_ITEMS]
        + [item[0] for item in VALORACION_INMUEBLE_ITEMS]
        + [item[0] for item in VALORACION_CONSTRUCTIVO_ITEMS]
        + [item[0] for item in VALORACION_ESTADO_ITEMS]
        + [item[0] for item in VALORACION_FECHAS_ITEMS]
        + [item[0] for item in VALORACION_METODO_ITEMS]
        + [item[0] for item in VALORACION_RESULTADO_ITEMS]
    )
    valores = {
        columna: limpiar_texto(form.get(f"valoracion__{columna}"))
        for columna in columnas
    }
    upsert_tabla_por_visita(cur, "valoracion_visita", visita_id, valores)


def etiquetar_opcion(valor: str, opciones: dict[str, str]) -> str:
    valor_limpio = limpiar_texto(valor)
    return opciones.get(valor_limpio, valor_limpio or "-")


def parsear_float(valor):
    try:
        return float(str(valor).strip())
    except (TypeError, ValueError):
        return None


def resumen_diario_a_tarjetas(resumen_diario):
    tarjetas = []
    for dia in resumen_diario or []:
        temperatura = dia.get("temperatura") or {}
        temp_min = temperatura.get("min")
        temp_max = temperatura.get("max")
        temp_media = temperatura.get("media")

        tarjetas.append(
            {
                "fecha": dia.get("fecha", ""),
                "temperatura_texto": (
                    f"{temp_min} °C / {temp_max} °C"
                    if temp_min is not None and temp_max is not None
                    else "-"
                ),
                "temperatura_media_texto": (
                    f"{temp_media} °C" if temp_media is not None else "-"
                ),
                "humedad_texto": (
                    f"{dia.get('humedad_media')} %"
                    if dia.get("humedad_media") is not None
                    else "-"
                ),
                "viento_texto": (
                    f"{dia.get('viento_max_kmh')} km/h"
                    if dia.get("viento_max_kmh") is not None
                    else "-"
                ),
                "precipitacion_texto": (
                    f"{dia.get('precipitacion_total_mm')} mm"
                    if dia.get("precipitacion_total_mm") is not None
                    else "-"
                ),
            }
        )

    return tarjetas


def construir_resumen_climatologia(resumen_diario):
    if not resumen_diario:
        return "No se pudo obtener climatología para esta ubicación."

    temp_min = min(
        (
            dia.get("temperatura", {}).get("min")
            for dia in resumen_diario
            if dia.get("temperatura", {}).get("min") is not None
        ),
        default=None,
    )
    temp_max = max(
        (
            dia.get("temperatura", {}).get("max")
            for dia in resumen_diario
            if dia.get("temperatura", {}).get("max") is not None
        ),
        default=None,
    )
    viento_max = max(
        (
            dia.get("viento_max_kmh")
            for dia in resumen_diario
            if dia.get("viento_max_kmh") is not None
        ),
        default=None,
    )
    precipitacion_total = round(
        sum(dia.get("precipitacion_total_mm") or 0 for dia in resumen_diario),
        2,
    )

    return (
        "Última semana registrada: "
        f"temperaturas entre {temp_min} °C y {temp_max} °C, "
        f"viento hasta {viento_max} km/h "
        f"y precipitación acumulada de {precipitacion_total} mm."
    )


def obtener_climatologia_guardada(cur, visita_id: int):
    clima = cur.execute(
        """
        SELECT *
        FROM climatologia_visitas
        WHERE visita_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (visita_id,),
    ).fetchone()

    detalle = []
    if clima and clima["detalle_json"]:
        try:
            payload = json.loads(clima["detalle_json"])
            if isinstance(payload, dict):
                detalle = resumen_diario_a_tarjetas(payload.get("resumen_diario") or [])
            elif isinstance(payload, list):
                detalle = payload
            else:
                detalle = []
        except json.JSONDecodeError:
            detalle = []

    return clima, detalle


def persistir_climatologia(cur, visita_id: int, climatologia: dict):
    cur.execute("DELETE FROM climatologia_visitas WHERE visita_id=?", (visita_id,))
    resumen_diario = climatologia.get("resumen_diario") or []
    resumen = climatologia.get("resumen") or construir_resumen_climatologia(resumen_diario)
    coordenadas = climatologia.get("coordenadas") or {}
    cur.execute(
        """
        INSERT INTO climatologia_visitas (
            visita_id,
            resumen,
            detalle_json,
            ubicacion,
            latitud,
            longitud,
            fecha_generacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            resumen,
            json.dumps(climatologia, ensure_ascii=False),
            climatologia.get("ubicacion"),
            coordenadas.get("lat"),
            coordenadas.get("lon"),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


async def solicitar_climatologia_open_meteo(
    *,
    latitud,
    longitud,
    municipio: str,
    ubicacion_label: str,
):
    lat = parsear_float(latitud)
    lon = parsear_float(longitud)

    if lat is None or lon is None:
        lat, lon = await geocodificar(municipio)

    climatologia = await obtener_climatologia(lat, lon)
    climatologia["ubicacion"] = limpiar_texto(ubicacion_label) or limpiar_texto(municipio)
    climatologia["resumen"] = construir_resumen_climatologia(
        climatologia.get("resumen_diario") or []
    )
    return climatologia


def crear_visita_si_no_existe(
    cur,
    expediente,
    visita_id,
    fecha: str,
    tecnico: str,
    observaciones_visita: str,
    ambito_visita: str = "",
    nivel_id=None,
    unidad_id=None,
):
    if visita_id:
        return visita_id, False

    cur.execute(
        """
        INSERT INTO visitas
        (expediente_id, fecha, tecnico, observaciones_visita, ambito_visita, nivel_id, unidad_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expediente["id"],
            fecha,
            tecnico,
            observaciones_visita,
            limpiar_texto(ambito_visita),
            nivel_id,
            unidad_id,
        ),
    )
    nueva_visita_id = cur.lastrowid

    return nueva_visita_id, True


def propagar_acabados_estancia(
    cur,
    expediente_id: int,
    estancia_id: int,
    acabados_anteriores: dict,
    acabados_nuevos: dict,
):
    for campo, valor_nuevo in acabados_nuevos.items():
        valor_limpio = limpiar_texto(valor_nuevo)
        valor_anterior = limpiar_texto(acabados_anteriores.get(campo))

        if valor_anterior or not valor_limpio:
            continue

        existe_previo = cur.execute(
            f"""
            SELECT 1
            FROM estancias es
            INNER JOIN visitas v ON es.visita_id = v.id
            WHERE v.expediente_id = ?
              AND es.id <> ?
              AND TRIM(IFNULL(es.{campo}, '')) <> ''
            LIMIT 1
            """,
            (expediente_id, estancia_id),
        ).fetchone()

        if existe_previo:
            continue

        cur.execute(
            f"""
            UPDATE estancias
            SET {campo} = ?
            WHERE id IN (
                SELECT es.id
                FROM estancias es
                INNER JOIN visitas v ON es.visita_id = v.id
                WHERE v.expediente_id = ?
                  AND es.id <> ?
                  AND TRIM(IFNULL(es.{campo}, '')) = ''
            )
            """,
            (valor_limpio, expediente_id, estancia_id),
        )


def generar_numero_expediente():
    sufijo_anio = datetime.now().strftime("%y")

    conn = get_connection()
    cur = conn.cursor()
    try:
        row = cur.execute(
            """
            SELECT MAX(CAST(SUBSTR(numero_expediente, 1, 3) AS INTEGER)) AS ultima_secuencia
            FROM expedientes
            WHERE numero_expediente GLOB ?
            """,
            (f"[0-9][0-9][0-9]-{sufijo_anio}",),
        ).fetchone()
    finally:
        conn.close()

    ultima_secuencia = row["ultima_secuencia"] or 0
    return f"{ultima_secuencia + 1:03d}-{sufijo_anio}"


def generar_numero_expediente_desde_cursor(cur):
    sufijo_anio = datetime.now().strftime("%y")
    row = cur.execute(
        """
        SELECT MAX(CAST(SUBSTR(numero_expediente, 1, 3) AS INTEGER)) AS ultima_secuencia
        FROM expedientes
        WHERE numero_expediente GLOB ?
        """,
        (f"[0-9][0-9][0-9]-{sufijo_anio}",),
    ).fetchone()
    ultima_secuencia = row["ultima_secuencia"] or 0
    return f"{ultima_secuencia + 1:03d}-{sufijo_anio}"


def parsear_entero_positivo(valor) -> int:
    try:
        numero = int(str(valor or "").strip())
        return max(numero, 0)
    except (TypeError, ValueError):
        return 0


def normalizar_configuracion_plantas(tiene_varias_plantas, numero_plantas) -> tuple[int, int]:
    marcado = limpiar_texto(tiene_varias_plantas).lower() in {"1", "on", "si", "sí", "true", "yes"}
    if not marcado:
        return 0, 1
    return 1, max(parsear_entero_positivo(numero_plantas), 2)


def opciones_planta_unidad(numero_plantas) -> list[str]:
    total = max(parsear_entero_positivo(numero_plantas), 1)
    return ["Planta baja"] + [f"Planta {indice}" for indice in range(1, total)]


def unidad_tiene_varias_plantas(unidad) -> bool:
    return bool(unidad and int(unidad["tiene_varias_plantas"] or 0))


def crear_estancias_base(cur, visita_id: int, tipo_inmueble: str, dormitorios, banos):
    visita = cur.execute(
        """
        SELECT ambito_visita, unidad_id
        FROM visitas
        WHERE id=?
        """,
        (visita_id,),
    ).fetchone()
    ambito_visita = limpiar_texto(visita["ambito_visita"]) if visita else ""
    unidad_id = visita["unidad_id"] if visita else None

    if ambito_visita and ambito_visita != "unidad":
        return

    existentes = cur.execute(
        "SELECT COUNT(*) AS total FROM estancias WHERE visita_id=?",
        (visita_id,),
    ).fetchone()

    if existentes and existentes["total"] > 0:
        return

    estancias_base = [("Salón", "Salón"), ("Cocina", "Cocina")]

    if tipo_inmueble == "Piso":
        estancias_base.append(("Pasillo", "Pasillo"))

    for nombre, tipo_estancia in estancias_base:
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones,
                unidad_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, nombre, tipo_estancia, "", "", "", "", "", "", unidad_id),
        )

    for i in range(1, parsear_entero_positivo(dormitorios) + 1):
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones,
                unidad_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                f"Dormitorio {i}",
                "Dormitorio",
                "",
                "",
                "",
                "",
                "",
                "",
                unidad_id,
            ),
        )

    for i in range(1, parsear_entero_positivo(banos) + 1):
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones,
                unidad_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, f"Baño {i}", "Baño", "", "", "", "", "", "", unidad_id),
        )


def copiar_estancias_visita_anterior(cur, expediente_id: int, nueva_visita_id: int) -> bool:
    visita_actual = cur.execute(
        """
        SELECT ambito_visita, unidad_id
        FROM visitas
        WHERE id=?
        """,
        (nueva_visita_id,),
    ).fetchone()
    ambito_visita = limpiar_texto(visita_actual["ambito_visita"]) if visita_actual else ""
    unidad_id_actual = visita_actual["unidad_id"] if visita_actual else None

    if ambito_visita and ambito_visita != "unidad":
        return False

    existentes = cur.execute(
        "SELECT COUNT(*) AS total FROM estancias WHERE visita_id=?",
        (nueva_visita_id,),
    ).fetchone()

    if existentes and existentes["total"] > 0:
        return False

    ultima_visita = None
    if unidad_id_actual:
        ultima_visita = cur.execute(
            """
            SELECT id
            FROM visitas
            WHERE expediente_id = ? AND id <> ? AND unidad_id = ?
              AND EXISTS (
                  SELECT 1
                  FROM estancias
                  WHERE visita_id = visitas.id
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (expediente_id, nueva_visita_id, unidad_id_actual),
        ).fetchone()

    if not ultima_visita:
        ultima_visita = cur.execute(
            """
            SELECT id
            FROM visitas
            WHERE expediente_id = ? AND id <> ?
              AND EXISTS (
                  SELECT 1
                  FROM estancias
                  WHERE visita_id = visitas.id
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (expediente_id, nueva_visita_id),
        ).fetchone()

    if not ultima_visita:
        return False

    estancias_previas = cur.execute(
        """
        SELECT
            nombre,
            tipo_estancia,
            ventilacion,
            planta,
            acabado_pavimento,
            acabado_paramento,
            acabado_techo,
            observaciones,
            unidad_id
        FROM estancias
        WHERE visita_id = ?
        ORDER BY id ASC
        """,
        (ultima_visita["id"],),
    ).fetchall()

    if not estancias_previas:
        return False

    for estancia in estancias_previas:
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones,
                unidad_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nueva_visita_id,
                estancia["nombre"],
                estancia["tipo_estancia"],
                estancia["ventilacion"],
                estancia["planta"],
                estancia["acabado_pavimento"],
                estancia["acabado_paramento"],
                estancia["acabado_techo"],
                estancia["observaciones"],
                unidad_id_actual or estancia["unidad_id"],
            ),
        )

    return True


def eliminar_expediente_completo(cur, expediente_id: int):
    expediente = cur.execute(
        "SELECT imagen_catastro FROM expedientes WHERE id=?",
        (expediente_id,),
    ).fetchone()

    visitas = cur.execute(
        "SELECT id FROM visitas WHERE expediente_id=?",
        (expediente_id,),
    ).fetchall()
    visita_ids = [visita["id"] for visita in visitas]

    if visita_ids:
        placeholders = ",".join(["?"] * len(visita_ids))
        fotos = cur.execute(
            f"""
            SELECT foto
            FROM registros_patologias
            WHERE visita_id IN ({placeholders}) AND foto IS NOT NULL AND foto <> ''
            """,
            visita_ids,
        ).fetchall()
        fotos_exteriores = cur.execute(
            f"""
            SELECT foto
            FROM registros_patologias_exteriores
            WHERE visita_id IN ({placeholders}) AND foto IS NOT NULL AND foto <> ''
            """,
            visita_ids,
        ).fetchall()
        fotos_registro_multi = cur.execute(
            f"""
            SELECT rpf.archivo
            FROM registro_patologia_fotos rpf
            JOIN registros_patologias rp ON rpf.registro_id = rp.id
            WHERE rp.visita_id IN ({placeholders})
            """,
            visita_ids,
        ).fetchall()
        fotos_estancias_multi = cur.execute(
            f"""
            SELECT ef.archivo
            FROM estancia_fotos ef
            JOIN estancias es ON ef.estancia_id = es.id
            WHERE es.visita_id IN ({placeholders})
            """,
            visita_ids,
        ).fetchall()
        fotos_exteriores_multi = cur.execute(
            f"""
            SELECT rpef.archivo
            FROM registro_patologia_exterior_fotos rpef
            JOIN registros_patologias_exteriores rpe ON rpef.registro_id = rpe.id
            WHERE rpe.visita_id IN ({placeholders})
            """,
            visita_ids,
        ).fetchall()
        imagenes_mapa = cur.execute(
            f"""
            SELECT imagen_base
            FROM mapas_patologia
            WHERE visita_id IN ({placeholders}) AND imagen_base IS NOT NULL AND imagen_base <> ''
            """,
            visita_ids,
        ).fetchall()
        fotos_cuadrantes = cur.execute(
            f"""
            SELECT qmp.foto_detalle
            FROM cuadrantes_mapa_patologia qmp
            JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
            WHERE mp.visita_id IN ({placeholders})
              AND qmp.foto_detalle IS NOT NULL
              AND qmp.foto_detalle <> ''
            """,
            visita_ids,
        ).fetchall()
        fotos_cuadrantes_multi = cur.execute(
            f"""
            SELECT qmpf.archivo
            FROM cuadrante_mapa_patologia_fotos qmpf
            JOIN cuadrantes_mapa_patologia qmp ON qmpf.cuadrante_id = qmp.id
            JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
            WHERE mp.visita_id IN ({placeholders})
            """,
            visita_ids,
        ).fetchall()

        for foto in fotos:
            borrar_foto_si_existe(foto["foto"])
        for foto in fotos_exteriores:
            borrar_foto_si_existe(foto["foto"])
        for foto in fotos_registro_multi:
            borrar_foto_si_existe(foto["archivo"])
        for foto in fotos_estancias_multi:
            borrar_foto_si_existe(foto["archivo"])
        for foto in fotos_exteriores_multi:
            borrar_foto_si_existe(foto["archivo"])
        for imagen in imagenes_mapa:
            borrar_foto_si_existe(imagen["imagen_base"])
        for foto in fotos_cuadrantes:
            borrar_foto_si_existe(foto["foto_detalle"])
        for foto in fotos_cuadrantes_multi:
            borrar_foto_si_existe(foto["archivo"])

        cur.execute(
            f"""
            DELETE FROM cuadrante_mapa_patologia_fotos
            WHERE cuadrante_id IN (
                SELECT qmp.id
                FROM cuadrantes_mapa_patologia qmp
                JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
                WHERE mp.visita_id IN ({placeholders})
            )
            """,
            visita_ids,
        )
        cur.execute(
            f"""
            DELETE FROM registro_patologia_exterior_fotos
            WHERE registro_id IN (
                SELECT id
                FROM registros_patologias_exteriores
                WHERE visita_id IN ({placeholders})
            )
            """,
            visita_ids,
        )
        cur.execute(
            f"""
            DELETE FROM registro_patologia_fotos
            WHERE registro_id IN (
                SELECT id
                FROM registros_patologias
                WHERE visita_id IN ({placeholders})
            )
            """,
            visita_ids,
        )
        cur.execute(
            f"""
            DELETE FROM estancia_fotos
            WHERE estancia_id IN (
                SELECT id
                FROM estancias
                WHERE visita_id IN ({placeholders})
            )
            """,
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM climatologia_visitas WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM inspeccion_general_visita WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM inspeccion_exterior WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM inspeccion_elementos_comunes WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM inspeccion_estancias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM habitabilidad_general_visita WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM habitabilidad_exterior WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM habitabilidad_estancias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM valoracion_visita WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM comparables_valoracion WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"""
            DELETE FROM cuadrantes_mapa_patologia
            WHERE mapa_id IN (
                SELECT id
                FROM mapas_patologia
                WHERE visita_id IN ({placeholders})
            )
            """,
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM mapas_patologia WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM registros_patologias_exteriores WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM registros_patologias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM estancias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM visitas WHERE id IN ({placeholders})",
            visita_ids,
        )

    cur.execute("DELETE FROM unidades_expediente WHERE expediente_id=?", (expediente_id,))
    cur.execute("DELETE FROM niveles_edificio WHERE expediente_id=?", (expediente_id,))

    cur.execute("DELETE FROM expedientes WHERE id=?", (expediente_id,))

    if expediente and expediente["imagen_catastro"]:
        borrar_foto_si_existe(expediente["imagen_catastro"])


def eliminar_visita_completa(cur, visita_id: int):
    fotos = cur.execute(
        """
        SELECT foto
        FROM registros_patologias
        WHERE visita_id=? AND foto IS NOT NULL AND foto <> ''
        """,
        (visita_id,),
    ).fetchall()
    fotos_exteriores = cur.execute(
        """
        SELECT foto
        FROM registros_patologias_exteriores
        WHERE visita_id=? AND foto IS NOT NULL AND foto <> ''
        """,
        (visita_id,),
    ).fetchall()
    fotos_registro_multi = cur.execute(
        """
        SELECT rpf.archivo
        FROM registro_patologia_fotos rpf
        JOIN registros_patologias rp ON rpf.registro_id = rp.id
        WHERE rp.visita_id=?
        """,
        (visita_id,),
    ).fetchall()
    fotos_estancias_multi = cur.execute(
        """
        SELECT ef.archivo
        FROM estancia_fotos ef
        JOIN estancias es ON ef.estancia_id = es.id
        WHERE es.visita_id=?
        """,
        (visita_id,),
    ).fetchall()
    fotos_exteriores_multi = cur.execute(
        """
        SELECT rpef.archivo
        FROM registro_patologia_exterior_fotos rpef
        JOIN registros_patologias_exteriores rpe ON rpef.registro_id = rpe.id
        WHERE rpe.visita_id=?
        """,
        (visita_id,),
    ).fetchall()
    imagenes_mapa = cur.execute(
        """
        SELECT imagen_base
        FROM mapas_patologia
        WHERE visita_id=? AND imagen_base IS NOT NULL AND imagen_base <> ''
        """,
        (visita_id,),
    ).fetchall()
    fotos_cuadrantes = cur.execute(
        """
        SELECT qmp.foto_detalle
        FROM cuadrantes_mapa_patologia qmp
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        WHERE mp.visita_id=?
          AND qmp.foto_detalle IS NOT NULL
          AND qmp.foto_detalle <> ''
        """,
        (visita_id,),
    ).fetchall()
    fotos_cuadrantes_multi = cur.execute(
        """
        SELECT qmpf.archivo
        FROM cuadrante_mapa_patologia_fotos qmpf
        JOIN cuadrantes_mapa_patologia qmp ON qmpf.cuadrante_id = qmp.id
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        WHERE mp.visita_id=?
        """,
        (visita_id,),
    ).fetchall()

    for foto in fotos:
        borrar_foto_si_existe(foto["foto"])
    for foto in fotos_exteriores:
        borrar_foto_si_existe(foto["foto"])
    for foto in fotos_registro_multi:
        borrar_foto_si_existe(foto["archivo"])
    for foto in fotos_estancias_multi:
        borrar_foto_si_existe(foto["archivo"])
    for foto in fotos_exteriores_multi:
        borrar_foto_si_existe(foto["archivo"])
    for imagen in imagenes_mapa:
        borrar_foto_si_existe(imagen["imagen_base"])
    for foto in fotos_cuadrantes:
        borrar_foto_si_existe(foto["foto_detalle"])
    for foto in fotos_cuadrantes_multi:
        borrar_foto_si_existe(foto["archivo"])

    cur.execute(
        """
        DELETE FROM cuadrante_mapa_patologia_fotos
        WHERE cuadrante_id IN (
            SELECT qmp.id
            FROM cuadrantes_mapa_patologia qmp
            JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
            WHERE mp.visita_id=?
        )
        """,
        (visita_id,),
    )
    cur.execute(
        """
        DELETE FROM registro_patologia_exterior_fotos
        WHERE registro_id IN (
            SELECT id
            FROM registros_patologias_exteriores
            WHERE visita_id=?
        )
        """,
        (visita_id,),
    )
    cur.execute(
        """
        DELETE FROM registro_patologia_fotos
        WHERE registro_id IN (
            SELECT id
            FROM registros_patologias
            WHERE visita_id=?
        )
        """,
        (visita_id,),
    )
    cur.execute(
        """
        DELETE FROM estancia_fotos
        WHERE estancia_id IN (
            SELECT id
            FROM estancias
            WHERE visita_id=?
        )
        """,
        (visita_id,),
    )
    cur.execute("DELETE FROM climatologia_visitas WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM inspeccion_general_visita WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM inspeccion_exterior WHERE visita_id=?", (visita_id,))
    cur.execute(
        "DELETE FROM inspeccion_elementos_comunes WHERE visita_id=?",
        (visita_id,),
    )
    cur.execute("DELETE FROM inspeccion_estancias WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM habitabilidad_general_visita WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM habitabilidad_exterior WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM habitabilidad_estancias WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM valoracion_visita WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM comparables_valoracion WHERE visita_id=?", (visita_id,))
    cur.execute(
        """
        DELETE FROM cuadrantes_mapa_patologia
        WHERE mapa_id IN (
            SELECT id
            FROM mapas_patologia
            WHERE visita_id=?
        )
        """,
        (visita_id,),
    )
    cur.execute("DELETE FROM mapas_patologia WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM registros_patologias_exteriores WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM registros_patologias WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM estancias WHERE visita_id=?", (visita_id,))
    cur.execute("DELETE FROM visitas WHERE id=?", (visita_id,))


def get_informe_path(nombre_archivo: str) -> Path:
    nombre_seguro = Path(nombre_archivo).name
    ruta = (Path(INFORMES_DIR) / nombre_seguro).resolve()
    base = Path(INFORMES_DIR).resolve()

    if ruta.parent != base or not ruta.exists():
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return ruta


def get_informe_path_for_expediente(expediente, nombre_archivo: str) -> Path:
    ruta = get_informe_path(nombre_archivo)
    prefijo = limpiar_nombre_archivo(
        f"{expediente['numero_expediente']}_{expediente['cliente']}"
    )
    nombre_esperado = f"informe_{prefijo}_"

    if not ruta.name.startswith(nombre_esperado):
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return ruta


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2_sha256$100000${binascii.hexlify(salt).decode()}${binascii.hexlify(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = binascii.unhexlify(salt_hex.encode())
        expected = binascii.unhexlify(digest_hex.encode())
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, binascii.Error):
        return False


def get_user_by_id(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        return cur.execute(
            "SELECT * FROM usuarios WHERE id=? AND activo=1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def sign_session_value(value: str) -> str:
    return hmac.new(
        SESSION_SECRET_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_session_user_id(request: Request):
    raw_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw_cookie or ":" not in raw_cookie:
        return None

    user_id_str, signature = raw_cookie.split(":", 1)
    expected = sign_session_value(user_id_str)

    if not hmac.compare_digest(signature, expected):
        return None

    try:
        return int(user_id_str)
    except ValueError:
        return None


def get_current_user_optional(request: Request):
    cached_user = getattr(request.state, "current_user", None)
    if cached_user is not None:
        return cached_user

    user_id = get_session_user_id(request)
    if not user_id:
        return None

    user = get_user_by_id(user_id)
    if user is not None:
        request.state.current_user = user
    return user


def get_current_user(request: Request):
    user = get_current_user_optional(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return user


def render_template(request: Request, template_name: str, context: dict | None = None):
    data = {
        "request": request,
        "current_user": get_current_user_optional(request),
    }
    if context:
        data.update(context)
    return templates.TemplateResponse(request, template_name, data)


def normalizar_redirect_interno(destino: str | None) -> str:
    destino_limpio = limpiar_texto(destino)
    if not destino_limpio:
        return ""
    if not destino_limpio.startswith("/") or destino_limpio.startswith("//"):
        return ""
    return destino_limpio


def obtener_estancia_id_referer(request: Request) -> int | None:
    referer = request.headers.get("referer") or ""
    if not referer:
        return None
    query = parse_qs(urlparse(referer).query)
    return parse_optional_int((query.get("estancia_id") or [""])[0])


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def get_owned_expediente(cur, expediente_id: int, user_id: int):
    return cur.execute(
        "SELECT * FROM expedientes WHERE id=? AND owner_user_id=?",
        (expediente_id, user_id),
    ).fetchone()


def get_owned_nivel(cur, nivel_id: int, user_id: int):
    return cur.execute(
        """
        SELECT n.*, e.owner_user_id
        FROM niveles_edificio n
        JOIN expedientes e ON n.expediente_id = e.id
        WHERE n.id=? AND e.owner_user_id=?
        """,
        (nivel_id, user_id),
    ).fetchone()


def get_owned_unidad(cur, unidad_id: int, user_id: int):
    return cur.execute(
        """
        SELECT u.*, e.owner_user_id
        FROM unidades_expediente u
        JOIN expedientes e ON u.expediente_id = e.id
        WHERE u.id=? AND e.owner_user_id=?
        """,
        (unidad_id, user_id),
    ).fetchone()


def cargar_estructura_multiunidad(cur, expediente_id: int):
    niveles = [
        dict(row)
        for row in cur.execute(
            """
            SELECT *
            FROM niveles_edificio
            WHERE expediente_id=?
            ORDER BY CASE WHEN orden_nivel IS NULL THEN 1 ELSE 0 END, orden_nivel ASC, id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]

    unidades = [
        dict(row)
        for row in cur.execute(
            """
            SELECT
                u.*,
                n.nombre_nivel,
                p.identificador AS unidad_principal_identificador
            FROM unidades_expediente u
            LEFT JOIN niveles_edificio n ON u.nivel_id = n.id
            LEFT JOIN unidades_expediente p ON u.unidad_principal_id = p.id
            WHERE u.expediente_id=?
            ORDER BY
                CASE WHEN u.nivel_id IS NULL THEN 1 ELSE 0 END,
                COALESCE(n.orden_nivel, 999999),
                COALESCE(n.nombre_nivel, ''),
                u.id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]

    for nivel in niveles:
        nivel["principales"] = []
        nivel["comunes"] = []
        nivel["exteriores"] = []
        nivel["otras"] = []
        nivel["tipo_nivel_label"] = etiquetar_opcion(
            nivel.get("tipo_nivel", ""), TIPO_NIVEL_LABELS
        )

    niveles_por_id = {nivel["id"]: nivel for nivel in niveles}
    principales_por_id = {}
    sin_nivel = {"principales": [], "comunes": [], "exteriores": [], "otras": []}
    anejos_sueltos = []

    for unidad in unidades:
        unidad["tipo_unidad_label"] = etiquetar_opcion(
            unidad.get("tipo_unidad", ""), TIPO_UNIDAD_LABELS
        )
        unidad["vinculo_unidad_label"] = etiquetar_opcion(
            unidad.get("vinculo_unidad", ""), VINCULO_UNIDAD_LABELS
        )
        unidad["tipo_anejo_label"] = etiquetar_opcion(
            unidad.get("tipo_anejo", ""), TIPO_ANEJO_LABELS
        )
        unidad["tiene_varias_plantas"] = int(unidad.get("tiene_varias_plantas") or 0)
        unidad["numero_plantas"] = max(parsear_entero_positivo(unidad.get("numero_plantas")), 1)
        unidad["anejos"] = []
        unidad["es_anejo"] = (
            limpiar_texto(unidad.get("vinculo_unidad")) == "anejo"
            or int(unidad.get("es_principal") or 0) == 0
        )
        if not unidad["es_anejo"] and limpiar_texto(unidad.get("vinculo_unidad")) in {
            "",
            "principal",
        }:
            principales_por_id[unidad["id"]] = unidad

    for unidad in unidades:
        if unidad["es_anejo"]:
            principal = principales_por_id.get(unidad.get("unidad_principal_id"))
            if principal:
                principal["anejos"].append(unidad)
            else:
                anejos_sueltos.append(unidad)
            continue

        contenedor = niveles_por_id.get(unidad.get("nivel_id"), sin_nivel)
        vinculo = limpiar_texto(unidad.get("vinculo_unidad"))
        tipo_unidad = limpiar_texto(unidad.get("tipo_unidad"))

        if vinculo == "comun" or tipo_unidad == "zona_comun":
            contenedor["comunes"].append(unidad)
        elif vinculo == "exterior" or tipo_unidad == "exterior":
            contenedor["exteriores"].append(unidad)
        elif vinculo in {"", "principal"} or int(unidad.get("es_principal") or 0) == 1:
            contenedor["principales"].append(unidad)
        else:
            contenedor["otras"].append(unidad)

    unidades_principales = [
        unidad
        for unidad in unidades
        if not unidad["es_anejo"]
        and limpiar_texto(unidad.get("vinculo_unidad")) in {"", "principal"}
    ]

    return {
        "niveles": niveles,
        "unidades": unidades,
        "sin_nivel": sin_nivel,
        "anejos_sueltos": anejos_sueltos,
        "unidades_principales": unidades_principales,
    }


def preparar_resumen_registro_expediente(cur, expediente_id: int):
    estructura_multiunidad = cargar_estructura_multiunidad(cur, expediente_id)

    visita_fotos_exteriores_rows = cur.execute(
        """
        SELECT vf.*, v.fecha AS visita_fecha
        FROM visita_fotos vf
        JOIN visitas v ON vf.visita_id = v.id
        WHERE v.expediente_id = ? AND vf.categoria = 'exterior'
        ORDER BY v.fecha DESC, vf.id ASC
        """,
        (expediente_id,),
    ).fetchall()
    visita_fotos_exteriores = []
    for row in visita_fotos_exteriores_rows:
        foto = dict(row)
        foto["url"] = f"/uploads/{foto['ruta']}"
        visita_fotos_exteriores.append(foto)

    patologias_exteriores_rows = cur.execute(
        """
        SELECT rpe.*,
               v.fecha AS visita_fecha,
               u.identificador AS unidad_identificador,
               n.nombre_nivel AS nivel_nombre
        FROM registros_patologias_exteriores rpe
        JOIN visitas v ON rpe.visita_id = v.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        WHERE v.expediente_id = ?
        ORDER BY v.fecha DESC, rpe.id DESC
        """,
        (expediente_id,),
    ).fetchall()
    patologias_exteriores = []
    for row in patologias_exteriores_rows:
        registro = dict(row)
        registro["zona_exterior_label"] = etiquetar_opcion(
            registro.get("zona_exterior", ""),
            ZONA_EXTERIOR_LABELS,
        )
        registro["elemento_exterior_label"] = etiquetar_opcion(
            registro.get("elemento_exterior", ""),
            ELEMENTO_EXTERIOR_LABELS,
        )
        registro["localizacion_dano_exterior_label"] = etiquetar_opcion(
            registro.get("localizacion_dano_exterior", ""),
            LOCALIZACION_EXTERIOR_LABELS,
        )
        patologias_exteriores.append(registro)

    patologias_interiores_rows = cur.execute(
        """
        SELECT rp.id,
               rp.estancia_id,
               rp.patologia
        FROM registros_patologias rp
        JOIN visitas v ON rp.visita_id = v.id
        WHERE v.expediente_id = ?
        ORDER BY rp.id ASC
        """,
        (expediente_id,),
    ).fetchall()
    patologias_por_estancia: dict[int, list[dict]] = {}
    for row in patologias_interiores_rows:
        estancia_id = row["estancia_id"]
        if not estancia_id:
            continue
        patologias_por_estancia.setdefault(estancia_id, []).append(
            {
                "id": row["id"],
                "patologia": limpiar_texto(row["patologia"]),
            }
        )

    estancias_rows = cur.execute(
        """
        SELECT es.*,
               v.fecha AS visita_fecha,
               ue.identificador AS unidad_identificador,
               ue.tipo_unidad AS unidad_tipo_unidad,
               ue.uso AS unidad_uso,
               ne.nombre_nivel AS nivel_nombre,
               EXISTS(
                   SELECT 1
                   FROM estancia_fotos ef
                   WHERE ef.estancia_id = es.id
                   LIMIT 1
               ) AS tiene_foto_principal
        FROM estancias es
        JOIN visitas v ON es.visita_id = v.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE v.expediente_id = ?
        ORDER BY
            CASE WHEN ue.nivel_id IS NULL THEN 1 ELSE 0 END,
            COALESCE(ne.orden_nivel, 999999),
            COALESCE(ne.nombre_nivel, ''),
            COALESCE(ue.identificador, ''),
            es.id ASC
        """,
        (expediente_id,),
    ).fetchall()

    unidades_por_id = {
        unidad["id"]: {
            **unidad,
            "tipo_unidad_label": unidad.get("tipo_unidad_label")
            or etiquetar_opcion(unidad.get("tipo_unidad", ""), TIPO_UNIDAD_LABELS),
            "nivel_nombre": limpiar_texto(unidad.get("nombre_nivel")),
            "estancias": [],
        }
        for unidad in estructura_multiunidad["unidades"]
    }

    estancias_sin_unidad = []
    for row in estancias_rows:
        estancia = dict(row)
        estancia["foto_principal_url"] = "__resumen__" if estancia.get("tiene_foto_principal") else ""
        estancia["esta_pendiente"] = not calcular_estancia_rellena(estancia)
        estancia["patologias"] = patologias_por_estancia.get(estancia["id"], [])
        estancia["total_patologias"] = len(estancia["patologias"])
        unidad_id = estancia.get("unidad_id")
        if unidad_id and unidad_id in unidades_por_id:
            unidades_por_id[unidad_id]["estancias"].append(estancia)
        else:
            estancias_sin_unidad.append(estancia)

    def construir_resumen_unidad(unidad: dict):
        unidad_resumen = unidades_por_id.get(unidad["id"], dict(unidad))
        unidad_resumen.setdefault("estancias", [])
        unidad_resumen["tipo_unidad_label"] = unidad_resumen.get(
            "tipo_unidad_label"
        ) or etiquetar_opcion(unidad_resumen.get("tipo_unidad", ""), TIPO_UNIDAD_LABELS)
        unidad_resumen["nivel_nombre"] = limpiar_texto(
            unidad_resumen.get("nivel_nombre") or unidad_resumen.get("nombre_nivel")
        )
        return unidad_resumen

    grupos_unidades = []
    for nivel in estructura_multiunidad["niveles"]:
        unidades_nivel = []
        for grupo in ("principales", "comunes", "exteriores", "otras"):
            unidades_nivel.extend(
                construir_resumen_unidad(unidad) for unidad in nivel.get(grupo, [])
            )
        grupos_unidades.append(
            {
                "titulo": nivel["nombre_nivel"],
                "meta": nivel.get("tipo_nivel_label") or "",
                "unidades": unidades_nivel,
            }
        )

    unidades_sin_nivel = []
    for grupo in ("principales", "comunes", "exteriores", "otras"):
        unidades_sin_nivel.extend(
            construir_resumen_unidad(unidad)
            for unidad in estructura_multiunidad["sin_nivel"].get(grupo, [])
        )

    if estancias_sin_unidad:
        unidades_sin_nivel.append(
            {
                "id": None,
                "identificador": "Sin unidad asignada",
                "nivel_nombre": "",
                "tipo_unidad_label": "",
                "uso": "",
                "estancias": estancias_sin_unidad,
            }
        )

    if unidades_sin_nivel:
        grupos_unidades.append(
            {
                "titulo": "Sin nivel asignado",
                "meta": "",
                "unidades": unidades_sin_nivel,
            }
        )

    return {
        "visita_fotos_exteriores": visita_fotos_exteriores,
        "patologias_exteriores": patologias_exteriores,
        "grupos_unidades": grupos_unidades,
        "hay_unidades_o_estancias": bool(grupos_unidades),
    }


def preparar_grupos_estructura_estancias(estancias: list[dict]) -> list[dict]:
    grupos: list[dict] = []
    grupos_por_titulo: dict[str, dict] = {}

    for estancia in estancias:
        nivel_titulo = limpiar_texto(estancia.get("nivel_nombre")) or "Sin nivel asignado"
        grupo = grupos_por_titulo.get(nivel_titulo)
        if not grupo:
            grupo = {"titulo": nivel_titulo, "meta": "", "unidades": [], "_unidades": {}}
            grupos_por_titulo[nivel_titulo] = grupo
            grupos.append(grupo)

        unidad_clave = estancia.get("unidad_id") or f"sin-unidad-{nivel_titulo}"
        unidad = grupo["_unidades"].get(unidad_clave)
        if not unidad:
            unidad = {
                "id": estancia.get("unidad_id"),
                "identificador": limpiar_texto(estancia.get("unidad_identificador"))
                or "Sin unidad asignada",
                "nivel_nombre": limpiar_texto(estancia.get("nivel_nombre")),
                "tipo_unidad_label": estancia.get("unidad_tipo_unidad_label") or "",
                "uso": limpiar_texto(estancia.get("unidad_uso")),
                "estancias": [],
            }
            grupo["_unidades"][unidad_clave] = unidad
            grupo["unidades"].append(unidad)

        unidad["estancias"].append(estancia)

    for grupo in grupos:
        grupo.pop("_unidades", None)

    return grupos


def preparar_pendientes_revision_expediente(cur, expediente_id: int) -> dict:
    pendientes = []

    visitas = cur.execute(
        """
        SELECT v.*, e.tipo_informe
        FROM visitas v
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.expediente_id = ?
        ORDER BY v.id DESC
        """,
        (expediente_id,),
    ).fetchall()
    total_visitas = len(visitas)

    if not visitas:
        pendientes.append(
            {
                "tipo": "expediente_sin_visitas",
                "titulo": "Expediente sin visitas",
                "descripcion": "Todavía no hay ninguna visita registrada para este expediente.",
                "url": f"/nueva-visita/{expediente_id}",
                "accion": "Crear visita",
            }
        )

    for visita in visitas:
        objeto_visita = etiquetar_opcion(
            visita["ambito_visita"],
            AMBITO_VISITA_LABELS,
        ) or "Visita"
        estancias_count = cur.execute(
            "SELECT COUNT(*) FROM estancias WHERE visita_id = ?",
            (visita["id"],),
        ).fetchone()[0]
        patologias_interiores_count = cur.execute(
            "SELECT COUNT(*) FROM registros_patologias WHERE visita_id = ?",
            (visita["id"],),
        ).fetchone()[0]
        patologias_exteriores_count = cur.execute(
            "SELECT COUNT(*) FROM registros_patologias_exteriores WHERE visita_id = ?",
            (visita["id"],),
        ).fetchone()[0]

        if not cur.execute(
            """
            SELECT 1
            FROM visita_fotos
            WHERE visita_id = ? AND categoria = 'exterior'
            LIMIT 1
            """,
            (visita["id"],),
        ).fetchone():
            pendientes.append(
                {
                    "tipo": "visita_sin_foto_exterior",
                    "titulo": "Visita sin fotografía exterior",
                    "descripcion": f"Visita {visita['fecha']} · añade al menos una foto descriptiva del exterior.",
                    "url": f"/nueva-visita/{expediente_id}?visita_id={visita['id']}#exterior-edificio",
                    "accion": "Añadir foto exterior",
                }
            )

        if not cur.execute(
            "SELECT 1 FROM climatologia_visitas WHERE visita_id = ? LIMIT 1",
            (visita["id"],),
        ).fetchone():
            pendientes.append(
                {
                    "tipo": "visita_sin_climatologia",
                    "titulo": "Visita sin climatología",
                    "descripcion": f"Visita {visita['fecha']} · {objeto_visita}",
                    "url": f"/nueva-visita/{expediente_id}?visita_id={visita['id']}",
                    "accion": "Registrar climatología",
                }
            )

        if estancias_count == 0:
            pendientes.append(
                {
                    "tipo": "visita_sin_estancias",
                    "titulo": "Visita sin estancias",
                    "descripcion": f"Visita {visita['fecha']} · {objeto_visita}",
                    "url": f"/definir-estancias/{visita['id']}",
                    "accion": "Definir estancias",
                }
            )

        if limpiar_texto(visita["tipo_informe"]) == "patologias" and (
            patologias_interiores_count + patologias_exteriores_count
        ) == 0:
            pendientes.append(
                {
                    "tipo": "visita_sin_patologias",
                    "titulo": "Visita sin patologías registradas",
                    "descripcion": f"Visita {visita['fecha']} · {objeto_visita}",
                    "url": f"/registrar-patologias/{visita['id']}",
                    "accion": "Registrar patologías",
                }
            )

    estancias_pendientes_rows = cur.execute(
        """
        SELECT es.*,
               v.fecha AS visita_fecha,
               ue.identificador AS unidad_identificador,
               ne.nombre_nivel AS nivel_nombre,
               EXISTS(
                   SELECT 1
                   FROM estancia_fotos ef
                   WHERE ef.estancia_id = es.id
                   LIMIT 1
               ) AS tiene_foto_principal
        FROM estancias es
        JOIN visitas v ON es.visita_id = v.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE v.expediente_id = ?
        ORDER BY v.id DESC, es.id ASC
        """,
        (expediente_id,),
    ).fetchall()
    for row in estancias_pendientes_rows:
        estancia = dict(row)
        estancia["foto_principal_url"] = "__revision__" if estancia.get("tiene_foto_principal") else ""
        if calcular_estancia_rellena(estancia):
            continue
        contexto = " · ".join(
            texto
            for texto in (
                f"Visita {estancia['visita_fecha']}",
                estancia["unidad_identificador"],
                estancia["nivel_nombre"],
            )
            if limpiar_texto(texto)
        )
        pendientes.append(
            {
                "tipo": "estancia_pendiente",
                "titulo": f"Estancia pendiente: {estancia['nombre']}",
                "descripcion": contexto or "Faltan datos o evidencias de la estancia.",
                "url": f"/editar-estancia/{estancia['id']}?next=/resumen-registro/{expediente_id}",
                "accion": "Completar estancia",
                "visita_id": estancia["visita_id"],
            }
        )

    estancias_sin_foto = cur.execute(
        """
        SELECT es.id, es.nombre, es.visita_id, v.fecha,
               ue.identificador AS unidad_identificador,
               ne.nombre_nivel AS nivel_nombre
        FROM estancias es
        JOIN visitas v ON es.visita_id = v.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE v.expediente_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM estancia_fotos ef WHERE ef.estancia_id = es.id
          )
        ORDER BY v.id DESC, es.id ASC
        """,
        (expediente_id,),
    ).fetchall()
    for estancia in estancias_sin_foto:
        contexto = " · ".join(
            texto
            for texto in (
                f"Visita {estancia['fecha']}",
                estancia["unidad_identificador"],
                estancia["nivel_nombre"],
            )
            if limpiar_texto(texto)
        )
        pendientes.append(
            {
                "tipo": "estancia_sin_foto",
                "titulo": f"Estancia sin foto: {estancia['nombre']}",
                "descripcion": contexto,
                "url": f"/editar-estancia/{estancia['id']}?next=/resumen-registro/{expediente_id}",
                "accion": "Añadir foto",
            }
        )

    registros_sin_foto = cur.execute(
        """
        SELECT rp.id, rp.patologia, rp.visita_id, v.fecha,
               es.nombre AS estancia_nombre,
               ue.identificador AS unidad_identificador
        FROM registros_patologias rp
        JOIN visitas v ON rp.visita_id = v.id
        JOIN estancias es ON rp.estancia_id = es.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        WHERE v.expediente_id = ?
          AND TRIM(IFNULL(rp.foto, '')) = ''
          AND NOT EXISTS (
              SELECT 1 FROM registro_patologia_fotos rpf WHERE rpf.registro_id = rp.id
          )
        ORDER BY v.id DESC, rp.id DESC
        """,
        (expediente_id,),
    ).fetchall()
    for registro in registros_sin_foto:
        contexto = " · ".join(
            texto
            for texto in (
                f"Visita {registro['fecha']}",
                registro["estancia_nombre"],
                registro["unidad_identificador"],
            )
            if limpiar_texto(texto)
        )
        pendientes.append(
            {
                "tipo": "patologia_interior_sin_foto",
                "titulo": f"Patología interior sin foto: {registro['patologia']}",
                "descripcion": contexto,
                "url": f"/editar-registro/{registro['id']}?next=/resumen-registro/{expediente_id}",
                "accion": "Añadir foto",
            }
        )

    registros_exteriores_sin_foto = cur.execute(
        """
        SELECT rpe.id, rpe.patologia, rpe.zona_exterior, rpe.elemento_exterior,
               rpe.visita_id, v.fecha
        FROM registros_patologias_exteriores rpe
        JOIN visitas v ON rpe.visita_id = v.id
        WHERE v.expediente_id = ?
          AND TRIM(IFNULL(rpe.foto, '')) = ''
          AND NOT EXISTS (
              SELECT 1 FROM registro_patologia_exterior_fotos rpef
              WHERE rpef.registro_id = rpe.id
          )
        ORDER BY v.id DESC, rpe.id DESC
        """,
        (expediente_id,),
    ).fetchall()
    for registro in registros_exteriores_sin_foto:
        zona = etiquetar_opcion(registro["zona_exterior"], ZONA_EXTERIOR_LABELS)
        elemento = etiquetar_opcion(registro["elemento_exterior"], ELEMENTO_EXTERIOR_LABELS)
        contexto = " · ".join(
            texto
            for texto in (f"Visita {registro['fecha']}", zona, elemento)
            if limpiar_texto(texto)
        )
        pendientes.append(
            {
                "tipo": "patologia_exterior_sin_foto",
                "titulo": f"Patología exterior sin foto: {registro['patologia']}",
                "descripcion": contexto,
                "url": f"/editar-registro-exterior/{registro['id']}",
                "accion": "Añadir foto",
            }
        )

    cuadrantes_incompletos = cur.execute(
        """
        SELECT qmp.id, qmp.codigo_cuadrante, qmp.patologia_detectada, qmp.patologia_id,
               mp.titulo AS mapa_titulo, mp.visita_id, v.fecha
        FROM cuadrantes_mapa_patologia qmp
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        JOIN visitas v ON mp.visita_id = v.id
        WHERE v.expediente_id = ?
          AND (
              (
                  TRIM(IFNULL(qmp.patologia_detectada, '')) <> ''
                  AND qmp.patologia_id IS NULL
              )
              OR (
                  (
                      TRIM(IFNULL(qmp.descripcion, '')) <> ''
                      OR TRIM(IFNULL(qmp.patologia_detectada, '')) <> ''
                      OR TRIM(IFNULL(qmp.gravedad, '')) <> ''
                      OR qmp.patologia_id IS NOT NULL
                  )
                  AND TRIM(IFNULL(qmp.foto_detalle, '')) = ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM cuadrante_mapa_patologia_fotos qmpf
                      WHERE qmpf.cuadrante_id = qmp.id
                  )
              )
          )
        ORDER BY v.id DESC, mp.id DESC, qmp.id ASC
        """,
        (expediente_id,),
    ).fetchall()
    for cuadrante in cuadrantes_incompletos:
        falta_vinculo = limpiar_texto(cuadrante["patologia_detectada"]) and not cuadrante["patologia_id"]
        pendientes.append(
            {
                "tipo": "cuadrante_incompleto",
                "titulo": f"Cuadrante pendiente: {cuadrante['codigo_cuadrante']}",
                "descripcion": (
                    f"{cuadrante['mapa_titulo']} · Visita {cuadrante['fecha']} · "
                    f"{'sin patología vinculada' if falta_vinculo else 'sin foto de detalle'}"
                ),
                "url": f"/editar-cuadrante-mapa-patologia/{cuadrante['id']}",
                "accion": "Revisar cuadrante",
            }
        )

    prioridad_siguiente = (
        "expediente_sin_visitas",
        "visita_sin_foto_exterior",
        "visita_sin_estancias",
        "estancia_pendiente",
        "estancia_sin_foto",
        "patologia_interior_sin_foto",
        "patologia_exterior_sin_foto",
        "visita_sin_patologias",
    )

    def texto_siguiente_accion(pendiente: dict) -> str:
        tipo = pendiente["tipo"]
        titulo = limpiar_texto(pendiente["titulo"])
        if tipo == "expediente_sin_visitas":
            return "Crear primera visita"
        if tipo == "visita_sin_foto_exterior":
            return "Añadir foto exterior"
        if tipo == "visita_sin_estancias":
            return "Definir estancias"
        if tipo == "estancia_pendiente":
            return "Completar estructura interior"
        if tipo == "estancia_sin_foto":
            return f"Añadir foto a {titulo.replace('Estancia sin foto:', '').strip() or 'estancia'}"
        if tipo == "patologia_interior_sin_foto":
            return "Completar patología interior"
        if tipo == "patologia_exterior_sin_foto":
            return "Completar patología exterior"
        if tipo == "visita_sin_patologias":
            return "Registrar patologías"
        return pendiente["accion"]

    siguiente_accion = {
        "titulo": "Revisión completa",
        "descripcion": "No hay pendientes prioritarios detectados. Vuelve al expediente para cerrar la revisión de la visita.",
        "url": f"/detalle-expediente/{expediente_id}",
    }
    for tipo_prioritario in prioridad_siguiente:
        pendiente = next(
            (
                item
                for item in pendientes
                if item["tipo"] == tipo_prioritario
            ),
            None,
        )
        if pendiente:
            if tipo_prioritario == "estancia_pendiente":
                siguiente_accion = {
                    "titulo": "Completar estructura interior",
                    "descripcion": "Hay estancias pendientes de completar.",
                    "url": f"/definir-estancias/{pendiente['visita_id']}#estructura-interior",
                }
                break
            siguiente_accion = {
                "titulo": texto_siguiente_accion(pendiente),
                "descripcion": pendiente["descripcion"],
                "url": pendiente["url"],
            }
            break

    return {
        "pendientes": pendientes,
        "total": len(pendientes),
        "total_visitas": total_visitas,
        "siguiente_accion": siguiente_accion,
    }


def cargar_opciones_visita_multiunidad(cur, expediente_id: int):
    estructura = cargar_estructura_multiunidad(cur, expediente_id)
    unidades = estructura["unidades"]
    return {
        "niveles": estructura["niveles"],
        "unidades": unidades,
        "unidades_generales": [
            unidad
            for unidad in unidades
            if limpiar_texto(unidad.get("tipo_unidad")) not in {"zona_comun", "exterior"}
        ],
        "unidades_comunes": [
            unidad
            for unidad in unidades
            if limpiar_texto(unidad.get("tipo_unidad")) == "zona_comun"
            or limpiar_texto(unidad.get("vinculo_unidad")) == "comun"
        ],
        "unidades_exteriores": [
            unidad
            for unidad in unidades
            if limpiar_texto(unidad.get("tipo_unidad")) == "exterior"
            or limpiar_texto(unidad.get("vinculo_unidad")) == "exterior"
        ],
    }


def resolver_objeto_visita_label(
    ambito_visita: str,
    nivel_id,
    unidad_id,
    opciones_visita_multiunidad: dict,
):
    ambito = limpiar_texto(ambito_visita) or "edificio_completo"
    nivel_id_txt = str(nivel_id or "")
    unidad_id_txt = str(unidad_id or "")

    if ambito == "nivel" and nivel_id_txt:
        for nivel in opciones_visita_multiunidad["niveles"]:
            if str(nivel["id"]) == nivel_id_txt:
                return f"Nivel: {nivel['nombre_nivel']}"
    if ambito in {"unidad", "zona_comun", "exterior"} and unidad_id_txt:
        for unidad in opciones_visita_multiunidad["unidades"]:
            if str(unidad["id"]) == unidad_id_txt:
                etiqueta = {
                    "unidad": "Unidad",
                    "zona_comun": "Zona común",
                    "exterior": "Exterior",
                }.get(ambito, "Unidad")
                return f"{etiqueta}: {unidad['identificador']}"
    return etiquetar_opcion(ambito, AMBITO_VISITA_LABELS)


def validar_asociacion_visita(
    cur,
    expediente_id: int,
    user_id: int,
    ambito_visita: str,
    nivel_id,
    unidad_id,
):
    ambito_limpio = limpiar_texto(ambito_visita) or "edificio_completo"
    nivel_id_int = parse_optional_int(nivel_id)
    unidad_id_int = parse_optional_int(unidad_id)

    if ambito_limpio == "nivel":
        if not nivel_id_int:
            raise ValueError("Debes seleccionar un nivel para este ámbito de visita.")
        nivel = get_owned_nivel(cur, nivel_id_int, user_id)
        if not nivel or nivel["expediente_id"] != expediente_id:
            raise ValueError("El nivel seleccionado no es válido para este expediente.")
        unidad_id_int = None
    elif ambito_limpio in {"unidad", "zona_comun", "exterior"}:
        if not unidad_id_int:
            raise ValueError("Debes seleccionar una unidad para este ámbito de visita.")
        unidad = get_owned_unidad(cur, unidad_id_int, user_id)
        if not unidad or unidad["expediente_id"] != expediente_id:
            raise ValueError("La unidad seleccionada no es válida para este expediente.")
        tipo_unidad = limpiar_texto(unidad["tipo_unidad"])
        vinculo_unidad = limpiar_texto(unidad["vinculo_unidad"])
        if ambito_limpio == "zona_comun" and not (
            tipo_unidad == "zona_comun" or vinculo_unidad == "comun"
        ):
            raise ValueError("La unidad seleccionada no corresponde a una zona común.")
        if ambito_limpio == "exterior" and not (
            tipo_unidad == "exterior" or vinculo_unidad == "exterior"
        ):
            raise ValueError("La unidad seleccionada no corresponde a un exterior.")
        nivel_id_int = None
    else:
        nivel_id_int = None
        unidad_id_int = None

    return ambito_limpio, nivel_id_int, unidad_id_int


def redirect_detalle_expediente(expediente_id: int, mensaje: str = "", error: str = ""):
    url = f"/detalle-expediente/{expediente_id}"
    params = []
    if mensaje:
        params.append(f"mensaje={quote_plus(mensaje)}")
    if error:
        params.append(f"error={quote_plus(error)}")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return RedirectResponse(url=url, status_code=303)


def get_owned_visita(cur, visita_id: int, user_id: int):
    return cur.execute(
        """
        SELECT v.*,
               e.numero_expediente,
               e.direccion,
               e.owner_user_id,
               e.tipo_informe,
               e.ambito_patologias,
               e.tipo_inmueble,
               e.reformado,
               e.fecha_reforma,
               e.observaciones_reforma,
               e.dormitorios_unidad,
               e.banos_unidad,
               n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita,
               u.tipo_unidad AS tipo_unidad_visita
        FROM visitas v
        JOIN expedientes e ON v.expediente_id = e.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE v.id=? AND e.owner_user_id=?
        """,
        (visita_id, user_id),
    ).fetchone()


def describir_objeto_visita(visita) -> str:
    if not visita:
        return ""

    ambito = limpiar_texto(visita["ambito_visita"])
    if ambito == "nivel" and limpiar_texto(visita["nombre_nivel_visita"]):
        return f"Nivel: {visita['nombre_nivel_visita']}"
    if ambito == "zona_comun" and limpiar_texto(visita["identificador_unidad_visita"]):
        return f"Zona común: {visita['identificador_unidad_visita']}"
    if ambito == "exterior" and limpiar_texto(visita["identificador_unidad_visita"]):
        return f"Exterior: {visita['identificador_unidad_visita']}"
    if limpiar_texto(visita["identificador_unidad_visita"]):
        return f"Unidad: {visita['identificador_unidad_visita']}"
    return etiquetar_opcion(ambito, AMBITO_VISITA_LABELS)


def calcular_estancia_rellena(estancia: dict) -> bool:
    tiene_nombre = bool(limpiar_texto(estancia.get("nombre")))
    tiene_tipo = bool(limpiar_texto(estancia.get("tipo_estancia")))
    tiene_foto = any(
        [
            bool(estancia.get("foto_principal_url")),
            bool(limpiar_texto(estancia.get("foto"))),
            parsear_entero_positivo(estancia.get("tiene_foto_principal")) > 0,
            parsear_entero_positivo(estancia.get("total_fotos")) > 0,
        ]
    )
    requiere_planta = any(
        parsear_entero_positivo(estancia.get(campo)) > 0
        for campo in (
            "unidad_tiene_varias_plantas",
            "tiene_varias_plantas",
            "estancia_unidad_tiene_varias_plantas",
        )
    )
    tiene_planta_si_aplica = (
        bool(limpiar_texto(estancia.get("planta"))) if requiere_planta else True
    )

    return tiene_nombre and tiene_tipo and tiene_foto and tiene_planta_si_aplica


def preparar_navegacion_estancias_multiunidad(
    estructura_multiunidad: dict,
    estancias: list[dict],
    visita_id: int,
    unidad_id_seleccionada: int | None = None,
):
    resumen_por_unidad: dict[int, dict[str, int]] = {}
    sin_unidad = {"total": 0, "pendientes": 0}

    for estancia in estancias:
        unidad_estancia_id = estancia.get("unidad_id")
        if unidad_estancia_id:
            destino = resumen_por_unidad.setdefault(
                unidad_estancia_id, {"total": 0, "pendientes": 0}
            )
        else:
            destino = sin_unidad
        destino["total"] += 1
        if not estancia.get("esta_rellena"):
            destino["pendientes"] += 1

    def enriquecer_unidad(unidad: dict):
        stats = resumen_por_unidad.get(unidad["id"], {"total": 0, "pendientes": 0})
        unidad["total_estancias"] = stats["total"]
        unidad["pendientes_estancias"] = stats["pendientes"]
        unidad["tiene_estancias"] = stats["total"] > 0
        unidad["seleccionada"] = unidad["id"] == unidad_id_seleccionada
        unidad["gestion_url"] = f"/definir-estancias/{visita_id}?unidad_id={unidad['id']}"
        if unidad["tiene_estancias"]:
            unidad["gestion_url"] += "#estructura-interior"
        for anejo in unidad.get("anejos", []):
            enriquecer_unidad(anejo)

    for nivel in estructura_multiunidad["niveles"]:
        for grupo in ("principales", "otras"):
            for unidad in nivel.get(grupo, []):
                enriquecer_unidad(unidad)

    for grupo in ("principales", "otras"):
        for unidad in estructura_multiunidad["sin_nivel"].get(grupo, []):
            enriquecer_unidad(unidad)

    for anejo in estructura_multiunidad.get("anejos_sueltos", []):
        enriquecer_unidad(anejo)

    return {
        "estructura": estructura_multiunidad,
        "sin_unidad": sin_unidad,
    }


def validar_estancia_para_visita(cur, visita, estancia_id: int):
    estancia = cur.execute(
        """
        SELECT id, visita_id, unidad_id
        FROM estancias
        WHERE id=? AND visita_id=?
        """,
        (estancia_id, visita["id"]),
    ).fetchone()
    require_row(estancia, "Estancia no encontrada")

    visita_unidad_id = visita["unidad_id"]
    estancia_unidad_id = estancia["unidad_id"]

    if visita_unidad_id and estancia_unidad_id and visita_unidad_id != estancia_unidad_id:
        raise HTTPException(
            status_code=400,
            detail="La estancia seleccionada no es coherente con la unidad de la visita.",
        )

    return estancia


def get_owned_estancia(cur, estancia_id: int, user_id: int):
    return cur.execute(
        """
        SELECT es.*, v.expediente_id, v.unidad_id AS visita_unidad_id,
               v.ambito_visita, n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita,
               u.tiene_varias_plantas AS visita_unidad_tiene_varias_plantas,
               u.numero_plantas AS visita_unidad_numero_plantas,
               ue.identificador AS identificador_unidad_estancia,
               ue.tiene_varias_plantas AS estancia_unidad_tiene_varias_plantas,
               ue.numero_plantas AS estancia_unidad_numero_plantas,
               ne.nombre_nivel AS nombre_nivel_estancia
        FROM estancias es
        JOIN visitas v ON es.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE es.id=? AND e.owner_user_id=?
        """,
        (estancia_id, user_id),
    ).fetchone()


def preparar_modo_inspector_estancias(
    cur,
    visita_id: int,
    estancia_id: int,
    expediente_id: int,
):
    estancias = [
        dict(row)
        for row in cur.execute(
            """
            SELECT es.id, es.nombre, es.visita_id,
                   COUNT(DISTINCT ef.id) AS total_fotos,
                   COUNT(DISTINCT rp.id) AS total_patologias
            FROM estancias es
            LEFT JOIN estancia_fotos ef ON ef.estancia_id = es.id
            LEFT JOIN registros_patologias rp ON rp.estancia_id = es.id
            WHERE es.visita_id=?
            GROUP BY es.id
            ORDER BY es.id ASC
            """,
            (visita_id,),
        ).fetchall()
    ]

    indice_actual = next(
        (indice for indice, estancia in enumerate(estancias) if estancia["id"] == estancia_id),
        None,
    )
    if indice_actual is None:
        return None

    actual = estancias[indice_actual]
    anterior = estancias[indice_actual - 1] if indice_actual > 0 else None
    siguiente = (
        estancias[indice_actual + 1]
        if indice_actual + 1 < len(estancias)
        else None
    )
    revision_url = f"/resumen-registro/{expediente_id}"

    return {
        "actual": actual,
        "anterior": anterior,
        "siguiente": siguiente,
        "posicion": indice_actual + 1,
        "total": len(estancias),
        "revision_url": revision_url,
        "patologias_url": f"/registrar-patologias/{visita_id}?estancia_id={estancia_id}",
        "anterior_url": (
            f"/editar-estancia/{anterior['id']}?next={revision_url}"
            if anterior
            else ""
        ),
        "siguiente_url": (
            f"/editar-estancia/{siguiente['id']}?next={revision_url}"
            if siguiente
            else ""
        ),
    }


def get_owned_registro(cur, registro_id: int, user_id: int):
    return cur.execute(
        """
        SELECT rp.*, v.expediente_id, v.ambito_visita,
               n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita,
               es.nombre AS estancia_nombre,
               ue.identificador AS identificador_unidad_estancia,
               ne.nombre_nivel AS nombre_nivel_estancia
        FROM registros_patologias rp
        JOIN visitas v ON rp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        LEFT JOIN estancias es ON rp.estancia_id = es.id
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE rp.id=? AND e.owner_user_id=?
        """,
        (registro_id, user_id),
    ).fetchone()


def parsear_decimal_coste_patologia(valor, default: float = 0.0) -> float:
    texto = limpiar_texto(valor).replace("€", "").replace(" ", "")
    if not texto:
        return default
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return default


def obtener_costes_patologia(cur, patologia_id: int):
    return cur.execute(
        """
        SELECT
            pc.*,
            cc.codigo AS concepto_codigo,
            cc.resumen AS concepto_resumen,
            cc.estado AS concepto_estado,
            cb.nombre AS base_nombre,
            cb.origen AS base_origen
        FROM patologia_costes pc
        JOIN costes_conceptos cc ON cc.id = pc.concepto_id
        JOIN costes_bases cb ON cb.id = cc.base_id
        WHERE pc.patologia_id = ?
        ORDER BY pc.created_at DESC, pc.id DESC
        """,
        (patologia_id,),
    ).fetchall()


def buscar_partidas_coste_para_patologia(cur, q: str):
    q_limpia = limpiar_texto(q)
    if not q_limpia:
        return []
    patron = f"%{q_limpia.lower()}%"
    return cur.execute(
        """
        SELECT
            cc.id, cc.codigo, cc.unidad, cc.resumen, cc.descripcion,
            cc.precio, cc.moneda, cc.estado, cb.nombre AS base_nombre
        FROM costes_conceptos cc
        JOIN costes_bases cb ON cb.id = cc.base_id
        WHERE
            cc.estado = 'validado'
            AND (
                lower(cc.codigo) LIKE ?
                OR lower(cc.resumen) LIKE ?
                OR lower(COALESCE(cc.descripcion, '')) LIKE ?
            )
        ORDER BY cc.codigo COLLATE NOCASE, cc.resumen COLLATE NOCASE
        LIMIT 20
        """,
        (patron, patron, patron),
    ).fetchall()


def calcular_total_costes_patologia(costes) -> float:
    return round(sum(float(item["importe"] or 0) for item in costes), 2)


def preparar_presupuesto_reparacion_expediente(cur, expediente_id: int):
    filas = cur.execute(
        """
        SELECT
            pc.id AS vinculo_id,
            pc.patologia_id,
            pc.descripcion_actuacion,
            pc.cantidad,
            pc.unidad,
            pc.precio_unitario,
            pc.importe,
            pc.estado AS vinculo_estado,
            pc.observaciones AS vinculo_observaciones,
            rp.patologia,
            rp.elemento,
            rp.localizacion_dano,
            rp.detalle_localizacion,
            rp.observaciones AS patologia_observaciones,
            es.nombre AS estancia_nombre,
            cc.codigo AS concepto_codigo,
            cc.resumen AS concepto_resumen,
            cc.estado AS concepto_estado,
            cb.nombre AS base_nombre,
            cb.origen AS base_origen,
            cap.codigo AS capitulo_codigo,
            cap.nombre AS capitulo_nombre
        FROM patologia_costes pc
        JOIN registros_patologias rp ON rp.id = pc.patologia_id
        JOIN visitas v ON v.id = rp.visita_id
        LEFT JOIN estancias es ON es.id = rp.estancia_id
        JOIN costes_conceptos cc ON cc.id = pc.concepto_id
        JOIN costes_bases cb ON cb.id = cc.base_id
        LEFT JOIN costes_capitulos cap ON cap.id = cc.capitulo_id
        WHERE v.expediente_id = ?
        ORDER BY es.nombre COLLATE NOCASE, rp.id, pc.id
        """,
        (expediente_id,),
    ).fetchall()

    patologias_por_id: dict[int, dict] = {}
    resumen_capitulos: dict[str, dict] = {}
    total = 0.0

    for fila in filas:
        patologia_id = fila["patologia_id"]
        patologia = patologias_por_id.setdefault(
            patologia_id,
            {
                "id": patologia_id,
                "patologia": fila["patologia"],
                "elemento": fila["elemento"],
                "localizacion_dano": fila["localizacion_dano"],
                "detalle_localizacion": fila["detalle_localizacion"],
                "observaciones": fila["patologia_observaciones"],
                "estancia_nombre": fila["estancia_nombre"],
                "partidas": [],
                "subtotal": 0.0,
            },
        )
        importe = round(float(fila["importe"] or 0), 2)
        partida = dict(fila)
        partida["importe"] = importe
        patologia["partidas"].append(partida)
        patologia["subtotal"] = round(patologia["subtotal"] + importe, 2)
        total = round(total + importe, 2)

        clave_capitulo = limpiar_texto(fila["capitulo_codigo"])
        nombre_capitulo = limpiar_texto(fila["capitulo_nombre"])
        if not clave_capitulo:
            codigo = limpiar_texto(fila["concepto_codigo"])
            clave_capitulo = codigo.split(".")[0] if "." in codigo else codigo[:3]
            nombre_capitulo = f"Sin capítulo · {clave_capitulo or 'sin código'}"
        resumen = resumen_capitulos.setdefault(
            clave_capitulo,
            {
                "codigo": clave_capitulo,
                "nombre": nombre_capitulo or clave_capitulo,
                "importe": 0.0,
            },
        )
        resumen["importe"] = round(resumen["importe"] + importe, 2)

    return {
        "patologias": list(patologias_por_id.values()),
        "resumen_capitulos": sorted(
            resumen_capitulos.values(),
            key=lambda item: (item["codigo"] or "", item["nombre"] or ""),
        ),
        "total_pem": round(total, 2),
        "tiene_costes": bool(filas),
    }


def buscar_partidas_coste_para_actuacion(cur, q: str):
    q_limpia = limpiar_texto(q)
    if not q_limpia:
        return []
    patron = f"%{q_limpia.lower()}%"
    return cur.execute(
        """
        SELECT
            cc.id, cc.codigo, cc.unidad, cc.resumen, cc.descripcion,
            cc.precio, cc.moneda, cc.estado,
            cb.nombre AS base_nombre, cb.origen AS base_origen
        FROM costes_conceptos cc
        JOIN costes_bases cb ON cb.id = cc.base_id
        WHERE
            cc.estado = 'validado'
            AND (
                lower(cc.codigo) LIKE ?
                OR lower(cc.resumen) LIKE ?
                OR lower(COALESCE(cc.descripcion, '')) LIKE ?
            )
        ORDER BY cc.codigo COLLATE NOCASE, cc.resumen COLLATE NOCASE
        LIMIT 25
        """,
        (patron, patron, patron),
    ).fetchall()


def preparar_actuaciones_reparacion_expediente(cur, expediente_id: int):
    actuaciones = [
        dict(row)
        for row in cur.execute(
            """
            SELECT *
            FROM actuaciones_reparacion
            WHERE expediente_id = ?
            ORDER BY orden ASC, id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]

    actuaciones_por_id = {}
    total = 0.0
    for actuacion in actuaciones:
        actuacion["partidas"] = []
        actuacion["subtotal"] = 0.0
        actuaciones_por_id[actuacion["id"]] = actuacion

    if actuaciones_por_id:
        placeholders = ",".join("?" for _ in actuaciones_por_id)
        partidas = cur.execute(
            f"""
            SELECT
                ap.*,
                cc.codigo AS concepto_codigo,
                cc.resumen AS concepto_resumen,
                cc.estado AS concepto_estado,
                cb.nombre AS base_nombre,
                cb.origen AS base_origen
            FROM actuacion_partidas ap
            JOIN costes_conceptos cc ON cc.id = ap.concepto_id
            JOIN costes_bases cb ON cb.id = cc.base_id
            WHERE ap.actuacion_id IN ({placeholders})
            ORDER BY ap.id ASC
            """,
            tuple(actuaciones_por_id.keys()),
        ).fetchall()
        for fila in partidas:
            partida = dict(fila)
            importe = round(float(partida.get("importe") or 0), 2)
            partida["importe"] = importe
            actuacion = actuaciones_por_id[partida["actuacion_id"]]
            actuacion["partidas"].append(partida)
            actuacion["subtotal"] = round(actuacion["subtotal"] + importe, 2)
            total = round(total + importe, 2)

    return {
        "actuaciones": actuaciones,
        "total_pem": round(total, 2),
        "tiene_actuaciones": bool(actuaciones),
    }


PERICIAL_LIMITACION_KEYWORDS = (
    "no se pudo acceder",
    "no se puede comprobar",
    "sin realizar catas",
    "sin catas",
    "pruebas destructivas",
    "ensayos destructivos",
    "elementos ocultos",
    "documentación aportada",
    "documentacion aportada",
    "escasa visibilidad",
    "ausencia de luz",
    "no consta",
    "pendiente de comprobar",
)

PERICIAL_RECOMENDACION_KEYWORDS = (
    "revisar",
    "inspeccionar",
    "comprobar",
    "seguimiento",
    "recomend",
    "actuar",
    "prevenir",
    "moho",
    "insectos",
    "madera",
    "estructura",
    "urgencia",
    "desaconseja",
)


INFORME_V2_CAPITULOS = [
    {"clave": "resumen_ejecutivo", "titulo": "Resumen ejecutivo", "orden": 1},
    {"clave": "antecedentes_objeto", "titulo": "Antecedentes y objeto", "orden": 2},
    {"clave": "metodologia", "titulo": "Metodología", "orden": 3},
    {"clave": "limitaciones", "titulo": "Limitaciones", "orden": 4},
    {"clave": "analisis_causal", "titulo": "Análisis causal", "orden": 5},
    {
        "clave": "inventario_resumido_danos",
        "titulo": "Inventario resumido de daños",
        "orden": 6,
    },
    {
        "clave": "actuaciones_verificadas",
        "titulo": "Actuaciones verificadas",
        "orden": 7,
    },
    {"clave": "propuesta_reparacion", "titulo": "Propuesta de reparación", "orden": 8},
    {"clave": "valoracion_economica", "titulo": "Valoración económica", "orden": 9},
    {
        "clave": "recomendaciones_tecnicas",
        "titulo": "Recomendaciones técnicas",
        "orden": 10,
    },
    {
        "clave": "conclusiones_periciales",
        "titulo": "Conclusiones",
        "orden": 11,
    },
    {
        "clave": "anexo_e_partida_4",
        "titulo": "ANEXO E. Análisis de ejecución de la partida nº 4",
        "orden": 12,
    },
    {
        "clave": "anexo_f_mediciones",
        "titulo": "ANEXO F. Justificación de mediciones",
        "orden": 13,
    },
]

INFORME_V2_AYUDAS_CAPITULOS = {
    "resumen_ejecutivo": {
        "funcion": "Ofrecer una visión sintética del informe.",
        "incluir": "Encargo, daños principales, causa probable, reparación propuesta y coste estimado si procede.",
        "evitar": "Desarrollo técnico completo o inventarios detallados.",
        "relacion": "Resume el contenido del resto del informe.",
    },
    "antecedentes_objeto": {
        "funcion": "Delimitar el encargo y el objeto del dictamen.",
        "incluir": "Antecedentes relevantes, alcance solicitado, inmueble afectado y documentación de partida.",
        "evitar": "Entrar en conclusiones, valoración económica o inventario detallado.",
        "relacion": "Sitúa el marco del análisis que desarrollan los capítulos posteriores.",
    },
    "metodologia": {
        "funcion": "Explicar cómo se realizó el análisis.",
        "incluir": "Visita, documentación consultada, inspecciones y criterios aplicados.",
        "evitar": "Conclusiones técnicas o económicas.",
        "relacion": "Justifica la validez del análisis posterior.",
    },
    "limitaciones": {
        "funcion": "Identificar restricciones del trabajo realizado.",
        "incluir": "Zonas no accesibles, documentación no disponible o condicionantes relevantes.",
        "evitar": "Justificar conclusiones débiles.",
        "relacion": "Contextualiza el alcance del dictamen.",
    },
    "analisis_causal": {
        "funcion": "Explicar la relación entre causa y daño.",
        "incluir": "Mecanismo lesional, indicios observados y razonamiento técnico.",
        "evitar": "Repetir el inventario completo de daños.",
        "relacion": "Sirve de base para conclusiones y reparación.",
    },
    "inventario_resumido_danos": {
        "funcion": "Describir los daños observados.",
        "incluir": "Ubicación, alcance y características de cada lesión.",
        "evitar": "Explicaciones causales extensas.",
        "relacion": "Documenta los hechos observados.",
    },
    "actuaciones_verificadas": {
        "funcion": "Recoger intervenciones ya ejecutadas o comprobadas.",
        "incluir": "Trabajos realizados y evidencias observadas.",
        "evitar": "Propuestas futuras.",
        "relacion": "Complementa el análisis causal.",
    },
    "propuesta_reparacion": {
        "funcion": "Definir las medidas correctoras recomendadas.",
        "incluir": "Actuaciones necesarias para resolver los daños.",
        "evitar": "Desarrollo económico detallado.",
        "relacion": "Se valora económicamente en el capítulo siguiente.",
    },
    "valoracion_economica": {
        "funcion": "Cuantificar económicamente la reparación.",
        "incluir": "Importes, criterios y alcance económico.",
        "evitar": "Justificar técnicamente cada reparación.",
        "relacion": "Desarrolla económicamente la propuesta de reparación.",
    },
    "recomendaciones_tecnicas": {
        "funcion": "Aportar medidas preventivas o de seguimiento.",
        "incluir": "Mantenimiento, inspecciones futuras o controles recomendados.",
        "evitar": "Repetir conclusiones.",
        "relacion": "Complementa la reparación propuesta.",
    },
    "conclusiones_periciales": {
        "funcion": "Cerrar el dictamen.",
        "incluir": "Síntesis técnica, síntesis económica y dictamen final.",
        "evitar": "Copiar literalmente capítulos anteriores.",
        "relacion": "Resume el criterio pericial final.",
    },
    "anexo_e_partida_4": {
        "funcion": "Analizar de forma específica la ejecución de la partida nº 4.",
        "incluir": "Objeto del análisis, comprobaciones, valoración técnica y conclusión de la partida.",
        "evitar": "Repetir el presupuesto completo o sustituir la valoración general.",
        "relacion": "Complementa la valoración económica detallada.",
    },
    "anexo_f_mediciones": {
        "funcion": "Justificar mediciones y criterios de cuantificación.",
        "incluir": "Criterios de medición, unidades, zonas computadas y observaciones de alcance.",
        "evitar": "Duplicar la redacción de propuesta o conclusiones.",
        "relacion": "Da soporte a la valoración económica y a los anexos de coste.",
    },
}

INFORME_V2_CAPITULOS_POR_CLAVE = {
    capitulo["clave"]: capitulo for capitulo in INFORME_V2_CAPITULOS
}

PDF_EXPORT_PROFILE_DEFAULT = "informe_anexos"

PDF_EXPORT_PROFILES = {
    "master": {
        "codigo": "master",
        "nombre": "Maestro",
        "descripcion": "PDF completo actual, sin compresión adicional, para archivo maestro.",
        "incluye_anexos": True,
        "objetivo_mb": None,
        "optimizar_imagenes": False,
        "jpeg_quality": 95,
        "max_dimension": 3000,
        "remove_exif": False,
    },
    "email": {
        "codigo": "email",
        "nombre": "Email",
        "descripcion": "Perfil preparado para envío por email; en V1 reutiliza la generación completa.",
        "incluye_anexos": True,
        "objetivo_mb": 20,
        "optimizar_imagenes": True,
        "jpeg_quality": 75,
        "max_dimension": 1400,
        "remove_exif": True,
    },
    "judicial": {
        "codigo": "judicial",
        "nombre": "Judicial / LexNET",
        "descripcion": "Perfil preparado para presentación judicial; en V1 reutiliza la generación completa.",
        "incluye_anexos": True,
        "objetivo_mb": 10,
        "optimizar_imagenes": True,
        "jpeg_quality": 60,
        "max_dimension": 1200,
        "remove_exif": True,
    },
    "solo_informe": {
        "codigo": "solo_informe",
        "nombre": "Solo informe",
        "descripcion": "Genera únicamente el cuerpo principal del informe, sin anexos PDF fusionados.",
        "incluye_anexos": False,
        "objetivo_mb": None,
        "optimizar_imagenes": True,
        "jpeg_quality": 80,
        "max_dimension": 1600,
        "remove_exif": True,
    },
    "informe_anexos": {
        "codigo": "informe_anexos",
        "nombre": "Informe + anexos",
        "descripcion": "Equivalente funcional al comportamiento actual.",
        "incluye_anexos": True,
        "objetivo_mb": None,
        "optimizar_imagenes": False,
        "jpeg_quality": 95,
        "max_dimension": 3000,
        "remove_exif": False,
    },
    "anexo_fotografico": {
        "codigo": "anexo_fotografico",
        "nombre": "Anexo fotográfico",
        "descripcion": "Perfil preparado para generar solo el anexo fotográfico en una fase posterior.",
        "incluye_anexos": False,
        "objetivo_mb": None,
        "optimizar_imagenes": True,
        "jpeg_quality": 75,
        "max_dimension": 1600,
        "remove_exif": True,
        "implementado": False,
    },
}


INFORME_V2_CLAVES_FUERA_CUERPO_PDF = {
    "conclusiones_periciales",
    "anexo_e_partida_4",
    "anexo_f_mediciones",
}

INFORME_V2_CLAVE_CONCLUSIONES = "conclusiones_periciales"
INFORME_V2_CLAVE_CONCLUSIONES_LEGACY = "conclusiones_tecnicas"

INFORME_V2_ESTADOS_REVISION = (
    "Pendiente",
    "Borrador",
    "En revisión",
    "Terminado",
    "Bloqueado",
)

INFORME_V2_CAPITULOS_OBLIGATORIOS_DIAGNOSTICO = (
    "resumen_ejecutivo",
    "metodologia",
    "analisis_causal",
    "inventario_resumido_danos",
    "actuaciones_verificadas",
    "propuesta_reparacion",
    "valoracion_economica",
    "conclusiones_periciales",
)


TIPOS_DOCUMENTALES_ANEXO_A = (
    "Presupuesto",
    "Factura",
    "Informe técnico",
    "Certificado",
    "Correo electrónico",
    "Documento registral/catastral",
    "Fotografía histórica",
    "Otro",
)


def contenido_base_anexo_e_partida_4_v2() -> str:
    return (
        "E.1 Objeto\n\n"
        "El presente anexo tiene por objeto analizar la ejecución material de la partida nº 4 incluida en el presupuesto de reparación de cubierta aportado para su estudio, verificando su adecuación técnica respecto a los trabajos realmente observados durante la inspección.\n\n"
        "E.2 Documentación analizada\n\n"
        "Para la elaboración del presente análisis se ha tenido en consideración la documentación aportada por la propiedad, el presupuesto de reparación de cubierta, el reportaje fotográfico disponible y la inspección visual realizada durante la visita técnica.\n\n"
        "E.3 Descripción de la partida analizada\n\n"
        "[Completar descripción de la partida nº 4 según presupuesto aportado.]\n\n"
        "E.4 Comprobaciones realizadas\n\n"
        "[Completar comprobaciones efectuadas durante la inspección.]\n\n"
        "E.5 Valoración técnica\n\n"
        "[Completar valoración sobre ejecución correcta, parcial, insuficiente o no verificable.]\n\n"
        "E.6 Conclusión\n\n"
        "[Completar conclusión técnica sobre la partida analizada.]"
    )


def contenido_base_anexo_f_mediciones_v2() -> str:
    return (
        "F.1 Criterios de medición\n\n"
        "Las mediciones empleadas en la valoración económica se han obtenido a partir de la inspección realizada, de las superficies afectadas observadas durante la visita y de las comprobaciones efectuadas mediante reportaje fotográfico y documentación disponible.\n\n"
        "F.2 Desarrollo de mediciones\n\n"
        "[Completar desglose de mediciones por estancia, zona o actuación.]\n\n"
        "F.3 Observaciones\n\n"
        "[Completar observaciones sobre estimaciones, limitaciones, mediciones indirectas o zonas no accesibles.]"
    )


def normalizar_busqueda_pericial(texto: str) -> str:
    texto = limpiar_texto(texto).lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def dividir_fragmentos_periciales(texto: str) -> list[str]:
    texto = limpiar_texto(texto)
    if not texto:
        return []
    partes = re.split(r"[\n\r]+|(?<=[.!?])\s+", texto)
    return [limpiar_texto(parte) for parte in partes if limpiar_texto(parte)]


def extraer_candidatos_periciales(
    fuentes: list[dict],
    keywords: tuple[str, ...],
    limite: int = 12,
) -> list[dict]:
    candidatos = []
    vistos = set()
    keywords_norm = [normalizar_busqueda_pericial(item) for item in keywords]
    for fuente in fuentes:
        origen = limpiar_texto(fuente.get("origen"))
        texto = limpiar_texto(fuente.get("texto"))
        for fragmento in dividir_fragmentos_periciales(texto):
            fragmento_norm = normalizar_busqueda_pericial(fragmento)
            if not any(keyword in fragmento_norm for keyword in keywords_norm):
                continue
            clave = fragmento_norm[:220]
            if clave in vistos:
                continue
            vistos.add(clave)
            candidatos.append(
                {
                    "origen": origen or "Texto técnico",
                    "texto": fragmento,
                }
            )
            if len(candidatos) >= limite:
                return candidatos
    return candidatos


def estado_capitulo_pericial(completo: bool, parcial: bool = False) -> str:
    if completo:
        return "completo"
    if parcial:
        return "parcial"
    return "pendiente"


def generar_borrador_informe_v2(
    expediente: dict,
    visitas: list[dict],
    inventario: list[dict],
    metricas: dict,
    actuaciones: dict,
    limitaciones_candidatas: list[dict],
    recomendaciones_candidatas: list[dict],
) -> list[dict]:
    numero = limpiar_texto(expediente.get("numero_expediente")) or "sin numero"
    descripcion = limpiar_texto(expediente.get("descripcion_dano"))
    causa = limpiar_texto(expediente.get("causa_probable"))
    pruebas = limpiar_texto(expediente.get("pruebas_indicios"))
    evolucion = limpiar_texto(expediente.get("evolucion_preexistencia"))
    propuesta = limpiar_texto(expediente.get("propuesta_reparacion"))
    urgencia = limpiar_texto(expediente.get("urgencia_gravedad"))
    total_patologias = (
        metricas.get("patologias_interiores", 0)
        + metricas.get("patologias_exteriores", 0)
    )
    pem_total = formatear_numero_es(metricas.get("pem_total"), 2)
    roles_causa = [
        item
        for item in inventario
        if "causa" in normalizar_busqueda_pericial(item.get("rol_patologia_observado"))
    ]
    roles_efecto = [
        item
        for item in inventario
        if "efecto" in normalizar_busqueda_pericial(item.get("rol_patologia_observado"))
    ]
    tecnicos = sorted(
        {
            limpiar_texto(visita.get("tecnico"))
            for visita in visitas
            if limpiar_texto(visita.get("tecnico"))
        }
    )
    climas = [
        limpiar_texto(visita.get("climatologia"))
        for visita in visitas
        if limpiar_texto(visita.get("climatologia"))
    ]

    resumen_parrafos = [
        (
            f"El expediente {numero} documenta {descripcion}."
            if descripcion
            else f"El expediente {numero} no tiene todavia una descripcion de danos formal."
        ),
        (
            f"La causa probable consignada es: {causa}."
            if causa
            else "No consta causa probable informada en los datos existentes."
        ),
        (
            f"El alcance registrado incluye {total_patologias} patologias y "
            f"{metricas.get('fotografias', 0)} fotografias. "
            f"La valoracion economica disponible asciende a {pem_total} EUR de PEM."
        ),
    ]

    metodologia_parrafos = [
        (
            f"Constan {len(visitas)} visita(s) asociadas al expediente"
            + (f", realizadas por {', '.join(tecnicos)}." if tecnicos else ".")
            if visitas
            else "No constan visitas registradas para construir la metodologia."
        ),
        (
            "La climatologia disponible indica: " + " / ".join(climas) + "."
            if climas
            else "No consta resumen climatologico asociado a las visitas."
        ),
        (
            f"El soporte grafico disponible incluye {metricas.get('fotografias', 0)} "
            "fotografias vinculadas a visita, estancias o patologias."
        ),
    ]

    if limitaciones_candidatas:
        limitaciones_parrafos = [
            "Como limitaciones tecnicas candidatas se identifican: "
            + "; ".join(
                f"{item['origen']}: {item['texto']}"
                for item in limitaciones_candidatas[:5]
            )
            + "."
        ]
    else:
        limitaciones_parrafos = [
            "No se han detectado limitaciones candidatas con los datos actuales; "
            "este capitulo requiere revision expresa del tecnico."
        ]

    analisis_parrafos = [
        (
            f"El analisis causal parte de la causa probable registrada: {causa}."
            if causa
            else "No consta causa probable suficiente para redactar el analisis causal."
        ),
        (
            f"Los indicios recogidos son: {pruebas}."
            if pruebas
            else "No constan pruebas o indicios formalizados en el expediente."
        ),
        (
            f"Se han identificado {len(roles_causa)} patologia(s) con rol causa y "
            f"{len(roles_efecto)} con rol efecto."
            if roles_causa or roles_efecto
            else "No hay roles causa/efecto suficientes en las patologias; la relacion causal debe revisarse manualmente."
        ),
    ]

    recomendaciones_fuente = []
    for etiqueta, texto in [
        ("Urgencia / gravedad", urgencia),
        ("Evolucion / preexistencia", evolucion),
        ("Propuesta de reparacion", propuesta),
    ]:
        if texto:
            recomendaciones_fuente.append(f"{etiqueta}: {texto}")
    recomendaciones_fuente.extend(
        f"{item['origen']}: {item['texto']}"
        for item in recomendaciones_candidatas[:5]
    )
    recomendaciones_parrafos = [
        (
            "Las recomendaciones candidatas derivadas de los datos actuales son: "
            + "; ".join(recomendaciones_fuente)
            + "."
        )
        if recomendaciones_fuente
        else "No se han detectado recomendaciones tecnicas candidatas; este capitulo requiere redaccion tecnica."
    ]

    return [
        {
            "titulo": "Resumen ejecutivo",
            "parrafos": resumen_parrafos,
            "fuentes": [
                "descripcion_dano",
                "causa_probable",
                "patologias",
                "fotografias",
                "actuaciones_reparacion",
            ],
        },
        {
            "titulo": "Metodologia",
            "parrafos": metodologia_parrafos,
            "fuentes": ["visitas", "climatologia_visitas", "fotografias"],
        },
        {
            "titulo": "Limitaciones",
            "parrafos": limitaciones_parrafos,
            "fuentes": ["limitaciones candidatas derivadas"],
        },
        {
            "titulo": "Analisis causal",
            "parrafos": analisis_parrafos,
            "fuentes": [
                "causa_probable",
                "pruebas_indicios",
                "roles causa/efecto",
            ],
        },
        {
            "titulo": "Recomendaciones",
            "parrafos": recomendaciones_parrafos,
            "fuentes": [
                "urgencia_gravedad",
                "evolucion_preexistencia",
                "propuesta_reparacion",
                "recomendaciones candidatas derivadas",
            ],
        },
    ]


def unir_parrafos_borrador(bloque: dict | None) -> str:
    if not bloque:
        return ""
    return "\n\n".join(limpiar_texto(parrafo) for parrafo in bloque.get("parrafos", []) if limpiar_texto(parrafo))


def generar_contenido_inicial_editor_v2(workbench: dict) -> dict[str, str]:
    expediente = workbench["expediente"]
    metricas = workbench["metricas"]
    borradores = {
        bloque["titulo"]: bloque
        for bloque in workbench.get("borrador_informe", [])
    }
    inventario = workbench.get("inventario", [])
    actuaciones = workbench.get("actuaciones", {})

    lineas_inventario = []
    for item in inventario:
        zona = limpiar_texto(item.get("zona")) or "Zona sin identificar"
        patologia = limpiar_texto(item.get("patologia")) or "Patología sin identificar"
        elemento = limpiar_texto(item.get("elemento")) or "Elemento sin identificar"
        rol = limpiar_texto(item.get("rol_patologia_observado")) or "rol pendiente"
        fotos = item.get("fotos") or 0
        lineas_inventario.append(
            f"- {zona}: {patologia} en {elemento} ({rol}, {fotos} foto(s))."
        )

    lineas_actuaciones = []
    for actuacion in actuaciones.get("actuaciones", []):
        lineas_actuaciones.append(
            f"- {actuacion.get('titulo')}: {formatear_numero_es(actuacion.get('subtotal'), 2)} EUR."
        )
        for partida in actuacion.get("partidas", []):
            lineas_actuaciones.append(
                "  - "
                f"{partida.get('descripcion_snapshot') or partida.get('concepto_resumen')}: "
                f"{formatear_numero_es(partida.get('cantidad'), 4)} "
                f"{partida.get('unidad_snapshot') or ''} x "
                f"{formatear_numero_es(partida.get('precio_unitario_snapshot'), 2)} EUR = "
                f"{formatear_numero_es(partida.get('importe'), 2)} EUR."
            )

    objeto = limpiar_texto(expediente.get("objeto_pericia"))
    antecedentes = objeto or (
        "El presente informe tiene por objeto analizar los daños descritos en el expediente "
        f"{limpiar_texto(expediente.get('numero_expediente'))}, valorar su alcance técnico "
        "y ordenar la información disponible para su revisión pericial."
    )
    propuesta = limpiar_texto(expediente.get("propuesta_reparacion"))
    causa = limpiar_texto(expediente.get("causa_probable"))
    pruebas = limpiar_texto(expediente.get("pruebas_indicios"))

    return {
        "resumen_ejecutivo": unir_parrafos_borrador(borradores.get("Resumen ejecutivo")),
        "antecedentes_objeto": antecedentes,
        "metodologia": unir_parrafos_borrador(borradores.get("Metodologia")),
        "limitaciones": unir_parrafos_borrador(borradores.get("Limitaciones")),
        "analisis_causal": unir_parrafos_borrador(borradores.get("Analisis causal")),
        "inventario_resumido_danos": "\n".join(lineas_inventario)
        or "No hay inventario resumido de daños disponible.",
        "actuaciones_verificadas": "\n".join(lineas_actuaciones)
        or "No constan actuaciones verificadas en los datos existentes.",
        "propuesta_reparacion": propuesta or "No consta propuesta de reparación formal.",
        "valoracion_economica": (
            f"La valoración económica disponible asciende a "
            f"{formatear_numero_es(metricas.get('pem_total'), 2)} EUR de PEM."
        ),
        "recomendaciones_tecnicas": unir_parrafos_borrador(
            borradores.get("Recomendaciones")
        ),
        "conclusiones_tecnicas": (
            f"De los datos actuales se desprende como causa probable: {causa}."
            if causa
            else "Conclusiones técnicas pendientes de redacción."
        ),
        "conclusiones_periciales": (
            f"Los indicios disponibles ({pruebas}) deberán integrarse en una conclusión pericial final defendible."
            if pruebas
            else "Conclusiones periciales pendientes de redacción."
        ),
        "anexo_e_partida_4": contenido_base_anexo_e_partida_4_v2(),
        "anexo_f_mediciones": contenido_base_anexo_f_mediciones_v2(),
    }


def obtener_capitulos_guardados_informe_v2(cur, expediente_id: int) -> dict[str, dict]:
    filas = cur.execute(
        """
        SELECT *
        FROM informe_v2_capitulos
        WHERE expediente_id = ?
        ORDER BY orden ASC, id ASC
        """,
        (expediente_id,),
    ).fetchall()
    return {fila["clave"]: dict(fila) for fila in filas}


def obtener_versiones_informe_v2(cur, expediente_id: int) -> dict[str, list[dict]]:
    filas = cur.execute(
        """
        SELECT *
        FROM informe_v2_capitulo_versiones
        WHERE expediente_id = ?
        ORDER BY clave ASC, created_at DESC, id DESC
        """,
        (expediente_id,),
    ).fetchall()
    versiones: dict[str, list[dict]] = {}
    for fila in filas:
        version = dict(fila)
        versiones.setdefault(version["clave"], []).append(version)
    return versiones


def resolver_metadatos_portada_informe_v2(metadatos: dict | None = None) -> dict:
    metadatos = metadatos or {}
    titulo = limpiar_texto(metadatos.get("titulo_portada"))
    subtitulo = limpiar_texto(metadatos.get("subtitulo_portada"))
    return {
        "titulo_portada": titulo,
        "subtitulo_portada": subtitulo,
        "titulo_portada_pdf": titulo or INFORME_V2_TITULO_PORTADA_DEFAULT,
        "subtitulo_portada_pdf": subtitulo or INFORME_V2_SUBTITULO_PORTADA_DEFAULT,
        "updated_at": limpiar_texto(metadatos.get("updated_at")),
    }


def obtener_metadatos_informe_v2(cur, expediente_id: int) -> dict:
    fila = cur.execute(
        """
        SELECT titulo_portada, subtitulo_portada, updated_at
        FROM informe_v2_metadatos
        WHERE expediente_id = ?
        """,
        (expediente_id,),
    ).fetchone()
    return resolver_metadatos_portada_informe_v2(dict(fila) if fila else {})


def guardar_metadatos_informe_v2(
    cur,
    expediente_id: int,
    titulo_portada: str | None,
    subtitulo_portada: str | None,
) -> dict:
    titulo = limpiar_texto(titulo_portada)
    subtitulo = limpiar_texto(subtitulo_portada)
    cur.execute(
        """
        INSERT INTO informe_v2_metadatos (
            expediente_id, titulo_portada, subtitulo_portada, updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(expediente_id) DO UPDATE SET
            titulo_portada = excluded.titulo_portada,
            subtitulo_portada = excluded.subtitulo_portada,
            updated_at = CURRENT_TIMESTAMP
        """,
        (expediente_id, titulo, subtitulo),
    )
    return obtener_metadatos_informe_v2(cur, expediente_id)


def guardar_campo_metadatos_informe_v2(
    cur,
    expediente_id: int,
    campo: str,
    valor: str | None,
) -> dict:
    actuales = obtener_metadatos_informe_v2(cur, expediente_id)
    datos = {
        "titulo_portada": actuales["titulo_portada"],
        "subtitulo_portada": actuales["subtitulo_portada"],
    }
    datos[campo] = limpiar_texto(valor)
    return guardar_metadatos_informe_v2(
        cur,
        expediente_id,
        datos["titulo_portada"],
        datos["subtitulo_portada"],
    )


def resolver_capitulo_guardado_editor_v2(
    guardados: dict[str, dict], clave: str
) -> tuple[dict | None, str]:
    guardado = guardados.get(clave)
    contenido = limpiar_texto(guardado.get("contenido")) if guardado else ""
    if clave != INFORME_V2_CLAVE_CONCLUSIONES or contenido:
        return guardado, contenido

    guardado_legacy = guardados.get(INFORME_V2_CLAVE_CONCLUSIONES_LEGACY)
    contenido_legacy = (
        limpiar_texto(guardado_legacy.get("contenido")) if guardado_legacy else ""
    )
    if contenido_legacy:
        return guardado, contenido_legacy
    return guardado, contenido


def normalizar_estado_revision_informe_v2(valor: str | None) -> str:
    estado = limpiar_texto(valor)
    return estado if estado in INFORME_V2_ESTADOS_REVISION else "Pendiente"


def resumir_estados_revision_informe_v2(capitulos: list[dict]) -> dict:
    conteos = {estado: 0 for estado in INFORME_V2_ESTADOS_REVISION}
    indicadores = []
    iconos = {
        "Pendiente": "✗",
        "Borrador": "•",
        "En revisión": "⚠",
        "Terminado": "✓",
        "Bloqueado": "⛔",
    }
    clases = {
        "Pendiente": "pendiente",
        "Borrador": "borrador",
        "En revisión": "revision",
        "Terminado": "terminado",
        "Bloqueado": "bloqueado",
    }
    for capitulo in capitulos:
        estado = normalizar_estado_revision_informe_v2(capitulo.get("estado_revision"))
        conteos[estado] += 1
        indicadores.append(
            {
                "clave": capitulo["clave"],
                "titulo": capitulo["titulo"],
                "estado": estado,
                "icono": iconos[estado],
                "clase": clases[estado],
            }
        )
    return {
        "conteos": conteos,
        "indicadores": indicadores,
        "opciones": INFORME_V2_ESTADOS_REVISION,
    }


def preparar_anexos_derivados_editor_v2(contexto_editor: dict) -> dict:
    total_fotos = 0
    patologias_con_fotos = set()
    estancias_con_danos = set()
    patologias_interiores = 0

    total_fotos += len(contexto_editor.get("fotos_exteriores") or [])

    for grupo in contexto_editor.get("grupos_unidades") or []:
        for unidad in grupo.get("unidades") or []:
            for estancia in unidad.get("estancias") or []:
                total_fotos += len(estancia.get("fotos") or [])
                patologias = estancia.get("patologias") or []
                if patologias:
                    estancias_con_danos.add(estancia.get("id"))
                for patologia in patologias:
                    patologias_interiores += 1
                    fotos_patologia = patologia.get("fotos") or []
                    total_fotos += len(fotos_patologia)
                    if fotos_patologia:
                        patologias_con_fotos.add(f"interior-{patologia.get('id')}")

    for patologia in contexto_editor.get("patologias_exteriores") or []:
        fotos_patologia = patologia.get("fotos") or []
        total_fotos += len(fotos_patologia)
        if fotos_patologia:
            patologias_con_fotos.add(f"exterior-{patologia.get('id')}")

    anexo_b_disponible = total_fotos > 0
    anexo_c_disponible = bool(estancias_con_danos) or patologias_interiores > 0
    return {
        "anexo_b": {
            "disponible": anexo_b_disponible,
            "fotografias": total_fotos,
            "patologias_con_fotos": len(patologias_con_fotos),
            "mensaje": (
                "El reportaje fotográfico se generará automáticamente agrupado por patología. "
                "No es necesario describir individualmente cada fotografía."
            ),
        },
        "anexo_c": {
            "disponible": anexo_c_disponible,
            "estancias_con_danos": len(estancias_con_danos),
            "patologias_interiores": patologias_interiores,
            "mensaje": (
                "Las fichas de daños se generarán automáticamente agrupadas por estancia. "
                "No es necesario reproducir aquí el inventario completo de daños estancia por estancia."
            ),
        },
    }


def contar_menciones_editoriales_v2(texto: str, terminos: tuple[str, ...]) -> int:
    texto_normalizado = limpiar_texto(texto).lower()
    return sum(
        len(
            re.findall(
                rf"(?<!\w){re.escape(termino)}(?!\w)",
                texto_normalizado,
            )
        )
        for termino in terminos
    )


def evaluar_advertencias_editoriales_informe_v2(
    capitulos: list[dict],
    anexos_derivados: dict,
) -> list[dict]:
    capitulos_por_clave = {capitulo["clave"]: capitulo for capitulo in capitulos}
    advertencias = []

    def contenido(clave: str) -> str:
        return limpiar_texto(capitulos_por_clave.get(clave, {}).get("contenido"))

    def titulo(clave: str) -> str:
        return limpiar_texto(capitulos_por_clave.get(clave, {}).get("titulo")) or clave

    def agregar(clave: str, explicacion: str, recomendacion: str, regla: str):
        advertencias.append(
            {
                "icono": "⚠",
                "clave": clave,
                "capitulo": titulo(clave),
                "explicacion": explicacion,
                "recomendacion": recomendacion,
                "regla": regla,
            }
        )

    claves_redaccion = [
        capitulo["clave"]
        for capitulo in capitulos
        if capitulo["clave"] not in {"anexo_e_partida_4", "anexo_f_mediciones"}
    ]
    if anexos_derivados.get("anexo_b", {}).get("disponible"):
        terminos_fotos = ("foto", "fotografía", "imagen", "figura")
        for clave in claves_redaccion:
            if contar_menciones_editoriales_v2(contenido(clave), terminos_fotos) >= 5:
                agregar(
                    clave,
                    "El capítulo contiene numerosas referencias a fotografías. Parte del contenido podría estar ya cubierto por el Anexo B (reportaje fotográfico).",
                    "Reduzca las menciones foto a foto y deje el detalle visual al anexo automático.",
                    "A",
                )

    if anexos_derivados.get("anexo_c", {}).get("disponible"):
        terminos_estancias = (
            "estancia",
            "dormitorio",
            "cocina",
            "baño",
            "salón",
            "habitación",
        )
        for clave in claves_redaccion:
            if contar_menciones_editoriales_v2(contenido(clave), terminos_estancias) >= 5:
                agregar(
                    clave,
                    "El capítulo contiene un inventario detallado de estancias o daños por estancia. Parte de la información podría estar ya cubierta por el Anexo C.",
                    "Mantenga aquí la síntesis y deje el detalle estancia por estancia a las fichas automáticas.",
                    "B",
                )

    if contar_menciones_editoriales_v2(
        contenido("conclusiones_periciales"),
        ("antecedentes", "cronología", "visita", "inspección realizada", "fecha de visita"),
    ) >= 3:
        agregar(
            "conclusiones_periciales",
            "Las conclusiones contienen elementos propios de antecedentes o cronología. Considere mantener las conclusiones centradas en las respuestas periciales.",
            "Traslade el relato temporal a antecedentes o metodología y reserve conclusiones para el dictamen final.",
            "C",
        )

    if contar_menciones_editoriales_v2(
        contenido("antecedentes_objeto"),
        (
            "concluye",
            "se concluye",
            "por tanto",
            "se determina",
            "responsabilidad",
            "causa principal",
        ),
    ) >= 3:
        agregar(
            "antecedentes_objeto",
            "Los antecedentes parecen incluir conclusiones periciales. Considere reservar las conclusiones para el capítulo específico.",
            "Deje en antecedentes solo encargo, contexto y objeto; mueva el criterio final a Conclusiones.",
            "D",
        )

    if contar_menciones_editoriales_v2(
        contenido("valoracion_economica"),
        ("origen del daño", "causa", "mecanismo lesional", "etiología"),
    ) >= 3:
        agregar(
            "valoracion_economica",
            "La valoración económica parece incluir análisis causal. Considere reservar el análisis técnico para los capítulos de daños y conclusiones.",
            "Mantenga la valoración centrada en importes, mediciones y alcance económico.",
            "E",
        )

    return advertencias


def evaluar_diagnostico_informe_v2(capitulos: list[dict], workbench: dict) -> dict:
    capitulos_por_clave = {capitulo["clave"]: capitulo for capitulo in capitulos}
    metricas = workbench.get("metricas", {})
    actuaciones = workbench.get("actuaciones", {})
    total_patologias = int(metricas.get("patologias_interiores") or 0) + int(
        metricas.get("patologias_exteriores") or 0
    )
    total_visitas = int(metricas.get("visitas") or 0)
    total_fotos = int(metricas.get("fotografias") or 0)
    total_actuaciones = len(actuaciones.get("actuaciones") or [])
    total_partidas = sum(
        len(actuacion.get("partidas") or [])
        for actuacion in actuaciones.get("actuaciones") or []
    )

    errores = []
    advertencias = []
    indicadores = []

    def contenido(clave: str) -> str:
        return limpiar_texto(capitulos_por_clave.get(clave, {}).get("contenido"))

    def titulo(clave: str) -> str:
        return limpiar_texto(capitulos_por_clave.get(clave, {}).get("titulo")) or clave

    def agregar_error(clave: str, mensaje: str):
        errores.append({"capitulo": titulo(clave), "clave": clave, "mensaje": mensaje})

    def agregar_advertencia(clave: str, mensaje: str):
        advertencias.append(
            {"capitulo": titulo(clave), "clave": clave, "mensaje": mensaje}
        )

    def longitud(clave: str) -> int:
        return len(contenido(clave))

    reglas_error_vacio = {
        "resumen_ejecutivo": "El resumen ejecutivo está vacío.",
        "metodologia": "La metodología está vacía.",
        "analisis_causal": "El análisis causal está vacío.",
        "inventario_resumido_danos": "El inventario de daños está vacío.",
        "actuaciones_verificadas": "Las actuaciones verificadas están vacías.",
        "propuesta_reparacion": "La propuesta de reparación está vacía.",
        "valoracion_economica": "La valoración económica está vacía.",
        "conclusiones_periciales": "Las conclusiones están vacías.",
    }
    for clave, mensaje in reglas_error_vacio.items():
        if not contenido(clave):
            agregar_error(clave, mensaje)

    if 0 < longitud("resumen_ejecutivo") < 300:
        agregar_advertencia(
            "resumen_ejecutivo",
            "El resumen ejecutivo contiene menos de 300 caracteres.",
        )
    if 0 < longitud("metodologia") < 200:
        agregar_advertencia("metodologia", "La metodología contiene menos de 200 caracteres.")
    if total_patologias and longitud("inventario_resumido_danos") < 500:
        agregar_advertencia(
            "inventario_resumido_danos",
            "Existen patologías registradas y el inventario de daños es breve.",
        )
    if total_visitas and longitud("actuaciones_verificadas") < 200:
        agregar_advertencia(
            "actuaciones_verificadas",
            "Existen visitas registradas y las actuaciones verificadas están vacías o son muy breves.",
        )
    if total_actuaciones and not contenido("propuesta_reparacion"):
        agregar_advertencia(
            "propuesta_reparacion",
            "Existen actuaciones de reparación registradas y la propuesta está vacía.",
        )
    if total_partidas and not contenido("valoracion_economica"):
        agregar_advertencia(
            "valoracion_economica",
            "Existen partidas de coste registradas y la valoración económica está vacía.",
        )
    if not contenido("recomendaciones_tecnicas"):
        agregar_advertencia("recomendaciones_tecnicas", "Las recomendaciones están vacías.")
    if 0 < longitud("conclusiones_periciales") < 250:
        agregar_advertencia(
            "conclusiones_periciales",
            "Las conclusiones contienen menos de 250 caracteres.",
        )
    if total_patologias and not contenido("inventario_resumido_danos"):
        agregar_advertencia(
            "inventario_resumido_danos",
            "Hay patologías registradas que no se han trasladado al inventario de daños.",
        )
    if total_visitas and not contenido("actuaciones_verificadas"):
        agregar_advertencia(
            "actuaciones_verificadas",
            "Hay visitas registradas que no se reflejan en actuaciones verificadas.",
        )
    if total_actuaciones and not contenido("propuesta_reparacion"):
        agregar_advertencia(
            "propuesta_reparacion",
            "Hay actuaciones registradas que no se han trasladado a la propuesta.",
        )
    if total_partidas and not contenido("valoracion_economica"):
        agregar_advertencia(
            "valoracion_economica",
            "Hay costes registrados que no se han trasladado a la valoración económica.",
        )
    if total_fotos > 10 and longitud("inventario_resumido_danos") < 250:
        agregar_advertencia(
            "inventario_resumido_danos",
            "Hay más de 10 fotografías registradas y el inventario de daños es extremadamente reducido.",
        )

    claves_con_error = {item["clave"] for item in errores}
    completos = 0
    for clave in INFORME_V2_CAPITULOS_OBLIGATORIOS_DIAGNOSTICO:
        completo = clave not in claves_con_error
        if completo:
            completos += 1
        indicadores.append(
            {
                "clave": clave,
                "titulo": titulo(clave),
                "completo": completo,
                "caracteres": longitud(clave),
            }
        )

    total_obligatorios = len(INFORME_V2_CAPITULOS_OBLIGATORIOS_DIAGNOSTICO)
    porcentaje = round((completos / total_obligatorios) * 100) if total_obligatorios else 0
    if errores:
        estado = {
            "clave": "incompleto",
            "texto": "Incompleto",
            "detalle": "Existen errores que deben revisarse antes de emitir.",
        }
    elif advertencias:
        estado = {
            "clave": "revisar",
            "texto": "Revisar",
            "detalle": "No hay errores, pero existen advertencias editoriales.",
        }
    else:
        estado = {
            "clave": "apto",
            "texto": "Apto para emisión",
            "detalle": "No hay errores ni advertencias detectadas.",
        }

    return {
        "estado": estado,
        "porcentaje": porcentaje,
        "errores": errores,
        "advertencias": advertencias,
        "indicadores": indicadores,
        "total_obligatorios": total_obligatorios,
        "completos": completos,
    }


def build_informe_v2_contexto(cur, expediente, workbench: dict | None = None) -> dict:
    expediente_id = expediente["id"]
    expediente_dict = dict(expediente)
    workbench = workbench or preparar_pericial_workbench(cur, expediente)
    estructura = cargar_estructura_multiunidad(cur, expediente_id)
    resumen_registro = preparar_resumen_registro_expediente(cur, expediente_id)
    visitas = workbench.get("visitas", [])
    visita_ids = [visita["id"] for visita in visitas]

    patologias_por_estancia: dict[int, list[dict]] = {}
    patologias_exteriores = []

    if visita_ids:
        placeholders = ",".join("?" for _ in visita_ids)
        patologias_rows = cur.execute(
            f"""
            SELECT rp.*,
                   e.nombre AS estancia_nombre,
                   e.planta AS estancia_planta,
                   u.identificador AS unidad_identificador,
                   n.nombre_nivel AS nivel_nombre
            FROM registros_patologias rp
            JOIN estancias e ON e.id = rp.estancia_id
            LEFT JOIN unidades_expediente u ON u.id = e.unidad_id
            LEFT JOIN niveles_edificio n ON n.id = u.nivel_id
            WHERE rp.visita_id IN ({placeholders})
            ORDER BY e.nombre COLLATE NOCASE, rp.id ASC
            """,
            tuple(visita_ids),
        ).fetchall()
        for row in patologias_rows:
            patologia = enriquecer_registro_con_fotos(
                cur,
                row,
                "registro_patologia_fotos",
                "registro_id",
                "foto",
            )
            patologias_por_estancia.setdefault(patologia["estancia_id"], []).append(
                patologia
            )

        patologias_exteriores_rows = cur.execute(
            f"""
            SELECT rpe.*,
                   v.fecha AS visita_fecha,
                   u.identificador AS unidad_identificador,
                   n.nombre_nivel AS nivel_nombre
            FROM registros_patologias_exteriores rpe
            JOIN visitas v ON v.id = rpe.visita_id
            LEFT JOIN unidades_expediente u ON u.id = v.unidad_id
            LEFT JOIN niveles_edificio n ON n.id = v.nivel_id
            WHERE rpe.visita_id IN ({placeholders})
            ORDER BY COALESCE(rpe.zona_exterior, '') COLLATE NOCASE, rpe.id ASC
            """,
            tuple(visita_ids),
        ).fetchall()
        for row in patologias_exteriores_rows:
            patologias_exteriores.append(
                enriquecer_registro_con_fotos(
                    cur,
                    row,
                    "registro_patologia_exterior_fotos",
                    "registro_id",
                    "foto",
                )
            )

    for grupo in resumen_registro.get("grupos_unidades", []):
        for unidad in grupo.get("unidades", []):
            for estancia in unidad.get("estancias", []):
                fotos_estancia = obtener_fotos_relacionadas(
                    cur,
                    "estancia_fotos",
                    "estancia_id",
                    estancia["id"],
                )
                for foto in fotos_estancia:
                    foto["url"] = f"/uploads/{foto['archivo']}"
                estancia["fotos"] = fotos_estancia
                estancia["patologias"] = patologias_por_estancia.get(estancia["id"], [])
                estancia["datos_tecnicos"] = [
                    {"label": "Tipo", "valor": limpiar_texto(estancia.get("tipo_estancia"))},
                    {"label": "Planta", "valor": limpiar_texto(estancia.get("planta"))},
                    {
                        "label": "Ventilación",
                        "valor": limpiar_texto(estancia.get("ventilacion")),
                    },
                    {
                        "label": "Pavimento",
                        "valor": limpiar_texto(estancia.get("acabado_pavimento")),
                    },
                    {
                        "label": "Paramento",
                        "valor": limpiar_texto(estancia.get("acabado_paramento")),
                    },
                    {
                        "label": "Techo",
                        "valor": limpiar_texto(estancia.get("acabado_techo")),
                    },
                ]

    observaciones = []
    for etiqueta, valor in [
        ("Descripción del daño", expediente_dict.get("descripcion_dano")),
        ("Causa probable", expediente_dict.get("causa_probable")),
        ("Pruebas e indicios", expediente_dict.get("pruebas_indicios")),
        ("Limitaciones", expediente_dict.get("alcance_limitaciones")),
        ("Propuesta de reparación", expediente_dict.get("propuesta_reparacion")),
    ]:
        texto = limpiar_texto(valor)
        if texto:
            observaciones.append({"origen": etiqueta, "texto": texto})
    for visita in visitas:
        texto = limpiar_texto(visita.get("observaciones_visita"))
        if texto:
            observaciones.append(
                {
                    "origen": f"Visita {visita.get('fecha') or visita.get('id')}",
                    "texto": texto,
                }
            )

    return {
        "expediente": {
            "numero_expediente": limpiar_texto(expediente_dict.get("numero_expediente")),
            "cliente": limpiar_texto(expediente_dict.get("cliente")),
            "direccion": limpiar_texto(expediente_dict.get("direccion")),
            "ciudad": limpiar_texto(expediente_dict.get("ciudad")),
            "provincia": limpiar_texto(expediente_dict.get("provincia")),
            "tipo_inmueble": limpiar_texto(expediente_dict.get("tipo_inmueble")),
        },
        "visitas": visitas,
        "niveles": estructura["niveles"],
        "unidades": estructura["unidades"],
        "grupos_unidades": resumen_registro.get("grupos_unidades", []),
        "patologias_exteriores": patologias_exteriores,
        "fotos_exteriores": resumen_registro.get("visita_fotos_exteriores", []),
        "observaciones": observaciones,
        "actuaciones": workbench.get("actuaciones", {}),
    }


def preparar_editor_informe_v2(cur, expediente) -> dict:
    workbench = preparar_pericial_workbench(cur, expediente)
    contexto_editor = build_informe_v2_contexto(cur, expediente, workbench)
    anexos_derivados = preparar_anexos_derivados_editor_v2(contexto_editor)
    pdf_mediciones_anexo_f = obtener_pdf_mediciones_anexo_f_informe_v2(
        cur,
        expediente["id"],
    )
    iniciales = generar_contenido_inicial_editor_v2(workbench)
    guardados = obtener_capitulos_guardados_informe_v2(cur, expediente["id"])
    metadatos = obtener_metadatos_informe_v2(cur, expediente["id"])
    versiones = obtener_versiones_informe_v2(cur, expediente["id"])
    documentos_aportados = obtener_documentos_aportados_expediente(cur, expediente["id"])
    documentos_anexo_a = recopilar_documentacion_anexo_v2(
        dict(expediente),
        {},
        documentos_aportados,
    )
    diagnostico_anexos_pdf = diagnosticar_peso_anexos_pdf_v2(
        documentos_anexo_a,
        pdf_mediciones_anexo_f,
    )
    capitulos = []

    for definicion in INFORME_V2_CAPITULOS:
        clave = definicion["clave"]
        guardado, contenido_guardado = resolver_capitulo_guardado_editor_v2(
            guardados, clave
        )
        guardado_editado_manual = bool(guardado.get("editado_manual")) if guardado else False
        if contenido_guardado or guardado_editado_manual:
            contenido = contenido_guardado
            editado_manual = guardado_editado_manual
            generado_desde = (
                limpiar_texto(guardado.get("generado_desde"))
                if guardado
                else "conclusiones-tecnicas-legacy"
            )
            updated_at = limpiar_texto(guardado.get("updated_at")) if guardado else ""
        else:
            contenido = limpiar_texto(iniciales.get(clave))
            editado_manual = False
            generado_desde = "pericial-wb-2"
            updated_at = ""

        estado = "vacío"
        if contenido and editado_manual:
            estado = "editado"
        elif contenido:
            estado = "generado"

        ayuda = dict(INFORME_V2_AYUDAS_CAPITULOS.get(clave, {}))
        avisos_ayuda = []
        if anexos_derivados["anexo_b"]["disponible"] and clave in {
            "resumen_ejecutivo",
            "inventario_resumido_danos",
            "analisis_causal",
            "conclusiones_periciales",
        }:
            avisos_ayuda.append(anexos_derivados["anexo_b"]["mensaje"])
        if anexos_derivados["anexo_c"]["disponible"] and clave in {
            "inventario_resumido_danos",
            "analisis_causal",
            "propuesta_reparacion",
            "conclusiones_periciales",
        }:
            avisos_ayuda.append(anexos_derivados["anexo_c"]["mensaje"])
        if ayuda:
            ayuda["avisos"] = avisos_ayuda

        capitulos.append(
            {
                **definicion,
                "contenido": contenido,
                "generado_desde": generado_desde,
                "editado_manual": editado_manual,
                "updated_at": updated_at,
                "estado_revision": normalizar_estado_revision_informe_v2(
                    guardado.get("estado_revision") if guardado else ""
                ),
                "estado": estado,
                "guardado": bool(guardado),
                "versiones": versiones.get(clave, []),
                "ayuda": ayuda,
            }
        )

    advertencias_editoriales = evaluar_advertencias_editoriales_informe_v2(
        capitulos,
        anexos_derivados,
    )
    claves_con_advertencia_editorial = {
        advertencia["clave"] for advertencia in advertencias_editoriales
    }
    for capitulo in capitulos:
        capitulo["advertencia_editorial"] = (
            capitulo["clave"] in claves_con_advertencia_editorial
        )

    diagnostico_informe = evaluar_diagnostico_informe_v2(capitulos, workbench)
    diagnostico_informe["anexos_derivados"] = [
        {
            "titulo": "Anexo B",
            "texto": "✓ Disponible" if anexos_derivados["anexo_b"]["disponible"] else "No disponible",
            "disponible": anexos_derivados["anexo_b"]["disponible"],
        },
        {
            "titulo": "Anexo C",
            "texto": "✓ Disponible" if anexos_derivados["anexo_c"]["disponible"] else "No disponible",
            "disponible": anexos_derivados["anexo_c"]["disponible"],
        },
    ]
    diagnostico_informe["advertencias_editoriales"] = advertencias_editoriales
    estados_revision = resumir_estados_revision_informe_v2(capitulos)
    revision_coherencia = analizar_consistencia_expediente(expediente["id"])

    return {
        **workbench,
        "contexto_editor": contexto_editor,
        "anexos_derivados": anexos_derivados,
        "pdf_mediciones_anexo_f": pdf_mediciones_anexo_f,
        "diagnostico_informe": diagnostico_informe,
        "revision_coherencia": revision_coherencia,
        "pdf_export_profiles": listar_perfiles_exportacion_pdf_v2(),
        "diagnostico_anexos_pdf": diagnostico_anexos_pdf,
        "estados_revision": estados_revision,
        "metadatos": metadatos,
        "capitulos": capitulos,
        "capitulos_guardados": len(guardados),
    }


def guardar_presentacion_informe_v2(cur, expediente_id: int, form_data) -> dict:
    if "titulo_portada" not in form_data and "subtitulo_portada" not in form_data:
        return obtener_metadatos_informe_v2(cur, expediente_id)
    return guardar_metadatos_informe_v2(
        cur,
        expediente_id,
        form_data.get("titulo_portada"),
        form_data.get("subtitulo_portada"),
    )


def guardar_capitulos_informe_v2(cur, expediente_id: int, form_data):
    for definicion in INFORME_V2_CAPITULOS:
        clave = definicion["clave"]
        contenido = limpiar_texto(form_data.get(f"contenido_{clave}"))
        guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            clave,
            contenido,
            origen_version="manual",
        )


def detectar_conflictos_guardado_manual_informe_v2(
    cur,
    expediente_id: int,
    form_data,
) -> list[str]:
    guardados = obtener_capitulos_guardados_informe_v2(cur, expediente_id)
    conflictos = []
    for definicion in INFORME_V2_CAPITULOS:
        clave = definicion["clave"]
        guardado = guardados.get(clave)
        if not guardado:
            continue
        updated_at_actual = limpiar_texto(guardado.get("updated_at"))
        updated_at_cargado = limpiar_texto(form_data.get(f"updated_at_{clave}"))
        if updated_at_actual and updated_at_actual != updated_at_cargado:
            conflictos.append(definicion["titulo"])
    return conflictos


def guardar_capitulo_informe_v2(
    cur,
    expediente_id: int,
    clave: str,
    contenido: str,
    origen_version: str = "manual",
):
    definicion = INFORME_V2_CAPITULOS_POR_CLAVE.get(limpiar_texto(clave))
    if not definicion:
        raise ValueError("Campo no permitido para el informe.")
    contenido_limpio = limpiar_texto(contenido)
    fila_actual = cur.execute(
        """
        SELECT contenido, updated_at
        FROM informe_v2_capitulos
        WHERE expediente_id = ? AND clave = ?
        """,
        (expediente_id, definicion["clave"]),
    ).fetchone()
    if fila_actual and limpiar_texto(fila_actual["contenido"]) != contenido_limpio:
        crear_snapshot_capitulo_informe_v2(
            cur,
            expediente_id,
            definicion["clave"],
            limpiar_texto(fila_actual["contenido"]),
            limpiar_texto(fila_actual["updated_at"]),
            origen_version,
        )
    cur.execute(
        """
        INSERT INTO informe_v2_capitulos (
            expediente_id, clave, titulo, orden, contenido,
            generado_desde, editado_manual, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(expediente_id, clave) DO UPDATE SET
            titulo = excluded.titulo,
            orden = excluded.orden,
            contenido = excluded.contenido,
            generado_desde = COALESCE(informe_v2_capitulos.generado_desde, excluded.generado_desde),
            editado_manual = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            expediente_id,
            definicion["clave"],
            definicion["titulo"],
            definicion["orden"],
            contenido_limpio,
            "pericial-wb-2",
        ),
    )


def crear_snapshot_capitulo_informe_v2(
    cur,
    expediente_id: int,
    clave: str,
    contenido: str,
    updated_at_original: str,
    origen: str,
):
    cur.execute(
        """
        INSERT INTO informe_v2_capitulo_versiones (
            expediente_id, clave, contenido, updated_at_original, origen
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            clave,
            contenido,
            limpiar_texto(updated_at_original),
            limpiar_texto(origen) or "manual",
        ),
    )
    cur.execute(
        """
        DELETE FROM informe_v2_capitulo_versiones
        WHERE expediente_id = ?
          AND clave = ?
          AND id IN (
              SELECT id
              FROM informe_v2_capitulo_versiones
              WHERE expediente_id = ? AND clave = ?
              ORDER BY created_at DESC, id DESC
              LIMIT -1 OFFSET 50
          )
        """,
        (expediente_id, clave, expediente_id, clave),
    )


def limpiar_contenido_pdf_v2(contenido: str) -> str:
    texto = limpiar_texto(contenido)
    if not texto:
        return ""

    patrones_internos = [
        r"\btexto generado autom[aá]ticamente\b",
        r"\brequiere revisi[oó]n t[eé]cnica\b",
        r"\bcontenido guardado\b",
        r"\b[uú]ltima actualizaci[oó]n\b",
        r"\bdiagn[oó]stico\b",
        r"\bpendiente de revisi[oó]n\b",
    ]
    for patron in patrones_internos:
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE)

    texto = re.sub(
        r"-\s*([^:\n]+):\s*([^(.\n]+?)\s+en\s+([^(.\n]+?)\s*\((?:rol pendiente|[^,)]*),\s*(\d+)\s*foto\(s\)\)\.",
        lambda match: (
            f"{match.group(1).strip()}:\n"
            f"Se observan {match.group(2).strip().lower()} en "
            f"{match.group(3).strip().lower()}, documentados mediante reportaje fotográfico."
        ),
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"\s*\(rol pendiente(?:,\s*\d+\s*foto\(s\))?\)", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*\(\d+\s*foto\(s\)\)", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip(" \n\t·-")


def imagen_url_pdf_v2(nombre_archivo: str | None, base_url: str = "") -> str:
    nombre = limpiar_texto(nombre_archivo)
    if not nombre:
        return ""
    prefijo = base_url.rstrip("/")
    return f"{prefijo}/uploads/{nombre}" if prefijo else f"/uploads/{nombre}"


def valor_campo_informe_v2(campos: list[dict], etiqueta: str) -> str:
    for campo in campos or []:
        if limpiar_texto(campo.get("label")).lower() == etiqueta.lower():
            valor = limpiar_texto(campo.get("value"))
            return "" if valor == "-" else valor
    return ""


ANEXO_B_MAX_FOTOS_POR_GRUPO = 6


ANEXO_B_CATEGORIAS = [
    {
        "codigo": "B.1",
        "clave": "filtraciones_humedades",
        "titulo": "FILTRACIONES Y HUMEDADES",
        "intro": (
            "Las siguientes imágenes muestran evidencias compatibles con entrada "
            "de agua, humedades y afecciones derivadas."
        ),
        "keywords": (
            "filtracion",
            "infiltracion",
            "humedad",
            "humedades",
            "entrada de agua",
            "agua",
            "cubierta",
            "eflorescencia",
            "eflorescencias",
            "salina",
            "salinas",
            "escorrentia",
        ),
    },
    {
        "codigo": "B.2",
        "clave": "revestimientos_acabados",
        "titulo": "DETERIORO DE REVESTIMIENTOS Y ACABADOS",
        "intro": (
            "Las siguientes imágenes muestran deterioros observados en "
            "revestimientos y acabados interiores."
        ),
        "keywords": (
            "deterioro",
            "revestimiento",
            "revestimientos",
            "acabado",
            "acabados",
            "paramento",
            "paramentos",
            "techo",
            "pavimento",
            "pintura",
            "yeso",
            "desprendimiento",
            "fisura",
            "desconchado",
        ),
    },
    {
        "codigo": "B.3",
        "clave": "mohos_colonizacion",
        "titulo": "MOHOS Y COLONIZACIÓN BIOLÓGICA",
        "intro": (
            "Las siguientes imágenes muestran indicios de mohos, manchas "
            "biológicas o colonización superficial asociada a humedad."
        ),
        "keywords": (
            "moho",
            "mohos",
            "hongos",
            "colonizacion",
            "biologica",
            "biológico",
            "biologica",
            "microorganismo",
            "mancha negra",
        ),
    },
    {
        "codigo": "B.4",
        "clave": "carpinterias_auxiliares",
        "titulo": "DAÑOS EN CARPINTERÍAS Y ELEMENTOS AUXILIARES",
        "intro": (
            "Las siguientes imágenes documentan daños apreciables en "
            "carpinterías, encuentros y elementos auxiliares."
        ),
        "keywords": (
            "carpinteria",
            "carpinterias",
            "puerta",
            "ventana",
            "marco",
            "premarco",
            "rodapie",
            "zócalo",
            "zocalo",
            "barandilla",
            "elemento auxiliar",
        ),
    },
    {
        "codigo": "B.5",
        "clave": "exteriores_fachada",
        "titulo": "DAÑOS EXTERIORES Y FACHADA",
        "intro": (
            "Las siguientes imágenes recogen daños o indicios localizados en "
            "zonas exteriores, fachada, cubierta o elementos de envolvente."
        ),
        "keywords": (
            "exterior",
            "fachada",
            "cubierta",
            "cornisa",
            "revestimiento exterior",
            "terraza",
            "patio",
            "medianera",
            "envolvente",
            "alero",
            "peto",
            "bajante",
            "canalon",
        ),
    },
    {
        "codigo": "B.6",
        "clave": "otras_evidencias",
        "titulo": "OTRAS EVIDENCIAS FOTOGRÁFICAS",
        "intro": (
            "Las siguientes imágenes completan el reportaje fotográfico cuando "
            "no existe información suficiente para clasificarlas en los grupos anteriores."
        ),
        "keywords": (),
    },
]


def normalizar_texto_clasificacion_v2(*valores) -> str:
    texto = " ".join(limpiar_texto(valor) for valor in valores if limpiar_texto(valor))
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def clasificar_foto_anexo_b_v2(foto: dict) -> str:
    def categoria_por_texto(texto: str) -> str:
        if not texto:
            return ""
        if any(palabra in texto for palabra in ("moho", "hongos", "colonizacion", "biologica")):
            return "mohos_colonizacion"
        if any(palabra in texto for palabra in ("carpinteria", "puerta", "ventana", "marco", "rodapie", "zocalo")):
            return "carpinterias_auxiliares"
        if (
            any(palabra in texto for palabra in ("revestimiento", "acabado", "paramento", "techo", "pavimento"))
            and any(palabra in texto for palabra in ("deterioro", "desprendimiento", "desconchado", "fisura"))
        ):
            return "revestimientos_acabados"
        if any(palabra in texto for palabra in ("fachada", "cornisa", "exterior", "terraza", "medianera", "alero", "peto", "bajante", "canalon")):
            return "exteriores_fachada"
        if any(palabra in texto for palabra in ("filtracion", "infiltracion", "humedad", "humedades", "entrada de agua", "agua", "cubierta", "eflorescencia", "eflorescencias", "salina", "salinas", "escorrentia")):
            return "filtraciones_humedades"
        for categoria in ANEXO_B_CATEGORIAS:
            if categoria["clave"] == "otras_evidencias":
                continue
            if any(normalizar_texto_clasificacion_v2(keyword) in texto for keyword in categoria["keywords"]):
                return categoria["clave"]
        return ""

    fuentes_prioritarias = [
        (foto.get("patologia"), foto.get("categoria_dano")),
        (foto.get("elemento"),),
        (foto.get("pie"), foto.get("estancia"), foto.get("observaciones")),
    ]
    for fuentes in fuentes_prioritarias:
        texto = normalizar_texto_clasificacion_v2(*fuentes)
        if not texto:
            continue
        clave = categoria_por_texto(texto)
        if clave:
            return clave
    return "otras_evidencias"


def construir_grupos_fotograficos_anexo_b_v2(
    fotos: list[dict],
    max_por_grupo: int = ANEXO_B_MAX_FOTOS_POR_GRUPO,
) -> list[dict]:
    prioridad_origen = {
        "patologia": 0,
        "patologia_exterior": 0,
        "estancia": 1,
        "visita": 2,
    }
    grupos_por_clave = {
        categoria["clave"]: {
            **categoria,
            "fotos": [],
            "total_clasificadas": 0,
            "omitidas": 0,
        }
        for categoria in ANEXO_B_CATEGORIAS
    }
    for foto in fotos:
        clave = clasificar_foto_anexo_b_v2(foto)
        grupo = grupos_por_clave[clave]
        grupo["total_clasificadas"] += 1
        foto = {**foto, "grupo_clave": clave}
        grupo["fotos"].append(foto)

    for grupo in grupos_por_clave.values():
        grupo["fotos"].sort(
            key=lambda foto: (
                prioridad_origen.get(limpiar_texto(foto.get("origen")), 3),
                0 if limpiar_texto(foto.get("patologia")) else 1,
                limpiar_texto(foto.get("estancia")).lower(),
                limpiar_texto(foto.get("pie")).lower(),
            )
        )
        total = len(grupo["fotos"])
        grupo["fotos"] = grupo["fotos"][:max_por_grupo]
        grupo["omitidas"] = max(0, total - len(grupo["fotos"]))

    return [
        grupo
        for categoria in ANEXO_B_CATEGORIAS
        for grupo in [grupos_por_clave[categoria["clave"]]]
        if grupo["total_clasificadas"] or categoria["clave"] != "otras_evidencias"
    ]


def agregar_documento_anexo_v2(
    documentos: list[dict],
    vistos: set[tuple[str, str, str]],
    nombre: str,
    tipo: str = "",
    fecha: str = "",
    descripcion: str = "",
) -> None:
    nombre = limpiar_texto(nombre)
    if not nombre:
        return
    item = {
        "nombre": nombre,
        "tipo": limpiar_texto(tipo),
        "fecha": limpiar_texto(fecha),
        "descripcion": limpiar_texto(descripcion),
    }
    clave = (item["nombre"].lower(), item["tipo"].lower(), item["descripcion"].lower())
    if clave in vistos:
        return
    vistos.add(clave)
    documentos.append(item)


def obtener_documentos_aportados_expediente(cur, expediente_id: int) -> list[dict]:
    filas = cur.execute(
        """
        SELECT *
        FROM expediente_documentos
        WHERE expediente_id = ?
        ORDER BY orden ASC, id ASC
        """,
        (expediente_id,),
    ).fetchall()
    documentos = []
    for fila in filas:
        item = dict(fila)
        item["fecha"] = limpiar_texto(item.get("created_at"))[:10]
        documentos.append(item)
    return documentos


def siguiente_orden_documento_expediente(cur, expediente_id: int) -> int:
    fila = cur.execute(
        """
        SELECT COALESCE(MAX(orden), 0) AS orden_max
        FROM expediente_documentos
        WHERE expediente_id = ?
        """,
        (expediente_id,),
    ).fetchone()
    return int(fila["orden_max"] or 0) + 10


def get_owned_expediente_documento(cur, documento_id: int, user_id: int):
    return cur.execute(
        """
        SELECT ed.*, e.owner_user_id, e.id AS expediente_id
        FROM expediente_documentos ed
        JOIN expedientes e ON e.id = ed.expediente_id
        WHERE ed.id = ? AND e.owner_user_id = ?
        """,
        (documento_id, user_id),
    ).fetchone()


def recopilar_documentacion_anexo_v2(
    expediente: dict,
    contexto_base: dict,
    documentos_aportados: list[dict] | None = None,
) -> list[dict]:
    if documentos_aportados:
        documentos = []
        for documento in documentos_aportados:
            tipo_documento = limpiar_texto(documento.get("tipo_documento"))
            if tipo_documento == TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES:
                continue
            incluido = True
            for campo_inclusion in (
                "incluir_en_anexo_a",
                "incluir_en_anexo",
                "incluir_en_pdf",
            ):
                if campo_inclusion in documento and documento.get(campo_inclusion) is not None:
                    incluido = str(documento.get(campo_inclusion)).strip().lower() not in {
                        "",
                        "0",
                        "false",
                        "no",
                    }
                    break
            if not incluido:
                continue
            nombre = limpiar_texto(documento.get("nombre_visible"))
            if not nombre:
                continue
            archivo_original = limpiar_texto(documento.get("archivo_nombre_original"))
            if not archivo_original:
                archivo_original = Path(limpiar_texto(documento.get("archivo_ruta"))).name
            mime_type = limpiar_texto(documento.get("mime_type"))
            es_pdf = mime_type.lower() in ("application/pdf", "application/x-pdf") or archivo_original.lower().endswith(".pdf")
            numero_anexo = f"A.{len(documentos) + 2}"
            documentos.append(
                {
                    "orden": documento.get("orden"),
                    "nombre": nombre,
                    "numero_anexo": numero_anexo,
                    "tipo": tipo_documento,
                    "fecha": limpiar_texto(documento.get("fecha") or documento.get("created_at"))[:10],
                    "descripcion": limpiar_texto(documento.get("descripcion")),
                    "archivo": archivo_original,
                    "archivo_ruta": limpiar_texto(documento.get("archivo_ruta")),
                    "mime_type": mime_type,
                    "es_pdf": es_pdf,
                }
            )
        return documentos

    documentos = []
    vistos = set()
    if limpiar_texto(expediente.get("imagen_catastro")):
        agregar_documento_anexo_v2(
            documentos,
            vistos,
            "Imagen catastral asociada al expediente",
            "Imagen",
            "",
            expediente.get("imagen_catastro"),
        )
    if limpiar_texto(expediente.get("referencia_catastral")):
        agregar_documento_anexo_v2(
            documentos,
            vistos,
            "Referencia catastral consignada",
            "Dato documental",
            "",
            expediente.get("referencia_catastral"),
        )

    anexo_economico = contexto_base.get("anexo_economico_reparacion") or {}
    for fuente in anexo_economico.get("fuentes") or []:
        nombre = limpiar_texto(fuente.get("nombre"))
        origen = limpiar_texto(fuente.get("origen"))
        version = limpiar_texto(fuente.get("version"))
        agregar_documento_anexo_v2(
            documentos,
            vistos,
            nombre,
            origen or "Fuente económica",
            "",
            f"Versión: {version}" if version else "",
        )
    return documentos


def agregar_foto_anexo_v2(
    fotos: list[dict],
    vistos: set[str],
    figura: dict,
    estancia: str = "",
    pie: str = "",
    patologia: str = "",
    elemento: str = "",
    categoria_dano: str = "",
    observaciones: str = "",
    origen: str = "",
) -> None:
    archivo = limpiar_texto(figura.get("archivo"))
    url = limpiar_texto(figura.get("url"))
    if not archivo or archivo in vistos:
        return
    vistos.add(archivo)
    fotos.append(
        {
            "archivo": archivo,
            "url": url,
            "pie": limpiar_texto(pie) or limpiar_texto(figura.get("caption")),
            "estancia": limpiar_texto(estancia) or "Sin estancia asociada",
            "patologia": limpiar_texto(patologia),
            "elemento": limpiar_texto(elemento),
            "categoria_dano": limpiar_texto(categoria_dano),
            "observaciones": limpiar_texto(observaciones),
            "origen": limpiar_texto(origen),
        }
    )


def recopilar_fotografias_anexo_v2(contexto_base: dict) -> list[dict]:
    fotos = []
    vistos = set()
    for visita in contexto_base.get("visitas") or []:
        for foto in visita.get("fotos_exteriores") or []:
            agregar_foto_anexo_v2(
                fotos,
                vistos,
                foto.get("figura") or {},
                "Exterior",
                foto.get("descripcion"),
                elemento="Exterior",
                origen="visita",
            )
    for estancia in contexto_base.get("estancias") or []:
        nombre_estancia = limpiar_texto(estancia.get("nombre")) or "Estancia"
        for figura in estancia.get("fotos") or []:
            agregar_foto_anexo_v2(
                fotos,
                vistos,
                figura,
                nombre_estancia,
                origen="estancia",
            )
        for patologia in estancia.get("patologias") or []:
            elemento = valor_campo_informe_v2(patologia.get("campos"), "Elemento")
            observaciones = valor_campo_informe_v2(patologia.get("campos"), "Observaciones")
            for figura in patologia.get("fotos") or []:
                agregar_foto_anexo_v2(
                    fotos,
                    vistos,
                    figura,
                    nombre_estancia,
                    patologia=patologia.get("titulo"),
                    elemento=elemento,
                    observaciones=observaciones,
                    origen="patologia",
                )
    for zona in contexto_base.get("patologias_exteriores") or []:
        nombre_zona = limpiar_texto(zona.get("zona")) or "Exterior"
        for patologia in zona.get("patologias") or []:
            elemento = valor_campo_informe_v2(patologia.get("campos"), "Elemento exterior")
            observaciones = valor_campo_informe_v2(patologia.get("campos"), "Observaciones")
            for figura in patologia.get("fotos") or []:
                agregar_foto_anexo_v2(
                    fotos,
                    vistos,
                    figura,
                    nombre_zona,
                    patologia=patologia.get("titulo"),
                    elemento=elemento,
                    observaciones=observaciones,
                    origen="patologia_exterior",
                )
    return fotos


def recopilar_fichas_danos_anexo_v2(contexto_base: dict) -> list[dict]:
    fichas = []
    for estancia in contexto_base.get("estancias") or []:
        danos = []
        elementos = []
        observaciones = []
        fotos = []
        vistos_fotos = set()
        nombre_estancia = limpiar_texto(estancia.get("nombre")) or "Estancia sin identificar"

        observacion_estancia = valor_campo_informe_v2(estancia.get("campos"), "Observaciones técnicas")
        if observacion_estancia:
            observaciones.append(observacion_estancia)
        for figura in estancia.get("fotos") or []:
            agregar_foto_anexo_v2(fotos, vistos_fotos, figura, nombre_estancia)

        for patologia in estancia.get("patologias") or []:
            titulo = limpiar_texto(patologia.get("titulo"))
            if titulo and titulo not in danos:
                danos.append(titulo)
            elemento = valor_campo_informe_v2(patologia.get("campos"), "Elemento")
            if elemento and elemento not in elementos:
                elementos.append(elemento)
            observacion = valor_campo_informe_v2(patologia.get("campos"), "Observaciones")
            if observacion and observacion not in observaciones:
                observaciones.append(observacion)
            for figura in patologia.get("fotos") or []:
                agregar_foto_anexo_v2(fotos, vistos_fotos, figura, nombre_estancia)

        fichas.append(
            {
                "tipo": "estancia",
                "nombre": nombre_estancia,
                "nivel": limpiar_texto(estancia.get("nivel")),
                "unidad": limpiar_texto(estancia.get("unidad")),
                "danos": danos,
                "elementos": elementos,
                "fotos": fotos,
                "observaciones": observaciones,
            }
        )

    for zona in contexto_base.get("patologias_exteriores") or []:
        danos = []
        elementos = []
        observaciones = []
        fotos = []
        vistos_fotos = set()
        nombre_zona = limpiar_texto(zona.get("zona")) or "Zona exterior"
        for patologia in zona.get("patologias") or []:
            titulo = limpiar_texto(patologia.get("titulo"))
            if titulo and titulo not in danos:
                danos.append(titulo)
            elemento = valor_campo_informe_v2(patologia.get("campos"), "Elemento exterior")
            if elemento and elemento not in elementos:
                elementos.append(elemento)
            observacion = valor_campo_informe_v2(patologia.get("campos"), "Observaciones")
            if observacion and observacion not in observaciones:
                observaciones.append(observacion)
            for figura in patologia.get("fotos") or []:
                agregar_foto_anexo_v2(fotos, vistos_fotos, figura, nombre_zona)
        fichas.append(
            {
                "tipo": "zona exterior",
                "nombre": nombre_zona,
                "nivel": "Exterior",
                "unidad": "",
                "danos": danos,
                "elementos": elementos,
                "fotos": fotos,
                "observaciones": observaciones,
            }
        )
    return fichas


def preparar_anexos_pdf_informe_v2(
    expediente: dict,
    contexto_base: dict,
    capitulo_anexo_e: dict | None = None,
    capitulo_anexo_f: dict | None = None,
    documentos_aportados: list[dict] | None = None,
    pdf_mediciones_anexo_f: dict | None = None,
) -> dict:
    anexo_economico = {**(contexto_base.get("anexo_economico_reparacion") or {})}
    anexo_economico["total_pem_formateado"] = (
        f"{formatear_numero_es(anexo_economico.get('total_pem'), 2)} €"
    )
    fotografias = recopilar_fotografias_anexo_v2(contexto_base)
    return {
        "documentacion": recopilar_documentacion_anexo_v2(
            expediente,
            contexto_base,
            documentos_aportados,
        ),
        "fotografias": fotografias,
        "fotografias_grupos": construir_grupos_fotograficos_anexo_b_v2(fotografias),
        "fotografias_max_por_grupo": ANEXO_B_MAX_FOTOS_POR_GRUPO,
        "fichas_danos": recopilar_fichas_danos_anexo_v2(contexto_base),
        "valoracion": anexo_economico,
        "analisis_partida_4": preparar_analisis_partida_4_anexo_v2(
            anexo_economico,
            capitulo_anexo_e,
        ),
        "justificacion_mediciones": preparar_justificacion_mediciones_anexo_v2(
            capitulo_anexo_f,
            pdf_mediciones_anexo_f,
        ),
    }


def preparar_justificacion_mediciones_anexo_v2(
    capitulo_anexo_f: dict | None = None,
    pdf_mediciones_anexo_f: dict | None = None,
) -> dict:
    contenido = limpiar_texto((capitulo_anexo_f or {}).get("contenido_pdf"))
    if not contenido:
        contenido = contenido_base_anexo_f_mediciones_v2()
    return {
        "contenido_pdf": contenido,
        "guardado": bool((capitulo_anexo_f or {}).get("guardado")),
        "editado_manual": bool((capitulo_anexo_f or {}).get("editado_manual")),
        "pdf_adjunto": pdf_mediciones_anexo_f,
    }


def preparar_analisis_partida_4_anexo_v2(
    anexo_economico: dict,
    capitulo_anexo_e: dict | None = None,
) -> dict:
    partidas = []
    for actuacion in anexo_economico.get("actuaciones") or []:
        for partida in actuacion.get("partidas") or []:
            partidas.append(
                {
                    "actuacion": limpiar_texto(actuacion.get("titulo")),
                    "codigo": limpiar_texto(partida.get("codigo") or partida.get("concepto_codigo")),
                    "descripcion": limpiar_texto(
                        partida.get("partida")
                        or partida.get("descripcion_snapshot")
                        or partida.get("concepto_resumen")
                    ),
                    "medicion": partida.get("cantidad"),
                    "unidad": limpiar_texto(partida.get("unidad") or partida.get("unidad_snapshot")),
                    "importe": partida.get("importe"),
                }
            )
    partida_4 = partidas[3] if len(partidas) >= 4 else None
    contenido = limpiar_texto((capitulo_anexo_e or {}).get("contenido_pdf"))
    if not contenido:
        contenido = contenido_base_anexo_e_partida_4_v2()
    return {
        "numero_partida": 4,
        "partida": partida_4,
        "total_partidas_estructuradas": len(partidas),
        "contenido_pdf": contenido,
        "guardado": bool((capitulo_anexo_e or {}).get("guardado")),
        "editado_manual": bool((capitulo_anexo_e or {}).get("editado_manual")),
    }


def preparar_conclusiones_pdf_informe_v2(capitulos: list[dict]) -> dict:
    conclusiones = []
    capitulo = next(
        (
            item
            for item in capitulos
            if item["clave"] == INFORME_V2_CLAVE_CONCLUSIONES
        ),
        None,
    )
    if capitulo and capitulo["contenido_pdf"]:
        conclusiones.append(
            {
                "titulo": "Conclusiones",
                "contenido_pdf": capitulo["contenido_pdf"],
                "clave": INFORME_V2_CLAVE_CONCLUSIONES,
            }
        )
    return {
        "numero": 13,
        "titulo": "Conclusiones",
        "bloques": conclusiones,
    }


def preparar_contexto_pdf_informe_v2(cur, expediente, base_url: str = "") -> dict:
    expediente_dict = dict(expediente)
    expediente_id = expediente_dict["id"]
    guardados = obtener_capitulos_guardados_informe_v2(cur, expediente_id)
    metadatos = obtener_metadatos_informe_v2(cur, expediente_id)
    capitulos = []

    for definicion in INFORME_V2_CAPITULOS:
        guardado, contenido = resolver_capitulo_guardado_editor_v2(
            guardados, definicion["clave"]
        )
        capitulos.append(
            {
                **definicion,
                "contenido": contenido,
                "contenido_pdf": limpiar_contenido_pdf_v2(contenido),
                "guardado": bool(guardado),
                "editado_manual": bool(guardado.get("editado_manual")) if guardado else False,
                "updated_at": limpiar_texto(guardado.get("updated_at")) if guardado else "",
            }
        )

    capitulos_principales = [
        capitulo
        for capitulo in capitulos
        if capitulo["clave"] not in INFORME_V2_CLAVES_FUERA_CUERPO_PDF
    ]
    for indice, capitulo in enumerate(capitulos_principales, start=3):
        capitulo["numero_pdf"] = indice
    conclusiones = preparar_conclusiones_pdf_informe_v2(capitulos)

    ultima_visita = cur.execute(
        """
        SELECT fecha, tecnico
        FROM visitas
        WHERE expediente_id = ?
        ORDER BY fecha DESC, id DESC
        LIMIT 1
        """,
        (expediente_id,),
    ).fetchone()
    contexto_base = build_informe_context(
        expediente_id,
        base_url=base_url,
        incluir_anexo_economico_reparacion=True,
    )
    capitulo_anexo_e = next(
        (capitulo for capitulo in capitulos if capitulo["clave"] == "anexo_e_partida_4"),
        None,
    )
    capitulo_anexo_f = next(
        (capitulo for capitulo in capitulos if capitulo["clave"] == "anexo_f_mediciones"),
        None,
    )
    documentos_aportados = obtener_documentos_aportados_expediente(cur, expediente_id)
    pdf_mediciones_anexo_f = obtener_pdf_mediciones_anexo_f_informe_v2(cur, expediente_id)
    anexos = preparar_anexos_pdf_informe_v2(
        expediente_dict,
        contexto_base,
        capitulo_anexo_e,
        capitulo_anexo_f,
        documentos_aportados,
        pdf_mediciones_anexo_f,
    )
    desplazamiento_paginas_anexo_a = 0
    for documento in anexos.get("documentacion") or []:
        if documento_anexo_a_pdf_v2(documento):
            paginas_pdf = contar_paginas_pdf_upload_v2(documento.get("archivo_ruta"))
            documento["paginas_pdf"] = paginas_pdf
            desplazamiento_paginas_anexo_a += paginas_pdf + 1
    indice = [
        {"numero": 1, "titulo": "Portada", "grupo": "cuerpo", "clave": "portada"},
        {"numero": 2, "titulo": "Índice", "grupo": "cuerpo", "clave": "indice"},
    ]
    indice.extend(
        {
            "numero": capitulo["numero_pdf"],
            "titulo": capitulo["titulo"],
            "grupo": "cuerpo",
            "clave": capitulo["clave"],
        }
        for capitulo in capitulos_principales
    )
    indice.append(
        {
            "numero": conclusiones["numero"],
            "titulo": "Conclusiones",
            "grupo": "cuerpo",
            "clave": "conclusiones",
        }
    )
    indice.extend(
        [
            {"numero": "A", "titulo": "Documentación aportada", "grupo": "anexos", "clave": "anexo_a"},
            {"numero": "B", "titulo": "Reportaje fotográfico", "grupo": "anexos", "clave": "anexo_b"},
            {"numero": "C", "titulo": "Fichas de daños por estancia", "grupo": "anexos", "clave": "anexo_c"},
            {"numero": "D", "titulo": "Valoración económica detallada", "grupo": "anexos", "clave": "anexo_d"},
            {"numero": "E", "titulo": "Análisis de ejecución de la partida nº 4", "grupo": "anexos", "clave": "anexo_e"},
            {"numero": "F", "titulo": "Justificación de mediciones", "grupo": "anexos", "clave": "anexo_f"},
        ]
    )

    expediente_dict["tipo_trabajo_label"] = etiquetar_opcion(
        expediente_dict.get("tipo_informe", ""), TIPO_INFORME_LABELS
    )
    return {
        "expediente": expediente_dict,
        "capitulos": capitulos_principales,
        "capitulos_editor": capitulos,
        "conclusiones": conclusiones,
        "indice": indice,
        "anexos": anexos,
        "pdf_mediciones_anexo_f": pdf_mediciones_anexo_f,
        "informe": metadatos,
        "desplazamiento_paginas_anexo_a": desplazamiento_paginas_anexo_a,
        "capitulos_guardados": len(guardados),
        "fecha_emision": datetime.now().strftime("%d/%m/%Y"),
        "tecnico": limpiar_texto(ultima_visita["tecnico"]) if ultima_visita else "",
        "fecha_visita": limpiar_texto(ultima_visita["fecha"]) if ultima_visita else "",
    }


def listar_perfiles_exportacion_pdf_v2() -> list[dict]:
    return [dict(perfil) for perfil in PDF_EXPORT_PROFILES.values()]


def resolver_perfil_exportacion_pdf_v2(codigo: str | None) -> dict:
    codigo_limpio = limpiar_texto(codigo) or PDF_EXPORT_PROFILE_DEFAULT
    perfil = PDF_EXPORT_PROFILES.get(codigo_limpio)
    if not perfil:
        raise HTTPException(
            status_code=400,
            detail="Perfil de exportación PDF no válido.",
        )
    return perfil


def slug_perfil_exportacion_pdf_v2(codigo: str) -> str:
    return limpiar_nombre_archivo(codigo.replace("_", "-")).lower()


def nombre_archivo_pdf_informe_v2(
    expediente,
    perfil_pdf: dict | None = None,
    incluir_perfil: bool = False,
) -> str:
    numero = limpiar_nombre_archivo(expediente["numero_expediente"] or "expediente")
    if perfil_pdf and incluir_perfil:
        return f"Informe-{numero}-{slug_perfil_exportacion_pdf_v2(perfil_pdf['codigo'])}.pdf"
    return f"Informe-{numero}.pdf"


def contar_paginas_pdf_upload_v2(ruta_relativa: str | None) -> int:
    ruta_pdf = resolver_ruta_upload_relativa_segura(ruta_relativa)
    if not ruta_pdf or not ruta_pdf.exists():
        return 0
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(ruta_pdf)).pages)
    except Exception as exc:
        logger.warning("No se pudieron contar páginas del PDF externo %s: %s", ruta_relativa, exc)
        return 0


def documento_anexo_a_pdf_v2(documento: dict) -> bool:
    mime = limpiar_texto(documento.get("mime_type")).lower()
    archivo = limpiar_texto(documento.get("archivo") or documento.get("archivo_ruta")).lower()
    return mime in ("application/pdf", "application/x-pdf") or archivo.endswith(".pdf")


def diagnosticar_peso_anexos_pdf_v2(
    documentos_anexo_a: list[dict] | None = None,
    pdf_mediciones: dict | None = None,
    pdf_informe: bytes | None = None,
) -> dict:
    informe_bytes = len(pdf_informe or b"")
    anexo_a_bytes = 0
    otros_anexos_bytes = 0
    anexos = []

    for documento in documentos_anexo_a or []:
        if not documento_anexo_a_pdf_v2(documento):
            continue
        ruta_pdf = resolver_ruta_upload_relativa_segura(documento.get("archivo_ruta"))
        if not ruta_pdf:
            continue
        peso = analizar_peso_pdf(ruta_pdf)
        anexo_a_bytes += int(peso["tamano_bytes"] or 0)
        anexos.append(
            {
                "categoria": "anexo_a",
                "nombre": limpiar_texto(documento.get("nombre")) or "Anexo A",
                **peso,
            }
        )

    anexo_f_bytes = 0
    if pdf_mediciones:
        ruta_pdf = resolver_ruta_upload_relativa_segura(pdf_mediciones.get("archivo_ruta"))
        if ruta_pdf:
            peso = analizar_peso_pdf(ruta_pdf)
            anexo_f_bytes += int(peso["tamano_bytes"] or 0)
            anexos.append(
                {
                    "categoria": "anexo_f",
                    "nombre": limpiar_texto(pdf_mediciones.get("archivo_nombre_original")) or "Anexo F",
                    **peso,
                }
            )

    total = informe_bytes + anexo_a_bytes + anexo_f_bytes + otros_anexos_bytes
    return {
        "informe_principal_mb": bytes_a_mb(informe_bytes),
        "anexo_a_mb": bytes_a_mb(anexo_a_bytes),
        "anexo_f_mb": bytes_a_mb(anexo_f_bytes),
        "otros_anexos_mb": bytes_a_mb(otros_anexos_bytes),
        "total_estimado_mb": bytes_a_mb(total),
        "anexos": anexos,
        "hay_anexos_pdf": bool(anexo_a_bytes or anexo_f_bytes or otros_anexos_bytes),
        "hay_anexos_pdf_pesados": any(
            (item.get("tamano_bytes") or 0) >= 5 * 1024 * 1024
            for item in anexos
        ),
    }


def normalizar_busqueda_pdf_v2(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", limpiar_texto(texto).lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def encontrar_pagina_pdf_v2(reader, patrones: list[str], inicio: int = 0) -> int | None:
    patrones_normalizados = [
        normalizar_busqueda_pdf_v2(patron)
        for patron in patrones
        if limpiar_texto(patron)
    ]
    if not patrones_normalizados:
        return None
    for indice_pagina, pagina in enumerate(reader.pages):
        if indice_pagina < inicio:
            continue
        try:
            texto_pagina = normalizar_busqueda_pdf_v2(pagina.extract_text() or "")
        except Exception:
            texto_pagina = ""
        if all(patron in texto_pagina for patron in patrones_normalizados):
            return indice_pagina
    return None


def leer_paginas_pdf_upload_v2(ruta_relativa: str | None, etiqueta: str) -> list:
    ruta_pdf = resolver_ruta_upload_relativa_segura(ruta_relativa)
    return leer_paginas_pdf_path_v2(ruta_pdf, etiqueta)


def leer_paginas_pdf_path_v2(ruta_pdf: Path | None, etiqueta: str) -> list:
    if not ruta_pdf or not ruta_pdf.exists():
        logger.warning("No se pudo integrar %s: archivo no encontrado.", etiqueta)
        return []
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(ruta_pdf))
        return [pagina for pagina in reader.pages]
    except Exception as exc:
        logger.warning("No se pudo integrar %s: %s", etiqueta, exc)
        return []


def generar_paginas_portadilla_anexo_a_v2(documento: dict, pdf_integrado: bool) -> list:
    try:
        from playwright.sync_api import sync_playwright
        from pypdf import PdfReader
    except ImportError as exc:
        logger.warning("No se pudo generar portadilla Anexo A: %s", exc)
        return []

    numero = html.escape(limpiar_texto(documento.get("numero_anexo")) or "A")
    nombre = html.escape(limpiar_texto(documento.get("nombre")) or "Documento aportado")
    tipo = html.escape(limpiar_texto(documento.get("tipo")) or "Documento aportado")
    fecha = html.escape(limpiar_texto(documento.get("fecha")) or "-")
    descripcion = html.escape(limpiar_texto(documento.get("descripcion")) or "-")
    estado = (
        "Documento aportado por la propiedad."
        if pdf_integrado
        else "El documento queda referenciado, pero el PDF aportado no se pudo incorporar físicamente."
    )
    estado = html.escape(estado)
    html_portadilla = f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 20mm; }}
            body {{
                color: #1f2933;
                font-family: Arial, Helvetica, sans-serif;
                margin: 0;
            }}
            .page {{
                align-items: center;
                border-bottom: 2px solid #1f2933;
                border-top: 2px solid #1f2933;
                box-sizing: border-box;
                display: flex;
                min-height: 250mm;
            }}
            .number {{
                color: #6b7280;
                font-size: 14px;
                font-weight: 700;
                margin: 0 0 6px;
            }}
            h1 {{
                font-size: 25px;
                line-height: 1.25;
                margin: 0 0 18px;
                text-transform: uppercase;
            }}
            .meta {{
                border-top: 1px solid #d8dee6;
                color: #374151;
                font-size: 13px;
                line-height: 1.55;
                padding-top: 12px;
                width: 100%;
            }}
            .meta p {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <section class="page">
            <div>
                <p class="number">{numero}</p>
                <h1>{nombre}</h1>
                <div class="meta">
                    <p><strong>Tipo:</strong> {tipo}</p>
                    <p><strong>Fecha:</strong> {fecha}</p>
                    <p><strong>Descripción:</strong> {descripcion}</p>
                    <p>{estado}</p>
                </div>
            </div>
        </section>
    </body>
    </html>
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 794, "height": 1123})
            page.emulate_media(media="print")
            page.set_content(html_portadilla, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                margin={
                    "top": "0",
                    "right": "0",
                    "bottom": "0",
                    "left": "0",
                },
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
        return [pagina for pagina in PdfReader(BytesIO(pdf_bytes)).pages]
    except Exception as exc:
        logger.warning("No se pudo generar portadilla Anexo A %s: %s", nombre, exc)
        return []


def fusionar_pdf_informe_v2_con_anexos_integrados(
    pdf_informe: bytes,
    documentos_anexo_a: list[dict] | None,
    pdf_mediciones: dict | None,
    perfil_pdf: dict | None = None,
    sesion_optimizacion_anexos=None,
    diagnostico_anexos_pdf: dict | None = None,
) -> bytes:
    documentos_pdf = [
        documento
        for documento in documentos_anexo_a or []
        if documento_anexo_a_pdf_v2(documento)
    ]
    if not documentos_pdf and not pdf_mediciones:
        return pdf_informe
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        logger.warning("No se pudieron integrar PDFs externos: pypdf no está instalado.")
        return pdf_informe

    try:
        informe_reader = PdfReader(BytesIO(pdf_informe))
    except Exception as exc:
        logger.warning("No se pudo leer el PDF base para integrar anexos externos: %s", exc)
        return pdf_informe

    inserciones: dict[int, list] = {}
    pagina_anexo_b = encontrar_pagina_pdf_v2(
        informe_reader,
        ["ANEXO B", "REPORTAJE FOTOGRÁFICO"],
        inicio=3,
    )
    pagina_fallback_anexo_a = (
        max(0, pagina_anexo_b - 1)
        if pagina_anexo_b is not None
        else max(0, len(informe_reader.pages) - 1)
    )

    for indice_documento, documento in enumerate(documentos_pdf, start=2):
        etiqueta = documento.get("nombre") or documento.get("archivo") or "documento Anexo A"
        ruta_documento = resolver_ruta_upload_relativa_segura(documento.get("archivo_ruta"))
        if sesion_optimizacion_anexos and ruta_documento:
            resultado_optimizacion = sesion_optimizacion_anexos.optimizar(
                ruta_documento,
                categoria="anexo_a",
            )
            ruta_documento = Path(resultado_optimizacion.get("ruta") or ruta_documento)
        paginas_documento = leer_paginas_pdf_path_v2(ruta_documento, f"Anexo A {etiqueta}")
        paginas_portadilla = generar_paginas_portadilla_anexo_a_v2(
            documento,
            bool(paginas_documento),
        )
        paginas_unidad_documental = [*paginas_portadilla, *paginas_documento]
        if not paginas_unidad_documental:
            continue
        numero_anexo = limpiar_texto(documento.get("numero_anexo")) or f"A.{indice_documento}"
        documento["numero_anexo"] = numero_anexo
        inserciones.setdefault(pagina_fallback_anexo_a, []).extend(paginas_unidad_documental)

    if pdf_mediciones:
        ruta_mediciones = resolver_ruta_upload_relativa_segura(pdf_mediciones.get("archivo_ruta"))
        if sesion_optimizacion_anexos and ruta_mediciones:
            resultado_optimizacion = sesion_optimizacion_anexos.optimizar(
                ruta_mediciones,
                categoria="anexo_f",
            )
            ruta_mediciones = Path(resultado_optimizacion.get("ruta") or ruta_mediciones)
        paginas_mediciones = leer_paginas_pdf_path_v2(
            ruta_mediciones,
            "Anexo F.4 Desarrollo completo de mediciones",
        )
        if paginas_mediciones:
            pagina_f4 = encontrar_pagina_pdf_v2(
                informe_reader,
                ["F.4", "Desarrollo completo de mediciones"],
            )
            if pagina_f4 is None:
                pagina_f4 = max(0, len(informe_reader.pages) - 1)
            inserciones.setdefault(pagina_f4, []).extend(paginas_mediciones)

    if not inserciones:
        return pdf_informe

    writer = PdfWriter()
    for indice_pagina, pagina in enumerate(informe_reader.pages):
        writer.add_page(pagina)
        for pagina_insertada in inserciones.get(indice_pagina, []):
            writer.add_page(pagina_insertada)

    salida = BytesIO()
    writer.write(salida)
    return salida.getvalue()


def fusionar_pdf_informe_v2_con_anexo_a(
    pdf_informe: bytes,
    documentos_anexo_a: list[dict] | None,
) -> bytes:
    documentos_pdf = [
        documento
        for documento in documentos_anexo_a or []
        if documento_anexo_a_pdf_v2(documento)
    ]
    if not documentos_pdf:
        return pdf_informe
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        logger.warning("No se pudo anexar PDFs del Anexo A: pypdf no está instalado.")
        return pdf_informe

    try:
        writer = PdfWriter()
        informe_reader = PdfReader(BytesIO(pdf_informe))
        for pagina in informe_reader.pages:
            writer.add_page(pagina)
    except Exception as exc:
        logger.warning("No se pudo leer el PDF base para anexar Anexo A: %s", exc)
        return pdf_informe

    anexado = False
    for documento in documentos_pdf:
        ruta_pdf = resolver_ruta_upload_relativa_segura(documento.get("archivo_ruta"))
        if not ruta_pdf or not ruta_pdf.exists():
            logger.warning(
                "No se pudo anexar documento Anexo A %s: archivo no encontrado.",
                documento.get("archivo") or documento.get("nombre"),
            )
            continue
        try:
            reader = PdfReader(str(ruta_pdf))
            for pagina in reader.pages:
                writer.add_page(pagina)
            anexado = True
        except Exception as exc:
            logger.warning(
                "No se pudo anexar documento Anexo A %s: %s",
                documento.get("archivo") or documento.get("nombre"),
                exc,
            )

    if not anexado:
        return pdf_informe
    salida = BytesIO()
    writer.write(salida)
    return salida.getvalue()


def fusionar_pdf_informe_v2_con_mediciones(
    pdf_informe: bytes,
    pdf_mediciones: dict | None,
) -> bytes:
    if not pdf_mediciones:
        return pdf_informe
    ruta_pdf = resolver_ruta_upload_relativa_segura(pdf_mediciones.get("archivo_ruta"))
    if not ruta_pdf or not ruta_pdf.exists():
        return pdf_informe
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="pypdf no está instalado. Actualiza dependencias para anexar el PDF de mediciones.",
        ) from exc

    try:
        writer = PdfWriter()
        informe_reader = PdfReader(BytesIO(pdf_informe))
        mediciones_reader = PdfReader(str(ruta_pdf))
        for pagina in informe_reader.pages:
            writer.add_page(pagina)
        for pagina in mediciones_reader.pages:
            writer.add_page(pagina)
        salida = BytesIO()
        writer.write(salida)
        return salida.getvalue()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo anexar el PDF de mediciones al informe.",
        ) from exc


def preparar_pericial_workbench(cur, expediente) -> dict:
    expediente_id = expediente["id"]
    expediente_dict = dict(expediente)
    visitas = [
        dict(row)
        for row in cur.execute(
            """
            SELECT v.*, cv.resumen AS climatologia
            FROM visitas v
            LEFT JOIN climatologia_visitas cv ON cv.id = (
                SELECT id
                FROM climatologia_visitas
                WHERE visita_id = v.id
                ORDER BY id DESC
                LIMIT 1
            )
            WHERE v.expediente_id = ?
            ORDER BY v.fecha ASC, v.id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]
    visita_ids = [visita["id"] for visita in visitas]

    metricas = {
        "visitas": len(visitas),
        "estancias": 0,
        "patologias_interiores": 0,
        "patologias_exteriores": 0,
        "fotografias": 0,
        "actuaciones": 0,
        "pem_total": 0.0,
    }

    if visita_ids:
        placeholders = ",".join("?" for _ in visita_ids)
        metricas["estancias"] = cur.execute(
            f"SELECT COUNT(*) FROM estancias WHERE visita_id IN ({placeholders})",
            tuple(visita_ids),
        ).fetchone()[0]
        metricas["patologias_interiores"] = cur.execute(
            f"""
            SELECT COUNT(*)
            FROM registros_patologias
            WHERE visita_id IN ({placeholders})
            """,
            tuple(visita_ids),
        ).fetchone()[0]
        metricas["patologias_exteriores"] = cur.execute(
            f"""
            SELECT COUNT(*)
            FROM registros_patologias_exteriores
            WHERE visita_id IN ({placeholders})
            """,
            tuple(visita_ids),
        ).fetchone()[0]
        fotos_visita = cur.execute(
            f"SELECT COUNT(*) FROM visita_fotos WHERE visita_id IN ({placeholders})",
            tuple(visita_ids),
        ).fetchone()[0]
        fotos_estancia = cur.execute(
            f"""
            SELECT COUNT(*)
            FROM estancia_fotos ef
            JOIN estancias e ON e.id = ef.estancia_id
            WHERE e.visita_id IN ({placeholders})
            """,
            tuple(visita_ids),
        ).fetchone()[0]
        fotos_patologia = cur.execute(
            f"""
            SELECT COUNT(*)
            FROM registro_patologia_fotos rpf
            JOIN registros_patologias rp ON rp.id = rpf.registro_id
            WHERE rp.visita_id IN ({placeholders})
            """,
            tuple(visita_ids),
        ).fetchone()[0]
        fotos_patologia_exterior = cur.execute(
            f"""
            SELECT COUNT(*)
            FROM registro_patologia_exterior_fotos rpf
            JOIN registros_patologias_exteriores rp ON rp.id = rpf.registro_id
            WHERE rp.visita_id IN ({placeholders})
            """,
            tuple(visita_ids),
        ).fetchone()[0]
        metricas["fotografias"] = (
            fotos_visita + fotos_estancia + fotos_patologia + fotos_patologia_exterior
        )

    actuaciones = preparar_actuaciones_reparacion_expediente(cur, expediente_id)
    metricas["actuaciones"] = len(actuaciones["actuaciones"])
    metricas["pem_total"] = actuaciones["total_pem"]
    documentos_aportados = obtener_documentos_aportados_expediente(cur, expediente_id)

    inventario = []
    if visita_ids:
        placeholders = ",".join("?" for _ in visita_ids)
        inventario.extend(
            [
                {
                    **dict(row),
                    "tipo": "interior",
                    "zona": row["estancia_nombre"],
                    "nivel_unidad": " · ".join(
                        item
                        for item in [
                            limpiar_texto(row["nombre_nivel"]),
                            limpiar_texto(row["identificador_unidad"]),
                            limpiar_texto(row["planta"]),
                        ]
                        if item
                    ),
                    "edit_url": f"/editar-registro/{row['id']}",
                }
                for row in cur.execute(
                    f"""
                    SELECT
                        rp.id,
                        rp.elemento,
                        rp.patologia,
                        rp.localizacion_dano,
                        rp.detalle_localizacion,
                        rp.observaciones,
                        rp.rol_patologia_observado,
                        e.nombre AS estancia_nombre,
                        e.planta,
                        n.nombre_nivel,
                        u.identificador AS identificador_unidad,
                        (
                            SELECT COUNT(*)
                            FROM registro_patologia_fotos rpf
                            WHERE rpf.registro_id = rp.id
                        ) AS fotos
                    FROM registros_patologias rp
                    JOIN estancias e ON e.id = rp.estancia_id
                    LEFT JOIN unidades_expediente u ON u.id = e.unidad_id
                    LEFT JOIN niveles_edificio n ON n.id = u.nivel_id
                    WHERE rp.visita_id IN ({placeholders})
                    ORDER BY e.nombre COLLATE NOCASE, rp.id
                    """,
                    tuple(visita_ids),
                ).fetchall()
            ]
        )
        inventario.extend(
            [
                {
                    **dict(row),
                    "tipo": "exterior",
                    "zona": row["zona_exterior"],
                    "nivel_unidad": "Exterior",
                    "elemento": row["elemento_exterior"],
                    "localizacion_dano": row["localizacion_dano_exterior"],
                    "detalle_localizacion": "",
                    "rol_patologia_observado": "",
                    "edit_url": f"/editar-registro-exterior/{row['id']}",
                }
                for row in cur.execute(
                    f"""
                    SELECT
                        rpe.id,
                        rpe.zona_exterior,
                        rpe.elemento_exterior,
                        rpe.localizacion_dano_exterior,
                        rpe.patologia,
                        rpe.observaciones,
                        (
                            SELECT COUNT(*)
                            FROM registro_patologia_exterior_fotos rpf
                            WHERE rpf.registro_id = rpe.id
                        ) AS fotos
                    FROM registros_patologias_exteriores rpe
                    WHERE rpe.visita_id IN ({placeholders})
                    ORDER BY rpe.zona_exterior COLLATE NOCASE, rpe.id
                    """,
                    tuple(visita_ids),
                ).fetchall()
            ]
        )

    fuentes_texto = [
        {"origen": "Descripción del daño", "texto": expediente_dict.get("descripcion_dano")},
        {"origen": "Causa probable", "texto": expediente_dict.get("causa_probable")},
        {"origen": "Pruebas e indicios", "texto": expediente_dict.get("pruebas_indicios")},
        {
            "origen": "Evolución / preexistencia",
            "texto": expediente_dict.get("evolucion_preexistencia"),
        },
        {
            "origen": "Propuesta de reparación",
            "texto": expediente_dict.get("propuesta_reparacion"),
        },
        {"origen": "Urgencia / gravedad", "texto": expediente_dict.get("urgencia_gravedad")},
    ]
    for visita in visitas:
        fuentes_texto.append(
            {
                "origen": f"Visita {visita.get('fecha') or visita.get('id')}",
                "texto": visita.get("observaciones_visita"),
            }
        )
    if visita_ids:
        placeholders = ",".join("?" for _ in visita_ids)
        fuentes_texto.extend(
            {
                "origen": f"Estancia {row['nombre']}",
                "texto": row["observaciones"],
            }
            for row in cur.execute(
                f"""
                SELECT nombre, observaciones
                FROM estancias
                WHERE visita_id IN ({placeholders})
                  AND TRIM(COALESCE(observaciones, '')) <> ''
                """,
                tuple(visita_ids),
            ).fetchall()
        )
        fuentes_texto.extend(
            {
                "origen": f"Patología {row['patologia']}",
                "texto": row["observaciones"],
            }
            for row in cur.execute(
                f"""
                SELECT patologia, observaciones
                FROM registros_patologias
                WHERE visita_id IN ({placeholders})
                  AND TRIM(COALESCE(observaciones, '')) <> ''
                """,
                tuple(visita_ids),
            ).fetchall()
        )

    limitaciones_candidatas = extraer_candidatos_periciales(
        fuentes_texto, PERICIAL_LIMITACION_KEYWORDS
    )
    recomendaciones_candidatas = extraer_candidatos_periciales(
        fuentes_texto, PERICIAL_RECOMENDACION_KEYWORDS
    )

    tiene_descripcion = bool(limpiar_texto(expediente_dict.get("descripcion_dano")))
    tiene_causa = bool(limpiar_texto(expediente_dict.get("causa_probable")))
    tiene_pruebas = bool(limpiar_texto(expediente_dict.get("pruebas_indicios")))
    tiene_propuesta = bool(limpiar_texto(expediente_dict.get("propuesta_reparacion")))
    tiene_metodologia = bool(limpiar_texto(expediente_dict.get("metodologia_pericial")))
    tiene_limitaciones = bool(limpiar_texto(expediente_dict.get("alcance_limitaciones")))
    tiene_roles = any(limpiar_texto(item.get("rol_patologia_observado")) for item in inventario)

    diagnostico = [
        {
            "capitulo": "Resumen ejecutivo",
            "estado": estado_capitulo_pericial(False, tiene_descripcion and tiene_causa),
            "nota": "Puede componerse con descripción, causa, daños y PEM; no se guarda en esta fase.",
        },
        {
            "capitulo": "Metodología",
            "estado": estado_capitulo_pericial(tiene_metodologia, bool(visitas)),
            "nota": "Usa visitas existentes; falta texto formal si el campo está vacío.",
        },
        {
            "capitulo": "Limitaciones",
            "estado": estado_capitulo_pericial(
                tiene_limitaciones, bool(limitaciones_candidatas)
            ),
            "nota": "Diagnóstico desde campo existente y textos técnicos; no se guarda.",
        },
        {
            "capitulo": "Análisis causal",
            "estado": estado_capitulo_pericial(tiene_causa and tiene_pruebas and tiene_roles, tiene_causa and tiene_pruebas),
            "nota": "Causa y pruebas existen; roles causa/efecto mejoran la defensa.",
        },
        {
            "capitulo": "Inventario de daños",
            "estado": estado_capitulo_pericial(bool(inventario)),
            "nota": "Derivado de patologías interiores y exteriores.",
        },
        {
            "capitulo": "Actuaciones verificadas",
            "estado": estado_capitulo_pericial(False, actuaciones["tiene_actuaciones"]),
            "nota": "Hay actuaciones económicas, pero no estado de verificación.",
        },
        {
            "capitulo": "Propuesta de reparación",
            "estado": estado_capitulo_pericial(tiene_propuesta),
            "nota": "Texto existente; revisar mezcla con recomendaciones.",
        },
        {
            "capitulo": "Valoración económica",
            "estado": estado_capitulo_pericial(actuaciones["total_pem"] > 0),
            "nota": "Basada en actuaciones y partidas snapshot.",
        },
        {
            "capitulo": "Recomendaciones",
            "estado": estado_capitulo_pericial(False, bool(recomendaciones_candidatas)),
            "nota": "Candidatas derivadas de textos; no se guardan.",
        },
        {
            "capitulo": "Conclusiones",
            "estado": estado_capitulo_pericial(False, tiene_causa and bool(inventario)),
            "nota": "Requiere síntesis técnica/pericial final.",
        },
    ]

    advertencias = []
    for campo, etiqueta in [
        ("objeto_pericia", "Objeto pericial vacío"),
        ("metodologia_pericial", "Metodología pericial formal vacía"),
        ("alcance_limitaciones", "Ausencia de limitaciones formales"),
    ]:
        if not limpiar_texto(expediente_dict.get(campo)):
            advertencias.append(etiqueta)
    if not tiene_roles and metricas["patologias_interiores"]:
        advertencias.append("No hay roles técnicos causa/efecto informados")
    if actuaciones["tiene_actuaciones"]:
        advertencias.append("Actuaciones económicas sin estado de verificación")
    else:
        advertencias.append("No hay actuaciones económicas registradas")
    if actuaciones["total_pem"] > 0:
        advertencias.append("No hay trazabilidad formal daño-reparación-coste")
    if not limitaciones_candidatas and not tiene_limitaciones:
        advertencias.append("No se han detectado limitaciones candidatas")

    borrador_informe = generar_borrador_informe_v2(
        expediente_dict,
        visitas,
        inventario,
        metricas,
        actuaciones,
        limitaciones_candidatas,
        recomendaciones_candidatas,
    )

    fecha_referencia = visitas[-1]["fecha"] if visitas else ""
    expediente_dict["tipo_trabajo_label"] = etiquetar_opcion(
        expediente_dict.get("tipo_informe", ""), TIPO_INFORME_LABELS
    )
    return {
        "expediente": expediente_dict,
        "fecha_referencia": fecha_referencia,
        "ultima_visita_id": visitas[-1]["id"] if visitas else None,
        "metricas": metricas,
        "diagnostico": diagnostico,
        "inventario": inventario,
        "visitas": visitas,
        "limitaciones_candidatas": limitaciones_candidatas,
        "recomendaciones_candidatas": recomendaciones_candidatas,
        "borrador_informe": borrador_informe,
        "actuaciones": actuaciones,
        "documentos_aportados": documentos_aportados,
        "tipos_documentales_anexo_a": TIPOS_DOCUMENTALES_ANEXO_A,
        "advertencias": advertencias,
    }


def get_owned_actuacion_reparacion(cur, actuacion_id: int, user_id: int):
    return cur.execute(
        """
        SELECT ar.*, e.owner_user_id, e.numero_expediente
        FROM actuaciones_reparacion ar
        JOIN expedientes e ON e.id = ar.expediente_id
        WHERE ar.id = ? AND e.owner_user_id = ?
        """,
        (actuacion_id, user_id),
    ).fetchone()


def get_owned_actuacion_partida(cur, partida_id: int, user_id: int):
    return cur.execute(
        """
        SELECT ap.*, ar.expediente_id, e.owner_user_id
        FROM actuacion_partidas ap
        JOIN actuaciones_reparacion ar ON ar.id = ap.actuacion_id
        JOIN expedientes e ON e.id = ar.expediente_id
        WHERE ap.id = ? AND e.owner_user_id = ?
        """,
        (partida_id, user_id),
    ).fetchone()


def redirect_actuaciones_reparacion(
    expediente_id: int,
    mensaje: str = "",
    error: str = "",
    actuacion_id: int | None = None,
    q: str = "",
):
    url = f"/expedientes/{expediente_id}/actuaciones-reparacion"
    params = []
    if mensaje:
        params.append(f"mensaje={quote_plus(mensaje)}")
    if error:
        params.append(f"error={quote_plus(error)}")
    if actuacion_id:
        params.append(f"actuacion_id={actuacion_id}")
    if q:
        params.append(f"q={quote_plus(q)}")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return RedirectResponse(url=url, status_code=303)


def redirect_editar_registro_costes(
    registro_id: int,
    mensaje: str = "",
    error: str = "",
    aviso: str = "",
):
    params = []
    if mensaje:
        params.append(f"mensaje={quote_plus(mensaje)}")
    if error:
        params.append(f"error={quote_plus(error)}")
    if aviso:
        params.append(f"aviso={quote_plus(aviso)}")
    url = f"/editar-registro/{registro_id}"
    if params:
        url = f"{url}?{'&'.join(params)}"
    return RedirectResponse(url=url, status_code=303)


def get_owned_registro_exterior(cur, registro_id: int, user_id: int):
    return cur.execute(
        """
        SELECT rpe.*, v.expediente_id, v.ambito_visita,
               n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita
        FROM registros_patologias_exteriores rpe
        JOIN visitas v ON rpe.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE rpe.id=? AND e.owner_user_id=?
        """,
        (registro_id, user_id),
    ).fetchone()


def get_owned_comparable_valoracion(cur, comparable_id: int, user_id: int):
    return cur.execute(
        """
        SELECT cv.*, v.expediente_id
        FROM comparables_valoracion cv
        JOIN visitas v ON cv.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE cv.id=? AND e.owner_user_id=?
        """,
        (comparable_id, user_id),
    ).fetchone()


def get_owned_testigo_valoracion(cur, testigo_id: int, user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM testigos_valoracion
        WHERE id = ? AND owner_user_id = ?
        """,
        (testigo_id, user_id),
    ).fetchone()


def get_owned_valoracion_expediente_testigo(
    cur,
    vinculo_id: int,
    expediente_id: int,
    user_id: int,
):
    return cur.execute(
        """
        SELECT vet.*, e.owner_user_id
        FROM valoracion_expediente_testigos vet
        JOIN expedientes e ON e.id = vet.expediente_id
        WHERE vet.id = ?
          AND vet.expediente_id = ?
          AND e.owner_user_id = ?
        """,
        (vinculo_id, expediente_id, user_id),
    ).fetchone()


def get_owned_valoracion_expediente_testigo_detalle(
    cur,
    vinculo_id: int,
    expediente_id: int,
    user_id: int,
):
    return cur.execute(
        """
        SELECT vet.*,
               e.numero_expediente,
               e.direccion AS expediente_direccion,
               e.tipo_informe,
               e.owner_user_id,
               tv.direccion_testigo,
               tv.referencia_testigo,
               tv.fuente_testigo,
               tv.precio_unitario_inicial,
               tv.precio_depurado,
               tv.superficie_tomada,
               tv.valor_unitario,
               tv.superficie_construida,
               tv.estado_conservacion,
               tv.observaciones,
               vta.ajuste_superficie_construida,
               vta.ajuste_ubicacion,
               vta.ajuste_antiguedad,
               vta.ajuste_calidades,
               vta.ajuste_caracteristicas_constructivas,
               vta.coeficiente_total,
               vta.justificacion
        FROM valoracion_expediente_testigos vet
        JOIN expedientes e ON e.id = vet.expediente_id
        LEFT JOIN testigos_valoracion tv ON tv.id = vet.testigo_id
        LEFT JOIN valoracion_testigo_ajustes vta
          ON vta.expediente_testigo_id = vet.id
         AND COALESCE(vta.variable, '') = ''
        WHERE vet.id = ?
          AND vet.expediente_id = ?
          AND e.owner_user_id = ?
        """,
        (vinculo_id, expediente_id, user_id),
    ).fetchone()


def get_owned_mapa_patologia(cur, mapa_id: int, user_id: int):
    return cur.execute(
        """
        SELECT mp.*, v.expediente_id, v.ambito_visita,
               n.nombre_nivel AS nombre_nivel_visita,
               u.identificador AS identificador_unidad_visita
        FROM mapas_patologia mp
        JOIN visitas v ON mp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        LEFT JOIN niveles_edificio n ON v.nivel_id = n.id
        LEFT JOIN unidades_expediente u ON v.unidad_id = u.id
        WHERE mp.id=? AND e.owner_user_id=?
        """,
        (mapa_id, user_id),
    ).fetchone()


def get_owned_cuadrante_mapa_patologia(cur, cuadrante_id: int, user_id: int):
    return cur.execute(
        """
        SELECT qmp.*, mp.visita_id, mp.ambito_mapa, v.expediente_id, v.ambito_visita,
               mp.titulo AS mapa_titulo
        FROM cuadrantes_mapa_patologia qmp
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        JOIN visitas v ON mp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE qmp.id=? AND e.owner_user_id=?
        """,
        (cuadrante_id, user_id),
    ).fetchone()


def indice_a_letras(indice: int) -> str:
    letras = ""
    valor = indice + 1
    while valor > 0:
        valor, resto = divmod(valor - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def generar_codigo_cuadrante(fila_idx: int, columna_idx: int) -> str:
    return f"{indice_a_letras(fila_idx)}{columna_idx + 1}"


def generar_cuadrantes_mapa(cur, mapa_id: int, filas: int, columnas: int):
    for fila_idx in range(filas):
        for columna_idx in range(columnas):
            cur.execute(
                """
                INSERT INTO cuadrantes_mapa_patologia (mapa_id, codigo_cuadrante)
                VALUES (?, ?)
                """,
                (mapa_id, generar_codigo_cuadrante(fila_idx, columna_idx)),
            )


def obtener_registros_patologia_vinculables(cur, visita_id: int):
    opciones = []
    candidatos_por_id: dict[int, list[dict]] = {}

    registros_interiores = cur.execute(
        """
        SELECT rp.id, rp.patologia, rp.localizacion_dano, es.nombre AS estancia_nombre
        FROM registros_patologias rp
        JOIN estancias es ON rp.estancia_id = es.id
        WHERE rp.visita_id=?
        ORDER BY rp.id DESC
        """,
        (visita_id,),
    ).fetchall()
    for registro in registros_interiores:
        label = f"Interior · {registro['estancia_nombre']} · {registro['patologia']}"
        if limpiar_texto(registro["localizacion_dano"]):
            label += f" · {registro['localizacion_dano']}"
        opcion = {
            "value": f"interior:{registro['id']}",
            "tipo": "interior",
            "id": registro["id"],
            "label": label,
            "patologia": registro["patologia"],
        }
        opciones.append(opcion)
        candidatos_por_id.setdefault(registro["id"], []).append(opcion)

    registros_exteriores = cur.execute(
        """
        SELECT id, patologia, zona_exterior, localizacion_dano_exterior
        FROM registros_patologias_exteriores
        WHERE visita_id=?
        ORDER BY id DESC
        """,
        (visita_id,),
    ).fetchall()
    for registro in registros_exteriores:
        label = f"Exterior · {registro['zona_exterior'] or 'Zona'} · {registro['patologia']}"
        if limpiar_texto(registro["localizacion_dano_exterior"]):
            label += f" · {registro['localizacion_dano_exterior']}"
        opcion = {
            "value": f"exterior:{registro['id']}",
            "tipo": "exterior",
            "id": registro["id"],
            "label": label,
            "patologia": registro["patologia"],
        }
        opciones.append(opcion)
        candidatos_por_id.setdefault(registro["id"], []).append(opcion)

    return opciones, candidatos_por_id


def resolver_patologia_vinculada(
    candidatos_por_id: dict[int, list[dict]],
    patologia_id,
    patologia_detectada: str = "",
):
    if not patologia_id:
        return None

    candidatos = candidatos_por_id.get(patologia_id, [])
    if not candidatos:
        return None
    if len(candidatos) == 1:
        return candidatos[0]

    texto = limpiar_texto(patologia_detectada).lower()
    if texto:
        for candidato in candidatos:
            if limpiar_texto(candidato["patologia"]).lower() == texto:
                return candidato

    return candidatos[0]


def mapa_patologia_es_exterior(visita, mapa=None) -> bool:
    ambito_mapa = limpiar_texto((mapa or {}).get("ambito_mapa"))
    ambito_visita = limpiar_texto(visita.get("ambito_visita"))
    ambito_referencia = ambito_mapa or ambito_visita
    return ambito_referencia in {"exterior", "zona_comun"}


def preparar_mapas_patologia(cur, visita_id: int):
    mapas = [
        dict(row)
        for row in cur.execute(
            """
            SELECT *
            FROM mapas_patologia
            WHERE visita_id=?
            ORDER BY id DESC
            """,
            (visita_id,),
        ).fetchall()
    ]
    _, candidatos_por_id = obtener_registros_patologia_vinculables(cur, visita_id)

    for mapa in mapas:
        mapa["ambito_mapa_label"] = etiquetar_opcion(
            mapa.get("ambito_mapa", ""), AMBITO_MAPA_LABELS
        )
        mapa["imagen_base_url"] = (
            f"/uploads/{mapa['imagen_base']}" if mapa.get("imagen_base") else ""
        )
        mapa["imagen_mapa_url"] = construir_imagen_mapa_url(mapa.get("imagen_base"))
        cuadrantes = [
            dict(row)
            for row in cur.execute(
                """
                SELECT *
                FROM cuadrantes_mapa_patologia
                WHERE mapa_id=?
                ORDER BY id ASC
                """,
                (mapa["id"],),
            ).fetchall()
        ]
        mapa["cuadrantes"] = cuadrantes
        mapa["total_cuadrantes_con_incidencia"] = sum(
            1
            for cuadrante in cuadrantes
            if limpiar_texto(cuadrante.get("patologia_detectada"))
        )
        mapa["total_cuadrantes_vinculados"] = sum(
            1 for cuadrante in cuadrantes if cuadrante.get("patologia_id")
        )
        for cuadrante in cuadrantes:
            patologia_vinculada = resolver_patologia_vinculada(
                candidatos_por_id,
                cuadrante.get("patologia_id"),
                cuadrante.get("patologia_detectada", ""),
            )
            cuadrante["patologia_vinculada"] = patologia_vinculada
            cuadrante["patologia_vinculada_label"] = (
                patologia_vinculada["label"] if patologia_vinculada else ""
            )
            cuadrante["patologia_ref_actual"] = (
                patologia_vinculada["value"] if patologia_vinculada else ""
            )
            cuadrante["tiene_patologia_vinculada"] = bool(patologia_vinculada)
            cuadrante["gravedad_label"] = etiquetar_opcion(
                cuadrante.get("gravedad", ""), GRAVEDAD_CUADRANTE_LABELS
            )
            fotos = obtener_fotos_relacionadas(
                cur,
                "cuadrante_mapa_patologia_fotos",
                "cuadrante_id",
                cuadrante["id"],
            )
            if not fotos and cuadrante.get("foto_detalle"):
                fotos = [{"id": None, "archivo": cuadrante["foto_detalle"], "created_at": None}]
            for foto in fotos:
                foto["url"] = f"/uploads/{foto['archivo']}"
            cuadrante["fotos"] = fotos
            cuadrante["foto_detalle_url"] = fotos[0]["url"] if fotos else ""

    return mapas


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    user_id = get_session_user_id(request)
    user = get_user_by_id(user_id) if user_id else None
    request.state.current_user = user

    if user is None and not is_public_path(path):
        response = RedirectResponse(url="/login", status_code=303)
        if user_id:
            response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    if user is not None and path in AUTH_PAGES:
        return RedirectResponse(url="/", status_code=303)

    return await call_next(request)


app.include_router(backups_router.router)
app.include_router(clientes_router.router)
app.include_router(costes_router.router)
app.include_router(crm_router.router)
app.include_router(dashboard_router.router)
app.include_router(emails_router.router)
app.include_router(facturacion_router.router)
app.include_router(gastos_router.router)
app.include_router(leads_router.router)
app.include_router(propuestas_router.router)


# -------------------------------------------------------
# PWA / ARCHIVOS MÓVIL
# -------------------------------------------------------


@app.get("/manifest.json")
def manifest():
    return FileResponse(
        str(STATIC_PATH / "manifest.json"),
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        str(STATIC_PATH / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/favicon.ico")
def favicon():
    return FileResponse(
        str(STATIC_PATH / "favicon.png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/apple-touch-icon.png")
def apple_touch_icon():
    return FileResponse(
        str(STATIC_PATH / "icon-192.png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# -------------------------------------------------------
# AUTENTICACIÓN
# -------------------------------------------------------


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_template(request, "login.html")


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    conn = get_connection()
    cur = conn.cursor()

    user = cur.execute(
        "SELECT * FROM usuarios WHERE username=? AND activo=1",
        (username.strip(),),
    ).fetchone()

    conn.close()

    if user is None or not verify_password(password, user["password_hash"]):
        return render_template(
            request,
            "login.html",
            {
                "error": "Usuario o contraseña incorrectos.",
                "form_data": {"username": username},
            },
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        f"{user['id']}:{sign_session_value(str(user['id']))}",
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
        path="/",
    )
    return response


@app.get("/crear-usuario", response_class=HTMLResponse)
def crear_usuario_page(request: Request):
    return render_template(request, "crear_usuario.html")


@app.post("/crear-usuario", response_class=HTMLResponse)
def crear_usuario(
    request: Request,
    nombre: str = Form(...),
    apellido1: str = Form(...),
    apellido2: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    titulacion: str = Form(""),
    numero_colegiado: str = Form(""),
    username: str = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...),
):
    form_data = {
        "nombre": nombre,
        "apellido1": apellido1,
        "apellido2": apellido2,
        "telefono": telefono,
        "email": email,
        "titulacion": titulacion,
        "numero_colegiado": numero_colegiado,
        "username": username,
    }

    if password != confirmar_password:
        return render_template(
            request,
            "crear_usuario.html",
            {
                "error": "Las contraseñas no coinciden.",
                "form_data": form_data,
            },
        )

    conn = get_connection()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM usuarios WHERE username=?",
        (username.strip(),),
    ).fetchone()

    if existing:
        conn.close()
        return render_template(
            request,
            "crear_usuario.html",
            {
                "error": "El usuario ya existe.",
                "form_data": form_data,
            },
        )

    cur.execute(
        """
        INSERT INTO usuarios (
            nombre,
            apellido1,
            apellido2,
            telefono,
            email,
            titulacion,
            numero_colegiado,
            username,
            password_hash,
            activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            nombre.strip(),
            apellido1.strip(),
            apellido2.strip(),
            telefono.strip(),
            email.strip(),
            titulacion.strip(),
            numero_colegiado.strip(),
            username.strip(),
            hash_password(password),
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/login", status_code=303)


@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/autocompletar-direccion")
async def autocompletar_direccion_endpoint(
    request: Request,
    direccion: str = Query(..., min_length=3),
):
    get_current_user(request)
    try:
        datos = await autocompletar_direccion(direccion)
        return JSONResponse(content=datos or {})
    except Exception:
        return JSONResponse(content={})


@app.get("/buscar-direcciones")
async def buscar_direcciones_endpoint(
    request: Request,
    q: str = Query(..., min_length=3),
):
    get_current_user(request)
    try:
        resultados = await sugerir_direcciones(q)
        return JSONResponse(content=resultados or [])
    except Exception:
        return JSONResponse(content=[])


@app.get("/api/catastro")
async def api_catastro(
    request: Request,
    referencia_catastral: str = Query(""),
):
    get_current_user(request)

    try:
        datos_catastro = await consultar_catastro_por_referencia(referencia_catastral)
        imagen_catastro = guardar_imagen_catastro_si_existe(
            datos_catastro.pop("imagen_bytes", None),
            datos_catastro.pop("imagen_extension", None),
        )
        aviso = datos_catastro.pop("aviso", "")

        return JSONResponse(
            {
                "ok": True,
                "datos": {
                    **datos_catastro,
                    "imagen_catastro": imagen_catastro,
                    "imagen_catastro_url": (
                        f"/uploads/{imagen_catastro}" if imagen_catastro else ""
                    ),
                },
                "aviso": aviso,
            }
        )
    except ValueError as exc:
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=200,
        )
    except Exception as exc:
        logger.error("[ERROR catastro] %s", exc)
        return JSONResponse(
            {
                "ok": False,
                "error": "No se pudo consultar Catastro. Puedes seguir rellenando el expediente manualmente.",
            },
            status_code=200,
        )


@app.get("/biblioteca-patologias", response_class=HTMLResponse)
def biblioteca_patologias(request: Request):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias WHERE COALESCE(activo, 1) = 1 ORDER BY nombre ASC"
    ).fetchall()
    conn.close()

    return render_template(
        request,
        "biblioteca_patologias.html",
        {
            "patologias": patologias,
            "categoria_options": BIBLIOTECA_CATEGORIA_OPTIONS,
            "categoria_labels": BIBLIOTECA_CATEGORIA_LABELS,
            "elemento_afectado_options": BIBLIOTECA_ELEMENTO_AFECTADO_OPTIONS,
            "mecanismo_options": BIBLIOTECA_MECANISMO_OPTIONS,
        },
    )


@app.post("/biblioteca-patologias")
def guardar_patologia_biblioteca(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    causa: str = Form(""),
    solucion: str = Form(""),
    categoria: str = Form(""),
    elemento_afectado: str = Form(""),
    mecanismo: str = Form(""),
    rol_patologia: str = Form(""),
):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO biblioteca_patologias (
            nombre, descripcion, causa, solucion, categoria, elemento_afectado, mecanismo, rol_patologia
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            descripcion,
            causa,
            solucion,
            categoria,
            elemento_afectado,
            mecanismo,
            rol_patologia,
        ),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/biblioteca-patologias", status_code=303)


@app.get("/biblioteca-patologias/{patologia_id}/editar", response_class=HTMLResponse)
def editar_patologia_biblioteca(request: Request, patologia_id: int):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    patologia = cur.execute(
        "SELECT * FROM biblioteca_patologias WHERE id=? AND COALESCE(activo, 1) = 1",
        (patologia_id,),
    ).fetchone()
    require_row(patologia, "Patología no encontrada")

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias WHERE COALESCE(activo, 1) = 1 ORDER BY nombre ASC"
    ).fetchall()
    conn.close()

    return render_template(
        request,
        "biblioteca_patologias.html",
        {
            "patologias": patologias,
            "patologia_edicion": patologia,
            "categoria_options": BIBLIOTECA_CATEGORIA_OPTIONS,
            "categoria_labels": BIBLIOTECA_CATEGORIA_LABELS,
            "elemento_afectado_options": BIBLIOTECA_ELEMENTO_AFECTADO_OPTIONS,
            "mecanismo_options": BIBLIOTECA_MECANISMO_OPTIONS,
        },
    )


@app.post("/biblioteca-patologias/{patologia_id}/editar")
def actualizar_patologia_biblioteca(
    request: Request,
    patologia_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    causa: str = Form(""),
    solucion: str = Form(""),
    categoria: str = Form(""),
    elemento_afectado: str = Form(""),
    mecanismo: str = Form(""),
    rol_patologia: str = Form(""),
):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    updated = cur.execute(
        """
        UPDATE biblioteca_patologias
        SET nombre=?, descripcion=?, causa=?, solucion=?, categoria=?, elemento_afectado=?, mecanismo=?, rol_patologia=?
        WHERE id=?
        """,
        (
            nombre,
            descripcion,
            causa,
            solucion,
            categoria,
            elemento_afectado,
            mecanismo,
            rol_patologia,
            patologia_id,
        ),
    )
    if updated.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Patología no encontrada")
    conn.commit()
    conn.close()

    return RedirectResponse(url="/biblioteca-patologias", status_code=303)


@app.post("/borrar-patologia/{patologia_id}")
def borrar_patologia_biblioteca(request: Request, patologia_id: int):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    patologia = cur.execute(
        "SELECT id FROM biblioteca_patologias WHERE id=? AND COALESCE(activo, 1) = 1",
        (patologia_id,),
    ).fetchone()
    require_row(patologia, "Patología no encontrada")

    cur.execute(
        "UPDATE biblioteca_patologias SET activo = 0 WHERE id=?",
        (patologia_id,),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/biblioteca-patologias", status_code=303)


# -------------------------------------------------------
# INICIO
# -------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = ""):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    search = q.strip()
    if search:
        expedientes = cur.execute(
            """
            SELECT *
            FROM expedientes
            WHERE owner_user_id=?
              AND (
                  numero_expediente LIKE ?
                  OR direccion LIKE ?
                  OR cliente LIKE ?
              )
            ORDER BY id DESC
            """,
            (
                current_user["id"],
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
            ),
        ).fetchall()
    else:
        expedientes = cur.execute(
            """
            SELECT *
            FROM expedientes
            WHERE owner_user_id=?
            ORDER BY id DESC
            """,
            (current_user["id"],),
        ).fetchall()

    conn.close()

    return render_template(
        request,
        "index.html",
        {
            "expedientes": expedientes,
            "search_query": search,
        },
    )


@app.get("/ping")
def ping():
    return {"mensaje": "Servidor funcionando"}


# -------------------------------------------------------
# EXPEDIENTES
# -------------------------------------------------------


@app.get("/expedientes", response_class=HTMLResponse)
def listar_expedientes(request: Request):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expedientes = cur.execute(
        """
        SELECT *
        FROM expedientes
        WHERE owner_user_id=?
        ORDER BY id DESC
        """,
        (current_user["id"],),
    ).fetchall()

    conn.close()

    expedientes_procesados = []
    for expediente in expedientes:
        item = dict(expediente)
        item["descripcion_plantas"] = formatear_plantas(
            item.get("plantas_bajo_rasante"),
            item.get("plantas_sobre_baja"),
        )
        expedientes_procesados.append(item)

    return render_template(
        request,
        "expedientes.html",
        {"expedientes": expedientes_procesados},
    )


@app.get("/nuevo-expediente", response_class=HTMLResponse)
def nuevo_expediente(
    request: Request,
    cliente_id: int | None = Query(None),
    propuesta_id: int | None = Query(None),
):
    current_user = get_current_user(request)
    prefill = {
        "cliente_id": "",
        "propuesta_id": "",
        "cliente": "",
        "direccion": "",
        "codigo_postal": "",
        "ciudad": "",
        "provincia": "",
        "tipo_informe": "patologias",
        "tipo_inmueble": "",
        "observaciones_generales": "",
        "objeto_pericia": "",
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        cliente = None
        propuesta = None
        lead = None
        if propuesta_id:
            propuesta = cur.execute(
                """
                SELECT p.*,
                       c.nombre AS cliente_nombre,
                       c.apellidos AS cliente_apellidos,
                       c.razon_social AS cliente_razon_social,
                       c.email AS cliente_email,
                       c.telefono AS cliente_telefono,
                       c.direccion AS cliente_direccion,
                       c.codigo_postal AS cliente_codigo_postal,
                       c.ciudad AS cliente_ciudad,
                       c.provincia AS cliente_provincia,
                       l.nombre AS lead_nombre,
                       l.email AS lead_email,
                       l.telefono AS lead_telefono,
                       l.servicio_solicitado AS lead_servicio_solicitado,
                       l.mensaje AS lead_mensaje
                FROM propuestas p
                LEFT JOIN clientes c ON c.id = p.cliente_id
                LEFT JOIN leads l ON l.id = p.lead_id
                WHERE p.id = ? AND p.owner_user_id = ?
                """,
                (propuesta_id, current_user["id"]),
            ).fetchone()
            if not propuesta:
                raise HTTPException(status_code=404, detail="Propuesta no encontrada")
            if propuesta["expediente_id"]:
                conn.close()
                return RedirectResponse(
                    url=f"/detalle-expediente/{propuesta['expediente_id']}",
                    status_code=303,
                )
            cliente_id = propuesta["cliente_id"] or cliente_id
            prefill["propuesta_id"] = str(propuesta_id)

        if cliente_id:
            cliente = cur.execute(
                """
                SELECT *
                FROM clientes
                WHERE id = ? AND owner_user_id = ?
                """,
                (cliente_id, current_user["id"]),
            ).fetchone()
            if not cliente:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            prefill["cliente_id"] = str(cliente_id)

        if propuesta and propuesta["lead_id"] and not cliente:
            lead = cur.execute(
                """
                SELECT *
                FROM leads
                WHERE id = ? AND owner_user_id = ?
                """,
                (propuesta["lead_id"], current_user["id"]),
            ).fetchone()

        if cliente:
            nombre_cliente_form = limpiar_texto(cliente["razon_social"]) or " ".join(
                parte
                for parte in (
                    limpiar_texto(cliente["nombre"]),
                    limpiar_texto(cliente["apellidos"]),
                )
                if parte
            )
            prefill.update(
                {
                    "cliente": nombre_cliente_form,
                    "direccion": limpiar_texto(cliente["direccion"]),
                    "codigo_postal": limpiar_texto(cliente["codigo_postal"]),
                    "ciudad": limpiar_texto(cliente["ciudad"]),
                    "provincia": limpiar_texto(cliente["provincia"]),
                    "observaciones_generales": " · ".join(
                        parte
                        for parte in (
                            f"Email: {cliente['email']}" if limpiar_texto(cliente["email"]) else "",
                            f"Teléfono: {cliente['telefono']}" if limpiar_texto(cliente["telefono"]) else "",
                        )
                        if parte
                    ),
                }
            )

        if propuesta:
            tipo_trabajo = limpiar_texto(propuesta["tipo_trabajo"]).lower()
            if "inspe" in tipo_trabajo:
                prefill["tipo_informe"] = "inspeccion"
            elif "valor" in tipo_trabajo or "tas" in tipo_trabajo:
                prefill["tipo_informe"] = "valoracion"
            elif "habit" in tipo_trabajo:
                prefill["tipo_informe"] = "habitabilidad"
            elif "patolog" in tipo_trabajo:
                prefill["tipo_informe"] = "patologias"

            nombre_propuesta_cliente = (
                limpiar_texto(propuesta["cliente_razon_social"])
                or " ".join(
                    parte
                    for parte in (
                        limpiar_texto(propuesta["cliente_nombre"]),
                        limpiar_texto(propuesta["cliente_apellidos"]),
                    )
                    if parte
                )
                or limpiar_texto(propuesta["lead_nombre"])
            )
            if nombre_propuesta_cliente:
                prefill["cliente"] = nombre_propuesta_cliente
            if limpiar_texto(propuesta["direccion_inmueble"]):
                prefill["direccion"] = limpiar_texto(propuesta["direccion_inmueble"])
            if not prefill["cliente"] and lead:
                prefill["cliente"] = limpiar_texto(lead["nombre"])
            prefill["objeto_pericia"] = limpiar_texto(propuesta["alcance"])
            prefill["observaciones_generales"] = "\n".join(
                parte
                for parte in (
                    prefill["observaciones_generales"],
                    f"Origen: propuesta {propuesta['numero_propuesta']}.",
                    f"Plazo estimado: {propuesta['plazo_estimado']}" if limpiar_texto(propuesta["plazo_estimado"]) else "",
                    f"Condiciones: {propuesta['condiciones']}" if limpiar_texto(propuesta["condiciones"]) else "",
                )
                if parte
            )
    finally:
        if conn:
            conn.close()

    return render_template(
        request,
        "nuevo_expediente.html",
        {
            "numero_expediente_sugerido": generar_numero_expediente(),
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
            "prefill": prefill,
        },
    )


@app.post("/guardar-expediente")
def guardar_expediente(
    request: Request,
    tipo_informe: str = Form("patologias"),
    destinatario: str = Form("particular"),
    ambito_patologias: str = Form("interior"),
    descripcion_dano: str = Form(""),
    causa_probable: str = Form(""),
    pruebas_indicios: str = Form(""),
    evolucion_preexistencia: str = Form(""),
    propuesta_reparacion: str = Form(""),
    urgencia_gravedad: str = Form(""),
    cliente: str = Form(...),
    referencia_catastral: str = Form(""),
    direccion: str = Form(...),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
    tipo_inmueble: str = Form(""),
    orientacion_inmueble: str = Form(""),
    anio_construccion: str = Form(""),
    plantas_bajo_rasante: str = Form("0"),
    plantas_sobre_baja: str = Form("0"),
    uso_inmueble: str = Form(""),
    observaciones_generales: str = Form(""),
    planta_unidad: str = Form(""),
    puerta_unidad: str = Form(""),
    analisis_unidades: str = Form("una_unidad"),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    dormitorios_unidad: str = Form(""),
    banos_unidad: str = Form(""),
    observaciones_bloque: str = Form(""),
    observaciones_unidad: str = Form(""),
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
    procedimiento_judicial: str = Form(""),
    juzgado: str = Form(""),
    auto_judicial: str = Form(""),
    parte_solicitante: str = Form(""),
    objeto_pericia: str = Form(""),
    alcance_limitaciones: str = Form(""),
    metodologia_pericial: str = Form(""),
    imagen_catastro: str = Form(""),
    cliente_id: str = Form(""),
    propuesta_id: str = Form(""),
):
    current_user = get_current_user(request)
    expediente_id = None
    propuesta_id_int = parse_optional_int(propuesta_id)

    for _ in range(3):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN IMMEDIATE")
            if propuesta_id_int:
                propuesta = cur.execute(
                    """
                    SELECT id, expediente_id
                    FROM propuestas
                    WHERE id = ? AND owner_user_id = ?
                    """,
                    (propuesta_id_int, current_user["id"]),
                ).fetchone()
                if not propuesta:
                    raise HTTPException(status_code=404, detail="Propuesta no encontrada")
                if propuesta["expediente_id"]:
                    conn.rollback()
                    conn.close()
                    return RedirectResponse(
                        url=f"/detalle-expediente/{propuesta['expediente_id']}",
                        status_code=303,
                    )

            numero_expediente = generar_numero_expediente_desde_cursor(cur)

            existe = cur.execute(
                """
                SELECT id
                FROM expedientes
                WHERE numero_expediente=?
                """,
                (numero_expediente,),
            ).fetchone()

            if existe:
                conn.rollback()
                conn.close()
                continue

            cur.execute(
                """
                INSERT INTO expedientes (
                    numero_expediente,
                    tipo_informe,
                    destinatario,
                    ambito_patologias,
                    descripcion_dano,
                    causa_probable,
                    pruebas_indicios,
                    evolucion_preexistencia,
                    propuesta_reparacion,
                    urgencia_gravedad,
                    cliente,
                    referencia_catastral,
                    direccion,
                    codigo_postal,
                    ciudad,
                    provincia,
                    tipo_inmueble,
                    orientacion_inmueble,
                    anio_construccion,
                    plantas_bajo_rasante,
                    plantas_sobre_baja,
                    uso_inmueble,
                    observaciones_generales,
                    planta_unidad,
                    puerta_unidad,
                    analisis_unidades,
                    superficie_construida,
                    superficie_util,
                    dormitorios_unidad,
                    banos_unidad,
                    observaciones_bloque,
                    observaciones_unidad,
                    reformado,
                    fecha_reforma,
                    observaciones_reforma,
                    procedimiento_judicial,
                    juzgado,
                    auto_judicial,
                    parte_solicitante,
                    objeto_pericia,
                    alcance_limitaciones,
                    metodologia_pericial,
                    imagen_catastro,
                    owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    numero_expediente,
                    tipo_informe,
                    destinatario,
                    ambito_patologias,
                    descripcion_dano,
                    causa_probable,
                    pruebas_indicios,
                    evolucion_preexistencia,
                    propuesta_reparacion,
                    urgencia_gravedad,
                    cliente,
                    referencia_catastral,
                    direccion,
                    codigo_postal,
                    ciudad,
                    provincia,
                    tipo_inmueble,
                    orientacion_inmueble,
                    anio_construccion,
                    plantas_bajo_rasante,
                    plantas_sobre_baja,
                    uso_inmueble,
                    observaciones_generales,
                    planta_unidad,
                    puerta_unidad,
                    analisis_unidades,
                    superficie_construida,
                    superficie_util,
                    dormitorios_unidad,
                    banos_unidad,
                    observaciones_bloque,
                    observaciones_unidad,
                    reformado,
                    fecha_reforma,
                    observaciones_reforma,
                    procedimiento_judicial,
                    juzgado,
                    auto_judicial,
                    parte_solicitante,
                    objeto_pericia,
                    alcance_limitaciones,
                    metodologia_pericial,
                    imagen_catastro,
                    current_user["id"],
                ),
            )

            expediente_id = cur.lastrowid
            if propuesta_id_int:
                cur.execute(
                    """
                    UPDATE propuestas
                    SET expediente_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND owner_user_id = ?
                    """,
                    (expediente_id, propuesta_id_int, current_user["id"]),
                )
            conn.commit()
            conn.close()
            break
        except HTTPException:
            conn.rollback()
            conn.close()
            raise
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()

    if expediente_id is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar un número de expediente único.",
        )

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@app.get("/expedientes/{expediente_id}/presupuesto-reparacion", response_class=HTMLResponse)
def presupuesto_reparacion_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        presupuesto = preparar_presupuesto_reparacion_expediente(cur, expediente_id)
    finally:
        conn.close()

    expediente_data = dict(expediente)
    expediente_data["tipo_informe_label"] = etiquetar_opcion(
        expediente_data.get("tipo_informe", ""),
        TIPO_INFORME_LABELS,
    )

    return render_template(
        request,
        "presupuesto_reparacion.html",
        {
            "expediente": expediente_data,
            "presupuesto": presupuesto,
            "formatear_numero_es": formatear_numero_es,
        },
    )


@app.get("/expedientes/{expediente_id}/actuaciones-reparacion", response_class=HTMLResponse)
def actuaciones_reparacion_expediente(
    request: Request,
    expediente_id: int,
    q: str = "",
    actuacion_id: int | None = None,
    mensaje: str = "",
    error: str = "",
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        actuaciones = preparar_actuaciones_reparacion_expediente(cur, expediente_id)
        presupuesto_patologias = preparar_presupuesto_reparacion_expediente(cur, expediente_id)
        partidas_encontradas = buscar_partidas_coste_para_actuacion(cur, q)
    finally:
        conn.close()

    expediente_data = dict(expediente)
    expediente_data["tipo_informe_label"] = etiquetar_opcion(
        expediente_data.get("tipo_informe", ""),
        TIPO_INFORME_LABELS,
    )

    return render_template(
        request,
        "actuaciones_reparacion.html",
        {
            "expediente": expediente_data,
            "actuaciones": actuaciones,
            "tiene_presupuesto_patologias": presupuesto_patologias["tiene_costes"],
            "partidas_encontradas": partidas_encontradas,
            "q": q,
            "actuacion_id": actuacion_id,
            "mensaje": mensaje,
            "error": error,
            "formatear_numero_es": formatear_numero_es,
        },
    )


@app.post("/expedientes/{expediente_id}/actuaciones-reparacion")
def crear_actuacion_reparacion(
    request: Request,
    expediente_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    observaciones: str = Form(""),
    orden: str = Form(""),
):
    current_user = get_current_user(request)
    titulo_limpio = limpiar_texto(titulo)
    if not titulo_limpio:
        return redirect_actuaciones_reparacion(
            expediente_id,
            error="La actuación necesita un título.",
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        orden_num = parsear_entero_positivo(orden)
        if not orden_num:
            orden_num = (
                cur.execute(
                    """
                    SELECT COALESCE(MAX(orden), 0) + 1
                    FROM actuaciones_reparacion
                    WHERE expediente_id = ?
                    """,
                    (expediente_id,),
                ).fetchone()[0]
                or 1
            )
        cur.execute(
            """
            INSERT INTO actuaciones_reparacion (
                expediente_id, titulo, descripcion, observaciones, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                titulo_limpio,
                limpiar_texto(descripcion),
                limpiar_texto(observaciones),
                orden_num,
            ),
        )
        actuacion_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Actuación creada.",
        actuacion_id=actuacion_id,
    )


@app.post("/actuaciones-reparacion/{actuacion_id}/actualizar")
def actualizar_actuacion_reparacion(
    request: Request,
    actuacion_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    observaciones: str = Form(""),
    orden: str = Form(""),
):
    current_user = get_current_user(request)
    titulo_limpio = limpiar_texto(titulo)
    conn = get_connection()
    cur = conn.cursor()
    try:
        actuacion = get_owned_actuacion_reparacion(cur, actuacion_id, current_user["id"])
        require_row(actuacion, "Actuación no encontrada")
        expediente_id = actuacion["expediente_id"]
        if not titulo_limpio:
            return redirect_actuaciones_reparacion(
                expediente_id,
                error="La actuación necesita un título.",
                actuacion_id=actuacion_id,
            )
        orden_num = parsear_entero_positivo(orden) or 0
        cur.execute(
            """
            UPDATE actuaciones_reparacion
            SET titulo = ?, descripcion = ?, observaciones = ?,
                orden = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                titulo_limpio,
                limpiar_texto(descripcion),
                limpiar_texto(observaciones),
                orden_num,
                actuacion_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Actuación actualizada.",
        actuacion_id=actuacion_id,
    )


@app.post("/actuaciones-reparacion/{actuacion_id}/borrar")
def borrar_actuacion_reparacion(request: Request, actuacion_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        actuacion = get_owned_actuacion_reparacion(cur, actuacion_id, current_user["id"])
        require_row(actuacion, "Actuación no encontrada")
        expediente_id = actuacion["expediente_id"]
        cur.execute("DELETE FROM actuacion_partidas WHERE actuacion_id = ?", (actuacion_id,))
        cur.execute("DELETE FROM actuaciones_reparacion WHERE id = ?", (actuacion_id,))
        conn.commit()
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Actuación borrada.",
    )


@app.post("/actuaciones-reparacion/{actuacion_id}/partidas")
def anadir_partida_actuacion_reparacion(
    request: Request,
    actuacion_id: int,
    concepto_id: int = Form(...),
    cantidad: str = Form("1"),
    q: str = Form(""),
):
    current_user = get_current_user(request)
    cantidad_num = round(parsear_decimal_coste_patologia(cantidad, 0), 4)
    conn = get_connection()
    cur = conn.cursor()
    try:
        actuacion = get_owned_actuacion_reparacion(cur, actuacion_id, current_user["id"])
        require_row(actuacion, "Actuación no encontrada")
        expediente_id = actuacion["expediente_id"]
        if cantidad_num <= 0:
            return redirect_actuaciones_reparacion(
                expediente_id,
                error="La cantidad debe ser mayor que cero.",
                actuacion_id=actuacion_id,
                q=q,
            )
        concepto = cur.execute(
            """
            SELECT id, codigo, unidad, resumen, descripcion, precio, estado
            FROM costes_conceptos
            WHERE id = ?
            """,
            (concepto_id,),
        ).fetchone()
        require_row(concepto, "Partida de coste no encontrada")
        precio_unitario = round(float(concepto["precio"] or 0), 4)
        importe = round(cantidad_num * precio_unitario, 2)
        descripcion_snapshot = (
            limpiar_texto(concepto["descripcion"])
            or limpiar_texto(concepto["resumen"])
            or limpiar_texto(concepto["codigo"])
        )
        cur.execute(
            """
            INSERT INTO actuacion_partidas (
                actuacion_id, concepto_id, descripcion_snapshot,
                unidad_snapshot, precio_unitario_snapshot, cantidad,
                importe, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                actuacion_id,
                concepto_id,
                descripcion_snapshot,
                concepto["unidad"],
                precio_unitario,
                cantidad_num,
                importe,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Partida añadida a la actuación.",
        actuacion_id=actuacion_id,
        q=q,
    )


@app.post("/actuacion-partidas/{partida_id}/actualizar")
def actualizar_partida_actuacion_reparacion(
    request: Request,
    partida_id: int,
    cantidad: str = Form("1"),
):
    current_user = get_current_user(request)
    cantidad_num = round(parsear_decimal_coste_patologia(cantidad, 0), 4)
    if cantidad_num <= 0:
        cantidad_num = 0
    conn = get_connection()
    cur = conn.cursor()
    try:
        partida = get_owned_actuacion_partida(cur, partida_id, current_user["id"])
        require_row(partida, "Partida de actuación no encontrada")
        expediente_id = partida["expediente_id"]
        importe = round(
            cantidad_num * float(partida["precio_unitario_snapshot"] or 0),
            2,
        )
        cur.execute(
            """
            UPDATE actuacion_partidas
            SET cantidad = ?, importe = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (cantidad_num, importe, partida_id),
        )
        conn.commit()
        actuacion_id = partida["actuacion_id"]
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Partida actualizada.",
        actuacion_id=actuacion_id,
    )


@app.post("/actuacion-partidas/{partida_id}/borrar")
def borrar_partida_actuacion_reparacion(request: Request, partida_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        partida = get_owned_actuacion_partida(cur, partida_id, current_user["id"])
        require_row(partida, "Partida de actuación no encontrada")
        expediente_id = partida["expediente_id"]
        actuacion_id = partida["actuacion_id"]
        cur.execute("DELETE FROM actuacion_partidas WHERE id = ?", (partida_id,))
        conn.commit()
    finally:
        conn.close()

    return redirect_actuaciones_reparacion(
        expediente_id,
        mensaje="Partida borrada.",
        actuacion_id=actuacion_id,
    )


@app.get("/detalle-expediente/{expediente_id}", response_class=HTMLResponse)
def detalle_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    visitas = cur.execute(
        """
        SELECT v.*,
               (
                   SELECT COUNT(*)
                   FROM estancias e
                   WHERE e.visita_id = v.id
               ) AS total_estancias,
               (
                   SELECT COUNT(*)
                   FROM registros_patologias rp
                   WHERE rp.visita_id = v.id
               ) AS total_patologias
        FROM visitas v
        WHERE v.expediente_id=?
        ORDER BY v.id DESC
        """,
        (expediente_id,),
    ).fetchall()

    tipo_informe = limpiar_texto(expediente["tipo_informe"])
    estructura_multiunidad = cargar_estructura_multiunidad(cur, expediente_id)
    visitas_data = []
    resumen_tipo = {}
    revision_informe = preparar_pendientes_revision_expediente(cur, expediente_id)
    presupuesto_reparacion = preparar_presupuesto_reparacion_expediente(cur, expediente_id)
    actuaciones_reparacion = preparar_actuaciones_reparacion_expediente(cur, expediente_id)
    timeline_economico = construir_timeline_economico_expediente(
        cur,
        expediente_id,
        current_user["id"],
    )

    for visita in visitas:
        visita_data = dict(visita)
        visita_data["ambito_visita_label"] = etiquetar_opcion(
            visita_data.get("ambito_visita", ""), AMBITO_VISITA_LABELS
        )
        visita_data["nombre_nivel_visita"] = ""
        visita_data["identificador_unidad_visita"] = ""
        if visita_data.get("nivel_id"):
            nivel_row = cur.execute(
                "SELECT nombre_nivel FROM niveles_edificio WHERE id=?",
                (visita_data["nivel_id"],),
            ).fetchone()
            visita_data["nombre_nivel_visita"] = (
                limpiar_texto(nivel_row["nombre_nivel"]) if nivel_row else ""
            )
        if visita_data.get("unidad_id"):
            unidad_row = cur.execute(
                "SELECT identificador FROM unidades_expediente WHERE id=?",
                (visita_data["unidad_id"],),
            ).fetchone()
            visita_data["identificador_unidad_visita"] = (
                limpiar_texto(unidad_row["identificador"]) if unidad_row else ""
            )
        if tipo_informe == "patologias":
            visita_data["total_patologias_exteriores"] = cur.execute(
                """
                SELECT COUNT(*)
                FROM registros_patologias_exteriores
                WHERE visita_id = ?
                """,
                (visita["id"],),
            ).fetchone()[0]
            visita_data["total_mapas_patologia"] = cur.execute(
                "SELECT COUNT(*) FROM mapas_patologia WHERE visita_id=?",
                (visita["id"],),
            ).fetchone()[0]
            visita_data["total_cuadrantes_con_incidencia"] = cur.execute(
                """
                SELECT COUNT(*)
                FROM cuadrantes_mapa_patologia qmp
                JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
                WHERE mp.visita_id = ?
                  AND TRIM(IFNULL(qmp.patologia_detectada, '')) <> ''
                """,
                (visita["id"],),
            ).fetchone()[0]
            visita_data["total_cuadrantes_vinculados"] = cur.execute(
                """
                SELECT COUNT(*)
                FROM cuadrantes_mapa_patologia qmp
                JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
                WHERE mp.visita_id = ?
                  AND qmp.patologia_id IS NOT NULL
                """,
                (visita["id"],),
            ).fetchone()[0]
        elif tipo_informe == "inspeccion":
            visita_data["tiene_inspeccion_general"] = bool(
                cur.execute(
                    "SELECT 1 FROM inspeccion_general_visita WHERE visita_id=? LIMIT 1",
                    (visita["id"],),
                ).fetchone()
            )
            visita_data["total_estancias_inspeccion"] = cur.execute(
                "SELECT COUNT(*) FROM inspeccion_estancias WHERE visita_id=?",
                (visita["id"],),
            ).fetchone()[0]
        elif tipo_informe == "habitabilidad":
            visita_data["tiene_habitabilidad_general"] = bool(
                cur.execute(
                    "SELECT 1 FROM habitabilidad_general_visita WHERE visita_id=? LIMIT 1",
                    (visita["id"],),
                ).fetchone()
            )
            visita_data["total_estancias_habitabilidad"] = cur.execute(
                "SELECT COUNT(*) FROM habitabilidad_estancias WHERE visita_id=?",
                (visita["id"],),
            ).fetchone()[0]
            conclusion_row = cur.execute(
                """
                SELECT conclusion_habitabilidad
                FROM habitabilidad_general_visita
                WHERE visita_id=?
                LIMIT 1
                """,
                (visita["id"],),
            ).fetchone()
            visita_data["conclusion_habitabilidad"] = (
                limpiar_texto(conclusion_row["conclusion_habitabilidad"])
                if conclusion_row
                else ""
            )
            visita_data["conclusion_habitabilidad_label"] = etiquetar_opcion(
                visita_data["conclusion_habitabilidad"],
                {
                    "apto": "Apto",
                    "apto_con_deficiencias": "Apto con deficiencias",
                    "no_apto": "No apto",
                },
            )
        elif tipo_informe == "valoracion":
            visita_data["tiene_valoracion"] = bool(
                cur.execute(
                    "SELECT 1 FROM valoracion_visita WHERE visita_id=? LIMIT 1",
                    (visita["id"],),
                ).fetchone()
            )
            visita_data["total_comparables"] = cur.execute(
                "SELECT COUNT(*) FROM comparables_valoracion WHERE visita_id=?",
                (visita["id"],),
            ).fetchone()[0]
            valoracion_row = cur.execute(
                """
                SELECT valor_tasacion_final
                FROM valoracion_visita
                WHERE visita_id=?
                LIMIT 1
                """,
                (visita["id"],),
            ).fetchone()
            visita_data["valor_tasacion_final"] = (
                limpiar_texto(valoracion_row["valor_tasacion_final"])
                if valoracion_row
                else ""
            )
        visitas_data.append(visita_data)

    if tipo_informe == "patologias":
        resumen_tipo = {
            "total_interiores": cur.execute(
                """
                SELECT COUNT(*)
                FROM registros_patologias rp
                JOIN visitas v ON rp.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "total_exteriores": cur.execute(
                """
                SELECT COUNT(*)
                FROM registros_patologias_exteriores rpe
                JOIN visitas v ON rpe.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
        }
    elif tipo_informe == "inspeccion":
        resumen_tipo = {
            "visitas_con_checklist": cur.execute(
                """
                SELECT COUNT(*)
                FROM inspeccion_general_visita ig
                JOIN visitas v ON ig.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "estancias_inspeccionadas": cur.execute(
                """
                SELECT COUNT(*)
                FROM inspeccion_estancias ie
                JOIN visitas v ON ie.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "visitas_con_exterior": cur.execute(
                """
                SELECT COUNT(*)
                FROM inspeccion_exterior ie
                JOIN visitas v ON ie.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "visitas_con_comunes": cur.execute(
                """
                SELECT COUNT(*)
                FROM inspeccion_elementos_comunes ic
                JOIN visitas v ON ic.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
        }
    elif tipo_informe == "habitabilidad":
        ultima_habitabilidad = cur.execute(
            """
            SELECT hg.conclusion_habitabilidad
            FROM habitabilidad_general_visita hg
            JOIN visitas v ON hg.visita_id = v.id
            WHERE v.expediente_id = ?
            ORDER BY v.id DESC
            LIMIT 1
            """,
            (expediente_id,),
        ).fetchone()
        resumen_tipo = {
            "visitas_con_habitabilidad": cur.execute(
                """
                SELECT COUNT(*)
                FROM habitabilidad_general_visita hg
                JOIN visitas v ON hg.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "estancias_evaluadas": cur.execute(
                """
                SELECT COUNT(*)
                FROM habitabilidad_estancias he
                JOIN visitas v ON he.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "visitas_con_exterior": cur.execute(
                """
                SELECT COUNT(*)
                FROM habitabilidad_exterior he
                JOIN visitas v ON he.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "ultima_conclusion": (
                limpiar_texto(ultima_habitabilidad["conclusion_habitabilidad"])
                if ultima_habitabilidad
                else ""
            ),
        }
    elif tipo_informe == "valoracion":
        ultima_valoracion = cur.execute(
            """
            SELECT vv.valor_tasacion_final
            FROM valoracion_visita vv
            JOIN visitas v ON vv.visita_id = v.id
            WHERE v.expediente_id = ?
            ORDER BY v.id DESC
            LIMIT 1
            """,
            (expediente_id,),
        ).fetchone()
        comparables_legacy = cur.execute(
            """
            SELECT COUNT(*)
            FROM comparables_valoracion cv
            JOIN visitas v ON cv.visita_id = v.id
            WHERE v.expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()[0]
        testigos_vinculados = cur.execute(
            """
            SELECT COUNT(*)
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()[0]
        resumen_tipo = {
            "visitas_con_valoracion": cur.execute(
                """
                SELECT COUNT(*)
                FROM valoracion_visita vv
                JOIN visitas v ON vv.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
            "comparables": comparables_legacy + testigos_vinculados,
            "comparables_legacy": comparables_legacy,
            "testigos_vinculados": testigos_vinculados,
            "valor_tasacion_final": (
                limpiar_texto(ultima_valoracion["valor_tasacion_final"])
                if ultima_valoracion
                else ""
            ),
        }

    conn.close()

    expediente_data = dict(expediente)
    expediente_data["descripcion_plantas"] = formatear_plantas(
        expediente_data.get("plantas_bajo_rasante"),
        expediente_data.get("plantas_sobre_baja"),
    )
    expediente_data["tipo_informe_label"] = etiquetar_opcion(
        expediente_data.get("tipo_informe", ""),
        TIPO_INFORME_LABELS,
    )
    expediente_data["destinatario_label"] = etiquetar_opcion(
        expediente_data.get("destinatario", ""),
        DESTINATARIO_LABELS,
    )
    expediente_data["ambito_patologias_label"] = etiquetar_opcion(
        expediente_data.get("ambito_patologias", ""),
        AMBITO_PATOLOGIAS_LABELS,
    )
    expediente_data["es_judicial"] = (
        limpiar_texto(expediente_data.get("destinatario")) == "judicial"
    )
    expediente_data["es_informe_patologias"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "patologias"
    )
    expediente_data["es_informe_inspeccion"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "inspeccion"
    )
    expediente_data["es_informe_habitabilidad"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "habitabilidad"
    )
    expediente_data["es_informe_valoracion"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "valoracion"
    )
    expediente_data["imagen_catastro_url"] = (
        f"/uploads/{expediente_data['imagen_catastro']}"
        if expediente_data.get("imagen_catastro")
        else ""
    )
    expediente_data["analisis_unidades_resuelto"] = limpiar_texto(
        expediente_data.get("analisis_unidades")
    ) or (
        "varias_unidades"
        if estructura_multiunidad["niveles"] or estructura_multiunidad["unidades"]
        else "una_unidad"
    )
    expediente_data["ultima_conclusion_habitabilidad_label"] = etiquetar_opcion(
        resumen_tipo.get("ultima_conclusion", ""),
        {
            "apto": "Apto",
            "apto_con_deficiencias": "Apto con deficiencias",
            "no_apto": "No apto",
        },
    )

    return render_template(
        request,
        "detalle_expediente.html",
        {
            "expediente": expediente_data,
            "visitas": visitas_data,
            "resumen_tipo": resumen_tipo,
            "revision_informe": revision_informe,
            "timeline_economico": timeline_economico,
            "tiene_presupuesto_reparacion": (
                presupuesto_reparacion["tiene_costes"]
                or actuaciones_reparacion["total_pem"] > 0
            ),
            "niveles_edificio": estructura_multiunidad["niveles"],
            "unidades_expediente": estructura_multiunidad["unidades"],
            "unidades_sin_nivel": estructura_multiunidad["sin_nivel"],
            "anejos_sueltos": estructura_multiunidad["anejos_sueltos"],
            "unidades_principales_form": estructura_multiunidad["unidades_principales"],
            "tipo_nivel_options": TIPO_NIVEL_OPTIONS,
            "tipo_unidad_options": TIPO_UNIDAD_OPTIONS,
            "vinculo_unidad_options": VINCULO_UNIDAD_OPTIONS,
            "tipo_anejo_options": TIPO_ANEJO_OPTIONS,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.get("/expedientes/{expediente_id}/pericial-workbench", response_class=HTMLResponse)
def pericial_workbench_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El workbench pericial solo aplica a expedientes de patologías.",
            )
        workbench = preparar_pericial_workbench(cur, expediente)
    finally:
        conn.close()

    return render_template(
        request,
        "pericial_workbench.html",
        {
            "workbench": workbench,
            "expediente": workbench["expediente"],
            "metricas": workbench["metricas"],
            "diagnostico": workbench["diagnostico"],
            "inventario": workbench["inventario"],
            "visitas": workbench["visitas"],
            "limitaciones_candidatas": workbench["limitaciones_candidatas"],
            "recomendaciones_candidatas": workbench["recomendaciones_candidatas"],
            "borrador_informe": workbench["borrador_informe"],
            "actuaciones": workbench["actuaciones"],
            "documentos_aportados": workbench["documentos_aportados"],
            "tipos_documentales_anexo_a": workbench["tipos_documentales_anexo_a"],
            "advertencias": workbench["advertencias"],
            "formatear_numero_es": formatear_numero_es,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


def redirect_pericial_workbench(expediente_id: int, mensaje: str = "", error: str = ""):
    url = f"/expedientes/{expediente_id}/pericial-workbench"
    params = []
    if mensaje:
        params.append(f"mensaje={quote_plus(mensaje)}")
    if error:
        params.append(f"error={quote_plus(error)}")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return RedirectResponse(url=url, status_code=303)


def redirect_informe_v2_editor(expediente_id: int, mensaje: str = "", error: str = ""):
    url = f"/expedientes/{expediente_id}/informe-v2-editor"
    params = []
    if mensaje:
        params.append(f"mensaje={quote_plus(mensaje)}")
    if error:
        params.append(f"error={quote_plus(error)}")
    if params:
        url = f"{url}?{'&'.join(params)}"
    return RedirectResponse(url=url, status_code=303)


@app.post("/expedientes/{expediente_id}/pericial-workbench/documentos")
def subir_documento_anexo_a_workbench(
    request: Request,
    expediente_id: int,
    archivo: UploadFile | None = File(None),
    nombre_visible: str = Form(""),
    descripcion: str = Form(""),
    tipo_documento: str = Form("Otro"),
    orden: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El gestor documental del Anexo A solo aplica a expedientes de patologías.",
            )
        try:
            archivo_ruta, nombre_original, mime_type = guardar_documento_pdf_expediente(
                archivo,
                expediente_id,
            )
        except ValueError as exc:
            return redirect_pericial_workbench(expediente_id, error=str(exc))
        orden_int = parse_optional_int(orden)
        if orden_int is None:
            orden_int = siguiente_orden_documento_expediente(cur, expediente_id)
        nombre = limpiar_texto(nombre_visible) or nombre_visible_documento_desde_archivo(
            nombre_original
        )
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                nombre,
                limpiar_texto(descripcion),
                normalizar_tipo_documental_anexo_a(tipo_documento),
                archivo_ruta,
                nombre_original,
                mime_type,
                orden_int,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_pericial_workbench(
        expediente_id,
        mensaje="Documento incorporado al Anexo A.",
    )


@app.post("/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}")
def actualizar_documento_anexo_a_workbench(
    request: Request,
    expediente_id: int,
    documento_id: int,
    nombre_visible: str = Form(""),
    descripcion: str = Form(""),
    tipo_documento: str = Form("Otro"),
    orden: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        documento = get_owned_expediente_documento(cur, documento_id, current_user["id"])
        require_row(documento, "Documento no encontrado")
        if documento["expediente_id"] != expediente_id:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        orden_int = parse_optional_int(orden)
        if orden_int is None:
            orden_int = int(documento["orden"] or 0)
        nombre = limpiar_texto(nombre_visible) or documento["nombre_visible"]
        cur.execute(
            """
            UPDATE expediente_documentos
            SET nombre_visible = ?,
                descripcion = ?,
                tipo_documento = ?,
                orden = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                nombre,
                limpiar_texto(descripcion),
                normalizar_tipo_documental_anexo_a(tipo_documento),
                orden_int,
                documento_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_pericial_workbench(
        expediente_id,
        mensaje="Documento actualizado.",
    )


@app.post("/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}/eliminar")
def eliminar_documento_anexo_a_workbench(
    request: Request,
    expediente_id: int,
    documento_id: int,
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        documento = get_owned_expediente_documento(cur, documento_id, current_user["id"])
        require_row(documento, "Documento no encontrado")
        if documento["expediente_id"] != expediente_id:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        borrar_upload_relativo_si_existe(documento["archivo_ruta"])
        cur.execute("DELETE FROM expediente_documentos WHERE id = ?", (documento_id,))
        conn.commit()
    finally:
        conn.close()

    return redirect_pericial_workbench(
        expediente_id,
        mensaje="Documento eliminado del Anexo A.",
    )


@app.post("/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf")
def subir_pdf_mediciones_anexo_f_informe_v2(
    request: Request,
    expediente_id: int,
    archivo: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    archivo_ruta = ""
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El PDF de mediciones de Anexo F solo aplica a expedientes de patologías.",
            )
        try:
            archivo_ruta, nombre_original, mime_type = guardar_documento_pdf_expediente(
                archivo,
                expediente_id,
            )
        except ValueError as exc:
            return redirect_informe_v2_editor(expediente_id, error=str(exc))
        eliminar_pdfs_mediciones_anexo_f_informe_v2(cur, expediente_id)
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "PDF de mediciones para Anexo F",
                "Desarrollo completo de mediciones incorporado al informe.",
                TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES,
                archivo_ruta,
                nombre_original,
                mime_type,
                900,
            ),
        )
        conn.commit()
    except Exception:
        if archivo_ruta:
            borrar_upload_relativo_si_existe(archivo_ruta)
        raise
    finally:
        conn.close()

    return redirect_informe_v2_editor(
        expediente_id,
        mensaje="PDF de mediciones incorporado al Anexo F.",
    )


@app.post("/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf/eliminar")
def eliminar_pdf_mediciones_anexo_f_informe_v2(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El PDF de mediciones de Anexo F solo aplica a expedientes de patologías.",
            )
        eliminados = eliminar_pdfs_mediciones_anexo_f_informe_v2(cur, expediente_id)
        conn.commit()
    finally:
        conn.close()

    mensaje = (
        "PDF de mediciones eliminado del Anexo F."
        if eliminados
        else "No había PDF de mediciones asociado al Anexo F."
    )
    return redirect_informe_v2_editor(expediente_id, mensaje=mensaje)


@app.get("/expedientes/{expediente_id}/informe-v2-editor", response_class=HTMLResponse)
def informe_v2_editor(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El editor de informe solo aplica a expedientes de patologías.",
            )
        editor = preparar_editor_informe_v2(cur, expediente)
    finally:
        conn.close()

    return render_template(
        request,
        "informe_v2_editor.html",
        {
            "editor": editor,
            "expediente": editor["expediente"],
            "capitulos": editor["capitulos"],
            "contexto_editor": editor["contexto_editor"],
            "anexos_derivados": editor["anexos_derivados"],
            "pdf_mediciones_anexo_f": editor["pdf_mediciones_anexo_f"],
            "diagnostico_informe": editor["diagnostico_informe"],
            "revision_coherencia": editor["revision_coherencia"],
            "pdf_export_profiles": editor["pdf_export_profiles"],
            "diagnostico_anexos_pdf": editor["diagnostico_anexos_pdf"],
            "estados_revision": editor["estados_revision"],
            "metadatos": editor["metadatos"],
            "estados_revision_opciones": INFORME_V2_ESTADOS_REVISION,
            "metricas": editor["metricas"],
            "limitaciones_candidatas": editor["limitaciones_candidatas"],
            "recomendaciones_candidatas": editor["recomendaciones_candidatas"],
            "actuaciones": editor["actuaciones"],
            "formatear_numero_es": formatear_numero_es,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.get("/expedientes/{expediente_id}/revision-coherencia")
def revision_coherencia_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
    finally:
        conn.close()

    return JSONResponse(content=analizar_consistencia_expediente(expediente_id))


@app.post("/expedientes/{expediente_id}/informe-v2-editor")
async def guardar_informe_v2_editor(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    form_data = await request.form()

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El editor de informe solo aplica a expedientes de patologías.",
            )
        conflictos = detectar_conflictos_guardado_manual_informe_v2(
            cur,
            expediente_id,
            form_data,
        )
        if conflictos:
            capitulos = ", ".join(conflictos[:4])
            if len(conflictos) > 4:
                capitulos += f" y {len(conflictos) - 4} más"
            return RedirectResponse(
                url=(
                    f"/expedientes/{expediente_id}/informe-v2-editor?"
                    f"error={quote_plus('Hay cambios más recientes guardados automáticamente en: ' + capitulos + '. Recarga la página antes de guardar manualmente.')}"
                ),
                status_code=303,
            )
        guardar_presentacion_informe_v2(cur, expediente_id, form_data)
        guardar_capitulos_informe_v2(cur, expediente_id, form_data)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/expedientes/{expediente_id}/informe-v2-editor?mensaje=Informe%20guardado.",
        status_code=303,
    )


@app.post("/informes-v2/{expediente_id}/autosave")
async def autosave_informe_v2(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    form_data = await request.form()
    campo = limpiar_texto(form_data.get("campo"))
    valor = limpiar_texto(form_data.get("valor"))
    updated_at_cliente = limpiar_texto(form_data.get("updated_at"))

    if campo not in INFORME_V2_CAPITULOS_POR_CLAVE and campo not in INFORME_V2_CAMPOS_METADATOS:
        return JSONResponse(
            {"ok": False, "error": "Campo no permitido para el informe."},
            status_code=400,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return JSONResponse(
                {
                    "ok": False,
                    "error": "El autosalvado del informe solo aplica a expedientes de patologías.",
                },
                status_code=400,
            )

        if campo in INFORME_V2_CAMPOS_METADATOS:
            metadatos = guardar_campo_metadatos_informe_v2(
                cur,
                expediente_id,
                campo,
                valor,
            )
            conn.commit()
            return JSONResponse(
                {
                    "ok": True,
                    "campo": campo,
                    "updated_at": metadatos["updated_at"],
                    "tipo": "metadatos",
                }
            )

        fila_actual = cur.execute(
            """
            SELECT contenido, updated_at
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = ?
            """,
            (expediente_id, campo),
        ).fetchone()
        if fila_actual:
            updated_at_actual = limpiar_texto(fila_actual["updated_at"])
            contenido_actual = limpiar_texto(fila_actual["contenido"])
            if updated_at_actual != updated_at_cliente:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "Hay una versión más reciente de este capítulo. Recarga antes de autosalvar.",
                        "code": "conflict",
                        "campo": campo,
                        "updated_at": updated_at_actual,
                    },
                    status_code=409,
                )
            if not valor and contenido_actual:
                return JSONResponse(
                    {
                        "ok": False,
                        "error": "El autosalvado no vacía capítulos con contenido existente. Usa Guardar datos si quieres dejarlo vacío.",
                        "code": "empty_autosave",
                        "campo": campo,
                        "updated_at": updated_at_actual,
                    },
                    status_code=422,
                )

        guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            campo,
            valor,
            origen_version="autosave",
        )
        conn.commit()
        fila = cur.execute(
            """
            SELECT updated_at
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = ?
            """,
            (expediente_id, campo),
        ).fetchone()
    finally:
        conn.close()

    return JSONResponse(
        {
            "ok": True,
            "campo": campo,
            "updated_at": limpiar_texto(fila["updated_at"]) if fila else "",
        }
    )


@app.post("/informes-v2/{expediente_id}/capitulos/{clave}/estado")
async def guardar_estado_revision_informe_v2(
    request: Request,
    expediente_id: int,
    clave: str,
):
    current_user = get_current_user(request)
    clave_limpia = limpiar_texto(clave)
    definicion = INFORME_V2_CAPITULOS_POR_CLAVE.get(clave_limpia)
    if not definicion:
        return JSONResponse(
            {"ok": False, "error": "Campo no permitido para el informe."},
            status_code=400,
        )

    form_data = await request.form()
    estado = limpiar_texto(form_data.get("estado_revision"))
    if estado not in INFORME_V2_ESTADOS_REVISION:
        return JSONResponse(
            {"ok": False, "error": "Estado de revisión no permitido."},
            status_code=400,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return JSONResponse(
                {
                    "ok": False,
                    "error": "El estado del informe solo aplica a expedientes de patologías.",
                },
                status_code=400,
            )
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, estado_revision
            )
            VALUES (?, ?, ?, ?, NULL, ?, 0, ?)
            ON CONFLICT(expediente_id, clave) DO UPDATE SET
                estado_revision = excluded.estado_revision
            """,
            (
                expediente_id,
                definicion["clave"],
                definicion["titulo"],
                definicion["orden"],
                "pericial-wb-2",
                estado,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return JSONResponse(
        {
            "ok": True,
            "campo": definicion["clave"],
            "estado_revision": estado,
        }
    )


@app.post("/informes-v2/{expediente_id}/capitulos/{clave}/restaurar/{version_id}")
def restaurar_version_informe_v2(
    request: Request,
    expediente_id: int,
    clave: str,
    version_id: int,
):
    current_user = get_current_user(request)
    clave_limpia = limpiar_texto(clave)
    if clave_limpia not in INFORME_V2_CAPITULOS_POR_CLAVE:
        return redirect_detalle_expediente(
            expediente_id,
            error="Campo no permitido para el informe.",
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El editor de informe solo aplica a expedientes de patologías.",
            )
        version = cur.execute(
            """
            SELECT *
            FROM informe_v2_capitulo_versiones
            WHERE id = ? AND expediente_id = ? AND clave = ?
            """,
            (version_id, expediente_id, clave_limpia),
        ).fetchone()
        if not version:
            return RedirectResponse(
                url=(
                    f"/expedientes/{expediente_id}/informe-v2-editor?"
                    f"error={quote_plus('Versión de historial no encontrada.')}"
                ),
                status_code=303,
            )

        guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            clave_limpia,
            limpiar_texto(version["contenido"]),
            origen_version="restauracion",
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=(
            f"/expedientes/{expediente_id}/informe-v2-editor?"
            f"mensaje={quote_plus('Versión restaurada en el capítulo seleccionado.')}"
        ),
        status_code=303,
    )


@app.get("/informes-v2/{expediente_id}/respaldo.json")
def descargar_respaldo_informe_v2(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            raise HTTPException(
                status_code=400,
                detail="El respaldo del informe solo aplica a expedientes de patologías.",
            )
        guardados = obtener_capitulos_guardados_informe_v2(cur, expediente_id)
        metadatos = obtener_metadatos_informe_v2(cur, expediente_id)
    finally:
        conn.close()

    capitulos = []
    for definicion in INFORME_V2_CAPITULOS:
        guardado = guardados.get(definicion["clave"])
        capitulos.append(
            {
                "clave": definicion["clave"],
                "titulo": definicion["titulo"],
                "orden": definicion["orden"],
                "contenido": limpiar_texto(guardado.get("contenido")) if guardado else "",
                "updated_at": limpiar_texto(guardado.get("updated_at")) if guardado else "",
                "guardado": bool(guardado),
            }
        )

    payload = {
        "expediente": {
            "id": expediente["id"],
            "numero_expediente": limpiar_texto(expediente["numero_expediente"]),
            "direccion": limpiar_texto(expediente["direccion"]),
            "cliente": limpiar_texto(expediente["cliente"]),
            "tipo_informe": limpiar_texto(expediente["tipo_informe"]),
        },
        "fecha_exportacion": datetime.now().isoformat(timespec="seconds"),
        "metadatos": {
            "titulo_portada": metadatos["titulo_portada"],
            "subtitulo_portada": metadatos["subtitulo_portada"],
            "updated_at": metadatos["updated_at"],
        },
        "capitulos": capitulos,
    }
    numero = limpiar_nombre_archivo(expediente["numero_expediente"] or str(expediente_id))
    return JSONResponse(
        payload,
        headers={
            "Content-Disposition": f'attachment; filename="informe-respaldo-{numero}.json"'
        },
    )


@app.get("/expedientes/{expediente_id}/valoracion", response_class=HTMLResponse)
def editar_valoracion_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los datos de valoración solo aplican a expedientes de valoración.",
            )
        valoracion = cargar_valoracion_expediente_form(cur, expediente_id)
        legacy_valoracion = cargar_valoracion_legacy_expediente_form(cur, expediente_id)
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_expediente.html",
        {
            "expediente": dict(expediente),
            "valoracion": valoracion,
            "legacy_valoracion": legacy_valoracion,
            "valoracion_grupos": VALORACION_EXPEDIENTE_FORM_GROUPS,
            "valoracion_ayudas_rapidas": VALORACION_AYUDAS_RAPIDAS,
            "campos_checkbox": VALORACION_EXPEDIENTE_CHECKBOX_FIELDS,
        },
    )


@app.post("/expedientes/{expediente_id}/valoracion")
async def guardar_valoracion_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    form = await request.form()

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los datos de valoración solo aplican a expedientes de valoración.",
            )

        valores = {
            campo: ("1" if form.get(campo) == "1" else "")
            if campo in VALORACION_EXPEDIENTE_CHECKBOX_FIELDS
            else form.get(campo, "")
            for campo in VALORACION_EXPEDIENTE_FORM_FIELDS
        }
        upsert_valoracion_expediente(cur, expediente_id, valores)
        conn.commit()
    finally:
        conn.close()

    return redirect_detalle_expediente(
        expediente_id,
        mensaje="Datos estables de valoración guardados.",
    )


@app.get("/valoracion/testigos", response_class=HTMLResponse)
def listar_testigos_valoracion(
    request: Request,
    q: str = Query(""),
    tipologia: str = Query(""),
    municipio: str = Query(""),
    validacion: str = Query(""),
    reutilizable: str = Query(""),
):
    current_user = get_current_user(request)
    filtros = {
        "q": limpiar_texto(q),
        "tipologia": limpiar_texto(tipologia),
        "municipio": limpiar_texto(municipio),
        "validacion": limpiar_texto(validacion),
        "reutilizable": limpiar_texto(reutilizable),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        condiciones = ["owner_user_id = ?"]
        parametros = [current_user["id"]]
        if filtros["q"]:
            patron = f"%{filtros['q']}%"
            condiciones.append(
                """
                (
                    direccion_testigo LIKE ?
                    OR referencia_testigo LIKE ?
                    OR fuente_testigo LIKE ?
                    OR municipio LIKE ?
                    OR codigo_postal LIKE ?
                    OR provincia LIKE ?
                    OR tipologia LIKE ?
                    OR validacion_estado LIKE ?
                )
                """
            )
            parametros.extend([patron] * 8)
        if filtros["tipologia"]:
            condiciones.append("tipologia = ?")
            parametros.append(filtros["tipologia"])
        if filtros["municipio"]:
            condiciones.append("municipio = ?")
            parametros.append(filtros["municipio"])
        if filtros["validacion"]:
            condiciones.append("validacion_estado = ?")
            parametros.append(filtros["validacion"])
        if filtros["reutilizable"] in {"0", "1"}:
            condiciones.append("COALESCE(reutilizable, 1) = ?")
            parametros.append(int(filtros["reutilizable"]))

        testigos = cur.execute(
            f"""
            SELECT *
            FROM testigos_valoracion
            WHERE {" AND ".join(condiciones)}
            ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
            """,
            parametros,
        ).fetchall()
        opciones_filtros = cargar_opciones_filtro_testigos_valoracion(
            cur,
            current_user["id"],
        )
        testigos_enriquecidos = enriquecer_testigos_con_foto(cur, testigos)
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_testigos.html",
        {
            "testigos": testigos_enriquecidos,
            "busqueda": filtros["q"],
            "filtros": filtros,
            "opciones_filtros": opciones_filtros,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.get("/valoracion/testigos/biblioteca", response_class=HTMLResponse)
def biblioteca_testigos_valoracion(
    request: Request,
    municipio: str = Query(""),
    tipologia: str = Query(""),
    fuente: str = Query(""),
    fiabilidad: str = Query(""),
    verificacion: str = Query(""),
    incompletos: str = Query(""),
    ordenar: str = Query("fecha"),
    dir: str = Query("desc"),
    expediente_id: str = Query(""),
):
    current_user = get_current_user(request)
    filtros = {
        "municipio": limpiar_texto(municipio),
        "tipologia": limpiar_texto(tipologia),
        "fuente": limpiar_texto(fuente),
        "fiabilidad": limpiar_texto(fiabilidad),
        "verificacion": limpiar_texto(verificacion),
        "incompletos": limpiar_texto(incompletos),
        "expediente_id": limpiar_texto(expediente_id),
    }
    ordenes_validas = {"fecha", "unitario", "precio", "superficie", "fiabilidad"}
    ordenar_warning = ""
    ordenar = limpiar_texto(ordenar) or "fecha"
    if ordenar not in ordenes_validas:
        ordenar = "fecha"
        ordenar_warning = "La ordenación solicitada no existe; se usa fecha."
    direccion = limpiar_texto(dir).lower()
    if direccion not in {"asc", "desc"}:
        direccion = "desc"

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente_contexto = None
        ids_vinculados = set()
        expediente_contexto_id = parse_optional_int(filtros["expediente_id"])
        if expediente_contexto_id:
            expediente_row = get_owned_expediente(
                cur,
                expediente_contexto_id,
                current_user["id"],
            )
            if (
                expediente_row is not None
                and limpiar_texto(expediente_row["tipo_informe"]) == "valoracion"
            ):
                expediente_contexto = dict(expediente_row)
                ids_vinculados = {
                    row["testigo_id"]
                    for row in cur.execute(
                        """
                        SELECT testigo_id
                        FROM valoracion_expediente_testigos
                        WHERE expediente_id = ?
                          AND testigo_id IS NOT NULL
                        """,
                        (expediente_contexto_id,),
                    ).fetchall()
                }
        condiciones = ["owner_user_id = ?"]
        parametros = [current_user["id"]]
        if filtros["municipio"]:
            condiciones.append("municipio = ?")
            parametros.append(filtros["municipio"])
        if filtros["tipologia"]:
            condiciones.append("tipologia = ?")
            parametros.append(filtros["tipologia"])
        if filtros["fuente"]:
            condiciones.append("fuente_testigo = ?")
            parametros.append(filtros["fuente"])
        if filtros["fiabilidad"]:
            condiciones.append("fiabilidad_dato = ?")
            parametros.append(filtros["fiabilidad"])
        if filtros["verificacion"] in {"0", "1"}:
            condiciones.append("COALESCE(dato_verificado, 0) = ?")
            parametros.append(int(filtros["verificacion"]))
        rows = cur.execute(
            f"""
            SELECT *
            FROM testigos_valoracion
            WHERE {" AND ".join(condiciones)}
            """,
            parametros,
        ).fetchall()
        opciones_filtros = cargar_opciones_filtro_testigos_valoracion(
            cur,
            current_user["id"],
        )
    finally:
        conn.close()

    testigos = [enriquecer_testigo_valoracion(dict(row)) for row in rows]
    if filtros["incompletos"] in {"1", "si", "true"}:
        testigos = [item for item in testigos if testigo_biblioteca_incompleto(item)]
    testigos = ordenar_biblioteca_testigos(testigos, ordenar, direccion)
    diagnostico = diagnostico_biblioteca_testigos(testigos)
    return render_template(
        request,
        "valoracion_testigos_biblioteca.html",
        {
            "testigos": testigos,
            "diagnostico": diagnostico,
            "filtros": filtros,
            "opciones_filtros": opciones_filtros,
            "ordenar": ordenar,
            "dir": direccion,
            "ordenar_warning": ordenar_warning,
            "expediente_contexto": expediente_contexto,
            "ids_vinculados": ids_vinculados,
            "sort_links": [
                {
                    "key": key,
                    "label": label,
                    "url": biblioteca_testigos_url(
                        filtros,
                        key,
                        "asc" if ordenar == key and direccion == "desc" else "desc",
                    ),
                }
                for key, label in [
                    ("fecha", "Fecha"),
                    ("unitario", "€/m²"),
                    ("precio", "Precio"),
                    ("superficie", "Superficie"),
                    ("fiabilidad", "Fiabilidad"),
                ]
            ],
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.get("/valoracion/testigos/biblioteca/nuevo", response_class=HTMLResponse)
def nuevo_testigo_biblioteca_valoracion(
    request: Request,
    expediente_id: str = Query(""),
):
    get_current_user(request)
    valores = testigo_biblioteca_form_vacio(expediente_id)
    return render_template(
        request,
        "valoracion_testigo_biblioteca_form.html",
        {
            "testigo": valores,
            "fuente_presets": TESTIGO_BIBLIOTECA_FUENTE_PRESETS,
            "unitario_visual": calcular_unitario_visual_testigo_biblioteca(valores),
            "analisis_anuncio": analisis_anuncio_vacio(),
            "duplicados_posibles": [],
            "errores": [],
            "avisos": [],
        },
    )


@app.post("/valoracion/testigos/biblioteca/nuevo", response_class=HTMLResponse)
async def crear_testigo_biblioteca_valoracion(request: Request):
    current_user = get_current_user(request)
    form = await request.form()
    valores, errores, avisos = valores_testigo_biblioteca_desde_form(form)
    accion = limpiar_texto(form.get("accion")) or "guardar"
    expediente_id = limpiar_texto(valores.get("expediente_id"))

    if accion == "analizar_texto":
        analisis = analizar_texto_anuncio_inmobiliario(
            valores.get("texto_anuncio_bruto")
        )
        valores = aplicar_analisis_a_testigo_biblioteca(valores, analisis)
        if not limpiar_texto(form.get("fuente_testigo")) and analisis.get("campos", {}).get("fuente_testigo"):
            valores["fuente_tipo"] = analisis["campos"]["fuente_tipo"]
            valores["fuente_testigo"] = analisis["campos"]["fuente_testigo"]
        return render_template(
            request,
            "valoracion_testigo_biblioteca_form.html",
            {
                "testigo": valores,
                "fuente_presets": TESTIGO_BIBLIOTECA_FUENTE_PRESETS,
                "unitario_visual": calcular_unitario_visual_testigo_biblioteca(valores),
                "analisis_anuncio": analisis,
                "duplicados_posibles": [],
                "errores": [],
                "avisos": avisos,
            },
        )

    if errores:
        return render_template(
            request,
            "valoracion_testigo_biblioteca_form.html",
            {
                "testigo": valores,
                "fuente_presets": TESTIGO_BIBLIOTECA_FUENTE_PRESETS,
                "unitario_visual": calcular_unitario_visual_testigo_biblioteca(valores),
                "analisis_anuncio": analisis_anuncio_vacio(),
                "duplicados_posibles": [],
                "errores": errores,
                "avisos": avisos,
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        duplicados_posibles = buscar_duplicados_testigo_biblioteca(
            cur,
            current_user["id"],
            valores,
        )
        if duplicados_posibles and accion != "guardar_confirmado":
            return render_template(
                request,
                "valoracion_testigo_biblioteca_form.html",
                {
                    "testigo": valores,
                    "fuente_presets": TESTIGO_BIBLIOTECA_FUENTE_PRESETS,
                    "unitario_visual": calcular_unitario_visual_testigo_biblioteca(valores),
                    "analisis_anuncio": analisis_anuncio_vacio(),
                    "duplicados_posibles": duplicados_posibles,
                    "errores": [],
                    "avisos": avisos,
                },
            )
        testigo_id = insertar_testigo_biblioteca_rapido(
            cur,
            current_user["id"],
            valores,
        )
        conn.commit()
    finally:
        conn.close()

    if accion == "crear_otro":
        url = "/valoracion/testigos/biblioteca/nuevo?mensaje=Testigo%20guardado."
        if expediente_id:
            url += f"&expediente_id={quote_plus(expediente_id)}"
    elif accion == "volver_biblioteca":
        url = "/valoracion/testigos/biblioteca?mensaje=Testigo%20guardado."
        if expediente_id:
            url += f"&expediente_id={quote_plus(expediente_id)}"
    else:
        url = f"/valoracion/testigos/{testigo_id}?mensaje=Testigo%20guardado."
    return RedirectResponse(url=url, status_code=303)


@app.get("/valoracion/testigos/nuevo", response_class=HTMLResponse)
def nuevo_testigo_valoracion(request: Request):
    get_current_user(request)
    return render_template(
        request,
        "valoracion_testigo_form.html",
        {
            "testigo": testigo_valoracion_form_vacio(),
            "testigo_id": None,
            "modo": "nuevo",
            "testigo_grupos": TESTIGO_VALORACION_FORM_GROUPS,
            "campos_checkbox": TESTIGO_VALORACION_CHECKBOX_FIELDS,
            "campos_numericos": TESTIGO_VALORACION_NUMERIC_FIELDS,
            "campos_enteros": TESTIGO_VALORACION_INTEGER_FIELDS,
            "validacion_options": TESTIGO_VALORACION_VALIDACION_OPTIONS,
        },
    )


@app.post("/valoracion/testigos/nuevo")
async def crear_testigo_valoracion(request: Request):
    current_user = get_current_user(request)
    form = await request.form()
    valores = valores_testigo_desde_form(form)

    columnas_disponibles = get_table_columns("testigos_valoracion")
    columnas = [
        campo
        for campo in TESTIGO_VALORACION_FORM_FIELDS
        if campo in columnas_disponibles
    ]
    insert_columns = ["owner_user_id"] + columnas
    placeholders = ", ".join(["?"] * len(insert_columns))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            INSERT INTO testigos_valoracion ({", ".join(insert_columns)})
            VALUES ({placeholders})
            """,
            [current_user["id"]] + [valores[campo] for campo in columnas],
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url="/valoracion/testigos?mensaje=Testigo%20creado.",
        status_code=303,
    )


@app.get("/valoracion/testigos/{testigo_id}/editar", response_class=HTMLResponse)
def editar_testigo_valoracion(request: Request, testigo_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        _, testigo_form = cargar_testigo_valoracion_form(
            cur,
            testigo_id,
            current_user["id"],
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_testigo_form.html",
        {
            "testigo": testigo_form,
            "testigo_id": testigo_id,
            "modo": "editar",
            "testigo_grupos": TESTIGO_VALORACION_FORM_GROUPS,
            "campos_checkbox": TESTIGO_VALORACION_CHECKBOX_FIELDS,
            "campos_numericos": TESTIGO_VALORACION_NUMERIC_FIELDS,
            "campos_enteros": TESTIGO_VALORACION_INTEGER_FIELDS,
            "validacion_options": TESTIGO_VALORACION_VALIDACION_OPTIONS,
        },
    )


@app.post("/valoracion/testigos/{testigo_id}/editar")
async def actualizar_testigo_valoracion(request: Request, testigo_id: int):
    current_user = get_current_user(request)
    form = await request.form()
    valores = valores_testigo_desde_form(form)

    conn = get_connection()
    cur = conn.cursor()
    try:
        testigo = get_owned_testigo_valoracion(cur, testigo_id, current_user["id"])
        require_row(testigo, "Testigo no encontrado")

        columnas_disponibles = get_table_columns("testigos_valoracion")
        columnas = [
            campo
            for campo in TESTIGO_VALORACION_FORM_FIELDS
            if campo in columnas_disponibles
        ]
        assignments = ", ".join([f"{campo}=?" for campo in columnas])
        cur.execute(
            f"""
            UPDATE testigos_valoracion
            SET {assignments}, updated_at=CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            [valores[campo] for campo in columnas]
            + [testigo_id, current_user["id"]],
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url="/valoracion/testigos?mensaje=Testigo%20actualizado.",
        status_code=303,
    )


@app.get("/valoracion/testigos/{testigo_id}", response_class=HTMLResponse)
def detalle_testigo_valoracion(request: Request, testigo_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        testigo = get_owned_testigo_valoracion(cur, testigo_id, current_user["id"])
        require_row(testigo, "Testigo no encontrado")
        fotos = cargar_fotos_testigo_valoracion(cur, testigo_id)
        vinculos = cargar_vinculos_testigo_valoracion(
            cur,
            testigo_id,
            current_user["id"],
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_testigo_detalle.html",
        {
            "testigo": enriquecer_testigo_valoracion(dict(testigo)),
            "fotos": fotos,
            "vinculos": [
                {
                    **dict(vinculo),
                    "valor_unitario_base_fmt": formatear_precio_unitario_es(
                        vinculo["valor_unitario_base"]
                    ),
                    "valor_unitario_ajustado_fmt": formatear_precio_unitario_es(
                        vinculo["valor_unitario_ajustado"]
                    ),
                    "incluido_fmt": formatear_booleano_es(vinculo["incluido"]),
                }
                for vinculo in vinculos
            ],
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.post("/valoracion/testigos/{testigo_id}/fotos")
def guardar_fotos_testigo_valoracion(
    request: Request,
    testigo_id: int,
    descripcion: str = Form(""),
    origen: str = Form("manual"),
    fotos: list[UploadFile] = File([]),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        testigo = get_owned_testigo_valoracion(cur, testigo_id, current_user["id"])
        require_row(testigo, "Testigo no encontrado")
        descripcion_limpia = limpiar_texto(descripcion)
        origen_limpio = limpiar_texto(origen) or "manual"
        errores = validar_fotos_testigo_valoracion(fotos)
        if errores:
            return RedirectResponse(
                url=(
                    f"/valoracion/testigos/{testigo_id}?error="
                    f"{quote_plus(' '.join(errores))}"
                ),
                status_code=303,
            )
        nombres_fotos = guardar_uploads_contextuales(
            fotos,
            "testigo_valoracion",
            str(testigo_id),
        )
        for nombre in nombres_fotos:
            cur.execute(
                """
                INSERT INTO testigos_valoracion_fotos (
                    testigo_id, archivo, descripcion, origen
                )
                VALUES (?, ?, ?, ?)
                """,
                (testigo_id, nombre, descripcion_limpia, origen_limpio),
            )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/valoracion/testigos/{testigo_id}?mensaje=Fotos%20guardadas.",
        status_code=303,
    )


@app.get("/expedientes/{expediente_id}/valoracion/testigos", response_class=HTMLResponse)
def seleccionar_testigos_valoracion_expediente(
    request: Request,
    expediente_id: int,
    q: str = Query(""),
    tipologia: str = Query(""),
    municipio: str = Query(""),
    validacion: str = Query(""),
):
    current_user = get_current_user(request)
    filtros = {
        "q": limpiar_texto(q),
        "tipologia": limpiar_texto(tipologia),
        "municipio": limpiar_texto(municipio),
        "validacion": limpiar_texto(validacion),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los testigos solo aplican a expedientes de valoración.",
            )
        vinculados = cargar_testigos_expediente_valoracion(cur, expediente_id)
        comparacion_vinculos = preparar_resumen_comparacion_vinculos(cur, vinculados)
        ids_vinculados = {
            row["testigo_id"]
            for row in vinculados
            if row["testigo_id"] is not None
        }
        disponibles_base = []
        for testigo in cargar_testigos_valoracion_usuario(
            cur,
            current_user["id"],
            solo_reutilizables=True,
        ):
            if testigo["id"] in ids_vinculados:
                continue
            item = dict(testigo)
            texto_busqueda = " ".join(
                limpiar_texto(item.get(campo))
                for campo in (
                    "direccion_testigo",
                    "referencia_testigo",
                    "fuente_testigo",
                    "municipio",
                    "codigo_postal",
                    "provincia",
                    "tipologia",
                    "validacion_estado",
                )
            ).lower()
            if filtros["q"] and filtros["q"].lower() not in texto_busqueda:
                continue
            if filtros["tipologia"] and item.get("tipologia") != filtros["tipologia"]:
                continue
            if filtros["municipio"] and item.get("municipio") != filtros["municipio"]:
                continue
            if (
                filtros["validacion"]
                and item.get("validacion_estado") != filtros["validacion"]
            ):
                continue
            disponibles_base.append(item)
        opciones_filtros = cargar_opciones_filtro_testigos_valoracion(
            cur,
            current_user["id"],
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_expediente_testigos.html",
        {
            "expediente": dict(expediente),
            "testigos_vinculados": [
                enriquecer_vinculo_testigo_valoracion(dict(row))
                for row in comparacion_vinculos["items"]
            ],
            "resumen_comparacion": comparacion_vinculos["resumen"],
            "testigos_disponibles": disponibles_base,
            "filtros": filtros,
            "opciones_filtros": opciones_filtros,
            "representatividad_options": REPRESENTATIVIDAD_VALORACION_OPTIONS,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.get("/expediente/{expediente_id}/valoracion/workbench", response_class=HTMLResponse)
def workbench_valoracion_expediente(
    request: Request,
    expediente_id: int,
    testigo_id: str = Query(""),
    filtro: str = Query("todos"),
    ordenar: str = Query("homogeneizado"),
    dir: str = Query("desc"),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="El workbench solo aplica a expedientes de valoración.",
            )
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id)
    comparables = contexto.get("comparables_valoracion") or []
    conn = get_connection()
    cur = conn.cursor()
    try:
        fotos_por_testigo = cargar_fotos_workbench_testigos(
            cur,
            [comparable.get("testigo_id") for comparable in comparables],
            current_user["id"],
        )
    finally:
        conn.close()
    enriquecer_comparables_workbench_con_fotos(comparables, fotos_por_testigo)
    filtro = limpiar_texto(filtro) or "todos"
    filtro_warning = ""
    if filtro not in WORKBENCH_FILTROS:
        filtro = "todos"
        filtro_warning = "El filtro solicitado no existe; se muestran todos los testigos."
    ordenar = limpiar_texto(ordenar) or "homogeneizado"
    ordenar_warning = ""
    if ordenar not in WORKBENCH_ORDENES:
        ordenar = "homogeneizado"
        ordenar_warning = (
            "La ordenación solicitada no existe; se usa €/m² homogeneizado."
        )
    direccion = limpiar_texto(dir).lower()
    if direccion not in {"asc", "desc"}:
        direccion = "desc"
    comparables_filtrados = workbench_ordenar_comparables(
        workbench_filtrar_comparables(comparables, filtro),
        ordenar,
        direccion,
    )
    diagnostico = workbench_diagnostico(comparables)
    testigo_id = limpiar_texto(testigo_id)
    panel_testigo = comparables_filtrados[0] if comparables_filtrados else {}
    panel_warning = ""
    if testigo_id and comparables_filtrados:
        panel_testigo = next(
            (
                comparable
                for comparable in comparables_filtrados
                if testigo_id == workbench_comparable_id(comparable)
            ),
            None,
        )
        if panel_testigo is None:
            existe_en_contexto = any(
                testigo_id == workbench_comparable_id(comparable)
                for comparable in comparables
            )
            panel_testigo = comparables_filtrados[0]
            panel_warning = (
                "El testigo seleccionado queda fuera del filtro actual; "
                "se muestra el primer testigo filtrado."
                if existe_en_contexto
                else "El testigo solicitado no pertenece al contexto de este expediente; "
                "se muestra el primer testigo disponible."
            )
    elif testigo_id and not comparables_filtrados:
        panel_warning = (
            "El filtro actual no deja testigos visibles; ajusta el filtro para recuperar "
            "la selección."
        )
    view_state = {
        "filtro": filtro,
        "ordenar": ordenar,
        "dir": direccion,
        "testigo_id": testigo_id,
        "filtro_warning": filtro_warning,
        "ordenar_warning": ordenar_warning,
        "filter_links": [
            {
                "key": key,
                "label": label,
                "url": workbench_url(expediente_id, key, ordenar, direccion, testigo_id),
            }
            for key, label in [
                ("todos", "Todos"),
                ("incluidos", "Incluidos"),
                ("excluidos", "Excluidos"),
                ("advertencias", "Advertencias"),
                ("incompletos", "Incompletos"),
            ]
        ],
        "sort_links": [
            {
                "key": key,
                "label": label,
                "url": workbench_url(
                    expediente_id,
                    filtro,
                    key,
                    "asc" if ordenar == key and direccion == "desc" else "desc",
                    testigo_id,
                ),
            }
            for key, label in [
                ("homogeneizado", "€/m² homog."),
                ("peso", "Peso"),
                ("similitud", "Similitud"),
                ("fiabilidad", "Fiabilidad"),
                ("fecha", "Fecha"),
            ]
        ],
    }
    return render_template(
        request,
        "valoracion_workbench.html",
        {
            "expediente": dict(expediente),
            "contexto": contexto,
            "valoracion": contexto.get("valoracion"),
            "valoracion_eco": contexto.get("valoracion_eco") or {},
            "comparables": comparables_filtrados,
            "comparables_total": comparables,
            "resumen_comparacion": contexto.get("resumen_comparacion_valoracion") or {},
            "completitud": contexto.get("completitud_valoracion") or {},
            "diagnostico": diagnostico,
            "view_state": view_state,
            "panel_testigo": panel_testigo,
            "trazabilidad_homogeneizacion": workbench_trazabilidad_homogeneizacion(
                panel_testigo
            ),
            "panel_warning": panel_warning,
            "selected_testigo_id": testigo_id,
            "representatividad_options": REPRESENTATIVIDAD_VALORACION_OPTIONS,
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
            "error": limpiar_texto(request.query_params.get("error")),
        },
    )


@app.post("/expediente/{expediente_id}/valoracion/workbench/testigo/{testigo_id}")
async def guardar_microedicion_workbench_valoracion(
    request: Request,
    expediente_id: int,
    testigo_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()
    filtro = limpiar_texto(form.get("filtro")) or "todos"
    ordenar = limpiar_texto(form.get("ordenar")) or "homogeneizado"
    direccion = limpiar_texto(form.get("dir")) or "desc"
    redirect_url = workbench_url(
        expediente_id,
        filtro if filtro in WORKBENCH_FILTROS else "todos",
        ordenar if ordenar in WORKBENCH_ORDENES else "homogeneizado",
        direccion if direccion in {"asc", "desc"} else "desc",
        str(testigo_id),
    )

    try:
        valores = valores_microedicion_workbench_desde_form(form)
    except ValueError as exc:
        return RedirectResponse(
            url=workbench_url(
                expediente_id,
                filtro if filtro in WORKBENCH_FILTROS else "todos",
                ordenar if ordenar in WORKBENCH_ORDENES else "homogeneizado",
                direccion if direccion in {"asc", "desc"} else "desc",
                str(testigo_id),
                error=str(exc),
            ),
            status_code=303,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="El workbench solo aplica a expedientes de valoración.",
            )
        vinculo = cur.execute(
            """
            SELECT vet.*
            FROM valoracion_expediente_testigos vet
            JOIN expedientes e ON e.id = vet.expediente_id
            WHERE vet.expediente_id = ?
              AND vet.testigo_id = ?
              AND e.owner_user_id = ?
            """,
            (expediente_id, testigo_id, current_user["id"]),
        ).fetchone()
        require_row(vinculo, "Testigo no vinculado al expediente")
        actualizar_microedicion_workbench(cur, vinculo["id"], valores)
        conn.commit()
    finally:
        conn.close()

    mensaje = "Microedición de testigo guardada."
    if valores["incluido_calculo"] == 0 and not valores["motivo_exclusion"]:
        mensaje = "Microedición guardada. Recomendación: documenta el motivo de exclusión."
    return RedirectResponse(
        url=f"{redirect_url}&mensaje={quote_plus(mensaje)}",
        status_code=303,
    )


@app.get(
    "/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes",
    response_class=HTMLResponse,
)
def editar_ajustes_testigo_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = get_owned_valoracion_expediente_testigo_detalle(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        if limpiar_texto(vinculo["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los ajustes solo aplican a expedientes de valoración.",
            )
        ajustes = cargar_valoracion_testigo_ajustes(cur, vinculo_id)
        ajustes_homogeneizacion = cargar_ajustes_homogeneizacion(cur, vinculo_id)
        resumen_homogeneizacion = resumen_homogeneizacion_vinculo(
            dict(vinculo),
            ajustes_homogeneizacion,
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_testigo_ajustes.html",
        {
            "vinculo": dict(vinculo),
            "ajustes": ajustes,
            "ajustes_items": VALORACION_TESTIGO_AJUSTES_ITEMS,
            "ajustes_homogeneizacion": ajustes_homogeneizacion,
            "ajuste_homogeneizacion_form": ajuste_homogeneizacion_vacio(),
            "resumen_homogeneizacion": resumen_homogeneizacion,
            "variables_homogeneizacion": HOMOGENEIZACION_VARIABLE_OPTIONS,
            "tipos_homogeneizacion": HOMOGENEIZACION_TIPO_AJUSTE_OPTIONS,
            "signos_homogeneizacion": HOMOGENEIZACION_SIGNO_OPTIONS,
            "modo_homogeneizacion": "nuevo",
            "error": limpiar_texto(request.query_params.get("error")),
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
        },
    )


@app.post("/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes")
async def guardar_ajustes_testigo_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()

    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = get_owned_valoracion_expediente_testigo_detalle(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        if limpiar_texto(vinculo["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los ajustes solo aplican a expedientes de valoración.",
            )
        try:
            valores = valores_ajustes_desde_form(form)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        upsert_valoracion_testigo_ajustes(cur, vinculo, valores)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/expedientes/{expediente_id}/valoracion/testigos?mensaje=Ajustes%20guardados.",
        status_code=303,
    )


@app.post("/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion")
async def crear_ajuste_homogeneizacion_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()
    valores = valores_homogeneizacion_desde_form(form)

    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = get_owned_valoracion_expediente_testigo_detalle(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        if limpiar_texto(vinculo["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los ajustes solo aplican a expedientes de valoración.",
            )
        insertar_ajuste_homogeneizacion(cur, vinculo, valores)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=(
            f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes"
            "?mensaje=Ajuste%20de%20homogeneizaci%C3%B3n%20guardado."
        ),
        status_code=303,
    )


@app.get(
    "/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion/{ajuste_id}/editar",
    response_class=HTMLResponse,
)
def editar_ajuste_homogeneizacion_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
    ajuste_id: int,
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = get_owned_valoracion_expediente_testigo_detalle(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        ajuste = get_owned_ajuste_homogeneizacion(
            cur,
            ajuste_id,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(ajuste, "Ajuste no encontrado")
        ajustes = cargar_valoracion_testigo_ajustes(cur, vinculo_id)
        ajustes_homogeneizacion = cargar_ajustes_homogeneizacion(cur, vinculo_id)
        resumen_homogeneizacion = resumen_homogeneizacion_vinculo(
            dict(vinculo),
            ajustes_homogeneizacion,
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_testigo_ajustes.html",
        {
            "vinculo": dict(vinculo),
            "ajustes": ajustes,
            "ajustes_items": VALORACION_TESTIGO_AJUSTES_ITEMS,
            "ajustes_homogeneizacion": ajustes_homogeneizacion,
            "ajuste_homogeneizacion_form": row_ajuste_homogeneizacion(ajuste),
            "resumen_homogeneizacion": resumen_homogeneizacion,
            "variables_homogeneizacion": HOMOGENEIZACION_VARIABLE_OPTIONS,
            "tipos_homogeneizacion": HOMOGENEIZACION_TIPO_AJUSTE_OPTIONS,
            "signos_homogeneizacion": HOMOGENEIZACION_SIGNO_OPTIONS,
            "modo_homogeneizacion": "editar",
            "ajuste_homogeneizacion_id": ajuste_id,
            "error": limpiar_texto(request.query_params.get("error")),
            "mensaje": limpiar_texto(request.query_params.get("mensaje")),
        },
    )


@app.post(
    "/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion/{ajuste_id}/editar"
)
async def actualizar_ajuste_homogeneizacion_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
    ajuste_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()
    valores = valores_homogeneizacion_desde_form(form)

    conn = get_connection()
    cur = conn.cursor()
    try:
        ajuste = get_owned_ajuste_homogeneizacion(
            cur,
            ajuste_id,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(ajuste, "Ajuste no encontrado")
        actualizar_ajuste_homogeneizacion(cur, ajuste_id, valores)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=(
            f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes"
            "?mensaje=Ajuste%20actualizado."
        ),
        status_code=303,
    )


@app.post(
    "/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion/{ajuste_id}/desactivar"
)
def desactivar_ajuste_homogeneizacion_valoracion(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
    ajuste_id: int,
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        ajuste = get_owned_ajuste_homogeneizacion(
            cur,
            ajuste_id,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(ajuste, "Ajuste no encontrado")
        cur.execute(
            """
            UPDATE valoracion_testigo_ajustes
            SET activo = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ajuste_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=(
            f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes"
            "?mensaje=Ajuste%20desactivado."
        ),
        status_code=303,
    )


@app.post("/expedientes/{expediente_id}/valoracion/testigos/anadir")
async def anadir_testigo_valoracion_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)
    form = await request.form()
    testigo_id = parse_optional_int(form.get("testigo_id"))
    notas_seleccion = limpiar_texto(form.get("notas_seleccion"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los testigos solo aplican a expedientes de valoración.",
            )
        if not testigo_id:
            return redirect_detalle_expediente(
                expediente_id,
                error="Selecciona un testigo para vincular.",
            )
        testigo = get_owned_testigo_valoracion(cur, testigo_id, current_user["id"])
        require_row(testigo, "Testigo no encontrado")
        existente = cur.execute(
            """
            SELECT 1
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            LIMIT 1
            """,
            (expediente_id, testigo_id),
        ).fetchone()
        if existente:
            return RedirectResponse(
                url=(
                    f"/expedientes/{expediente_id}/valoracion/testigos"
                    "?error=El%20testigo%20ya%20est%C3%A1%20vinculado."
                ),
                status_code=303,
            )
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json,
                notas_seleccion, valor_unitario_base
            )
            VALUES (?, ?, ?, 1, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                siguiente_orden_testigo_expediente(cur, expediente_id),
                snapshot_testigo_valoracion(testigo),
                notas_seleccion,
                testigo["precio_unitario_inicial"] or testigo["valor_unitario"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/expedientes/{expediente_id}/valoracion/testigos?mensaje=Testigo%20vinculado.",
        status_code=303,
    )


@app.post("/expedientes/{expediente_id}/valoracion/testigos/biblioteca/{testigo_id}/vincular")
async def vincular_testigo_biblioteca_valoracion(
    request: Request,
    expediente_id: int,
    testigo_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()
    return_to = limpiar_texto(form.get("return_to"))
    destino_ok = (
        f"/expediente/{expediente_id}/valoracion/workbench?mensaje=Testigo%20vinculado."
        if return_to == "workbench"
        else f"/expedientes/{expediente_id}/valoracion/testigos?mensaje=Testigo%20vinculado."
    )
    destino_duplicado = (
        f"/expedientes/{expediente_id}/valoracion/testigos"
        "?error=El%20testigo%20ya%20est%C3%A1%20vinculado."
    )

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los testigos solo aplican a expedientes de valoración.",
            )
        testigo = get_owned_testigo_valoracion(cur, testigo_id, current_user["id"])
        require_row(testigo, "Testigo no encontrado")
        existente = cur.execute(
            """
            SELECT 1
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            LIMIT 1
            """,
            (expediente_id, testigo_id),
        ).fetchone()
        if existente:
            return RedirectResponse(url=destino_duplicado, status_code=303)
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, incluido_calculo,
                peso_porcentaje, representatividad, snapshot_json,
                notas_seleccion, valor_unitario_base
            )
            VALUES (?, ?, ?, 1, 1, NULL, '', ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                siguiente_orden_testigo_expediente(cur, expediente_id),
                snapshot_testigo_valoracion(testigo),
                "Vinculado desde biblioteca desktop.",
                testigo["precio_unitario_inicial"] or testigo["valor_unitario"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=destino_ok, status_code=303)


@app.post("/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/actualizar")
async def actualizar_testigo_valoracion_expediente(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
):
    current_user = get_current_user(request)
    form = await request.form()
    orden = parse_optional_int(form.get("orden"))
    incluido = 1 if form.get("incluido") == "1" else 0
    incluido_calculo = 1 if form.get("incluido_calculo") == "1" else 0
    peso_porcentaje = parsear_float(form.get("peso_porcentaje"))
    representatividad = limpiar_texto(form.get("representatividad"))
    notas_seleccion = limpiar_texto(form.get("notas_seleccion"))
    motivo_ponderacion = limpiar_texto(form.get("motivo_ponderacion"))
    motivo_exclusion = limpiar_texto(form.get("motivo_exclusion"))
    observaciones_ponderacion = limpiar_texto(form.get("observaciones_ponderacion"))

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los testigos solo aplican a expedientes de valoración.",
            )
        vinculo = get_owned_valoracion_expediente_testigo(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        cur.execute(
            """
            UPDATE valoracion_expediente_testigos
            SET orden = ?, incluido = ?, incluido_calculo = ?,
                peso_porcentaje = ?, representatividad = ?,
                notas_seleccion = ?, motivo_ponderacion = ?,
                motivo_exclusion = ?, observaciones_ponderacion = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                orden,
                incluido,
                incluido_calculo,
                peso_porcentaje,
                representatividad,
                notas_seleccion,
                motivo_ponderacion,
                motivo_exclusion,
                observaciones_ponderacion,
                vinculo_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/expedientes/{expediente_id}/valoracion/testigos?mensaje=V%C3%ADnculo%20actualizado.",
        status_code=303,
    )


@app.post("/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/quitar")
def quitar_testigo_valoracion_expediente(
    request: Request,
    expediente_id: int,
    vinculo_id: int,
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                expediente_id,
                error="Los testigos solo aplican a expedientes de valoración.",
            )
        vinculo = get_owned_valoracion_expediente_testigo(
            cur,
            vinculo_id,
            expediente_id,
            current_user["id"],
        )
        require_row(vinculo, "Vínculo no encontrado")
        cur.execute(
            "DELETE FROM valoracion_expediente_testigos WHERE id = ?",
            (vinculo_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/expedientes/{expediente_id}/valoracion/testigos?mensaje=Testigo%20quitado%20del%20expediente.",
        status_code=303,
    )


@app.get("/resumen-registro/{expediente_id}", response_class=HTMLResponse)
def resumen_registro(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    resumen_registro_data = preparar_resumen_registro_expediente(cur, expediente_id)
    revision_informe = preparar_pendientes_revision_expediente(cur, expediente_id)

    conn.close()

    expediente_data = dict(expediente)
    expediente_data["tipo_informe_label"] = etiquetar_opcion(
        expediente_data.get("tipo_informe", ""),
        TIPO_INFORME_LABELS,
    )
    expediente_data["es_informe_patologias"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "patologias"
    )
    expediente_data["es_informe_valoracion"] = (
        limpiar_texto(expediente_data.get("tipo_informe")) == "valoracion"
    )

    return render_template(
        request,
        "resumen_registro.html",
        {
            "expediente": expediente_data,
            "patologias_exteriores": resumen_registro_data["patologias_exteriores"],
            "visita_fotos_exteriores": resumen_registro_data["visita_fotos_exteriores"],
            "grupos_unidades": resumen_registro_data["grupos_unidades"],
            "hay_unidades_o_estancias": resumen_registro_data["hay_unidades_o_estancias"],
            "revision_informe": revision_informe,
        },
    )


@app.get("/editar-expediente/{expediente_id}", response_class=HTMLResponse)
def editar_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")
    estructura_multiunidad = cargar_estructura_multiunidad(cur, expediente_id)
    expediente_data = dict(expediente)
    expediente_data["analisis_unidades_resuelto"] = limpiar_texto(
        expediente_data.get("analisis_unidades")
    ) or (
        "varias_unidades"
        if estructura_multiunidad["niveles"] or estructura_multiunidad["unidades"]
        else "una_unidad"
    )

    conn.close()

    return render_template(
        request,
        "editar_expediente.html",
        {
            "expediente": expediente_data,
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
            "niveles_edificio": estructura_multiunidad["niveles"],
            "unidades_expediente": estructura_multiunidad["unidades"],
        },
    )


@app.post("/actualizar-expediente/{expediente_id}")
def actualizar_expediente(
    request: Request,
    expediente_id: int,
    numero_expediente: str = Form(...),
    tipo_informe: str = Form("patologias"),
    destinatario: str = Form("particular"),
    ambito_patologias: str = Form("interior"),
    descripcion_dano: str = Form(""),
    causa_probable: str = Form(""),
    pruebas_indicios: str = Form(""),
    evolucion_preexistencia: str = Form(""),
    propuesta_reparacion: str = Form(""),
    urgencia_gravedad: str = Form(""),
    cliente: str = Form(...),
    referencia_catastral: str = Form(""),
    direccion: str = Form(...),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
    tipo_inmueble: str = Form(""),
    orientacion_inmueble: str = Form(""),
    anio_construccion: str = Form(""),
    plantas_bajo_rasante: str = Form("0"),
    plantas_sobre_baja: str = Form("0"),
    uso_inmueble: str = Form(""),
    observaciones_generales: str = Form(""),
    planta_unidad: str = Form(""),
    puerta_unidad: str = Form(""),
    analisis_unidades: str = Form("una_unidad"),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    dormitorios_unidad: str = Form(""),
    banos_unidad: str = Form(""),
    observaciones_bloque: str = Form(""),
    observaciones_unidad: str = Form(""),
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
    procedimiento_judicial: str = Form(""),
    juzgado: str = Form(""),
    auto_judicial: str = Form(""),
    parte_solicitante: str = Form(""),
    objeto_pericia: str = Form(""),
    alcance_limitaciones: str = Form(""),
    metodologia_pericial: str = Form(""),
    imagen_catastro: str = Form(""),
    imagen_catastro_nueva: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    expediente_existente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente_existente, "Expediente no encontrado")

    duplicado = cur.execute(
        """
        SELECT id
        FROM expedientes
        WHERE numero_expediente=? AND id<>?
        LIMIT 1
        """,
        (numero_expediente, expediente_id),
    ).fetchone()

    if duplicado:
        estructura_multiunidad = cargar_estructura_multiunidad(cur, expediente_id)
        conn.close()
        expediente_form = {
            "id": expediente_id,
            "numero_expediente": numero_expediente,
            "tipo_informe": tipo_informe,
            "destinatario": destinatario,
            "ambito_patologias": ambito_patologias,
            "descripcion_dano": descripcion_dano,
            "causa_probable": causa_probable,
            "pruebas_indicios": pruebas_indicios,
            "evolucion_preexistencia": evolucion_preexistencia,
            "propuesta_reparacion": propuesta_reparacion,
            "urgencia_gravedad": urgencia_gravedad,
            "cliente": cliente,
            "referencia_catastral": referencia_catastral,
            "direccion": direccion,
            "codigo_postal": codigo_postal,
            "ciudad": ciudad,
            "provincia": provincia,
            "tipo_inmueble": tipo_inmueble,
            "orientacion_inmueble": orientacion_inmueble,
            "anio_construccion": anio_construccion,
            "plantas_bajo_rasante": plantas_bajo_rasante,
            "plantas_sobre_baja": plantas_sobre_baja,
            "uso_inmueble": uso_inmueble,
            "observaciones_generales": observaciones_generales,
            "planta_unidad": planta_unidad,
            "puerta_unidad": puerta_unidad,
            "analisis_unidades": analisis_unidades,
            "analisis_unidades_resuelto": limpiar_texto(analisis_unidades) or (
                "varias_unidades"
                if estructura_multiunidad["niveles"] or estructura_multiunidad["unidades"]
                else "una_unidad"
            ),
            "superficie_construida": superficie_construida,
            "superficie_util": superficie_util,
            "dormitorios_unidad": dormitorios_unidad,
            "banos_unidad": banos_unidad,
            "observaciones_bloque": observaciones_bloque,
            "observaciones_unidad": observaciones_unidad,
            "reformado": reformado,
            "fecha_reforma": fecha_reforma,
            "observaciones_reforma": observaciones_reforma,
            "procedimiento_judicial": procedimiento_judicial,
            "juzgado": juzgado,
            "auto_judicial": auto_judicial,
            "parte_solicitante": parte_solicitante,
            "objeto_pericia": objeto_pericia,
            "alcance_limitaciones": alcance_limitaciones,
            "metodologia_pericial": metodologia_pericial,
            "imagen_catastro": imagen_catastro,
        }
        return render_template(
            request,
            "editar_expediente.html",
            {
                "error": "Ya existe otro expediente con ese número.",
                "expediente": expediente_form,
                "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
                "niveles_edificio": estructura_multiunidad["niveles"],
                "unidades_expediente": estructura_multiunidad["unidades"],
            },
        )

    nueva_imagen_catastro = guardar_upload_si_existe(imagen_catastro_nueva)
    if nueva_imagen_catastro:
        imagen_catastro = nueva_imagen_catastro

    columnas = get_table_columns("expedientes")

    valores = {
        "numero_expediente": numero_expediente,
        "tipo_informe": tipo_informe,
        "destinatario": destinatario,
        "ambito_patologias": ambito_patologias,
        "descripcion_dano": descripcion_dano,
        "causa_probable": causa_probable,
        "pruebas_indicios": pruebas_indicios,
        "evolucion_preexistencia": evolucion_preexistencia,
        "propuesta_reparacion": propuesta_reparacion,
        "urgencia_gravedad": urgencia_gravedad,
        "cliente": cliente,
        "referencia_catastral": referencia_catastral,
        "direccion": direccion,
        "codigo_postal": codigo_postal,
        "ciudad": ciudad,
        "provincia": provincia,
        "tipo_inmueble": tipo_inmueble,
        "orientacion_inmueble": orientacion_inmueble,
        "anio_construccion": anio_construccion,
        "plantas_bajo_rasante": plantas_bajo_rasante,
        "plantas_sobre_baja": plantas_sobre_baja,
        "uso_inmueble": uso_inmueble,
        "observaciones_generales": observaciones_generales,
        "planta_unidad": planta_unidad,
        "puerta_unidad": puerta_unidad,
        "analisis_unidades": analisis_unidades,
        "superficie_construida": superficie_construida,
        "superficie_util": superficie_util,
        "dormitorios_unidad": dormitorios_unidad,
        "banos_unidad": banos_unidad,
        "observaciones_bloque": observaciones_bloque,
        "observaciones_unidad": observaciones_unidad,
        "reformado": reformado,
        "fecha_reforma": fecha_reforma,
        "observaciones_reforma": observaciones_reforma,
        "procedimiento_judicial": procedimiento_judicial,
        "juzgado": juzgado,
        "auto_judicial": auto_judicial,
        "parte_solicitante": parte_solicitante,
        "objeto_pericia": objeto_pericia,
        "alcance_limitaciones": alcance_limitaciones,
        "metodologia_pericial": metodologia_pericial,
        "imagen_catastro": imagen_catastro,
    }

    campos_actualizables = [campo for campo in valores.keys() if campo in columnas]

    sets = ", ".join([f"{campo}=?" for campo in campos_actualizables])
    params = [valores[campo] for campo in campos_actualizables] + [
        expediente_id,
        current_user["id"],
    ]

    updated = cur.execute(
        f"UPDATE expedientes SET {sets} WHERE id=? AND owner_user_id=?",
        params,
    )

    if updated.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    conn.commit()
    imagen_catastro_anterior = limpiar_texto(expediente_existente["imagen_catastro"])
    imagen_catastro_nueva = limpiar_texto(imagen_catastro)
    conn.close()

    if (
        imagen_catastro_anterior
        and imagen_catastro_anterior != imagen_catastro_nueva
    ):
        borrar_foto_si_existe(imagen_catastro_anterior)

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@app.post("/guardar-nivel-expediente/{expediente_id}")
def guardar_nivel_expediente(
    request: Request,
    expediente_id: int,
    nombre_nivel: str = Form(...),
    orden_nivel: str = Form(""),
    tipo_nivel: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    nombre_nivel = limpiar_texto(nombre_nivel)
    if not nombre_nivel:
        conn.close()
        return redirect_detalle_expediente(
            expediente_id, error="El nombre del nivel es obligatorio."
        )

    cur.execute(
        """
        INSERT INTO niveles_edificio (
            expediente_id, nombre_nivel, orden_nivel, tipo_nivel, observaciones
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            nombre_nivel,
            parse_optional_int(orden_nivel),
            limpiar_texto(tipo_nivel),
            limpiar_texto(observaciones),
        ),
    )
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(expediente_id, mensaje="Nivel guardado.")


@app.get("/editar-nivel-expediente/{nivel_id}", response_class=HTMLResponse)
def editar_nivel_expediente(request: Request, nivel_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    nivel = get_owned_nivel(cur, nivel_id, current_user["id"])
    require_row(nivel, "Nivel no encontrado")
    nivel_data = dict(nivel)

    conn.close()
    return render_template(
        request,
        "editar_nivel_expediente.html",
        {
            "nivel": nivel_data,
            "tipo_nivel_options": TIPO_NIVEL_OPTIONS,
        },
    )


@app.post("/actualizar-nivel-expediente/{nivel_id}")
def actualizar_nivel_expediente(
    request: Request,
    nivel_id: int,
    nombre_nivel: str = Form(...),
    orden_nivel: str = Form(""),
    tipo_nivel: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    nivel = get_owned_nivel(cur, nivel_id, current_user["id"])
    require_row(nivel, "Nivel no encontrado")

    nombre_nivel = limpiar_texto(nombre_nivel)
    if not nombre_nivel:
        conn.close()
        return render_template(
            request,
            "editar_nivel_expediente.html",
            {
                "error": "El nombre del nivel es obligatorio.",
                "nivel": {
                    "id": nivel_id,
                    "expediente_id": nivel["expediente_id"],
                    "nombre_nivel": nombre_nivel,
                    "orden_nivel": orden_nivel,
                    "tipo_nivel": tipo_nivel,
                    "observaciones": observaciones,
                },
                "tipo_nivel_options": TIPO_NIVEL_OPTIONS,
            },
        )

    cur.execute(
        """
        UPDATE niveles_edificio
        SET nombre_nivel=?, orden_nivel=?, tipo_nivel=?, observaciones=?
        WHERE id=?
        """,
        (
            nombre_nivel,
            parse_optional_int(orden_nivel),
            limpiar_texto(tipo_nivel),
            limpiar_texto(observaciones),
            nivel_id,
        ),
    )
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(
        nivel["expediente_id"], mensaje="Nivel actualizado."
    )


@app.post("/borrar-nivel-expediente/{nivel_id}")
def borrar_nivel_expediente(request: Request, nivel_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    nivel = get_owned_nivel(cur, nivel_id, current_user["id"])
    require_row(nivel, "Nivel no encontrado")

    cur.execute("UPDATE unidades_expediente SET nivel_id=NULL WHERE nivel_id=?", (nivel_id,))
    cur.execute("DELETE FROM niveles_edificio WHERE id=?", (nivel_id,))
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(
        nivel["expediente_id"], mensaje="Nivel eliminado."
    )


@app.post("/guardar-unidad-expediente/{expediente_id}")
def guardar_unidad_expediente(
    request: Request,
    expediente_id: int,
    nivel_id: str = Form(""),
    identificador: str = Form(...),
    tipo_unidad: str = Form("vivienda"),
    uso: str = Form(""),
    superficie: str = Form(""),
    referencia_catastral_unidad: str = Form(""),
    vinculo_unidad: str = Form("principal"),
    unidad_principal_id: str = Form(""),
    tipo_anejo: str = Form(""),
    tiene_varias_plantas: str = Form(""),
    numero_plantas: str = Form("1"),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    identificador = limpiar_texto(identificador)
    if not identificador:
        conn.close()
        return redirect_detalle_expediente(
            expediente_id, error="El identificador de la unidad es obligatorio."
        )

    nivel_id_int = parse_optional_int(nivel_id)
    if nivel_id_int:
        nivel = get_owned_nivel(cur, nivel_id_int, current_user["id"])
        if not nivel or nivel["expediente_id"] != expediente_id:
            conn.close()
            return redirect_detalle_expediente(
                expediente_id, error="El nivel seleccionado no es válido."
            )

    vinculo_limpio = limpiar_texto(vinculo_unidad) or "principal"
    principal_id_int = parse_optional_int(unidad_principal_id)
    tipo_anejo_limpio = limpiar_texto(tipo_anejo)
    es_principal = 0 if vinculo_limpio == "anejo" else 1
    tiene_varias_plantas_int, numero_plantas_int = normalizar_configuracion_plantas(
        tiene_varias_plantas,
        numero_plantas,
    )

    if vinculo_limpio == "anejo":
        principal = (
            get_owned_unidad(cur, principal_id_int, current_user["id"])
            if principal_id_int
            else None
        )
        if (
            not principal
            or principal["expediente_id"] != expediente_id
            or limpiar_texto(principal["vinculo_unidad"]) not in {"", "principal"}
            or int(principal["es_principal"] or 0) == 0
        ):
            conn.close()
            return redirect_detalle_expediente(
                expediente_id,
                error="Debes seleccionar una unidad principal válida para el anejo.",
            )
    else:
        principal_id_int = None
        tipo_anejo_limpio = ""

    cur.execute(
        """
        INSERT INTO unidades_expediente (
            expediente_id,
            nivel_id,
            identificador,
            tipo_unidad,
            uso,
            superficie,
            referencia_catastral_unidad,
            es_principal,
            unidad_principal_id,
            tipo_anejo,
            vinculo_unidad,
            tiene_varias_plantas,
            numero_plantas,
            observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            nivel_id_int,
            identificador,
            limpiar_texto(tipo_unidad),
            limpiar_texto(uso),
            limpiar_texto(superficie),
            limpiar_texto(referencia_catastral_unidad),
            es_principal,
            principal_id_int,
            tipo_anejo_limpio,
            vinculo_limpio,
            tiene_varias_plantas_int,
            numero_plantas_int,
            limpiar_texto(observaciones),
        ),
    )
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(expediente_id, mensaje="Unidad guardada.")


@app.get("/editar-unidad-expediente/{unidad_id}", response_class=HTMLResponse)
def editar_unidad_expediente(request: Request, unidad_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    unidad = get_owned_unidad(cur, unidad_id, current_user["id"])
    require_row(unidad, "Unidad no encontrada")
    estructura = cargar_estructura_multiunidad(cur, unidad["expediente_id"])
    niveles = estructura["niveles"]
    unidades_principales = [
        item for item in estructura["unidades_principales"] if item["id"] != unidad_id
    ]

    conn.close()
    return render_template(
        request,
        "editar_unidad_expediente.html",
        {
            "unidad": dict(unidad),
            "niveles_edificio": niveles,
            "unidades_principales_form": unidades_principales,
            "tipo_unidad_options": TIPO_UNIDAD_OPTIONS,
            "vinculo_unidad_options": VINCULO_UNIDAD_OPTIONS,
            "tipo_anejo_options": TIPO_ANEJO_OPTIONS,
        },
    )


@app.post("/actualizar-unidad-expediente/{unidad_id}")
def actualizar_unidad_expediente(
    request: Request,
    unidad_id: int,
    nivel_id: str = Form(""),
    identificador: str = Form(...),
    tipo_unidad: str = Form("vivienda"),
    uso: str = Form(""),
    superficie: str = Form(""),
    referencia_catastral_unidad: str = Form(""),
    vinculo_unidad: str = Form("principal"),
    unidad_principal_id: str = Form(""),
    tipo_anejo: str = Form(""),
    tiene_varias_plantas: str = Form(""),
    numero_plantas: str = Form("1"),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    unidad = get_owned_unidad(cur, unidad_id, current_user["id"])
    require_row(unidad, "Unidad no encontrada")

    expediente_id = unidad["expediente_id"]
    identificador = limpiar_texto(identificador)
    nivel_id_int = parse_optional_int(nivel_id)
    principal_id_int = parse_optional_int(unidad_principal_id)
    vinculo_limpio = limpiar_texto(vinculo_unidad) or "principal"
    tipo_anejo_limpio = limpiar_texto(tipo_anejo)
    tiene_varias_plantas_int, numero_plantas_int = normalizar_configuracion_plantas(
        tiene_varias_plantas,
        numero_plantas,
    )

    if not identificador:
        estructura = cargar_estructura_multiunidad(cur, expediente_id)
        conn.close()
        return render_template(
            request,
            "editar_unidad_expediente.html",
            {
                "error": "El identificador de la unidad es obligatorio.",
                "unidad": {
                    "id": unidad_id,
                    "expediente_id": expediente_id,
                    "nivel_id": nivel_id_int,
                    "identificador": identificador,
                    "tipo_unidad": tipo_unidad,
                    "uso": uso,
                    "superficie": superficie,
                    "referencia_catastral_unidad": referencia_catastral_unidad,
                    "vinculo_unidad": vinculo_limpio,
                    "unidad_principal_id": principal_id_int,
                    "tipo_anejo": tipo_anejo_limpio,
                    "tiene_varias_plantas": tiene_varias_plantas_int,
                    "numero_plantas": numero_plantas_int,
                    "observaciones": observaciones,
                },
                "niveles_edificio": estructura["niveles"],
                "unidades_principales_form": [
                    item
                    for item in estructura["unidades_principales"]
                    if item["id"] != unidad_id
                ],
                "tipo_unidad_options": TIPO_UNIDAD_OPTIONS,
                "vinculo_unidad_options": VINCULO_UNIDAD_OPTIONS,
                "tipo_anejo_options": TIPO_ANEJO_OPTIONS,
            },
        )

    if nivel_id_int:
        nivel = get_owned_nivel(cur, nivel_id_int, current_user["id"])
        if not nivel or nivel["expediente_id"] != expediente_id:
            conn.close()
            return redirect_detalle_expediente(
                expediente_id, error="El nivel seleccionado no es válido."
            )

    anejos_existentes = cur.execute(
        """
        SELECT COUNT(*)
        FROM unidades_expediente
        WHERE unidad_principal_id=?
        """,
        (unidad_id,),
    ).fetchone()[0]
    es_principal = 0 if vinculo_limpio == "anejo" else 1
    if anejos_existentes and vinculo_limpio != "principal":
        conn.close()
        return redirect_detalle_expediente(
            expediente_id,
            error="No se puede cambiar el vínculo de una unidad principal que tiene anejos asociados.",
        )
    if vinculo_limpio == "anejo":
        principal = (
            get_owned_unidad(cur, principal_id_int, current_user["id"])
            if principal_id_int
            else None
        )
        if (
            not principal
            or principal["expediente_id"] != expediente_id
            or principal["id"] == unidad_id
            or limpiar_texto(principal["vinculo_unidad"]) not in {"", "principal"}
            or int(principal["es_principal"] or 0) == 0
        ):
            conn.close()
            return redirect_detalle_expediente(
                expediente_id,
                error="Debes seleccionar una unidad principal válida para el anejo.",
            )
    else:
        principal_id_int = None
        tipo_anejo_limpio = ""

    cur.execute(
        """
        UPDATE unidades_expediente
        SET nivel_id=?,
            identificador=?,
            tipo_unidad=?,
            uso=?,
            superficie=?,
            referencia_catastral_unidad=?,
            es_principal=?,
            unidad_principal_id=?,
            tipo_anejo=?,
            vinculo_unidad=?,
            tiene_varias_plantas=?,
            numero_plantas=?,
            observaciones=?
        WHERE id=?
        """,
        (
            nivel_id_int,
            identificador,
            limpiar_texto(tipo_unidad),
            limpiar_texto(uso),
            limpiar_texto(superficie),
            limpiar_texto(referencia_catastral_unidad),
            es_principal,
            principal_id_int,
            tipo_anejo_limpio,
            vinculo_limpio,
            tiene_varias_plantas_int,
            numero_plantas_int,
            limpiar_texto(observaciones),
            unidad_id,
        ),
    )
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(expediente_id, mensaje="Unidad actualizada.")


@app.post("/borrar-unidad-expediente/{unidad_id}")
def borrar_unidad_expediente(request: Request, unidad_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    unidad = get_owned_unidad(cur, unidad_id, current_user["id"])
    require_row(unidad, "Unidad no encontrada")

    anejos = cur.execute(
        """
        SELECT COUNT(*)
        FROM unidades_expediente
        WHERE unidad_principal_id=?
        """,
        (unidad_id,),
    ).fetchone()[0]
    if anejos:
        conn.close()
        return redirect_detalle_expediente(
            unidad["expediente_id"],
            error="No se puede borrar una unidad principal con anejos asociados.",
        )

    cur.execute("DELETE FROM unidades_expediente WHERE id=?", (unidad_id,))
    conn.commit()
    conn.close()
    return redirect_detalle_expediente(
        unidad["expediente_id"], mensaje="Unidad eliminada."
    )


# -------------------------------------------------------
# VISITAS
# -------------------------------------------------------


@app.get("/nueva-visita/{expediente_id}", response_class=HTMLResponse)
def nueva_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Query(None),
    clima_error: str = Query(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    visita = None
    clima = None
    clima_detalle = []
    estancias = []
    inspeccion = {
        "general": {},
        "exterior": {},
        "comunes": {},
        "estancias": [],
    }
    habitabilidad = {
        "general": {},
        "exterior": {},
        "estancias": [],
    }
    valoracion = {}
    comparables_valoracion = []
    visita_fotos_exteriores = []
    visita_fotos_portal_contadores = []
    valoracion_visita_observaciones = valoracion_visita_observaciones_form_vacio()
    opciones_visita_multiunidad = cargar_opciones_visita_multiunidad(cur, expediente_id)
    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        clima, clima_detalle = obtener_climatologia_guardada(cur, visita_id)
        estancias = cur.execute(
            "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
            (visita_id,),
        ).fetchall()
        visita_fotos_exteriores = obtener_fotos_visita(cur, visita_id, "exterior")
        visita_fotos_portal_contadores = obtener_fotos_visita(
            cur,
            visita_id,
            "portal_contadores",
        )
        valoracion_visita_observaciones = cargar_valoracion_visita_observaciones_form(
            cur,
            visita_id,
        )
        if limpiar_texto(expediente["tipo_informe"]) == "inspeccion":
            inspeccion = cargar_datos_inspeccion_visita(cur, visita_id, estancias)
        if limpiar_texto(expediente["tipo_informe"]) == "habitabilidad":
            habitabilidad = cargar_datos_habitabilidad_visita(cur, visita_id, estancias)
        if limpiar_texto(expediente["tipo_informe"]) == "valoracion":
            valoracion = cargar_datos_valoracion_visita(cur, visita_id)
            comparables_valoracion = cur.execute(
                """
                SELECT *
                FROM comparables_valoracion
                WHERE visita_id=?
                ORDER BY id DESC
                """,
                (visita_id,),
            ).fetchall()

    conn.close()

    visita_form = {
        "id": visita["id"] if visita else "",
        "fecha": (visita["fecha"] if visita else datetime.now().strftime("%Y-%m-%d")),
        "tecnico": (
            visita["tecnico"]
            if visita
            else f"{current_user['nombre']} {current_user['apellido1']}".strip()
            or current_user["username"]
        ),
        "observaciones_visita": visita["observaciones_visita"] if visita else "",
        "ambito_visita": (
            limpiar_texto(visita["ambito_visita"]) if visita else "edificio_completo"
        ),
        "nivel_id": str(visita["nivel_id"] or "") if visita else "",
        "unidad_id": str(visita["unidad_id"] or "") if visita else "",
    }

    return render_template(
        request,
        "nueva_visita.html",
        {
            "expediente": expediente,
            "visita": visita,
            "visita_form": visita_form,
            "visita_fotos_exteriores": visita_fotos_exteriores,
            "visita_fotos_portal_contadores": visita_fotos_portal_contadores,
            "valoracion_visita_observaciones": valoracion_visita_observaciones,
            "clima": clima,
            "clima_detalle": clima_detalle,
            "clima_error": clima_error,
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
            "es_informe_inspeccion": limpiar_texto(expediente["tipo_informe"]) == "inspeccion",
            "es_informe_habitabilidad": limpiar_texto(expediente["tipo_informe"]) == "habitabilidad",
            "es_informe_valoracion": limpiar_texto(expediente["tipo_informe"]) == "valoracion",
            "permite_patologias_exteriores": limpiar_texto(expediente["tipo_informe"]) == "patologias"
            and limpiar_texto(expediente["ambito_patologias"]) in {"exterior", "interior_exterior"},
            "estados_inspeccion": ESTADO_INSPECCION_OPTIONS,
            "inspeccion_general_groups": INSPECCION_GENERAL_GROUPS,
            "inspeccion_exterior_items": INSPECCION_EXTERIOR_ITEMS,
            "inspeccion_elementos_comunes_items": INSPECCION_ELEMENTOS_COMUNES_ITEMS,
            "inspeccion": inspeccion,
            "estados_habitabilidad": ESTADO_HABITABILIDAD_OPTIONS,
            "conclusiones_habitabilidad": CONCLUSION_HABITABILIDAD_OPTIONS,
            "habitabilidad_general_items": HABITABILIDAD_GENERAL_ITEMS,
            "habitabilidad_estancia_items": HABITABILIDAD_ESTANCIA_ITEMS,
            "habitabilidad_exterior_items": HABITABILIDAD_EXTERIOR_ITEMS,
            "habitabilidad": habitabilidad,
            "valoracion_encargo_items": VALORACION_ENCARGO_ITEMS,
            "valoracion_documentacion_items": VALORACION_DOCUMENTACION_ITEMS,
            "valoracion_datos_generales_items": VALORACION_DATOS_GENERALES_ITEMS,
            "valoracion_superficies_items": VALORACION_SUPERFICIES_ITEMS,
            "valoracion_situacion_legal_items": VALORACION_SITUACION_LEGAL_ITEMS,
            "valoracion_entorno_items": VALORACION_ENTORNO_ITEMS,
            "valoracion_edificio_items": VALORACION_EDIFICIO_ITEMS,
            "valoracion_inmueble_items": VALORACION_INMUEBLE_ITEMS,
            "valoracion_constructivo_items": VALORACION_CONSTRUCTIVO_ITEMS,
            "valoracion_estado_items": VALORACION_ESTADO_ITEMS,
            "valoracion_fechas_items": VALORACION_FECHAS_ITEMS,
            "valoracion_metodo_items": VALORACION_METODO_ITEMS,
            "valoracion_resultado_items": VALORACION_RESULTADO_ITEMS,
            "valoracion_ayudas_rapidas": VALORACION_AYUDAS_RAPIDAS,
            "valoracion": valoracion,
            "comparables_valoracion_items": COMPARABLE_VALORACION_ITEMS,
            "comparables_valoracion": comparables_valoracion,
            "comparable_form": comparable_valoracion_form_vacio(),
            "objeto_visita_label": (
                describir_objeto_visita(visita)
                if visita
                else resolver_objeto_visita_label(
                    visita_form["ambito_visita"],
                    visita_form["nivel_id"],
                    visita_form["unidad_id"],
                    opciones_visita_multiunidad,
                )
            ),
            "ambito_visita_options": AMBITO_VISITA_OPTIONS,
            "niveles_visita_options": opciones_visita_multiunidad["niveles"],
            "unidades_visita_options": opciones_visita_multiunidad["unidades_generales"],
            "zonas_comunes_visita_options": opciones_visita_multiunidad["unidades_comunes"],
            "exteriores_visita_options": opciones_visita_multiunidad["unidades_exteriores"],
        },
    )


@app.post("/guardar-visita/{expediente_id}")
async def guardar_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Form(None),
    fecha: str = Form(...),
    tecnico: str = Form(...),
    observaciones_visita: str = Form(""),
    ambito_visita: str = Form("edificio_completo"),
    nivel_id: str = Form(""),
    unidad_id: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_limpia = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_limpio = limpiar_texto(tecnico) or current_user["username"]
    observaciones_limpias = observaciones_visita or ""
    try:
        ambito_visita_limpio, nivel_id_int, unidad_id_int = validar_asociacion_visita(
            cur,
            expediente_id,
            current_user["id"],
            ambito_visita,
            nivel_id,
            unidad_id,
        )
    except ValueError as exc:
        opciones_visita_multiunidad = cargar_opciones_visita_multiunidad(cur, expediente_id)
        visita = None
        clima = None
        clima_detalle = []
        estancias = []
        visita_fotos_exteriores = []
        visita_fotos_portal_contadores = []
        valoracion_visita_observaciones = valoracion_visita_observaciones_form_vacio()
        inspeccion = {"general": {}, "exterior": {}, "comunes": {}, "estancias": []}
        habitabilidad = {"general": {}, "exterior": {}, "estancias": []}
        valoracion = {}
        comparables_valoracion = []
        if visita_id:
            visita = get_owned_visita(cur, visita_id, current_user["id"])
            require_row(visita, "Visita no encontrada")
            clima, clima_detalle = obtener_climatologia_guardada(cur, visita_id)
            estancias = cur.execute(
                "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
                (visita_id,),
            ).fetchall()
            visita_fotos_exteriores = obtener_fotos_visita(cur, visita_id, "exterior")
            visita_fotos_portal_contadores = obtener_fotos_visita(
                cur,
                visita_id,
                "portal_contadores",
            )
            valoracion_visita_observaciones = cargar_valoracion_visita_observaciones_form(
                cur,
                visita_id,
            )
            tipo_informe = limpiar_texto(expediente["tipo_informe"])
            if tipo_informe == "inspeccion":
                inspeccion = cargar_datos_inspeccion_visita(cur, visita_id, estancias)
            if tipo_informe == "habitabilidad":
                habitabilidad = cargar_datos_habitabilidad_visita(cur, visita_id, estancias)
            if tipo_informe == "valoracion":
                valoracion = cargar_datos_valoracion_visita(cur, visita_id)
                comparables_valoracion = cur.execute(
                    """
                    SELECT *
                    FROM comparables_valoracion
                    WHERE visita_id=?
                    ORDER BY id DESC
                    """,
                    (visita_id,),
                ).fetchall()
        conn.close()
        return render_template(
            request,
            "nueva_visita.html",
            {
                "error": str(exc),
                "expediente": expediente,
                "visita": visita,
                "visita_form": {
                    "id": visita_id or "",
                    "fecha": fecha_limpia,
                    "tecnico": tecnico_limpio,
                    "observaciones_visita": observaciones_limpias,
                    "ambito_visita": limpiar_texto(ambito_visita) or "edificio_completo",
                    "nivel_id": nivel_id,
                    "unidad_id": unidad_id,
                },
                "visita_fotos_exteriores": visita_fotos_exteriores,
                "visita_fotos_portal_contadores": visita_fotos_portal_contadores,
                "valoracion_visita_observaciones": valoracion_visita_observaciones,
                "clima": clima,
                "clima_detalle": clima_detalle,
                "clima_error": "",
                "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
                "es_informe_inspeccion": limpiar_texto(expediente["tipo_informe"]) == "inspeccion",
                "es_informe_habitabilidad": limpiar_texto(expediente["tipo_informe"]) == "habitabilidad",
                "es_informe_valoracion": limpiar_texto(expediente["tipo_informe"]) == "valoracion",
                "permite_patologias_exteriores": limpiar_texto(expediente["tipo_informe"]) == "patologias"
                and limpiar_texto(expediente["ambito_patologias"]) in {"exterior", "interior_exterior"},
                "estados_inspeccion": ESTADO_INSPECCION_OPTIONS,
                "inspeccion_general_groups": INSPECCION_GENERAL_GROUPS,
                "inspeccion_exterior_items": INSPECCION_EXTERIOR_ITEMS,
                "inspeccion_elementos_comunes_items": INSPECCION_ELEMENTOS_COMUNES_ITEMS,
                "inspeccion": inspeccion,
                "estados_habitabilidad": ESTADO_HABITABILIDAD_OPTIONS,
                "conclusiones_habitabilidad": CONCLUSION_HABITABILIDAD_OPTIONS,
                "habitabilidad_general_items": HABITABILIDAD_GENERAL_ITEMS,
                "habitabilidad_estancia_items": HABITABILIDAD_ESTANCIA_ITEMS,
                "habitabilidad_exterior_items": HABITABILIDAD_EXTERIOR_ITEMS,
                "habitabilidad": habitabilidad,
                "valoracion_encargo_items": VALORACION_ENCARGO_ITEMS,
                "valoracion_documentacion_items": VALORACION_DOCUMENTACION_ITEMS,
                "valoracion_datos_generales_items": VALORACION_DATOS_GENERALES_ITEMS,
                "valoracion_superficies_items": VALORACION_SUPERFICIES_ITEMS,
                "valoracion_situacion_legal_items": VALORACION_SITUACION_LEGAL_ITEMS,
                "valoracion_entorno_items": VALORACION_ENTORNO_ITEMS,
                "valoracion_edificio_items": VALORACION_EDIFICIO_ITEMS,
                "valoracion_inmueble_items": VALORACION_INMUEBLE_ITEMS,
                "valoracion_constructivo_items": VALORACION_CONSTRUCTIVO_ITEMS,
                "valoracion_estado_items": VALORACION_ESTADO_ITEMS,
                "valoracion_fechas_items": VALORACION_FECHAS_ITEMS,
                "valoracion_metodo_items": VALORACION_METODO_ITEMS,
                "valoracion_resultado_items": VALORACION_RESULTADO_ITEMS,
                "valoracion_ayudas_rapidas": VALORACION_AYUDAS_RAPIDAS,
                "valoracion": valoracion,
                "comparables_valoracion_items": COMPARABLE_VALORACION_ITEMS,
                "comparables_valoracion": comparables_valoracion,
                "comparable_form": comparable_valoracion_form_vacio(),
                "objeto_visita_label": resolver_objeto_visita_label(
                    limpiar_texto(ambito_visita) or "edificio_completo",
                    nivel_id,
                    unidad_id,
                    opciones_visita_multiunidad,
                ),
                "ambito_visita_options": AMBITO_VISITA_OPTIONS,
                "niveles_visita_options": opciones_visita_multiunidad["niveles"],
                "unidades_visita_options": opciones_visita_multiunidad["unidades_generales"],
                "zonas_comunes_visita_options": opciones_visita_multiunidad["unidades_comunes"],
                "exteriores_visita_options": opciones_visita_multiunidad["unidades_exteriores"],
            },
        )

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?, ambito_visita=?, nivel_id=?, unidad_id=?
            WHERE id=?
            """,
            (
                fecha_limpia,
                tecnico_limpio,
                observaciones_limpias,
                ambito_visita_limpio,
                nivel_id_int,
                unidad_id_int,
                visita_id,
            ),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_limpia,
            tecnico_limpio,
            observaciones_limpias,
            ambito_visita_limpio,
            nivel_id_int,
            unidad_id_int,
        )

    tipo_informe = limpiar_texto(expediente["tipo_informe"])
    if tipo_informe in {"inspeccion", "habitabilidad", "valoracion"}:
        form = await request.form()
        estancias = cur.execute(
            "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
            (visita_id,),
        ).fetchall()
        if tipo_informe == "inspeccion":
            await guardar_datos_inspeccion_desde_form(cur, visita_id, estancias, form)
        elif tipo_informe == "habitabilidad":
            await guardar_datos_habitabilidad_desde_form(cur, visita_id, estancias, form)
        else:
            if any(str(campo).startswith("valoracion__") for campo in form.keys()):
                await guardar_datos_valoracion_desde_form(cur, visita_id, form)
            campos_observaciones = {
                "observaciones_portal",
                "observaciones_cuadro_contadores",
            }
            if any(campo in form for campo in campos_observaciones):
                existentes = cargar_valoracion_visita_observaciones_form(cur, visita_id)
                valores_observaciones = {
                    campo: form.get(campo, existentes.get(campo, ""))
                    for campo in VALORACION_VISITA_OBSERVACIONES_FIELDS
                }
                upsert_valoracion_visita_observaciones(
                    cur,
                    visita_id,
                    expediente_id,
                    valores_observaciones,
                )

    conn.commit()
    conn.close()

    if tipo_informe in {"inspeccion", "habitabilidad", "valoracion"}:
        return RedirectResponse(
            url=f"/nueva-visita/{expediente_id}?visita_id={visita_id}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/nueva-visita/{expediente_id}?visita_id={visita_id}#exterior-edificio",
        status_code=303,
    )


@app.post("/visitas/{visita_id}/fotos")
def guardar_fotos_visita(
    request: Request,
    visita_id: int,
    categoria: str = Form("exterior"),
    descripcion: str = Form(""),
    fotos: list[UploadFile] = File([]),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    categoria_limpia = limpiar_texto(categoria) or "exterior"
    descripcion_limpia = limpiar_texto(descripcion)
    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        "visita",
        categoria_limpia,
    )

    for nombre in nombres_fotos:
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, ?, ?, ?)
            """,
            (visita_id, categoria_limpia, nombre, descripcion_limpia),
        )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(url=next_url, status_code=303)

    return RedirectResponse(
        url=f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}#exterior-edificio",
        status_code=303,
    )


@app.post("/expedientes/{expediente_id}/reforma")
def guardar_reforma_expediente(
    request: Request,
    expediente_id: int,
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    cur.execute(
        """
        UPDATE expedientes
        SET reformado=?, fecha_reforma=?, observaciones_reforma=?
        WHERE id=?
        """,
        (reformado, fecha_reforma, observaciones_reforma, expediente_id),
    )
    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(url=next_url, status_code=303)

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@app.get("/editar-visita/{visita_id}", response_class=HTMLResponse)
def editar_visita(request: Request, visita_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    opciones_visita_multiunidad = cargar_opciones_visita_multiunidad(
        cur, visita["expediente_id"]
    )
    visita_fotos_exteriores = obtener_fotos_visita(cur, visita_id, "exterior")
    permite_patologias_exteriores = (
        limpiar_texto(visita["tipo_informe"]) == "patologias"
        and limpiar_texto(visita["ambito_patologias"]) in {"exterior", "interior_exterior"}
    )

    conn.close()

    if limpiar_texto(visita["tipo_informe"]) in {"inspeccion", "habitabilidad", "valoracion"}:
        return RedirectResponse(
            url=f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}",
            status_code=303,
        )

    return render_template(
        request,
        "editar_visita.html",
        {
            "visita": visita,
            "visita_fotos_exteriores": visita_fotos_exteriores,
            "permite_patologias_exteriores": permite_patologias_exteriores,
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
            "ambito_visita_options": AMBITO_VISITA_OPTIONS,
            "niveles_visita_options": opciones_visita_multiunidad["niveles"],
            "unidades_visita_options": opciones_visita_multiunidad["unidades_generales"],
            "zonas_comunes_visita_options": opciones_visita_multiunidad["unidades_comunes"],
            "exteriores_visita_options": opciones_visita_multiunidad["unidades_exteriores"],
        },
    )


@app.get("/visitas/{visita_id}/valoracion-observaciones", response_class=HTMLResponse)
def editar_valoracion_visita_observaciones(request: Request, visita_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    try:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if limpiar_texto(visita["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                visita["expediente_id"],
                error="Las observaciones de valoración solo aplican a visitas de valoración.",
            )
        observaciones = cargar_valoracion_visita_observaciones_form(cur, visita_id)
        legacy_observaciones = cargar_valoracion_visita_observaciones_legacy(
            cur,
            visita_id,
        )
    finally:
        conn.close()

    return render_template(
        request,
        "valoracion_visita_observaciones.html",
        {
            "visita": dict(visita),
            "observaciones": observaciones,
            "legacy_observaciones": legacy_observaciones,
            "observacion_grupos": VALORACION_VISITA_OBSERVACIONES_GROUPS,
            "valoracion_ayudas_rapidas": VALORACION_AYUDAS_RAPIDAS,
        },
    )


@app.post("/visitas/{visita_id}/valoracion-observaciones")
async def guardar_valoracion_visita_observaciones(request: Request, visita_id: int):
    current_user = get_current_user(request)
    form = await request.form()

    conn = get_connection()
    cur = conn.cursor()
    try:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if limpiar_texto(visita["tipo_informe"]) != "valoracion":
            return redirect_detalle_expediente(
                visita["expediente_id"],
                error="Las observaciones de valoración solo aplican a visitas de valoración.",
            )
        valores = {
            campo: form.get(campo, "")
            for campo in VALORACION_VISITA_OBSERVACIONES_FIELDS
        }
        upsert_valoracion_visita_observaciones(
            cur,
            visita_id,
            visita["expediente_id"],
            valores,
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}",
        status_code=303,
    )


@app.post("/guardar-comparable-valoracion")
def guardar_comparable_valoracion(
    request: Request,
    visita_id: int = Form(...),
    direccion_testigo: str = Form(""),
    fuente_testigo: str = Form(""),
    fecha_testigo: str = Form(""),
    precio_oferta: str = Form(""),
    valor_unitario: str = Form(""),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    tipologia: str = Form(""),
    planta: str = Form(""),
    dormitorios: str = Form(""),
    banos: str = Form(""),
    estado_conservacion: str = Form(""),
    antiguedad: str = Form(""),
    calidad_constructiva: str = Form(""),
    visitado: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    cur.execute(
        """
        INSERT INTO comparables_valoracion (
            visita_id, direccion_testigo, fuente_testigo, fecha_testigo,
            precio_oferta, valor_unitario, superficie_construida, superficie_util,
            tipologia, planta, dormitorios, banos, estado_conservacion,
            antiguedad, calidad_constructiva, visitado, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            direccion_testigo,
            fuente_testigo,
            fecha_testigo,
            precio_oferta,
            valor_unitario,
            superficie_construida,
            superficie_util,
            tipologia,
            planta,
            dormitorios,
            banos,
            estado_conservacion,
            antiguedad,
            calidad_constructiva,
            visitado,
            observaciones,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}",
        status_code=303,
    )


@app.get("/editar-comparable-valoracion/{comparable_id}", response_class=HTMLResponse)
def editar_comparable_valoracion(request: Request, comparable_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    comparable = get_owned_comparable_valoracion(cur, comparable_id, current_user["id"])
    require_row(comparable, "Comparable no encontrado")

    conn.close()

    return render_template(
        request,
        "editar_comparable_valoracion.html",
        {
            "comparable": comparable,
            "comparables_valoracion_items": COMPARABLE_VALORACION_ITEMS,
        },
    )


@app.post("/actualizar-comparable-valoracion/{comparable_id}")
def actualizar_comparable_valoracion(
    request: Request,
    comparable_id: int,
    direccion_testigo: str = Form(""),
    fuente_testigo: str = Form(""),
    fecha_testigo: str = Form(""),
    precio_oferta: str = Form(""),
    valor_unitario: str = Form(""),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    tipologia: str = Form(""),
    planta: str = Form(""),
    dormitorios: str = Form(""),
    banos: str = Form(""),
    estado_conservacion: str = Form(""),
    antiguedad: str = Form(""),
    calidad_constructiva: str = Form(""),
    visitado: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    comparable = get_owned_comparable_valoracion(cur, comparable_id, current_user["id"])
    require_row(comparable, "Comparable no encontrado")

    cur.execute(
        """
        UPDATE comparables_valoracion
        SET direccion_testigo=?, fuente_testigo=?, fecha_testigo=?, precio_oferta=?,
            valor_unitario=?, superficie_construida=?, superficie_util=?, tipologia=?,
            planta=?, dormitorios=?, banos=?, estado_conservacion=?, antiguedad=?,
            calidad_constructiva=?, visitado=?, observaciones=?
        WHERE id=?
        """,
        (
            direccion_testigo,
            fuente_testigo,
            fecha_testigo,
            precio_oferta,
            valor_unitario,
            superficie_construida,
            superficie_util,
            tipologia,
            planta,
            dormitorios,
            banos,
            estado_conservacion,
            antiguedad,
            calidad_constructiva,
            visitado,
            observaciones,
            comparable_id,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/nueva-visita/{comparable['expediente_id']}?visita_id={comparable['visita_id']}",
        status_code=303,
    )


@app.post("/borrar-comparable-valoracion/{comparable_id}")
def borrar_comparable_valoracion(request: Request, comparable_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    comparable = get_owned_comparable_valoracion(cur, comparable_id, current_user["id"])
    require_row(comparable, "Comparable no encontrado")

    cur.execute("DELETE FROM comparables_valoracion WHERE id=?", (comparable_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/nueva-visita/{comparable['expediente_id']}?visita_id={comparable['visita_id']}",
        status_code=303,
    )


@app.post("/actualizar-visita/{visita_id}")
def actualizar_visita(
    request: Request,
    visita_id: int,
    fecha: str = Form(...),
    tecnico: str = Form(...),
    observaciones_visita: str = Form(""),
    ambito_visita: str = Form("edificio_completo"),
    nivel_id: str = Form(""),
    unidad_id: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    try:
        ambito_visita_limpio, nivel_id_int, unidad_id_int = validar_asociacion_visita(
            cur,
            visita["expediente_id"],
            current_user["id"],
            ambito_visita,
            nivel_id,
            unidad_id,
        )
    except ValueError as exc:
        opciones_visita_multiunidad = cargar_opciones_visita_multiunidad(
            cur, visita["expediente_id"]
        )
        visita_fotos_exteriores = obtener_fotos_visita(cur, visita_id, "exterior")
        permite_patologias_exteriores = (
            limpiar_texto(visita["tipo_informe"]) == "patologias"
            and limpiar_texto(visita["ambito_patologias"]) in {"exterior", "interior_exterior"}
        )
        visita_data = dict(visita)
        visita_data.update(
            {
                "fecha": fecha,
                "tecnico": tecnico,
                "observaciones_visita": observaciones_visita,
                "ambito_visita": limpiar_texto(ambito_visita) or "edificio_completo",
                "nivel_id": parse_optional_int(nivel_id),
                "unidad_id": parse_optional_int(unidad_id),
            }
        )
        conn.close()
        return render_template(
            request,
            "editar_visita.html",
            {
                "error": str(exc),
                "visita": visita_data,
                "visita_fotos_exteriores": visita_fotos_exteriores,
                "permite_patologias_exteriores": permite_patologias_exteriores,
                "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
                "ambito_visita_options": AMBITO_VISITA_OPTIONS,
                "niveles_visita_options": opciones_visita_multiunidad["niveles"],
                "unidades_visita_options": opciones_visita_multiunidad["unidades_generales"],
                "zonas_comunes_visita_options": opciones_visita_multiunidad["unidades_comunes"],
                "exteriores_visita_options": opciones_visita_multiunidad["unidades_exteriores"],
            },
        )

    cur.execute(
        """
        UPDATE visitas
        SET fecha=?, tecnico=?, observaciones_visita=?, ambito_visita=?, nivel_id=?, unidad_id=?
        WHERE id=?
        """,
        (
            fecha,
            tecnico,
            observaciones_visita,
            ambito_visita_limpio,
            nivel_id_int,
            unidad_id_int,
            visita_id,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{visita['expediente_id']}",
        status_code=303,
    )


# -------------------------------------------------------
# ESTANCIAS
# -------------------------------------------------------


@app.get("/definir-estancias/{visita_id}", response_class=HTMLResponse)
def definir_estancias(
    request: Request,
    visita_id: int,
    unidad_id: int | None = Query(None),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    es_edificio_completo = limpiar_texto(visita["ambito_visita"]) == "edificio_completo"
    unidad_seleccionada = None
    estructura_multiunidad = None
    navegacion_multiunidad = None

    if es_edificio_completo:
        estructura_multiunidad = cargar_estructura_multiunidad(cur, visita["expediente_id"])
        if not estructura_multiunidad["unidades"]:
            es_edificio_completo = False
        if unidad_id is not None:
            unidad_bd = get_owned_unidad(cur, unidad_id, current_user["id"])
            if not unidad_bd or unidad_bd["expediente_id"] != visita["expediente_id"]:
                conn.close()
                raise HTTPException(status_code=404, detail="Unidad no encontrada")
            unidad_seleccionada = next(
                (
                    unidad
                    for unidad in estructura_multiunidad["unidades"]
                    if unidad["id"] == unidad_bd["id"]
                ),
                dict(unidad_bd),
            )
    elif visita["unidad_id"]:
        unidad_bd = get_owned_unidad(cur, visita["unidad_id"], current_user["id"])
        if unidad_bd and unidad_bd["expediente_id"] == visita["expediente_id"]:
            unidad_seleccionada = dict(unidad_bd)

    unidad_muestra_planta = unidad_tiene_varias_plantas(unidad_seleccionada)
    opciones_planta_estancia = (
        opciones_planta_unidad(unidad_seleccionada["numero_plantas"])
        if unidad_muestra_planta
        else []
    )

    estancias_rows = cur.execute(
        """
        SELECT es.*,
               ue.identificador AS unidad_identificador,
               ue.tipo_unidad AS unidad_tipo_unidad,
               ue.uso AS unidad_uso,
               ue.tiene_varias_plantas AS unidad_tiene_varias_plantas,
               ue.numero_plantas AS unidad_numero_plantas,
               ne.nombre_nivel AS nivel_nombre
        FROM estancias es
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE es.visita_id=?
        ORDER BY es.id ASC
        """,
        (visita_id,),
    ).fetchall()

    patologias_por_estancia: dict[int, list[dict]] = {}
    for row in cur.execute(
        """
        SELECT id, estancia_id, patologia
        FROM registros_patologias
        WHERE visita_id=?
        ORDER BY id ASC
        """,
        (visita_id,),
    ).fetchall():
        estancia_id = row["estancia_id"]
        if not estancia_id:
            continue
        patologias_por_estancia.setdefault(estancia_id, []).append(
            {
                "id": row["id"],
                "patologia": limpiar_texto(row["patologia"]),
            }
        )

    estancias = []
    for estancia_row in estancias_rows:
        estancia = dict(estancia_row)
        fotos = obtener_fotos_relacionadas(cur, "estancia_fotos", "estancia_id", estancia["id"])
        for foto in fotos:
            foto["url"] = f"/uploads/{foto['archivo']}"
        estancia["foto_principal_url"] = fotos[0]["url"] if fotos else ""
        estancia["esta_rellena"] = calcular_estancia_rellena(estancia)
        estancia["esta_pendiente"] = not estancia["esta_rellena"]
        estancia["patologias"] = patologias_por_estancia.get(estancia["id"], [])
        estancia["total_patologias"] = len(estancia["patologias"])
        estancia["unidad_tipo_unidad_label"] = etiquetar_opcion(
            estancia.get("unidad_tipo_unidad", ""), TIPO_UNIDAD_LABELS
        )
        estancia["mostrar_planta"] = bool(int(estancia.get("unidad_tiene_varias_plantas") or 0))
        estancias.append(estancia)

    if es_edificio_completo:
        navegacion_multiunidad = preparar_navegacion_estancias_multiunidad(
            estructura_multiunidad,
            estancias,
            visita_id,
            unidad_seleccionada["id"] if unidad_seleccionada else None,
        )

    estancias_visibles = estancias
    estancias_sin_unidad = []
    if es_edificio_completo and unidad_seleccionada:
        estancias_visibles = [
            estancia
            for estancia in estancias
            if estancia.get("unidad_id") == unidad_seleccionada["id"]
        ]
    elif es_edificio_completo:
        estancias_visibles = []
        estancias_sin_unidad = [
            estancia for estancia in estancias if not estancia.get("unidad_id")
        ]

    estancias_visibles.sort(key=lambda estancia: (estancia["esta_rellena"], estancia["id"]))
    estancias_sin_unidad.sort(key=lambda estancia: (estancia["esta_rellena"], estancia["id"]))
    grupos_estructura_estancias = preparar_grupos_estructura_estancias(
        estancias_visibles if estancias_visibles else estancias_sin_unidad
    )

    conn.close()

    return render_template(
        request,
        "definir_estancias.html",
        {
            "visita": visita,
            "estancias": estancias_visibles,
            "estancias_sin_unidad": estancias_sin_unidad,
            "grupos_estructura_estancias": grupos_estructura_estancias,
            "hay_estructura_estancias": bool(grupos_estructura_estancias),
            "objeto_visita_label": describir_objeto_visita(visita),
            "mostrar_navegacion_multiunidad": es_edificio_completo,
            "navegacion_multiunidad": navegacion_multiunidad,
            "unidad_seleccionada": unidad_seleccionada,
            "unidad_muestra_planta": unidad_muestra_planta,
            "opciones_planta_estancia": opciones_planta_estancia,
        },
    )


@app.post("/generar-estancias-base")
def generar_estancias_base(
    request: Request,
    visita_id: int = Form(...),
    num_dormitorios: int = Form(0),
    num_banos: int = Form(0),
    num_aseos: int = Form(0),
    num_salones: int = Form(0),
    num_cocinas: int = Form(0),
    num_escaleras: int = Form(0),
    num_distribuidores: int = Form(0),
    incluir_salon: str = Form("no"),
    incluir_cocina: str = Form("no"),
    incluir_pasillo: str = Form("no"),
    incluir_terraza: str = Form("no"),
    planta: str = Form(""),
    unidad_id_objetivo: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    unidad_id_estancia = visita["unidad_id"] if visita["unidad_id"] else None
    unidad_id_objetivo_int = parse_optional_int(unidad_id_objetivo)
    if unidad_id_objetivo_int:
        unidad = get_owned_unidad(cur, unidad_id_objetivo_int, current_user["id"])
        if not unidad or unidad["expediente_id"] != visita["expediente_id"]:
            conn.close()
            raise HTTPException(status_code=400, detail="La unidad seleccionada no es válida.")
        unidad_id_estancia = unidad_id_objetivo_int
    elif unidad_id_estancia:
        unidad = get_owned_unidad(cur, unidad_id_estancia, current_user["id"])
    else:
        unidad = None
    es_edificio_completo = limpiar_texto(visita["ambito_visita"]) == "edificio_completo"
    planta_estancia = limpiar_texto(planta) if unidad_tiene_varias_plantas(unidad) else ""

    def crear_si_no_existe(nombre: str, tipo_estancia: str):
        if es_edificio_completo:
            existe = cur.execute(
                """
                SELECT 1
                FROM estancias
                WHERE visita_id=? AND IFNULL(unidad_id, 0)=IFNULL(?, 0) AND nombre=?
                LIMIT 1
                """,
                (visita_id, unidad_id_estancia, nombre),
            ).fetchone()
        else:
            existe = cur.execute(
                """
                SELECT 1
                FROM estancias
                WHERE visita_id=? AND nombre=?
                LIMIT 1
                """,
                (visita_id, nombre),
            ).fetchone()
        if existe:
            return
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones,
                unidad_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, nombre, tipo_estancia, "", planta_estancia, "", "", "", "", unidad_id_estancia),
        )

    num_salones = max(parsear_entero_positivo(num_salones), 1 if incluir_salon == "si" else 0)
    num_cocinas = max(parsear_entero_positivo(num_cocinas), 1 if incluir_cocina == "si" else 0)
    num_pasillos = 1 if incluir_pasillo == "si" else 0
    num_terrazas = 1 if incluir_terraza == "si" else 0

    for i in range(1, num_salones + 1):
        crear_si_no_existe("Salón" if i == 1 else f"Salón {i}", "Salón")
    for i in range(1, num_cocinas + 1):
        crear_si_no_existe("Cocina" if i == 1 else f"Cocina {i}", "Cocina")
    for i in range(1, parsear_entero_positivo(num_dormitorios) + 1):
        crear_si_no_existe(f"Dormitorio {i}", "Dormitorio")
    for i in range(1, parsear_entero_positivo(num_banos) + 1):
        crear_si_no_existe(f"Baño {i}", "Baño")
    for i in range(1, parsear_entero_positivo(num_aseos) + 1):
        crear_si_no_existe("Aseo" if i == 1 else f"Aseo {i}", "Aseo")
    for i in range(1, parsear_entero_positivo(num_escaleras) + 1):
        crear_si_no_existe("Escalera" if i == 1 else f"Escalera {i}", "Escalera")
    for i in range(1, parsear_entero_positivo(num_distribuidores) + 1):
        crear_si_no_existe("Distribuidor" if i == 1 else f"Distribuidor {i}", "Distribuidor")
    for i in range(1, num_pasillos + 1):
        crear_si_no_existe("Pasillo" if i == 1 else f"Pasillo {i}", "Pasillo")
    for i in range(1, num_terrazas + 1):
        crear_si_no_existe("Terraza" if i == 1 else f"Terraza {i}", "Terraza")

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/definir-estancias/{visita_id}?unidad_id={unidad_id_estancia}"
            if es_edificio_completo and unidad_id_estancia
            else f"/definir-estancias/{visita_id}"
        ),
        status_code=303,
    )


@app.post("/guardar-estancia")
def guardar_estancia(
    request: Request,
    visita_id: int = Form(...),
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    ventilacion: str = Form(""),
    planta: str = Form(""),
    acabado_pavimento: str = Form(""),
    acabado_paramento: str = Form(""),
    acabado_techo: str = Form(""),
    observaciones: str = Form(""),
    unidad_id_objetivo: str = Form(""),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    unidad_id_estancia = None
    unidad_id_objetivo_int = parse_optional_int(unidad_id_objetivo)
    unidad_referencia_id = unidad_id_objetivo_int or visita["unidad_id"]
    unidad = None
    if unidad_referencia_id:
        unidad = get_owned_unidad(cur, unidad_referencia_id, current_user["id"])
        if not unidad or unidad["expediente_id"] != visita["expediente_id"]:
            conn.close()
            raise HTTPException(status_code=400, detail="La unidad asociada a la visita no es válida.")
        unidad_id_estancia = unidad_referencia_id
    planta_estancia = limpiar_texto(planta) if unidad_tiene_varias_plantas(unidad) else ""

    cur.execute(
        """
        INSERT INTO estancias
        (
            visita_id,
            nombre,
            tipo_estancia,
            ventilacion,
            planta,
            acabado_pavimento,
            acabado_paramento,
            acabado_techo,
            observaciones,
            unidad_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            nombre,
            tipo_estancia,
            limpiar_texto(ventilacion),
            planta_estancia,
            limpiar_texto(acabado_pavimento),
            limpiar_texto(acabado_paramento),
            limpiar_texto(acabado_techo),
            observaciones,
            unidad_id_estancia,
        ),
    )
    nueva_estancia_id = cur.lastrowid

    propagar_acabados_estancia(
        cur,
        visita["expediente_id"],
        nueva_estancia_id,
        {
            "acabado_pavimento": "",
            "acabado_paramento": "",
            "acabado_techo": "",
        },
        {
            "acabado_pavimento": acabado_pavimento,
            "acabado_paramento": acabado_paramento,
            "acabado_techo": acabado_techo,
        },
    )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    post_save_url = f"/editar-estancia/{nueva_estancia_id}?post_save=1"
    if unidad_id_estancia and limpiar_texto(visita["ambito_visita"]) == "edificio_completo":
        post_save_url += f"&unidad_id_contexto={unidad_id_estancia}"

    return RedirectResponse(
        url=post_save_url,
        status_code=303,
    )


@app.get("/editar-estancia/{estancia_id}", response_class=HTMLResponse)
def editar_estancia(
    request: Request,
    estancia_id: int,
    unidad_id_contexto: int | None = Query(None),
    next: str = Query(""),
    post_save: bool = Query(False),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")
    estancia = dict(estancia)
    fotos = obtener_fotos_relacionadas(cur, "estancia_fotos", "estancia_id", estancia_id)
    for foto in fotos:
        foto["url"] = f"/uploads/{foto['archivo']}"
    estancia["fotos"] = fotos
    estancia_tiene_varias_plantas = bool(
        int(
            estancia.get("estancia_unidad_tiene_varias_plantas")
            or estancia.get("visita_unidad_tiene_varias_plantas")
            or 0
        )
    )
    estancia_numero_plantas = (
        estancia.get("estancia_unidad_numero_plantas")
        or estancia.get("visita_unidad_numero_plantas")
        or 1
    )
    modo_inspector = preparar_modo_inspector_estancias(
        cur,
        estancia["visita_id"],
        estancia_id,
        estancia["expediente_id"],
    )

    conn.close()

    return render_template(
        request,
        "editar_estancia.html",
        {
            "estancia": estancia,
            "unidad_id_contexto": unidad_id_contexto,
            "next_url": normalizar_redirect_interno(next),
            "post_save": post_save,
            "modo_inspector": modo_inspector,
            "mostrar_planta_estancia": estancia_tiene_varias_plantas,
            "opciones_planta_estancia": opciones_planta_unidad(estancia_numero_plantas)
            if estancia_tiene_varias_plantas
            else [],
        },
    )


@app.post("/actualizar-estancia/{estancia_id}")
def actualizar_estancia(
    request: Request,
    estancia_id: int,
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    ventilacion: str = Form(""),
    planta: str = Form(""),
    acabado_pavimento: str = Form(""),
    acabado_paramento: str = Form(""),
    acabado_techo: str = Form(""),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
    unidad_id_contexto: str = Form(""),
    next: str = Form(""),
    redirect_after_save: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")

    visita_id = estancia["visita_id"]
    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    acabados_anteriores = {
        "acabado_pavimento": estancia["acabado_pavimento"],
        "acabado_paramento": estancia["acabado_paramento"],
        "acabado_techo": estancia["acabado_techo"],
    }
    acabados_nuevos = {
        "acabado_pavimento": acabado_pavimento,
        "acabado_paramento": acabado_paramento,
        "acabado_techo": acabado_techo,
    }
    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        nombre,
    )
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "estancia_fotos",
            "estancia_id",
            estancia_id,
            nombres_fotos,
        )

    permite_editar_planta = bool(
        int(
            estancia["estancia_unidad_tiene_varias_plantas"]
            or estancia["visita_unidad_tiene_varias_plantas"]
            or 0
        )
    )
    planta_final = limpiar_texto(planta) if permite_editar_planta else estancia["planta"]

    cur.execute(
        """
        UPDATE estancias
        SET nombre=?, tipo_estancia=?, ventilacion=?, planta=?,
            acabado_pavimento=?, acabado_paramento=?, acabado_techo=?, observaciones=?
        WHERE id=?
        """,
        (
            nombre,
            tipo_estancia,
            limpiar_texto(ventilacion),
            planta_final,
            limpiar_texto(acabado_pavimento),
            limpiar_texto(acabado_paramento),
            limpiar_texto(acabado_techo),
            observaciones,
            estancia_id,
        ),
    )

    propagar_acabados_estancia(
        cur,
        estancia["expediente_id"],
        estancia_id,
        acabados_anteriores,
        acabados_nuevos,
    )

    conn.commit()
    conn.close()

    unidad_id_contexto_int = parse_optional_int(unidad_id_contexto)
    next_url = normalizar_redirect_interno(redirect_after_save) or normalizar_redirect_interno(next)

    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    post_save_url = f"/editar-estancia/{estancia_id}?post_save=1"
    if unidad_id_contexto_int:
        post_save_url += f"&unidad_id_contexto={unidad_id_contexto_int}"
    return RedirectResponse(
        url=post_save_url,
        status_code=303,
    )


@app.post("/borrar-estancia/{estancia_id}")
def borrar_estancia(
    request: Request,
    estancia_id: int,
    unidad_id_contexto: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")

    visita_id = estancia["visita_id"]
    unidad_id_contexto_int = parse_optional_int(unidad_id_contexto)

    borrar_fotos_relacionadas(cur, "estancia_fotos", "estancia_id", estancia_id)
    cur.execute("DELETE FROM estancias WHERE id=?", (estancia_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/definir-estancias/{visita_id}?unidad_id={unidad_id_contexto_int}"
            if unidad_id_contexto_int
            and limpiar_texto(estancia["ambito_visita"]) == "edificio_completo"
            else f"/definir-estancias/{visita_id}"
        ),
        status_code=303,
    )


@app.post("/borrar-foto-estancia/{foto_id}")
def borrar_foto_estancia(
    request: Request,
    foto_id: int,
    unidad_id_contexto: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    foto = cur.execute(
        """
        SELECT ef.*, es.id AS estancia_real_id
        FROM estancia_fotos ef
        JOIN estancias es ON ef.estancia_id = es.id
        JOIN visitas v ON es.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE ef.id=? AND e.owner_user_id=?
        """,
        (foto_id, current_user["id"]),
    ).fetchone()
    require_row(foto, "Foto no encontrada")

    borrar_foto_si_existe(foto["archivo"])
    cur.execute("DELETE FROM estancia_fotos WHERE id=?", (foto_id,))
    conn.commit()
    conn.close()
    unidad_id_contexto_int = parse_optional_int(unidad_id_contexto)
    return RedirectResponse(
        url=(
            f"/editar-estancia/{foto['estancia_id']}?unidad_id_contexto={unidad_id_contexto_int}"
            if unidad_id_contexto_int
            else f"/editar-estancia/{foto['estancia_id']}"
        ),
        status_code=303,
    )


# -------------------------------------------------------
# CLIMATOLOGÍA
# -------------------------------------------------------


@app.post("/registrar-climatologia-visita/{expediente_id}")
async def registrar_climatologia_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Form(None),
    fecha: str = Form(""),
    tecnico: str = Form(""),
    observaciones_visita: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    ubicacion_referencia: str = Form(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_final = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_final = (
        limpiar_texto(tecnico)
        or f"{current_user['nombre']} {current_user['apellido1']}".strip()
        or current_user["username"]
    )

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?
            WHERE id=?
            """,
            (fecha_final, tecnico_final, observaciones_visita, visita_id),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_final,
            tecnico_final,
            observaciones_visita,
        )

    clima_error = ""
    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=latitud,
            longitud=longitud,
            municipio=expediente["direccion"],
            ubicacion_label=limpiar_texto(ubicacion_referencia) or expediente["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        clima_error = "No se pudo obtener la climatología en este momento. La visita sigue guardada y puedes intentarlo de nuevo."

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/nueva-visita/{expediente_id}?visita_id={visita_id}"
            + (
                f"&clima_error={quote_plus(clima_error)}"
                if clima_error
                else ""
            )
        ),
        status_code=303,
    )


@app.post("/anadir-climatologia/{visita_id}")
async def anadir_climatologia(request: Request, visita_id: int):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    clima_error = ""
    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=None,
            longitud=None,
            municipio=visita["direccion"],
            ubicacion_label=visita["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        clima_error = "No se pudo obtener la climatología en este momento. La visita sigue disponible y puedes intentarlo de nuevo."

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}"
            + (
                f"&clima_error={quote_plus(clima_error)}"
                if clima_error
                else ""
            )
        ),
        status_code=303,
    )


@app.post("/api/climatologia")
async def api_climatologia(
    request: Request,
    expediente_id: int = Form(...),
    visita_id: int | None = Form(None),
    fecha: str = Form(""),
    tecnico: str = Form(""),
    observaciones_visita: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    municipio: str = Form(""),
    ubicacion_referencia: str = Form(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_final = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_final = (
        limpiar_texto(tecnico)
        or f"{current_user['nombre']} {current_user['apellido1']}".strip()
        or current_user["username"]
    )
    observaciones_finales = observaciones_visita or ""

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?
            WHERE id=?
            """,
            (fecha_final, tecnico_final, observaciones_finales, visita_id),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_final,
            tecnico_final,
            observaciones_finales,
        )

    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=latitud,
            longitud=longitud,
            municipio=municipio or expediente["direccion"],
            ubicacion_label=limpiar_texto(ubicacion_referencia) or municipio or expediente["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
        conn.commit()
        conn.close()

        return JSONResponse(
            {
                "ok": True,
                "visita_id": visita_id,
                "clima": {
                    "ubicacion": climatologia.get("ubicacion"),
                    "resumen": climatologia.get("resumen"),
                    "resumen_diario": climatologia.get("resumen_diario") or [],
                },
            }
        )
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        conn.commit()
        conn.close()
        return JSONResponse(
            {
                "ok": False,
                "visita_id": visita_id,
                "clima_error": "No se pudo obtener la climatología. Puedes seguir trabajando y volver a intentarlo.",
            },
            status_code=200,
        )


# -------------------------------------------------------
# PATOLOGÍAS
# -------------------------------------------------------


@app.get("/registrar-patologias/{visita_id}", response_class=HTMLResponse)
def registrar_patologias(
    request: Request,
    visita_id: int,
    estancia_id: int | None = Query(None),
    next: str = Query(""),
    guardado: bool = Query(False),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    estancia_seleccionada = None
    estancia_id_param = estancia_id

    estancias = cur.execute(
        """
        SELECT es.*,
               ue.identificador AS identificador_unidad_estancia,
               ne.nombre_nivel AS nombre_nivel_estancia
        FROM estancias es
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE es.visita_id=?
        ORDER BY es.id ASC
        """,
        (visita_id,),
    ).fetchall()
    if estancia_id is None and estancias:
        estancia_seleccionada = estancias[0]
        estancia_id = estancia_seleccionada["id"]
    if estancia_id is not None:
        validar_estancia_para_visita(cur, visita, estancia_id)
        estancia_seleccionada = get_owned_estancia(cur, estancia_id, current_user["id"])
        if not estancia_seleccionada or estancia_seleccionada["visita_id"] != visita_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Estancia no encontrada")

    registros = cur.execute(
        """
        SELECT rp.*, e.nombre AS estancia_nombre,
               ue.identificador AS identificador_unidad_estancia,
               ne.nombre_nivel AS nombre_nivel_estancia
        FROM registros_patologias rp
        LEFT JOIN estancias e ON rp.estancia_id = e.id
        LEFT JOIN unidades_expediente ue ON e.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE rp.visita_id=?
        ORDER BY rp.id DESC
        """,
        (visita_id,),
    ).fetchall()
    registros = [
        enriquecer_registro_con_fotos(
            cur,
            registro,
            "registro_patologia_fotos",
            "registro_id",
            "foto",
        )
        for registro in registros
    ]
    registros_estancia_seleccionada = (
        [
            registro
            for registro in registros
            if registro["estancia_id"] == estancia_seleccionada["id"]
        ]
        if estancia_seleccionada
        else []
    )
    registros_exteriores = cur.execute(
        """
        SELECT *
        FROM registros_patologias_exteriores
        WHERE visita_id=?
        ORDER BY id DESC
        """,
        (visita_id,),
    ).fetchall()
    registros_exteriores = [
        enriquecer_registro_con_fotos(
            cur,
            registro,
            "registro_patologia_exterior_fotos",
            "registro_id",
            "foto",
        )
        for registro in registros_exteriores
    ]

    clima, clima_detalle = obtener_climatologia_guardada(cur, visita_id)

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()
    mapas_patologia = preparar_mapas_patologia(cur, visita_id)

    objeto_visita_label = describir_objeto_visita(visita)
    modo_inspector = (
        preparar_modo_inspector_estancias(
            cur,
            visita_id,
            estancia_seleccionada["id"],
            visita["expediente_id"],
        )
        if estancia_id_param is not None and estancia_seleccionada
        else None
    )

    conn.close()

    return render_template(
        request,
        "registrar_patologias.html",
        {
            "visita": visita,
            "estancias": estancias,
            "registros": registros,
            "registros_exteriores": registros_exteriores,
            "clima": clima,
            "clima_detalle": clima_detalle,
            "patologias": patologias,
            "objeto_visita_label": objeto_visita_label,
            "mapas_patologia": mapas_patologia,
            "ambito_mapa_options": AMBITO_MAPA_OPTIONS,
            "gravedad_cuadrante_labels": GRAVEDAD_CUADRANTE_LABELS,
            "estancia_seleccionada": estancia_seleccionada,
            "registros_estancia_seleccionada": registros_estancia_seleccionada,
            "modo_inspector": modo_inspector,
            "next_url": normalizar_redirect_interno(next),
            "guardado": guardado,
        },
    )


@app.post("/guardar-mapa-patologia")
def guardar_mapa_patologia(
    request: Request,
    visita_id: int = Form(...),
    titulo: str = Form(...),
    descripcion: str = Form(""),
    ambito_mapa: str = Form(""),
    filas: int = Form(4),
    columnas: int = Form(4),
    imagen_base: UploadFile | None = File(None),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    titulo_limpio = limpiar_texto(titulo)
    if not titulo_limpio:
        conn.close()
        raise HTTPException(status_code=400, detail="El título del mapa es obligatorio")
    filas_seguras = max(int(filas or 0), 1)
    columnas_seguras = max(int(columnas or 0), 1)
    nombre_imagen = guardar_upload_si_existe(imagen_base)

    cur.execute(
        """
        INSERT INTO mapas_patologia (
            visita_id, titulo, descripcion, ambito_mapa, filas, columnas, imagen_base, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            titulo_limpio,
            limpiar_texto(descripcion),
            limpiar_texto(ambito_mapa) or limpiar_texto(visita["ambito_visita"]),
            filas_seguras,
            columnas_seguras,
            nombre_imagen,
            limpiar_texto(observaciones),
        ),
    )
    mapa_id = cur.lastrowid
    generar_cuadrantes_mapa(cur, mapa_id, filas_seguras, columnas_seguras)
    if nombre_imagen:
        generar_imagen_anotada_mapa_patologia(
            nombre_imagen,
            filas_seguras,
            columnas_seguras,
        )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/registrar-patologias/{visita_id}", status_code=303)


@app.get("/editar-mapa-patologia/{mapa_id}", response_class=HTMLResponse)
def editar_mapa_patologia(request: Request, mapa_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    mapa = get_owned_mapa_patologia(cur, mapa_id, current_user["id"])
    require_row(mapa, "Mapa no encontrado")
    mapa = dict(mapa)
    mapa["imagen_base_url"] = (
        f"/uploads/{mapa['imagen_base']}" if mapa.get("imagen_base") else ""
    )
    mapa["imagen_mapa_url"] = construir_imagen_mapa_url(mapa.get("imagen_base"))
    cuadrantes = cur.execute(
        """
        SELECT *
        FROM cuadrantes_mapa_patologia
        WHERE mapa_id=?
        ORDER BY id ASC
        """,
        (mapa_id,),
    ).fetchall()
    objeto_visita_label = describir_objeto_visita(mapa)
    conn.close()

    return render_template(
        request,
        "editar_mapa_patologia.html",
        {
            "mapa": mapa,
            "cuadrantes": cuadrantes,
            "ambito_mapa_options": AMBITO_MAPA_OPTIONS,
            "objeto_visita_label": objeto_visita_label,
        },
    )


@app.post("/actualizar-mapa-patologia/{mapa_id}")
def actualizar_mapa_patologia(
    request: Request,
    mapa_id: int,
    titulo: str = Form(...),
    descripcion: str = Form(""),
    ambito_mapa: str = Form(""),
    filas: int = Form(4),
    columnas: int = Form(4),
    observaciones: str = Form(""),
    eliminar_imagen_base_actual: str = Form("no"),
    imagen_base: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    mapa = get_owned_mapa_patologia(cur, mapa_id, current_user["id"])
    require_row(mapa, "Mapa no encontrado")

    titulo_limpio = limpiar_texto(titulo)
    if not titulo_limpio:
        conn.close()
        imagen_url = (
            f"/uploads/{mapa['imagen_base']}" if mapa.get("imagen_base") else ""
        )
        return render_template(
            request,
            "editar_mapa_patologia.html",
            {
                "error": "El título del mapa es obligatorio.",
                "mapa": {
                    **dict(mapa),
                    "titulo": titulo_limpio,
                    "descripcion": descripcion,
                    "ambito_mapa": ambito_mapa,
                    "filas": filas,
                    "columnas": columnas,
                    "observaciones": observaciones,
                    "imagen_base_url": imagen_url,
                    "imagen_mapa_url": imagen_url,
                },
                "cuadrantes": cur.execute(
                    "SELECT * FROM cuadrantes_mapa_patologia WHERE mapa_id=? ORDER BY id ASC",
                    (mapa_id,),
                ).fetchall(),
                "ambito_mapa_options": AMBITO_MAPA_OPTIONS,
                "objeto_visita_label": describir_objeto_visita(mapa),
            },
            status_code=400,
        )
    filas_seguras = max(int(filas or 0), 1)
    columnas_seguras = max(int(columnas or 0), 1)
    imagen_base_actual = mapa["imagen_base"]

    total_cuadrantes_contenido = cur.execute(
        """
        SELECT COUNT(*)
        FROM cuadrantes_mapa_patologia
        WHERE mapa_id=?
          AND (
              TRIM(IFNULL(descripcion, '')) <> ''
              OR TRIM(IFNULL(patologia_detectada, '')) <> ''
              OR TRIM(IFNULL(gravedad, '')) <> ''
              OR TRIM(IFNULL(foto_detalle, '')) <> ''
              OR TRIM(IFNULL(observaciones, '')) <> ''
          )
        """,
        (mapa_id,),
    ).fetchone()[0]

    if (filas_seguras != mapa["filas"] or columnas_seguras != mapa["columnas"]) and total_cuadrantes_contenido:
        conn.close()
        imagen_url = (
            f"/uploads/{mapa['imagen_base']}" if mapa.get("imagen_base") else ""
        )
        return render_template(
            request,
            "editar_mapa_patologia.html",
            {
                "error": "No se pueden cambiar filas o columnas cuando ya hay cuadrantes con contenido.",
                "mapa": {
                    **dict(mapa),
                    "titulo": titulo_limpio,
                    "descripcion": descripcion,
                    "ambito_mapa": ambito_mapa,
                    "filas": filas_seguras,
                    "columnas": columnas_seguras,
                    "observaciones": observaciones,
                    "imagen_base_url": imagen_url,
                    "imagen_mapa_url": imagen_url,
                },
                "cuadrantes": cur.execute(
                    "SELECT * FROM cuadrantes_mapa_patologia WHERE mapa_id=? ORDER BY id ASC",
                    (mapa_id,),
                ).fetchall(),
                "ambito_mapa_options": AMBITO_MAPA_OPTIONS,
                "objeto_visita_label": describir_objeto_visita(mapa),
            },
            status_code=400,
        )

    if eliminar_imagen_base_actual == "si" and imagen_base_actual:
        borrar_imagen_anotada_mapa_si_existe(imagen_base_actual)
        borrar_foto_si_existe(imagen_base_actual)
        imagen_base_actual = None

    nueva_imagen = guardar_upload_si_existe(imagen_base)
    if nueva_imagen:
        if imagen_base_actual:
            borrar_imagen_anotada_mapa_si_existe(imagen_base_actual)
            borrar_foto_si_existe(imagen_base_actual)
        imagen_base_actual = nueva_imagen

    cur.execute(
        """
        UPDATE mapas_patologia
        SET titulo=?, descripcion=?, ambito_mapa=?, filas=?, columnas=?, imagen_base=?, observaciones=?
        WHERE id=?
        """,
        (
            titulo_limpio,
            limpiar_texto(descripcion),
            limpiar_texto(ambito_mapa),
            filas_seguras,
            columnas_seguras,
            imagen_base_actual,
            limpiar_texto(observaciones),
            mapa_id,
        ),
    )

    if filas_seguras != mapa["filas"] or columnas_seguras != mapa["columnas"]:
        cur.execute("DELETE FROM cuadrantes_mapa_patologia WHERE mapa_id=?", (mapa_id,))
        generar_cuadrantes_mapa(cur, mapa_id, filas_seguras, columnas_seguras)

    if imagen_base_actual:
        generar_imagen_anotada_mapa_patologia(
            imagen_base_actual,
            filas_seguras,
            columnas_seguras,
        )

    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/registrar-patologias/{mapa['visita_id']}",
        status_code=303,
    )


@app.post("/borrar-mapa-patologia/{mapa_id}")
def borrar_mapa_patologia(request: Request, mapa_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    mapa = get_owned_mapa_patologia(cur, mapa_id, current_user["id"])
    require_row(mapa, "Mapa no encontrado")

    if mapa["imagen_base"]:
        borrar_imagen_anotada_mapa_si_existe(mapa["imagen_base"])
        borrar_foto_si_existe(mapa["imagen_base"])

    fotos_cuadrantes = cur.execute(
        """
        SELECT foto_detalle
        FROM cuadrantes_mapa_patologia
        WHERE mapa_id=? AND foto_detalle IS NOT NULL AND foto_detalle <> ''
        """,
        (mapa_id,),
    ).fetchall()
    for foto in fotos_cuadrantes:
        borrar_foto_si_existe(foto["foto_detalle"])

    cur.execute("DELETE FROM cuadrantes_mapa_patologia WHERE mapa_id=?", (mapa_id,))
    cur.execute("DELETE FROM mapas_patologia WHERE id=?", (mapa_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/registrar-patologias/{mapa['visita_id']}",
        status_code=303,
    )


@app.get(
    "/editar-cuadrante-mapa-patologia/{cuadrante_id}",
    response_class=HTMLResponse,
)
def editar_cuadrante_mapa_patologia(request: Request, cuadrante_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    cuadrante = get_owned_cuadrante_mapa_patologia(cur, cuadrante_id, current_user["id"])
    require_row(cuadrante, "Cuadrante no encontrado")
    cuadrante = enriquecer_registro_con_fotos(
        cur,
        cuadrante,
        "cuadrante_mapa_patologia_fotos",
        "cuadrante_id",
        "foto_detalle",
    )
    mapa = get_owned_mapa_patologia(cur, cuadrante["mapa_id"], current_user["id"])
    require_row(mapa, "Mapa no encontrado")
    patologias_vinculables, candidatos_por_id = obtener_registros_patologia_vinculables(
        cur, mapa["visita_id"]
    )
    patologia_vinculada = resolver_patologia_vinculada(
        candidatos_por_id,
        cuadrante["patologia_id"],
        cuadrante["patologia_detectada"],
    )
    objeto_visita_label = describir_objeto_visita(mapa)
    conn.close()

    return render_template(
        request,
        "editar_cuadrante_mapa_patologia.html",
        {
            "cuadrante": cuadrante,
            "mapa": mapa,
            "gravedad_cuadrante_options": GRAVEDAD_CUADRANTE_OPTIONS,
            "patologias_vinculables": patologias_vinculables,
            "patologia_ref_actual": patologia_vinculada["value"] if patologia_vinculada else "",
            "objeto_visita_label": objeto_visita_label,
        },
    )


@app.post("/actualizar-cuadrante-mapa-patologia/{cuadrante_id}")
def actualizar_cuadrante_mapa_patologia(
    request: Request,
    cuadrante_id: int,
    descripcion: str = Form(""),
    patologia_detectada: str = Form(""),
    patologia_ref: str = Form(""),
    gravedad: str = Form(""),
    observaciones: str = Form(""),
    fotos_detalle: list[UploadFile] = File([]),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    cuadrante = get_owned_cuadrante_mapa_patologia(cur, cuadrante_id, current_user["id"])
    require_row(cuadrante, "Cuadrante no encontrado")
    mapa = get_owned_mapa_patologia(cur, cuadrante["mapa_id"], current_user["id"])
    require_row(mapa, "Mapa no encontrado")
    visita = get_owned_visita(cur, mapa["visita_id"], current_user["id"])
    require_row(visita, "Visita no encontrada")
    patologia_id = None
    patologia_detectada_limpia = limpiar_texto(patologia_detectada)
    patologia_ref_limpia = limpiar_texto(patologia_ref)
    if patologia_ref_limpia:
        _, candidatos_por_id = obtener_registros_patologia_vinculables(cur, mapa["visita_id"])
        try:
            _, patologia_id_texto = patologia_ref_limpia.split(":", 1)
            patologia_id = int(patologia_id_texto)
        except (ValueError, AttributeError):
            conn.close()
            raise HTTPException(status_code=400, detail="Patología vinculada no válida")
        patologia_vinculada = resolver_patologia_vinculada(
            candidatos_por_id,
            patologia_id,
            "",
        )
        if not patologia_vinculada or patologia_vinculada["value"] != patologia_ref_limpia:
            conn.close()
            raise HTTPException(status_code=400, detail="Patología vinculada no válida")
        if not patologia_detectada_limpia:
            patologia_detectada_limpia = patologia_vinculada["patologia"]

    nombres_fotos = guardar_uploads_contextuales(
        fotos_detalle,
        visita["numero_expediente"],
        "mapa",
        cuadrante["codigo_cuadrante"],
    )
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "cuadrante_mapa_patologia_fotos",
            "cuadrante_id",
            cuadrante_id,
            nombres_fotos,
        )

    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET descripcion=?, patologia_detectada=?, patologia_id=?, gravedad=?, foto_detalle=?, observaciones=?
        WHERE id=?
        """,
        (
            limpiar_texto(descripcion),
            patologia_detectada_limpia,
            patologia_id,
            limpiar_texto(gravedad),
            cuadrante["foto_detalle"],
            limpiar_texto(observaciones),
            cuadrante_id,
        ),
    )
    sincronizar_foto_principal(
        cur,
        "cuadrantes_mapa_patologia",
        "id",
        "foto_detalle",
        cuadrante_id,
        "cuadrante_mapa_patologia_fotos",
        "cuadrante_id",
    )

    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/registrar-patologias/{cuadrante['visita_id']}",
        status_code=303,
    )


@app.get(
    "/crear-patologia-desde-cuadrante/{cuadrante_id}",
    response_class=HTMLResponse,
)
def crear_patologia_desde_cuadrante(request: Request, cuadrante_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    cuadrante = get_owned_cuadrante_mapa_patologia(cur, cuadrante_id, current_user["id"])
    require_row(cuadrante, "Cuadrante no encontrado")
    mapa = get_owned_mapa_patologia(cur, cuadrante["mapa_id"], current_user["id"])
    require_row(mapa, "Mapa no encontrado")
    visita = get_owned_visita(cur, mapa["visita_id"], current_user["id"])
    require_row(visita, "Visita no encontrada")
    es_exterior = mapa_patologia_es_exterior(visita, mapa)
    estancias = []
    if not es_exterior:
        estancias = cur.execute(
            "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
            (visita["id"],),
        ).fetchall()
    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()
    objeto_visita_label = describir_objeto_visita(visita)
    conn.close()

    return render_template(
        request,
        "crear_patologia_desde_cuadrante.html",
        {
            "cuadrante": cuadrante,
            "mapa": mapa,
            "visita": visita,
            "estancias": estancias,
            "patologias": patologias,
            "objeto_visita_label": objeto_visita_label,
            "modo_patologia": "exterior" if es_exterior else "interior",
        },
    )


@app.post("/crear-patologia-desde-cuadrante/{cuadrante_id}")
def guardar_patologia_desde_cuadrante(
    request: Request,
    cuadrante_id: int,
    estancia_id: int | None = Form(None),
    elemento: str = Form(""),
    localizacion_dano: str = Form(""),
    zona_exterior: str = Form(""),
    elemento_exterior: str = Form(""),
    localizacion_dano_exterior: str = Form(""),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    cuadrante = get_owned_cuadrante_mapa_patologia(cur, cuadrante_id, current_user["id"])
    require_row(cuadrante, "Cuadrante no encontrado")
    mapa = get_owned_mapa_patologia(cur, cuadrante["mapa_id"], current_user["id"])
    require_row(mapa, "Mapa no encontrado")
    visita = get_owned_visita(cur, mapa["visita_id"], current_user["id"])
    require_row(visita, "Visita no encontrada")

    contexto_base = [
        visita["numero_expediente"],
        "desde",
        cuadrante["codigo_cuadrante"],
    ]
    nombres_foto: list[str] = []
    nombre_foto = None
    es_exterior = mapa_patologia_es_exterior(visita, mapa)
    patologia_limpia = limpiar_texto(patologia)
    observaciones_base = limpiar_texto(cuadrante["descripcion"])
    observaciones_limpias = limpiar_texto(observaciones)
    if observaciones_base and observaciones_limpias:
        observaciones_limpias = f"{observaciones_base}\n{observaciones_limpias}"
    elif observaciones_base and not observaciones_limpias:
        observaciones_limpias = observaciones_base

    if es_exterior:
        nombres_foto = guardar_uploads_contextuales(
            fotos,
            *contexto_base,
            zona_exterior or "exterior",
            elemento_exterior or "elemento",
        )
        nombre_foto = nombres_foto[0] if nombres_foto else None
        cur.execute(
            """
            INSERT INTO registros_patologias_exteriores (
                visita_id,
                zona_exterior,
                elemento_exterior,
                localizacion_dano_exterior,
                patologia,
                observaciones,
                foto
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita["id"],
                limpiar_texto(zona_exterior),
                limpiar_texto(elemento_exterior),
                limpiar_texto(localizacion_dano_exterior) or cuadrante["codigo_cuadrante"],
                patologia_limpia,
                observaciones_limpias,
                nombre_foto,
            ),
        )
        nuevo_registro_id = cur.lastrowid
        if nombres_foto:
            insertar_fotos_relacionadas(
                cur,
                "registro_patologia_exterior_fotos",
                "registro_id",
                nuevo_registro_id,
                nombres_foto,
            )
    else:
        if not estancia_id:
            conn.close()
            raise HTTPException(status_code=400, detail="Debes seleccionar una estancia")
        validar_estancia_para_visita(cur, visita, estancia_id)
        estancia = cur.execute(
            "SELECT nombre FROM estancias WHERE id=?",
            (estancia_id,),
        ).fetchone()
        nombres_foto = guardar_uploads_contextuales(
            fotos,
            *contexto_base,
            estancia["nombre"] if estancia else "estancia",
            elemento or "elemento",
        )
        nombre_foto = nombres_foto[0] if nombres_foto else None
        cur.execute(
            """
            INSERT INTO registros_patologias
            (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita["id"],
                estancia_id,
                limpiar_texto(elemento),
                limpiar_texto(localizacion_dano) or cuadrante["codigo_cuadrante"],
                patologia_limpia,
                observaciones_limpias,
                nombre_foto,
            ),
        )
        nuevo_registro_id = cur.lastrowid
        if nombres_foto:
            insertar_fotos_relacionadas(
                cur,
                "registro_patologia_fotos",
                "registro_id",
                nuevo_registro_id,
                nombres_foto,
            )

    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET patologia_id=?, patologia_detectada=?
        WHERE id=?
        """,
        (nuevo_registro_id, patologia_limpia, cuadrante_id),
    )

    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/editar-cuadrante-mapa-patologia/{cuadrante_id}",
        status_code=303,
    )


@app.post("/borrar-cuadrante-mapa-patologia/{cuadrante_id}")
def borrar_cuadrante_mapa_patologia(request: Request, cuadrante_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    cuadrante = get_owned_cuadrante_mapa_patologia(cur, cuadrante_id, current_user["id"])
    require_row(cuadrante, "Cuadrante no encontrado")

    borrar_fotos_relacionadas(
        cur,
        "cuadrante_mapa_patologia_fotos",
        "cuadrante_id",
        cuadrante_id,
    )
    if cuadrante["foto_detalle"]:
        borrar_foto_si_existe(cuadrante["foto_detalle"])

    cur.execute(
        "DELETE FROM cuadrantes_mapa_patologia WHERE id=?",
        (cuadrante_id,),
    )
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/registrar-patologias/{cuadrante['visita_id']}",
        status_code=303,
    )


@app.post("/borrar-foto-registro/{foto_id}")
def borrar_foto_registro(request: Request, foto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    foto = cur.execute(
        """
        SELECT rpf.*, rp.visita_id, rp.id AS registro_real_id
        FROM registro_patologia_fotos rpf
        JOIN registros_patologias rp ON rpf.registro_id = rp.id
        JOIN visitas v ON rp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE rpf.id=? AND e.owner_user_id=?
        """,
        (foto_id, current_user["id"]),
    ).fetchone()
    require_row(foto, "Foto no encontrada")

    borrar_foto_si_existe(foto["archivo"])
    cur.execute("DELETE FROM registro_patologia_fotos WHERE id=?", (foto_id,))
    sincronizar_foto_principal(
        cur,
        "registros_patologias",
        "id",
        "foto",
        foto["registro_id"],
        "registro_patologia_fotos",
        "registro_id",
    )
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/editar-registro/{foto['registro_id']}",
        status_code=303,
    )


@app.post("/borrar-foto-registro-exterior/{foto_id}")
def borrar_foto_registro_exterior(request: Request, foto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    foto = cur.execute(
        """
        SELECT rpef.*, rpe.visita_id
        FROM registro_patologia_exterior_fotos rpef
        JOIN registros_patologias_exteriores rpe ON rpef.registro_id = rpe.id
        JOIN visitas v ON rpe.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE rpef.id=? AND e.owner_user_id=?
        """,
        (foto_id, current_user["id"]),
    ).fetchone()
    require_row(foto, "Foto no encontrada")

    borrar_foto_si_existe(foto["archivo"])
    cur.execute("DELETE FROM registro_patologia_exterior_fotos WHERE id=?", (foto_id,))
    sincronizar_foto_principal(
        cur,
        "registros_patologias_exteriores",
        "id",
        "foto",
        foto["registro_id"],
        "registro_patologia_exterior_fotos",
        "registro_id",
    )
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/editar-registro-exterior/{foto['registro_id']}",
        status_code=303,
    )


@app.post("/borrar-foto-cuadrante-mapa-patologia/{foto_id}")
def borrar_foto_cuadrante_mapa_patologia(request: Request, foto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    foto = cur.execute(
        """
        SELECT qmpf.*, qmp.id AS cuadrante_real_id, mp.visita_id
        FROM cuadrante_mapa_patologia_fotos qmpf
        JOIN cuadrantes_mapa_patologia qmp ON qmpf.cuadrante_id = qmp.id
        JOIN mapas_patologia mp ON qmp.mapa_id = mp.id
        JOIN visitas v ON mp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE qmpf.id=? AND e.owner_user_id=?
        """,
        (foto_id, current_user["id"]),
    ).fetchone()
    require_row(foto, "Foto no encontrada")

    borrar_foto_si_existe(foto["archivo"])
    cur.execute("DELETE FROM cuadrante_mapa_patologia_fotos WHERE id=?", (foto_id,))
    sincronizar_foto_principal(
        cur,
        "cuadrantes_mapa_patologia",
        "id",
        "foto_detalle",
        foto["cuadrante_id"],
        "cuadrante_mapa_patologia_fotos",
        "cuadrante_id",
    )
    conn.commit()
    conn.close()
    return RedirectResponse(
        url=f"/editar-cuadrante-mapa-patologia/{foto['cuadrante_id']}",
        status_code=303,
    )


@app.post("/guardar-registro")
def guardar_registro(
    request: Request,
    visita_id: int = Form(...),
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    localizacion_dano: str = Form(""),
    detalle_localizacion: str = Form(""),
    rol_patologia_observado: str = Form(""),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    validar_estancia_para_visita(cur, visita, estancia_id)
    estancia = cur.execute(
        "SELECT nombre FROM estancias WHERE id=?",
        (estancia_id,),
    ).fetchone()

    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        estancia["nombre"] if estancia else "estancia",
        elemento,
    )
    nombre_foto = nombres_fotos[0] if nombres_fotos else None

    cur.execute(
        """
        INSERT INTO registros_patologias
        (visita_id, estancia_id, elemento, localizacion_dano, detalle_localizacion, rol_patologia_observado, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            estancia_id,
            elemento,
            localizacion_dano,
            detalle_localizacion,
            rol_patologia_observado,
            patologia,
            observaciones,
            nombre_foto,
        ),
    )
    registro_id = cur.lastrowid
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "registro_patologia_fotos",
            "registro_id",
            registro_id,
            nombres_fotos,
        )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    if estancia_id:
        return RedirectResponse(
            url=f"/definir-estancias/{visita_id}#estructura-interior",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}?estancia_id={estancia_id}&guardado=1#formulario_patologia_interior",
        status_code=303,
    )


@app.get("/editar-registro/{registro_id}", response_class=HTMLResponse)
def editar_registro(
    request: Request,
    registro_id: int,
    next: str = Query(""),
    cost_q: str = Query(""),
    mensaje: str = Query(""),
    error: str = Query(""),
    aviso: str = Query(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")
    registro = enriquecer_registro_con_fotos(
        cur,
        registro,
        "registro_patologia_fotos",
        "registro_id",
        "foto",
    )

    estancias = cur.execute(
        """
        SELECT es.*,
               ue.identificador AS identificador_unidad_estancia,
               ne.nombre_nivel AS nombre_nivel_estancia
        FROM estancias es
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE es.visita_id=?
        ORDER BY es.id ASC
        """,
        (registro["visita_id"],),
    ).fetchall()

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()

    objeto_visita_label = describir_objeto_visita(registro)
    costes_patologia = obtener_costes_patologia(cur, registro_id)
    total_costes_patologia = calcular_total_costes_patologia(costes_patologia)
    partidas_coste = buscar_partidas_coste_para_patologia(cur, cost_q)

    conn.close()

    return render_template(
        request,
        "editar_registro.html",
        {
            "registro": registro,
            "estancias": estancias,
            "patologias": patologias,
            "objeto_visita_label": objeto_visita_label,
            "costes_patologia": costes_patologia,
            "total_costes_patologia": total_costes_patologia,
            "partidas_coste": partidas_coste,
            "cost_q": limpiar_texto(cost_q),
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
            "aviso": limpiar_texto(aviso),
            "next_url": normalizar_redirect_interno(next),
        },
    )


@app.post("/patologias/{registro_id}/costes")
def vincular_coste_patologia(
    request: Request,
    registro_id: int,
    concepto_id: int = Form(...),
    cantidad: str = Form("1"),
    descripcion_actuacion: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    cantidad_num = round(parsear_decimal_coste_patologia(cantidad, 0), 4)
    if cantidad_num <= 0:
        return redirect_editar_registro_costes(
            registro_id,
            error="La cantidad debe ser mayor que cero.",
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        registro = get_owned_registro(cur, registro_id, current_user["id"])
        require_row(registro, "Registro no encontrado")
        concepto = cur.execute(
            """
            SELECT id, codigo, unidad, resumen, precio, estado
            FROM costes_conceptos
            WHERE id = ?
            """,
            (concepto_id,),
        ).fetchone()
        require_row(concepto, "Partida de coste no encontrada")
        precio_unitario = round(float(concepto["precio"] or 0), 4)
        importe = round(cantidad_num * precio_unitario, 2)
        estado_vinculo = "incluido" if concepto["estado"] == "validado" else "borrador"
        descripcion = limpiar_texto(descripcion_actuacion) or concepto["resumen"]
        aviso = ""
        if concepto["estado"] != "validado":
            aviso = "La partida base está en borrador; el coste vinculado queda marcado como borrador."
        cur.execute(
            """
            INSERT INTO patologia_costes (
                patologia_id, concepto_id, descripcion_actuacion,
                cantidad, unidad, precio_unitario, importe, estado,
                observaciones, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                registro_id,
                concepto_id,
                descripcion,
                cantidad_num,
                concepto["unidad"],
                precio_unitario,
                importe,
                estado_vinculo,
                limpiar_texto(observaciones),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_editar_registro_costes(
        registro_id,
        mensaje="Partida vinculada al coste de subsanación.",
        aviso=aviso,
    )


@app.post("/patologias/costes/{vinculo_id}/actualizar")
def actualizar_coste_patologia(
    request: Request,
    vinculo_id: int,
    cantidad: str = Form("1"),
    descripcion_actuacion: str = Form(""),
    estado: str = Form("incluido"),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)
    cantidad_num = round(parsear_decimal_coste_patologia(cantidad, 0), 4)
    if cantidad_num <= 0:
        cantidad_num = 0
    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = cur.execute(
            """
            SELECT pc.*, rp.id AS registro_id
            FROM patologia_costes pc
            JOIN registros_patologias rp ON rp.id = pc.patologia_id
            WHERE pc.id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        require_row(vinculo, "Coste de patología no encontrado")
        registro = get_owned_registro(cur, vinculo["registro_id"], current_user["id"])
        require_row(registro, "Registro no encontrado")
        estado_limpio = limpiar_texto(estado)
        if estado_limpio not in ("borrador", "incluido"):
            estado_limpio = "incluido"
        precio_unitario = float(vinculo["precio_unitario"] or 0)
        importe = round(cantidad_num * precio_unitario, 2)
        cur.execute(
            """
            UPDATE patologia_costes
            SET descripcion_actuacion = ?, cantidad = ?, importe = ?,
                estado = ?, observaciones = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                limpiar_texto(descripcion_actuacion),
                cantidad_num,
                importe,
                estado_limpio,
                limpiar_texto(observaciones),
                vinculo_id,
            ),
        )
        conn.commit()
        registro_id = vinculo["registro_id"]
    finally:
        conn.close()

    return redirect_editar_registro_costes(registro_id, mensaje="Coste actualizado.")


@app.post("/patologias/costes/{vinculo_id}/borrar")
def borrar_coste_patologia(request: Request, vinculo_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        vinculo = cur.execute(
            """
            SELECT pc.id, pc.patologia_id AS registro_id
            FROM patologia_costes pc
            WHERE pc.id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        require_row(vinculo, "Coste de patología no encontrado")
        registro = get_owned_registro(cur, vinculo["registro_id"], current_user["id"])
        require_row(registro, "Registro no encontrado")
        cur.execute("DELETE FROM patologia_costes WHERE id = ?", (vinculo_id,))
        conn.commit()
        registro_id = vinculo["registro_id"]
    finally:
        conn.close()

    return redirect_editar_registro_costes(registro_id, mensaje="Coste borrado.")


@app.post("/actualizar-registro/{registro_id}")
def actualizar_registro(
    request: Request,
    registro_id: int,
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    localizacion_dano: str = Form(""),
    detalle_localizacion: str = Form(""),
    rol_patologia_observado: str = Form(""),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    visita_id = registro["visita_id"]
    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    validar_estancia_para_visita(cur, visita, estancia_id)
    estancia = cur.execute(
        "SELECT nombre FROM estancias WHERE id=?",
        (estancia_id,),
    ).fetchone()
    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        estancia["nombre"] if estancia else "estancia",
        elemento,
    )
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "registro_patologia_fotos",
            "registro_id",
            registro_id,
            nombres_fotos,
        )

    cur.execute(
        """
        UPDATE registros_patologias
        SET estancia_id=?, elemento=?, localizacion_dano=?, detalle_localizacion=?, rol_patologia_observado=?, patologia=?, observaciones=?, foto=?
        WHERE id=?
        """,
        (
            estancia_id,
            elemento,
            localizacion_dano,
            detalle_localizacion,
            rol_patologia_observado,
            patologia,
            observaciones,
            registro["foto"],
            registro_id,
        ),
    )
    sincronizar_foto_principal(
        cur,
        "registros_patologias",
        "id",
        "foto",
        registro_id,
        "registro_patologia_fotos",
        "registro_id",
    )
    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET patologia_detectada=?
        WHERE patologia_id=?
          AND mapa_id IN (SELECT id FROM mapas_patologia WHERE visita_id=?)
        """,
        (patologia, registro_id, visita_id),
    )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.post("/guardar-registro-exterior")
def guardar_registro_exterior(
    request: Request,
    visita_id: int = Form(...),
    estancia_id_contexto: str = Form(""),
    zona_exterior: str = Form(""),
    elemento_exterior: str = Form(""),
    localizacion_dano_exterior: str = Form(""),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        zona_exterior or "exterior",
        elemento_exterior or "elemento",
    )
    nombre_foto = nombres_fotos[0] if nombres_fotos else None

    cur.execute(
        """
        INSERT INTO registros_patologias_exteriores (
            visita_id,
            zona_exterior,
            elemento_exterior,
            localizacion_dano_exterior,
            patologia,
            observaciones,
            foto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            zona_exterior,
            elemento_exterior,
            localizacion_dano_exterior,
            patologia,
            observaciones,
            nombre_foto,
        ),
    )
    registro_id = cur.lastrowid
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "registro_patologia_exterior_fotos",
            "registro_id",
            registro_id,
            nombres_fotos,
        )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    estancia_id_inspector = parse_optional_int(estancia_id_contexto) or obtener_estancia_id_referer(request)
    if estancia_id_inspector:
        return RedirectResponse(
            url=f"/definir-estancias/{visita_id}#estructura-interior",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-registro-exterior/{registro_id}", response_class=HTMLResponse)
def editar_registro_exterior(request: Request, registro_id: int, next: str = Query("")):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro_exterior(cur, registro_id, current_user["id"])
    require_row(registro, "Registro exterior no encontrado")
    registro = enriquecer_registro_con_fotos(
        cur,
        registro,
        "registro_patologia_exterior_fotos",
        "registro_id",
        "foto",
    )

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()

    objeto_visita_label = describir_objeto_visita(registro)

    conn.close()

    return render_template(
        request,
        "editar_registro_exterior.html",
        {
            "registro": registro,
            "patologias": patologias,
            "objeto_visita_label": objeto_visita_label,
            "next_url": normalizar_redirect_interno(next),
        },
    )


@app.post("/actualizar-registro-exterior/{registro_id}")
def actualizar_registro_exterior(
    request: Request,
    registro_id: int,
    zona_exterior: str = Form(""),
    elemento_exterior: str = Form(""),
    localizacion_dano_exterior: str = Form(""),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    fotos: list[UploadFile] = File([]),
    next: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro_exterior(cur, registro_id, current_user["id"])
    require_row(registro, "Registro exterior no encontrado")

    visita_id = registro["visita_id"]
    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    nombres_fotos = guardar_uploads_contextuales(
        fotos,
        visita["numero_expediente"],
        zona_exterior or "exterior",
        elemento_exterior or "elemento",
    )
    if nombres_fotos:
        insertar_fotos_relacionadas(
            cur,
            "registro_patologia_exterior_fotos",
            "registro_id",
            registro_id,
            nombres_fotos,
        )

    cur.execute(
        """
        UPDATE registros_patologias_exteriores
        SET zona_exterior=?, elemento_exterior=?, localizacion_dano_exterior=?, patologia=?, observaciones=?, foto=?
        WHERE id=?
        """,
        (
            zona_exterior,
            elemento_exterior,
            localizacion_dano_exterior,
            patologia,
            observaciones,
            registro["foto"],
            registro_id,
        ),
    )
    sincronizar_foto_principal(
        cur,
        "registros_patologias_exteriores",
        "id",
        "foto",
        registro_id,
        "registro_patologia_exterior_fotos",
        "registro_id",
    )
    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET patologia_detectada=?
        WHERE patologia_id=?
          AND mapa_id IN (SELECT id FROM mapas_patologia WHERE visita_id=?)
        """,
        (patologia, registro_id, visita_id),
    )

    conn.commit()
    conn.close()

    next_url = normalizar_redirect_interno(next)
    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.post("/borrar-registro/{registro_id}")
def borrar_registro(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    borrar_fotos_relacionadas(cur, "registro_patologia_fotos", "registro_id", registro_id)
    if registro["foto"]:
        borrar_foto_si_existe(registro["foto"])

    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET patologia_id=NULL
        WHERE patologia_id=?
          AND mapa_id IN (SELECT id FROM mapas_patologia WHERE visita_id=?)
          AND (
              TRIM(IFNULL(patologia_detectada, '')) = ''
              OR TRIM(IFNULL(patologia_detectada, '')) = ?
          )
        """,
        (registro_id, registro["visita_id"], registro["patologia"]),
    )
    cur.execute("DELETE FROM registros_patologias WHERE id=?", (registro_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}",
        status_code=303,
    )


@app.post("/duplicar-registro/{registro_id}")
def duplicar_registro(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    cur.execute(
        """
        INSERT INTO registros_patologias (
            visita_id,
            estancia_id,
            elemento,
            localizacion_dano,
            detalle_localizacion,
            rol_patologia_observado,
            patologia,
            observaciones,
            foto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registro["visita_id"],
            registro["estancia_id"],
            registro["elemento"],
            registro["localizacion_dano"],
            registro["detalle_localizacion"],
            registro["rol_patologia_observado"],
            registro["patologia"],
            registro["observaciones"],
            None,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}?estancia_id={registro['estancia_id']}#formulario_patologia",
        status_code=303,
    )


@app.post("/duplicar-registro-exterior/{registro_id}")
def duplicar_registro_exterior(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro_exterior(cur, registro_id, current_user["id"])
    require_row(registro, "Registro exterior no encontrado")

    cur.execute(
        """
        INSERT INTO registros_patologias_exteriores (
            visita_id,
            zona_exterior,
            elemento_exterior,
            localizacion_dano_exterior,
            patologia,
            observaciones,
            foto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registro["visita_id"],
            registro["zona_exterior"],
            registro["elemento_exterior"],
            registro["localizacion_dano_exterior"],
            registro["patologia"],
            registro["observaciones"],
            None,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}",
        status_code=303,
    )


@app.post("/eliminar-registro/{registro_id}")
def eliminar_registro(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    cur.execute("DELETE FROM registros_patologias WHERE id=?", (registro_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}?estancia_id={registro['estancia_id']}#formulario_patologia",
        status_code=303,
    )


@app.post("/borrar-registro-exterior/{registro_id}")
def borrar_registro_exterior(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro_exterior(cur, registro_id, current_user["id"])
    require_row(registro, "Registro exterior no encontrado")

    borrar_fotos_relacionadas(
        cur,
        "registro_patologia_exterior_fotos",
        "registro_id",
        registro_id,
    )
    if registro["foto"]:
        borrar_foto_si_existe(registro["foto"])

    cur.execute(
        """
        UPDATE cuadrantes_mapa_patologia
        SET patologia_id=NULL
        WHERE patologia_id=?
          AND mapa_id IN (SELECT id FROM mapas_patologia WHERE visita_id=?)
          AND (
              TRIM(IFNULL(patologia_detectada, '')) = ''
              OR TRIM(IFNULL(patologia_detectada, '')) = ?
          )
        """,
        (registro_id, registro["visita_id"], registro["patologia"]),
    )
    cur.execute(
        "DELETE FROM registros_patologias_exteriores WHERE id=?",
        (registro_id,),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}",
        status_code=303,
    )


@app.get("/generar-informe/{expediente_id}")
def generar_informe_endpoint(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")

    ruta_archivo, nombre_archivo = generar_informe(expediente_id)

    return RedirectResponse(
        url=f"/descargar-informe/{expediente_id}/{nombre_archivo}",
        status_code=303,
    )


@app.get("/informes/{expediente_id}/imprimir", response_class=HTMLResponse)
def imprimir_informe_pdf(
    request: Request,
    expediente_id: int,
    incluir_anexo_economico_reparacion: str = Query(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")
    incluir_anexo = limpiar_texto(incluir_anexo_economico_reparacion) == "1"
    contexto = build_informe_context(
        expediente_id,
        incluir_anexo_economico_reparacion=incluir_anexo,
    )

    return render_template(
        request,
        "informes/imprimir.html",
        {
            **contexto,
            "modo_pdf": False,
        },
    )


@app.get("/generar-informe-pdf/{expediente_id}")
def generar_informe_pdf_endpoint(
    request: Request,
    expediente_id: int,
    incluir_anexo_economico_reparacion: str = Query(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")
    pdf_bytes = generar_informe_pdf_bytes(
        request,
        expediente_id,
        incluir_anexo_economico_reparacion=limpiar_texto(incluir_anexo_economico_reparacion) == "1",
    )
    nombre_archivo = nombre_archivo_pdf_informe(expediente)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )


@app.get("/generar-informe-v2-pdf/{expediente_id}")
def generar_informe_v2_pdf_endpoint(
    request: Request,
    expediente_id: int,
    perfil: str = Query(""),
):
    current_user = get_current_user(request)
    perfil_explicitado = bool(limpiar_texto(perfil))
    perfil_pdf = resolver_perfil_exportacion_pdf_v2(perfil)

    conn = get_connection()
    cur = conn.cursor()
    try:
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
        require_row(expediente, "Expediente no encontrado")
        if limpiar_texto(expediente["tipo_informe"]) != "patologias":
            return redirect_detalle_expediente(
                expediente_id,
                error="El PDF del informe solo aplica a expedientes de patologías.",
            )
        if not perfil_pdf.get("implementado", True):
            raise HTTPException(
                status_code=501,
                detail=(
                    "El perfil de anexo fotográfico queda preparado, "
                    "pero requiere una generación separada en una fase posterior."
                ),
            )
        contexto = preparar_contexto_pdf_informe_v2(
            cur,
            expediente,
            base_url=str(request.base_url).rstrip("/"),
        )
    finally:
        conn.close()

    sesion_optimizacion = crear_sesion_optimizacion_pdf(perfil_pdf)
    sesion_optimizacion_anexos = crear_sesion_optimizacion_anexos_pdf(perfil_pdf)
    try:
        contexto["perfil_exportacion_pdf"] = perfil_pdf
        contexto["optimizacion_imagenes_pdf"] = optimizar_contexto_imagenes_pdf(
            contexto,
            sesion_optimizacion,
            UPLOAD_PATH,
        )
        pdf_bytes = generar_informe_v2_pdf_bytes(request, contexto)
        contexto["diagnostico_anexos_pdf"] = diagnosticar_peso_anexos_pdf_v2(
            contexto.get("anexos", {}).get("documentacion"),
            contexto.get("pdf_mediciones_anexo_f"),
            pdf_bytes,
        )
        if perfil_pdf.get("incluye_anexos"):
            pdf_bytes = fusionar_pdf_informe_v2_con_anexos_integrados(
                pdf_bytes,
                contexto.get("anexos", {}).get("documentacion"),
                contexto.get("pdf_mediciones_anexo_f"),
                perfil_pdf=perfil_pdf,
                sesion_optimizacion_anexos=sesion_optimizacion_anexos,
                diagnostico_anexos_pdf=contexto.get("diagnostico_anexos_pdf"),
            )
    finally:
        sesion_optimizacion.cleanup()
        sesion_optimizacion_anexos.cleanup()
    nombre_archivo = nombre_archivo_pdf_informe_v2(
        expediente,
        perfil_pdf=perfil_pdf,
        incluir_perfil=perfil_explicitado,
    )

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )


@app.get("/generar-informe-docx-editable/{expediente_id}")
def generar_informe_docx_editable_endpoint(
    request: Request,
    expediente_id: int,
    incluir_anexo_economico_reparacion: str = Query(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")
    docx_bytes = generar_informe_docx_editable_bytes(
        expediente_id,
        incluir_anexo_economico_reparacion=limpiar_texto(incluir_anexo_economico_reparacion) == "1",
    )
    nombre_archivo = nombre_archivo_docx_editable_informe(expediente)

    return StreamingResponse(
        BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )


@app.get("/descargar-informe/{expediente_id}/{nombre_archivo}")
def descargar_informe(request: Request, expediente_id: int, nombre_archivo: str):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")
    ruta = get_informe_path_for_expediente(expediente, nombre_archivo)

    return FileResponse(
        path=str(ruta),
        filename=ruta.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.post("/borrar-expediente/{expediente_id}")
def borrar_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    eliminar_expediente_completo(cur, expediente_id)

    conn.commit()
    conn.close()

    return RedirectResponse(url="/expedientes", status_code=303)


@app.post("/borrar-visita/{visita_id}")
def borrar_visita(request: Request, visita_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    eliminar_visita_completa(cur, visita_id)

    conn.commit()
    conn.close()

    return redirect_detalle_expediente(
        visita["expediente_id"],
        mensaje="Visita eliminada.",
    )
