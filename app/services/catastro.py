import re
import logging
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import xml.etree.ElementTree as ET

import httpx

from app.config import UPLOAD_DIR


CATASTRO_CONSULTA_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC"
)
CATASTRO_FICHA_URL = "https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCListaBienes.aspx"
CATASTRO_MAPA_URL = "https://www1.sedecatastro.gob.es/Cartografia/mapa.aspx"
CATASTRO_WMS_URL = "https://www1.sedecatastro.gob.es/Cartografia/GeneraMapa.aspx"
XML_NS = {"cat": "http://www.catastro.meh.es/"}
CATASTRO_CACHE_DIR = Path(UPLOAD_DIR) / "catastro"
CATASTRO_CACHE_EXTS = (".png", ".jpg", ".gif")
logger = logging.getLogger(__name__)


def normalizar_referencia_catastral(referencia: str) -> str:
    return "".join(str(referencia or "").upper().split())


def _text(node, xpath: str) -> str:
    encontrado = node.find(xpath, XML_NS)
    if encontrado is None or encontrado.text is None:
        return ""
    return encontrado.text.strip()


def _construir_direccion(root: ET.Element) -> str:
    tipo_via = _text(root, ".//cat:lourb/cat:dir/cat:tv")
    nombre_via = _text(root, ".//cat:lourb/cat:dir/cat:nv")
    numero = _text(root, ".//cat:lourb/cat:dir/cat:pnp")
    sufijo_numero = _text(root, ".//cat:lourb/cat:dir/cat:snp")
    escalera = _text(root, ".//cat:lourb/cat:loint/cat:es")
    planta = _text(root, ".//cat:lourb/cat:loint/cat:pt")
    puerta = _text(root, ".//cat:lourb/cat:loint/cat:pu")

    partes = [tipo_via, nombre_via, numero]
    if sufijo_numero and sufijo_numero != "0":
        partes.append(sufijo_numero)

    direccion = " ".join(parte for parte in partes if parte).strip()

    interior = []
    if escalera:
        interior.append(f"Esc. {escalera}")
    if planta:
        interior.append(f"Pl. {planta}")
    if puerta:
        interior.append(f"Pta. {puerta}")

    if interior:
        direccion = f"{direccion}, {' '.join(interior)}".strip(", ")

    if not direccion:
        direccion = _text(root, ".//cat:ldt")

    return direccion


def _detectar_extension_imagen(contenido: bytes) -> str | None:
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if contenido.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if contenido.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    return None


def _ruta_cache_catastro(referencia_catastral: str, extension: str) -> Path:
    referencia = normalizar_referencia_catastral(referencia_catastral)
    return CATASTRO_CACHE_DIR / f"{referencia}{extension}"


def _leer_imagen_cache(
    referencia_catastral: str,
) -> tuple[bytes | None, str | None]:
    referencia = normalizar_referencia_catastral(referencia_catastral)
    for extension in CATASTRO_CACHE_EXTS:
        ruta = _ruta_cache_catastro(referencia, extension)
        if ruta.exists():
            logger.info("[catastro] Cache hit para ref=%s ruta=%s", referencia, ruta)
            return ruta.read_bytes(), extension

    logger.info("[catastro] Cache miss para ref=%s", referencia)
    return None, None


def _guardar_imagen_cache(
    referencia_catastral: str,
    imagen_bytes: bytes | None,
    imagen_extension: str | None,
) -> None:
    if not imagen_bytes or imagen_extension not in CATASTRO_CACHE_EXTS:
        return

    CATASTRO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ruta = _ruta_cache_catastro(referencia_catastral, imagen_extension)
    ruta.write_bytes(imagen_bytes)
    logger.info(
        "[catastro] Imagen cacheada para ref=%s ruta=%s",
        normalizar_referencia_catastral(referencia_catastral),
        ruta,
    )


def _separar_referencia_para_ficha(referencia_catastral: str) -> tuple[str, str]:
    referencia = normalizar_referencia_catastral(referencia_catastral)
    if len(referencia) <= 7:
        return referencia, ""
    return referencia[:7], referencia[7:]


