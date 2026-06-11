import shutil
import subprocess
from pathlib import Path

from app.services.costes_parser import parsear_coste_desde_texto


def _extraer_con_pytesseract(ruta_imagen: Path) -> tuple[str, list[str], bool]:
    try:
        from PIL import Image
    except ImportError:
        return "", ["Pillow no está disponible para abrir la imagen."], False

    try:
        import pytesseract
    except ImportError:
        return "", ["pytesseract no está instalado; se mantiene revisión manual."], False

    try:
        with Image.open(ruta_imagen) as imagen:
            return pytesseract.image_to_string(imagen, lang="spa+eng"), [], True
    except Exception as exc:  # pragma: no cover - defensivo ante entornos OCR variables
        return "", [f"No se pudo ejecutar OCR local con pytesseract: {exc}"], False


def _extraer_con_tesseract_binario(ruta_imagen: Path) -> tuple[str, list[str], bool]:
    tesseract_path = shutil.which("tesseract")
    if not tesseract_path:
        return "", ["Binario tesseract no disponible; se mantiene revisión manual."], False

    try:
        resultado = subprocess.run(
            [tesseract_path, str(ruta_imagen), "stdout", "-l", "spa+eng"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", [f"No se pudo ejecutar tesseract local: {exc}"], False

    if resultado.returncode != 0:
        detalle = (resultado.stderr or "").strip()
        mensaje = "tesseract local no devolvió texto utilizable."
        if detalle:
            mensaje = f"{mensaje} {detalle[:180]}"
        return "", [mensaje], False
    return resultado.stdout or "", [], True


def extraer_coste_desde_imagen(ruta_imagen: str | Path) -> dict:
    ruta = Path(ruta_imagen)
    advertencias = []
    texto_detectado = ""
    ocr_disponible = False

    if not ruta.exists() or not ruta.is_file():
        advertencias.append("La imagen de captura no existe o no es un archivo.")
    else:
        texto_detectado, avisos, ocr_disponible = _extraer_con_pytesseract(ruta)
        advertencias.extend(avisos)
        if not ocr_disponible:
            texto_detectado, avisos_binario, ocr_disponible = _extraer_con_tesseract_binario(ruta)
            advertencias.extend(avisos_binario)

    parseado = parsear_coste_desde_texto(texto_detectado)
    advertencias.extend(parseado["advertencias"])
    return {
        "ocr_disponible": ocr_disponible,
        "texto_detectado": texto_detectado,
        "texto_ocr": texto_detectado,
        "datos_parseados": parseado["datos_parseados"],
        "advertencias": advertencias,
        "confianza": parseado.get("confianza", {}),
        "campos_detectados": parseado.get("campos_detectados", {}),
        "version_parser": parseado.get("version_parser", "costes-2d"),
    }
