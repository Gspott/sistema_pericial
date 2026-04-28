import binascii
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import shutil
import sqlite3
import unicodedata
from urllib.parse import quote_plus
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
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
from app.routers import dashboard as dashboard_router
from app.routers import facturacion as facturacion_router
from app.routers import gastos as gastos_router
from app.routers import leads as leads_router
from app.routers import propuestas as propuestas_router
from app.services.catastro import consultar_catastro_por_referencia
from app.services.clima import geocodificar, obtener_climatologia
from app.services.direccion import autocompletar_direccion, sugerir_direcciones
from app.services.informe import generar_informe, limpiar_nombre_archivo
from app.utils.helpers import formatear_plantas

app = FastAPI()

STATIC_PATH = Path(STATIC_DIR)
TEMPLATES_PATH = Path(TEMPLATES_DIR)
UPLOAD_PATH = Path(UPLOAD_DIR)
DB_FILE = Path(DB_PATH)

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
    copiado = copiar_estancias_visita_anterior(cur, expediente["id"], nueva_visita_id)

    if not copiado:
        crear_estancias_base(
            cur,
            nueva_visita_id,
            expediente["tipo_inmueble"] or "",
            expediente["dormitorios_unidad"],
            expediente["banos_unidad"],
        )

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
    return templates.TemplateResponse(template_name, data)


