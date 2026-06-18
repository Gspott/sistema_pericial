from __future__ import annotations

import logging
import tempfile
import time
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)


PDF_PAGINATION_CONFIG = {
    "enabled": True,
    "format": "Página {x} de {y}",
    "position": "footer_center",
    "font_name": "Helvetica",
    "font_size": 8.5,
    "text_color": (0, 0, 0),
    "box_fill": (1, 1, 1),
    "box_width": 118,
    "box_height": 16,
    "margin_bottom": 18,
}


def _normalizar_rotacion_pagina(pagina) -> None:
    rotacion = int(pagina.get("/Rotate", 0) or 0) % 360
    if rotacion and hasattr(pagina, "transfer_rotation_to_content"):
        pagina.transfer_rotation_to_content()


def _tamano_visible_pagina(pagina) -> tuple[float, float]:
    caja = getattr(pagina, "cropbox", None) or pagina.mediabox
    return float(caja.width), float(caja.height)


def _crear_overlay_paginacion(
    ancho: float,
    alto: float,
    texto: str,
    config: dict,
) -> bytes:
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    fuente = config["font_name"]
    tamano_fuente = float(config["font_size"])
    box_width = float(config["box_width"])
    box_height = float(config["box_height"])
    y = max(8.0, float(config["margin_bottom"]))
    x = max(8.0, (ancho - box_width) / 2)

    c.saveState()
    c.setFillColorRGB(*config["box_fill"])
    c.roundRect(x, y - 4, box_width, box_height, 2, stroke=0, fill=1)
    c.setFont(fuente, tamano_fuente)
    c.setFillColorRGB(*config["text_color"])
    c.drawCentredString(ancho / 2, y, texto)
    c.restoreState()
    c.save()
    return buffer.getvalue()


def _merge_overlay_visible(pagina, overlay_page) -> None:
    pagina.merge_page(overlay_page, over=True)


def _guardar_debug_pdf(
    debug_dir: str | Path | None,
    nombre: str,
    contenido: bytes,
) -> Path | None:
    if not debug_dir:
        return None
    carpeta = Path(debug_dir)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    ruta.write_bytes(contenido)
    return ruta


def paginar_pdf_final_bytes(
    pdf_bytes: bytes,
    perfil: str | dict = "master",
    config: dict | None = None,
    debug: bool = False,
    debug_dir: str | Path | None = None,
) -> bytes:
    configuracion = {**PDF_PAGINATION_CONFIG, **(config or {})}
    if not configuracion.get("enabled"):
        return pdf_bytes

    inicio = time.perf_counter()
    try:
        from pypdf import PdfReader, PdfWriter

        _guardar_debug_pdf(debug_dir, "final_antes_paginacion.pdf", pdf_bytes)
        reader = PdfReader(BytesIO(pdf_bytes))
        total_paginas = len(reader.pages)
        if total_paginas <= 0:
            return pdf_bytes

        writer = PdfWriter()
        overlay_test = None
        for indice, pagina in enumerate(reader.pages, start=1):
            _normalizar_rotacion_pagina(pagina)
            ancho, alto = _tamano_visible_pagina(pagina)
            texto = configuracion["format"].format(x=indice, y=total_paginas)
            overlay_bytes = _crear_overlay_paginacion(ancho, alto, texto, configuracion)
            if indice == 1:
                overlay_test = overlay_bytes
            overlay_page = PdfReader(BytesIO(overlay_bytes)).pages[0]
            writer.add_page(pagina)
            _merge_overlay_visible(writer.pages[-1], overlay_page)

        salida = BytesIO()
        writer.write(salida)
        resultado = salida.getvalue()
        _guardar_debug_pdf(debug_dir, "final_despues_paginacion.pdf", resultado)
        if overlay_test:
            _guardar_debug_pdf(debug_dir, "overlay_test_page_1.pdf", overlay_test)
        if debug:
            logger.info(
                "PDF final paginado: paginas=%s tamano_original=%s tamano_final=%s duracion_s=%.3f debug_dir=%s",
                total_paginas,
                len(pdf_bytes),
                len(resultado),
                time.perf_counter() - inicio,
                str(debug_dir or ""),
            )
        return resultado
    except Exception as exc:
        logger.warning("No se pudo paginar el PDF final: %s", exc)
        return pdf_bytes


def paginar_pdf_final(
    ruta_pdf,
    perfil: str | dict = "master",
    carpeta_temporal: str | Path | None = None,
    config: dict | None = None,
    debug: bool = False,
    debug_dir: str | Path | None = None,
) -> Path:
    ruta_origen = Path(ruta_pdf)
    carpeta = Path(carpeta_temporal) if carpeta_temporal else Path(tempfile.mkdtemp(prefix="pericial_pdf_paginated_"))
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta_destino = carpeta / f"{ruta_origen.stem}-paginado.pdf"
    ruta_destino.write_bytes(
        paginar_pdf_final_bytes(
            ruta_origen.read_bytes(),
            perfil=perfil,
            config=config,
            debug=debug,
            debug_dir=debug_dir,
        )
    )
    return ruta_destino
