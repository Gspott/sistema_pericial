from __future__ import annotations

import tempfile
from io import BytesIO
from pathlib import Path


PDF_PAGINATION_CONFIG = {
    "enabled": True,
    "format": "Página {x} de {y}",
    "position": "footer_center",
}


def _texto_pdf_literal(texto: str) -> str:
    return (
        texto.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("á", "\\341")
    )


def _anadir_paginacion_a_pagina(pagina, texto: str, writer=None) -> None:
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    ancho = float(pagina.mediabox.width)
    x = max(18, (ancho / 2) - (len(texto) * 2.1))
    contenido = (
        "q\n"
        "BT\n"
        "/Fpg 8 Tf\n"
        "0.38 0.42 0.48 rg\n"
        f"1 0 0 1 {x:.2f} 18 Tm\n"
        f"({_texto_pdf_literal(texto)}) Tj\n"
        "ET\n"
        "Q\n"
    )

    recursos = pagina.get("/Resources")
    if recursos is None:
        recursos = DictionaryObject()
        pagina[NameObject("/Resources")] = recursos
    elif hasattr(recursos, "get_object"):
        recursos = recursos.get_object()
    fuente = recursos.get("/Font")
    if fuente is None:
        fuente = DictionaryObject()
        recursos[NameObject("/Font")] = fuente
    elif hasattr(fuente, "get_object"):
        fuente = fuente.get_object()
    fuente[NameObject("/Fpg")] = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        }
    )

    stream = DecodedStreamObject()
    stream.set_data(contenido.encode("ascii"))
    stream_ref = writer._add_object(stream) if writer is not None else stream
    contenidos = pagina.get("/Contents")
    if contenidos is None:
        pagina[NameObject("/Contents")] = stream_ref
    elif isinstance(contenidos, ArrayObject):
        contenidos.append(stream_ref)
    else:
        pagina[NameObject("/Contents")] = ArrayObject([contenidos, stream_ref])


def paginar_pdf_final_bytes(
    pdf_bytes: bytes,
    perfil: str | dict = "master",
    config: dict | None = None,
) -> bytes:
    configuracion = {**PDF_PAGINATION_CONFIG, **(config or {})}
    if not configuracion.get("enabled"):
        return pdf_bytes

    try:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(BytesIO(pdf_bytes))
        total_paginas = len(reader.pages)
        if total_paginas <= 0:
            return pdf_bytes

        writer = PdfWriter()
        for indice, pagina in enumerate(reader.pages, start=1):
            texto = configuracion["format"].format(x=indice, y=total_paginas)
            _anadir_paginacion_a_pagina(pagina, texto, writer=writer)
            writer.add_page(pagina)

        salida = BytesIO()
        writer.write(salida)
        return salida.getvalue()
    except Exception:
        return pdf_bytes


def paginar_pdf_final(
    ruta_pdf,
    perfil: str | dict = "master",
    carpeta_temporal: str | Path | None = None,
    config: dict | None = None,
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
        )
    )
    return ruta_destino