def _obtener_referencias_ficha(referencia_catastral: str) -> list[str]:
    referencia = normalizar_referencia_catastral(referencia_catastral)
    candidatos: list[str] = []
    for candidata in (referencia, referencia[:14]):
        if candidata and candidata not in candidatos:
            candidatos.append(candidata)
    return candidatos


def _ajustar_tamano_croquis(url: str, ancho: int = 800, alto: int = 800) -> str:
    partes = urlsplit(url)
    params = dict(parse_qsl(partes.query, keep_blank_values=True))
    params["AnchoPixels"] = str(ancho)
    params["AltoPixels"] = str(alto)
    return urlunsplit(
        (partes.scheme, partes.netloc, partes.path, urlencode(params), partes.fragment)
    )


async def _obtener_croquis_desde_ficha(
    client: httpx.AsyncClient,
    referencia_catastral: str,
) -> tuple[bytes | None, str | None]:
    for referencia_ficha in _obtener_referencias_ficha(referencia_catastral):
        rc1, rc2 = _separar_referencia_para_ficha(referencia_ficha)
        respuesta_ficha = await client.get(
            CATASTRO_FICHA_URL,
            params={"RC1": rc1, "RC2": rc2},
        )
        respuesta_ficha.raise_for_status()
        html = respuesta_ficha.text

        contiene_croquis = "Croquis" in html
        candidatos = re.findall(
            r"[^'\"<>\s]*GeneraGraficoParcela\.aspx[^'\"<>\s]*",
            html,
            re.IGNORECASE,
        )
        candidatos_unicos = list(dict.fromkeys(unescape(c) for c in candidatos))

        logger.info(
            "[catastro] Ficha consultada url=%s ref=%s contiene_croquis=%s candidatos=%s",
            respuesta_ficha.url,
            referencia_ficha,
            contiene_croquis,
            candidatos_unicos,
        )

        if not candidatos_unicos:
            continue

        for candidato in candidatos_unicos:
            croquis_url = _ajustar_tamano_croquis(
                urljoin(str(respuesta_ficha.url), candidato)
            )
            logger.info("[catastro] Intentando descargar croquis url=%s", croquis_url)

            respuesta_imagen = await client.get(
                croquis_url,
                headers={"Referer": str(respuesta_ficha.url)},
            )
            content_type = respuesta_imagen.headers.get("content-type", "")
            extension = _detectar_extension_imagen(respuesta_imagen.content)

            logger.info(
                "[catastro] Descarga croquis status=%s content_type=%s es_imagen=%s",
                respuesta_imagen.status_code,
                content_type,
                bool(extension),
            )

            respuesta_imagen.raise_for_status()
            if not extension:
                continue

            return respuesta_imagen.content, extension

    return None, None


async def _obtener_imagen_catastro_wms(
    client: httpx.AsyncClient,
    referencia_catastral: str,
) -> tuple[bytes | None, str | None]:
    respuesta_mapa = await client.get(
        CATASTRO_MAPA_URL,
        params={"refcat": referencia_catastral},
    )
    respuesta_mapa.raise_for_status()
    html = respuesta_mapa.text

    match_x = re.search(r"id=['\"]x['\"].*?value=['\"]([^'\"]+)['\"]", html, re.DOTALL)
    match_y = re.search(r"id=['\"]y['\"].*?value=['\"]([^'\"]+)['\"]", html, re.DOTALL)

    if not match_x or not match_y:
        return None, None

    try:
        x = float(match_x.group(1))
        y = float(match_y.group(1))
    except ValueError:
        return None, None

    margen = 200
    parcela_ref = referencia_catastral[:14]
    respuesta_imagen = await client.get(
        CATASTRO_WMS_URL,
        params={
            "SERVICE": "WMS",
            "REQUEST": "GetMap",
            "VERSION": "1.1.1",
            "LAYERS": "CATASTRO",
            "STYLES": "",
            "SRS": "EPSG:25830",
            "BBOX": f"{x - margen},{y - margen},{x + margen},{y + margen}",
            "WIDTH": "700",
            "HEIGHT": "520",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "RefCat": parcela_ref,
        },
        headers={"Referer": f"{CATASTRO_MAPA_URL}?refcat={referencia_catastral}"},
    )
    respuesta_imagen.raise_for_status()

    contenido = respuesta_imagen.content
    extension = _detectar_extension_imagen(contenido)
    if not extension:
        return None, None

    return contenido, extension