def normalizar_redirect_interno(destino: str | None) -> str:
    destino_limpio = limpiar_texto(destino)
    if not destino_limpio:
        return ""
    if not destino_limpio.startswith("/") or destino_limpio.startswith("//"):
        return ""
    return destino_limpio


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
        "patologias_exteriores": patologias_exteriores,
        "grupos_unidades": grupos_unidades,
        "hay_unidades_o_estancias": bool(grupos_unidades),
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
    return all(
        [
            limpiar_texto(estancia.get("nombre")),
            limpiar_texto(estancia.get("tipo_estancia")),
            limpiar_texto(estancia.get("ventilacion")),
            limpiar_texto(estancia.get("planta")),
            limpiar_texto(estancia.get("acabado_pavimento")),
            limpiar_texto(estancia.get("acabado_paramento")),
            limpiar_texto(estancia.get("acabado_techo")),
            bool(estancia.get("foto_principal_url")),
        ]
    )


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
            unidad["gestion_url"] += "#estancias-registradas"
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
               ue.identificador AS identificador_unidad_estancia,
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
app.include_router(dashboard_router.router)
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
def nuevo_expediente(request: Request):
    return render_template(
        request,
        "nuevo_expediente.html",
        {
            "numero_expediente_sugerido": generar_numero_expediente(),
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
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
):
    current_user = get_current_user(request)
    expediente_id = None

    for _ in range(3):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN IMMEDIATE")
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
            conn.commit()
            conn.close()
            break
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
            "comparables": cur.execute(
                """
                SELECT COUNT(*)
                FROM comparables_valoracion cv
                JOIN visitas v ON cv.visita_id = v.id
                WHERE v.expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0],
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


@app.get("/resumen-registro/{expediente_id}", response_class=HTMLResponse)
def resumen_registro(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    resumen_registro_data = preparar_resumen_registro_expediente(cur, expediente_id)

    conn.close()

    expediente_data = dict(expediente)
    expediente_data["tipo_informe_label"] = etiquetar_opcion(
        expediente_data.get("tipo_informe", ""),
        TIPO_INFORME_LABELS,
    )

    return render_template(
        request,
        "resumen_registro.html",
        {
            "expediente": expediente_data,
            "patologias_exteriores": resumen_registro_data["patologias_exteriores"],
            "grupos_unidades": resumen_registro_data["grupos_unidades"],
            "hay_unidades_o_estancias": resumen_registro_data["hay_unidades_o_estancias"],
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
            observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "clima": clima,
            "clima_detalle": clima_detalle,
            "clima_error": clima_error,
            "es_informe_inspeccion": limpiar_texto(expediente["tipo_informe"]) == "inspeccion",
            "es_informe_habitabilidad": limpiar_texto(expediente["tipo_informe"]) == "habitabilidad",
            "es_informe_valoracion": limpiar_texto(expediente["tipo_informe"]) == "valoracion",
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
                "clima": clima,
                "clima_detalle": clima_detalle,
                "clima_error": "",
                "es_informe_inspeccion": limpiar_texto(expediente["tipo_informe"]) == "inspeccion",
                "es_informe_habitabilidad": limpiar_texto(expediente["tipo_informe"]) == "habitabilidad",
                "es_informe_valoracion": limpiar_texto(expediente["tipo_informe"]) == "valoracion",
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
            await guardar_datos_valoracion_desde_form(cur, visita_id, form)

    conn.commit()
    conn.close()

    if tipo_informe in {"inspeccion", "habitabilidad", "valoracion"}:
        return RedirectResponse(
            url=f"/nueva-visita/{expediente_id}?visita_id={visita_id}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
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
            "ambito_visita_options": AMBITO_VISITA_OPTIONS,
            "niveles_visita_options": opciones_visita_multiunidad["niveles"],
            "unidades_visita_options": opciones_visita_multiunidad["unidades_generales"],
            "zonas_comunes_visita_options": opciones_visita_multiunidad["unidades_comunes"],
            "exteriores_visita_options": opciones_visita_multiunidad["unidades_exteriores"],
        },
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

    estancias_rows = cur.execute(
        """
        SELECT es.*,
               ue.identificador AS unidad_identificador,
               ne.nombre_nivel AS nivel_nombre
        FROM estancias es
        LEFT JOIN unidades_expediente ue ON es.unidad_id = ue.id
        LEFT JOIN niveles_edificio ne ON ue.nivel_id = ne.id
        WHERE es.visita_id=?
        ORDER BY es.id ASC
        """,
        (visita_id,),
    ).fetchall()

    estancias = []
    for estancia_row in estancias_rows:
        estancia = dict(estancia_row)
        fotos = obtener_fotos_relacionadas(cur, "estancia_fotos", "estancia_id", estancia["id"])
        for foto in fotos:
            foto["url"] = f"/uploads/{foto['archivo']}"
        estancia["foto_principal_url"] = fotos[0]["url"] if fotos else ""
        estancia["esta_rellena"] = calcular_estancia_rellena(estancia)
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

    conn.close()

    dormitorios_sugeridos = int(visita["dormitorios_unidad"] or 0) if str(
        visita["dormitorios_unidad"] or ""
    ).isdigit() else 0
    banos_sugeridos = int(visita["banos_unidad"] or 0) if str(
        visita["banos_unidad"] or ""
    ).isdigit() else 0

    return render_template(
        request,
        "definir_estancias.html",
        {
            "visita": visita,
            "estancias": estancias_visibles,
            "estancias_sin_unidad": estancias_sin_unidad,
            "dormitorios_sugeridos": dormitorios_sugeridos,
            "banos_sugeridos": banos_sugeridos,
            "objeto_visita_label": describir_objeto_visita(visita),
            "mostrar_navegacion_multiunidad": es_edificio_completo,
            "navegacion_multiunidad": navegacion_multiunidad,
            "unidad_seleccionada": unidad_seleccionada,
        },
    )


@app.post("/generar-estancias-base")
def generar_estancias_base(
    request: Request,
    visita_id: int = Form(...),
    num_dormitorios: int = Form(0),
    num_banos: int = Form(0),
    incluir_salon: str = Form("no"),
    incluir_cocina: str = Form("no"),
    incluir_pasillo: str = Form("no"),
    incluir_terraza: str = Form("no"),
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
    es_edificio_completo = limpiar_texto(visita["ambito_visita"]) == "edificio_completo"

    if es_edificio_completo and unidad_id_estancia:
        existentes = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM estancias
            WHERE visita_id = ? AND unidad_id = ?
            """,
            (visita_id, unidad_id_estancia),
        ).fetchone()
    else:
        existentes = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM estancias
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone()

    total_existentes = existentes["total"] if existentes else 0

    if total_existentes == 0:
        if incluir_salon == "si":
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
                (visita_id, "Salón", "Salón", "", "", "", "", "", "", unidad_id_estancia),
            )

        if incluir_cocina == "si":
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
                (visita_id, "Cocina", "Cocina", "", "", "", "", "", "", unidad_id_estancia),
            )

        if incluir_pasillo == "si":
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
                (visita_id, "Pasillo", "Pasillo", "", "", "", "", "", "", unidad_id_estancia),
            )

        if incluir_terraza == "si":
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
                (visita_id, "Terraza", "Terraza", "", "", "", "", "", "", unidad_id_estancia),
            )

        for i in range(1, num_dormitorios + 1):
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
                    unidad_id_estancia,
                ),
            )

        for i in range(1, num_banos + 1):
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
                    f"Baño {i}",
                    "Baño",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    unidad_id_estancia,
                ),
            )

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
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    unidad_id_estancia = None
    unidad_id_objetivo_int = parse_optional_int(unidad_id_objetivo)
    unidad_referencia_id = unidad_id_objetivo_int or visita["unidad_id"]
    if unidad_referencia_id:
        unidad = get_owned_unidad(cur, unidad_referencia_id, current_user["id"])
        if not unidad or unidad["expediente_id"] != visita["expediente_id"]:
            conn.close()
            raise HTTPException(status_code=400, detail="La unidad asociada a la visita no es válida.")
        unidad_id_estancia = unidad_referencia_id

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
            planta,
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

    return RedirectResponse(
        url=(
            f"/definir-estancias/{visita_id}?unidad_id={unidad_id_estancia}"
            if limpiar_texto(visita["ambito_visita"]) == "edificio_completo" and unidad_id_estancia
            else f"/definir-estancias/{visita_id}"
        ),
        status_code=303,
    )


