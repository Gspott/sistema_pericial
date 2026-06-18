from __future__ import annotations

import shutil
import tempfile
from urllib.parse import quote
from pathlib import Path
from typing import Any
from uuid import uuid4

try:  # pragma: no cover - fallback defensivo si falta Pillow
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError:  # pragma: no cover
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception


PDF_IMAGE_OPTIMIZATION_DEFAULTS = {
    "master": {
        "optimizar_imagenes": False,
        "jpeg_quality": 95,
        "max_dimension": 3000,
        "remove_exif": False,
    },
    "email": {
        "optimizar_imagenes": True,
        "jpeg_quality": 75,
        "max_dimension": 1400,
        "remove_exif": True,
    },
    "judicial": {
        "optimizar_imagenes": True,
        "jpeg_quality": 60,
        "max_dimension": 1200,
        "remove_exif": True,
    },
    "solo_informe": {
        "optimizar_imagenes": True,
        "jpeg_quality": 80,
        "max_dimension": 1600,
        "remove_exif": True,
    },
    "informe_anexos": {
        "optimizar_imagenes": False,
        "jpeg_quality": 95,
        "max_dimension": 3000,
        "remove_exif": False,
    },
    "anexo_fotografico": {
        "optimizar_imagenes": True,
        "jpeg_quality": 75,
        "max_dimension": 1600,
        "remove_exif": True,
    },
}


def _resolver_config_perfil(perfil: str | dict | None) -> dict:
    if isinstance(perfil, dict):
        codigo = str(perfil.get("codigo") or "master")
        base = dict(PDF_IMAGE_OPTIMIZATION_DEFAULTS.get(codigo, {}))
        base.update(perfil)
        return base
    codigo = str(perfil or "master")
    return dict(PDF_IMAGE_OPTIMIZATION_DEFAULTS.get(codigo, PDF_IMAGE_OPTIMIZATION_DEFAULTS["master"]))


def _normalizar_rgb(imagen):
    if imagen.mode in ("RGBA", "LA"):
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen.convert("RGBA"), mask=imagen.convert("RGBA").getchannel("A"))
        return fondo
    if imagen.mode == "P":
        return _normalizar_rgb(imagen.convert("RGBA"))
    if imagen.mode != "RGB":
        return imagen.convert("RGB")
    return imagen


def optimizar_imagen_pdf(
    ruta_imagen,
    perfil: str | dict = "master",
    carpeta_temporal: str | Path | None = None,
) -> dict:
    ruta_origen = Path(ruta_imagen)
    config = _resolver_config_perfil(perfil)
    tamano_original = ruta_origen.stat().st_size if ruta_origen.exists() else 0

    if not config.get("optimizar_imagenes") or Image is None or ImageOps is None:
        return {
            "ruta": ruta_origen,
            "ruta_temporal": False,
            "tamano_original": tamano_original,
            "tamano_optimizado": tamano_original,
            "reduccion_porcentaje": 0,
        }

    carpeta = Path(carpeta_temporal) if carpeta_temporal else Path(tempfile.mkdtemp(prefix="pericial_pdf_img_"))
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_destino = carpeta / f"{ruta_origen.stem}-pdf-{config.get('codigo', 'perfil')}.jpg"

    try:
        with Image.open(ruta_origen) as imagen_original:
            imagen_original.load()
            imagen = ImageOps.exif_transpose(imagen_original)
            imagen = _normalizar_rgb(imagen)
            max_dimension = int(config.get("max_dimension") or 0)
            if max_dimension > 0 and max(imagen.size) > max_dimension:
                imagen.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            imagen.save(
                ruta_destino,
                format="JPEG",
                quality=int(config.get("jpeg_quality") or 75),
                optimize=True,
                progressive=True,
            )
    except (OSError, UnidentifiedImageError, ValueError):
        return {
            "ruta": ruta_origen,
            "ruta_temporal": False,
            "tamano_original": tamano_original,
            "tamano_optimizado": tamano_original,
            "reduccion_porcentaje": 0,
        }

    tamano_optimizado = ruta_destino.stat().st_size if ruta_destino.exists() else tamano_original
    reduccion = 0
    if tamano_original:
        reduccion = round(max(0, 1 - (tamano_optimizado / tamano_original)) * 100, 2)
    return {
        "ruta": ruta_destino,
        "ruta_temporal": True,
        "tamano_original": tamano_original,
        "tamano_optimizado": tamano_optimizado,
        "reduccion_porcentaje": reduccion,
    }