async def _obtener_imagen_catastro(
    client: httpx.AsyncClient,
    referencia_catastral: str,
) -> tuple[bytes | None, str | None, str]:
    logger.info("[catastro] Inicio obtencion de imagen para ref=%s", referencia_catastral)
    imagen_bytes, imagen_extension = _leer_imagen_cache(referencia_catastral)
    if imagen_bytes and imagen_extension:
        logger.info(
            "[catastro] Imagen servida desde cache para ref=%s",
            referencia_catastral,
        )
        return imagen_bytes, imagen_extension, ""

    imagen_bytes, imagen_extension = await _obtener_croquis_desde_ficha(
        client,
        referencia_catastral,
    )
    if imagen_bytes and imagen_extension:
        logger.info("[catastro] Croquis oficial obtenido para ref=%s", referencia_catastral)
        _guardar_imagen_cache(referencia_catastral, imagen_bytes, imagen_extension)
        return imagen_bytes, imagen_extension, ""

    logger.info(
        "[catastro] No fue posible obtener el croquis oficial; se intenta WMS para ref=%s",
        referencia_catastral,
    )
    imagen_bytes, imagen_extension = await _obtener_imagen_catastro_wms(
        client,
        referencia_catastral,
    )
    if imagen_bytes and imagen_extension:
        logger.info("[catastro] Imagen WMS obtenida para ref=%s", referencia_catastral)
        _guardar_imagen_cache(referencia_catastral, imagen_bytes, imagen_extension)
        return (
            imagen_bytes,
            imagen_extension,
            "No se pudo recuperar el croquis oficial de la ficha; se usó la cartografía catastral como alternativa.",
        )

    logger.info("[catastro] No se obtuvo imagen ni croquis para ref=%s", referencia_catastral)
    return None, None, ""


async def consultar_catastro_por_referencia(referencia_catastral: str) -> dict:
    referencia = normalizar_referencia_catastral(referencia_catastral)
    if not referencia:
        raise ValueError("Introduce una referencia catastral.")

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        respuesta = await client.get(
            CATASTRO_CONSULTA_URL,
            params={
                "Provincia": "",
                "Municipio": "",
                "RC": referencia,
            },
        )
        respuesta.raise_for_status()

        try:
            root = ET.fromstring(respuesta.text)
        except ET.ParseError as exc:
            raise ValueError("Respuesta inválida del Catastro.") from exc

        referencia_final = (
            _text(root, ".//cat:rc/cat:pc1")
            + _text(root, ".//cat:rc/cat:pc2")
            + _text(root, ".//cat:rc/cat:car")
            + _text(root, ".//cat:rc/cat:cc1")
            + _text(root, ".//cat:rc/cat:cc2")
        )
        if not referencia_final:
            raise ValueError("No se encontró información para esa referencia catastral.")

        datos = {
            "referencia_catastral": referencia_final,
            "direccion": _construir_direccion(root),
            "codigo_postal": _text(root, ".//cat:lourb/cat:dp"),
            "ciudad": _text(root, ".//cat:dt/cat:nm"),
            "provincia": _text(root, ".//cat:dt/cat:np"),
            "superficie_construida": _text(root, ".//cat:debi/cat:sfc"),
            "uso_inmueble": _text(root, ".//cat:debi/cat:luso"),
            "anio_construccion": _text(root, ".//cat:debi/cat:ant"),
            "imagen_bytes": None,
            "imagen_extension": None,
            "aviso": "",
        }

        try:
            imagen_bytes, imagen_extension, aviso_imagen = await _obtener_imagen_catastro(
                client,
                referencia_final,
            )
            datos["imagen_bytes"] = imagen_bytes
            datos["imagen_extension"] = imagen_extension
            if aviso_imagen:
                datos["aviso"] = aviso_imagen
        except Exception:
            datos["aviso"] = "No se pudo obtener la imagen catastral."

    return datos