@app.get("/editar-estancia/{estancia_id}", response_class=HTMLResponse)
def editar_estancia(
    request: Request,
    estancia_id: int,
    unidad_id_contexto: int | None = Query(None),
    next: str = Query(""),
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

    conn.close()

    return render_template(
        request,
        "editar_estancia.html",
        {
            "estancia": estancia,
            "unidad_id_contexto": unidad_id_contexto,
            "next_url": normalizar_redirect_interno(next),
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
    siguiente: str = Form("estancias"),
    unidad_id_contexto: str = Form(""),
    next: str = Form(""),
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
            planta,
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
    next_url = normalizar_redirect_interno(next)

    if next_url:
        return RedirectResponse(
            url=next_url,
            status_code=303,
        )

    if siguiente == "patologias":
        return RedirectResponse(
            url=f"/registrar-patologias/{visita_id}",
            status_code=303,
        )

    return RedirectResponse(
        url=(
            f"/definir-estancias/{visita_id}?unidad_id={unidad_id_contexto_int}"
            if unidad_id_contexto_int
            and limpiar_texto(visita["ambito_visita"]) == "edificio_completo"
            else f"/definir-estancias/{visita_id}"
        ),
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
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")
    estancia_seleccionada = None

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

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}?estancia_id={estancia_id}#formulario_patologia",
        status_code=303,
    )


@app.get("/editar-registro/{registro_id}", response_class=HTMLResponse)
def editar_registro(request: Request, registro_id: int, next: str = Query("")):
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

    conn.close()

    return render_template(
        request,
        "editar_registro.html",
        {
            "registro": registro,
            "estancias": estancias,
            "patologias": patologias,
            "objeto_visita_label": objeto_visita_label,
            "next_url": normalizar_redirect_interno(next),
        },
    )


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

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-registro-exterior/{registro_id}", response_class=HTMLResponse)
def editar_registro_exterior(request: Request, registro_id: int):
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