class PdfImageOptimizationSession:
    def __init__(self, perfil: str | dict):
        self.perfil = _resolver_config_perfil(perfil)
        self.temp_dir = tempfile.mkdtemp(prefix="pericial_pdf_images_")
        self.token = uuid4().hex
        self.public_url_base = ""
        self.cache: dict[str, dict] = {}
        self.metricas = {
            "imagenes": 0,
            "tamano_original": 0,
            "tamano_optimizado": 0,
            "reduccion_porcentaje": 0,
            "diagnostico": [],
        }

    @property
    def activa(self) -> bool:
        return bool(self.perfil.get("optimizar_imagenes")) and Image is not None and ImageOps is not None

    def optimizar(self, ruta_imagen: str | Path) -> dict:
        clave = str(Path(ruta_imagen).resolve())
        if clave not in self.cache:
            resultado = optimizar_imagen_pdf(
                ruta_imagen,
                self.perfil,
                carpeta_temporal=self.temp_dir,
            )
            self.cache[clave] = resultado
            if resultado.get("ruta_temporal"):
                self.metricas["imagenes"] += 1
                self.metricas["tamano_original"] += int(resultado.get("tamano_original") or 0)
                self.metricas["tamano_optimizado"] += int(resultado.get("tamano_optimizado") or 0)
                original = self.metricas["tamano_original"]
                optimizado = self.metricas["tamano_optimizado"]
                if original:
                    self.metricas["reduccion_porcentaje"] = round(
                        max(0, 1 - (optimizado / original)) * 100,
                        2,
                    )
        return self.cache[clave]

    def url_publica_temporal(self, ruta_imagen: str | Path) -> str:
        if not self.public_url_base:
            return Path(ruta_imagen).resolve().as_uri()
        return f"{self.public_url_base.rstrip('/')}/{self.token}/{quote(Path(ruta_imagen).name)}"

    def cleanup(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def crear_sesion_optimizacion_pdf(perfil: str | dict) -> PdfImageOptimizationSession:
    return PdfImageOptimizationSession(perfil)


def optimizar_contexto_imagenes_pdf(
    contexto: Any,
    sesion: PdfImageOptimizationSession,
    upload_dir: str | Path,
    public_url_base: str = "",
) -> dict:
    if not sesion.activa:
        return sesion.metricas

    sesion.public_url_base = public_url_base
    upload_path = Path(upload_dir)

    def visitar(nodo):
        if isinstance(nodo, dict):
            archivo = nodo.get("archivo")
            url = nodo.get("url")
            if archivo and url:
                ruta_origen = upload_path / str(archivo)
                if ruta_origen.exists():
                    resultado = sesion.optimizar(ruta_origen)
                    if resultado.get("ruta_temporal"):
                        ruta_optimizada = Path(resultado["ruta"]).resolve()
                        url_optimizada = sesion.url_publica_temporal(ruta_optimizada)
                        nodo["url_original"] = url
                        nodo["url"] = url_optimizada
                        nodo["ruta_optimizada_pdf"] = str(ruta_optimizada)
                        sesion.metricas["diagnostico"].append(
                            {
                                "archivo": str(archivo),
                                "campo": "url",
                                "url_original": str(url),
                                "url_optimizada": url_optimizada,
                                "ruta_original": str(ruta_origen),
                                "ruta_optimizada": str(ruta_optimizada),
                                "existe_original": ruta_origen.exists(),
                                "existe_optimizada": ruta_optimizada.exists(),
                            }
                        )
                    else:
                        sesion.metricas["diagnostico"].append(
                            {
                                "archivo": str(archivo),
                                "campo": "url",
                                "url_original": str(url),
                                "url_optimizada": str(url),
                                "ruta_original": str(ruta_origen),
                                "ruta_optimizada": "",
                                "existe_original": ruta_origen.exists(),
                                "existe_optimizada": False,
                                "fallback_original": True,
                            }
                        )
            for valor in nodo.values():
                visitar(valor)
        elif isinstance(nodo, list):
            for item in nodo:
                visitar(item)

    visitar(contexto)
    return sesion.metricas
