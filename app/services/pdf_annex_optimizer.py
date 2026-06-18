from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


GHOSTSCRIPT_PROFILES = {
    "email": {
        "pdfsettings": "/ebook",
        "timeout": 120,
    },
    "judicial": {
        "pdfsettings": "/screen",
        "timeout": 120,
    },
}


def bytes_a_mb(tamano_bytes: int | float | None) -> float:
    return round((float(tamano_bytes or 0) / (1024 * 1024)), 2)


def analizar_peso_pdf(path) -> dict:
    ruta = Path(path)
    tamano = ruta.stat().st_size if ruta.exists() else 0
    paginas = 0
    if ruta.exists():
        try:
            from pypdf import PdfReader

            paginas = len(PdfReader(str(ruta)).pages)
        except Exception:
            paginas = 0
    return {
        "ruta": ruta,
        "existe": ruta.exists(),
        "tamano_bytes": tamano,
        "tamano_mb": bytes_a_mb(tamano),
        "paginas": paginas,
    }


def _codigo_perfil(perfil: str | dict | None) -> str:
    codigo = perfil.get("codigo") if isinstance(perfil, dict) else perfil
    return str(codigo or "master")


def detectar_ghostscript() -> str | None:
    return shutil.which("gs")


def construir_comando_ghostscript(
    gs_path: str,
    ruta_origen: Path,
    ruta_destino: Path,
    perfil: str | dict | None,
) -> list[str]:
    codigo = _codigo_perfil(perfil)
    config = GHOSTSCRIPT_PROFILES.get(codigo, GHOSTSCRIPT_PROFILES["email"])
    return [
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={config['pdfsettings']}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={ruta_destino}",
        str(ruta_origen),
    ]


def _pdf_externo_valido(ruta: Path) -> bool:
    if not ruta.exists() or ruta.suffix.lower() != ".pdf":
        return False
    try:
        return ruta.read_bytes()[:5] == b"%PDF-"
    except OSError:
        return False


def _optimizar_con_ghostscript(ruta_origen: Path, ruta_destino: Path, perfil: str | dict | None) -> bool:
    gs = detectar_ghostscript()
    if not gs:
        return False
    codigo = _codigo_perfil(perfil)
    config = GHOSTSCRIPT_PROFILES.get(codigo, GHOSTSCRIPT_PROFILES["email"])
    comando = construir_comando_ghostscript(gs, ruta_origen, ruta_destino, perfil)
    try:
        subprocess.run(comando, check=True, timeout=config["timeout"])
    except Exception:
        ruta_destino.unlink(missing_ok=True)
        return False
    return ruta_destino.exists() and ruta_destino.stat().st_size > 0


def _optimizar_con_pypdf(ruta_origen: Path, ruta_destino: Path) -> bool:
    try:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(str(ruta_origen))
        writer = PdfWriter()
        for page in reader.pages:
            try:
                page.compress_content_streams()
            except Exception:
                pass
            writer.add_page(page)
        with ruta_destino.open("wb") as buffer:
            writer.write(buffer)
    except Exception:
        return False
    return ruta_destino.exists() and ruta_destino.stat().st_size > 0


def optimizar_pdf_externo(
    path,
    perfil: str | dict = "master",
    carpeta_temporal: str | Path | None = None,
) -> dict:
    ruta_origen = Path(path)
    tamano_original = ruta_origen.stat().st_size if ruta_origen.exists() else 0
    codigo = _codigo_perfil(perfil)
    if codigo not in {"email", "judicial"}:
        return {
            "ruta": ruta_origen,
            "optimizado": False,
            "metodo": "none",
            "tamano_original": tamano_original,
            "tamano_final": tamano_original,
            "reduccion_porcentaje": 0,
            "mensaje": "Perfil sin compresión de anexos externos.",
        }
    if not _pdf_externo_valido(ruta_origen):
        return {
            "ruta": ruta_origen,
            "optimizado": False,
            "metodo": "none",
            "tamano_original": tamano_original,
            "tamano_final": tamano_original,
            "reduccion_porcentaje": 0,
            "mensaje": "El archivo no existe o no parece un PDF válido.",
        }

    carpeta = Path(carpeta_temporal) if carpeta_temporal else Path(tempfile.mkdtemp(prefix="pericial_pdf_annex_"))
    carpeta.mkdir(parents=True, exist_ok=True)

    for metodo, optimizador in (
        ("ghostscript", lambda origen, destino: _optimizar_con_ghostscript(origen, destino, perfil)),
        ("pypdf", _optimizar_con_pypdf),
    ):
        ruta_destino = carpeta / f"{ruta_origen.stem}-{codigo}-{metodo}.pdf"
        if not optimizador(ruta_origen, ruta_destino):
            continue
        tamano_final = ruta_destino.stat().st_size
        reduccion = 0
        if tamano_original:
            reduccion = round(max(0, 1 - (tamano_final / tamano_original)) * 100, 2)
        if tamano_final < tamano_original:
            return {
                "ruta": ruta_destino,
                "optimizado": True,
                "metodo": metodo,
                "tamano_original": tamano_original,
                "tamano_final": tamano_final,
                "reduccion_porcentaje": reduccion,
                "mensaje": f"PDF externo optimizado con {metodo}.",
            }
        ruta_destino.unlink(missing_ok=True)

    return {
        "ruta": ruta_origen,
        "optimizado": False,
        "metodo": "none",
        "tamano_original": tamano_original,
        "tamano_final": tamano_original,
        "reduccion_porcentaje": 0,
        "mensaje": "No se obtuvo una versión más ligera; se conserva el PDF original.",
    }


class PdfAnnexOptimizationSession:
    def __init__(self, perfil: str | dict):
        self.perfil = perfil
        self.temp_dir = tempfile.mkdtemp(prefix="pericial_pdf_annexes_")
        self.cache: dict[str, dict] = {}
        self.resultados: list[dict] = []

    def optimizar(self, path, categoria: str = "") -> dict:
        clave = str(Path(path).resolve())
        if clave not in self.cache:
            resultado = optimizar_pdf_externo(
                path,
                self.perfil,
                carpeta_temporal=self.temp_dir,
            )
            resultado["categoria"] = categoria
            self.cache[clave] = resultado
            self.resultados.append(resultado)
        return self.cache[clave]

    def cleanup(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def crear_sesion_optimizacion_anexos_pdf(perfil: str | dict) -> PdfAnnexOptimizationSession:
    return PdfAnnexOptimizationSession(perfil)
