import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.config import BACKUPS_DIR, BASE_DIR, EXPORTS_DIR, UPLOAD_DIR
from app.routers.facturacion import calcular_resumen_iva

EXPORTS_PATH = Path(EXPORTS_DIR).resolve()
UPLOADS_PATH = Path(UPLOAD_DIR).resolve()
BASE_PATH = Path(BASE_DIR).resolve()
BACKUPS_PATH = Path(BACKUPS_DIR).resolve()


def escribir_csv(columnas: list[str], filas: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columnas, extrasaction="ignore")
    writer.writeheader()
    for fila in filas:
        writer.writerow({columna: fila.get(columna, "") for columna in columnas})
    return buffer.getvalue()


def nombre_cliente(factura) -> str:
    razon_social = (factura["cliente_razon_social"] or "").strip()
    if razon_social:
        return razon_social
    partes = [
        (factura["cliente_nombre"] or "").strip(),
        (factura["cliente_apellidos"] or "").strip(),
    ]
    return " ".join(parte for parte in partes if parte)


def resolver_archivo_en_uploads(nombre_archivo: str | None) -> Path | None:
    if not nombre_archivo:
        return None
    nombre_seguro = Path(nombre_archivo).name
    if nombre_seguro != nombre_archivo:
        return None
    ruta = (UPLOADS_PATH / nombre_seguro).resolve()
    if UPLOADS_PATH not in ruta.parents:
        return None
    if not ruta.exists() or not ruta.is_file():
        return None
    return ruta


def resolver_pdf_seguro(pdf_path: str | None) -> Path | None:
    if not pdf_path:
        return None
    if pdf_path.startswith("/uploads/"):
        return resolver_archivo_en_uploads(pdf_path.removeprefix("/uploads/"))
    ruta = Path(pdf_path).expanduser()
    if not ruta.is_absolute():
        return None
    ruta = ruta.resolve()
    if BASE_PATH not in ruta.parents:
        return None
    if BACKUPS_PATH in ruta.parents or EXPORTS_PATH in ruta.parents:
        return None
    if not ruta.exists() or not ruta.is_file():
        return None
    return ruta


def copiar_archivo_seguro(zip_file: ZipFile, origen: Path | None, carpeta: str, prefijo: str):
    if not origen:
        return ""
    nombre = f"{prefijo}_{origen.name}"
    zip_file.write(origen, f"{carpeta}/{nombre}")
    return f"{carpeta}/{nombre}"


def crear_exportacion_trimestral(owner_user_id, year, trimestre) -> Path:
    EXPORTS_PATH.mkdir(parents=True, exist_ok=True)
    resumen = calcular_resumen_iva(owner_user_id, year, trimestre)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_zip = EXPORTS_PATH / (
        f"exportacion_asesoria_{year}_T{trimestre}_{timestamp}.zip"
    )

    facturas_rows = []
    gastos_rows = []
    pdf_paths_por_factura = {}
    adjuntos_por_gasto = {}

    with ZipFile(ruta_zip, "w", ZIP_DEFLATED) as zip_file:
        for factura in resumen["facturas"]:
            pdf_interno = copiar_archivo_seguro(
                zip_file,
                resolver_pdf_seguro(factura["pdf_path"]),
                "facturas_pdf",
                f"factura_{factura['id']}",
            )
            pdf_paths_por_factura[factura["id"]] = pdf_interno

        for gasto in resumen["gastos"]:
            adjunto_interno = copiar_archivo_seguro(
                zip_file,
                resolver_archivo_en_uploads(gasto["archivo_path"]),
                "gastos_adjuntos",
                f"gasto_{gasto['id']}",
            )
            adjuntos_por_gasto[gasto["id"]] = adjunto_interno

        resumen_csv = escribir_csv(
            [
                "year",
                "trimestre",
                "fecha_inicio",
                "fecha_fin",
                "base_facturas_emitidas",
                "iva_repercutido",
                "total_facturado",
                "base_gastos_deducibles",
                "iva_soportado",
                "total_gastos_deducibles",
                "resultado_iva_estimado",
            ],
            [
                {
                    "year": year,
                    "trimestre": trimestre,
                    "fecha_inicio": resumen["fecha_inicio"],
                    "fecha_fin": resumen["fecha_fin"],
                    "base_facturas_emitidas": resumen["bases_facturas"],
                    "iva_repercutido": resumen["iva_repercutido"],
                    "total_facturado": resumen["total_facturado"],
                    "base_gastos_deducibles": resumen["bases_gastos"],
                    "iva_soportado": resumen["iva_soportado"],
                    "total_gastos_deducibles": resumen["total_gastos"],
                    "resultado_iva_estimado": resumen["resultado_estimado"],
                }
            ],
        )
        zip_file.writestr("resumen_iva.csv", resumen_csv)

        for factura in resumen["facturas"]:
            facturas_rows.append(
                {
                    "fecha": factura["fecha"],
                    "numero_factura": factura["numero_factura"] or "",
                    "cliente": nombre_cliente(factura),
                    "nif_cif": factura["cliente_nif_cif"] or "",
                    "base_imponible": factura["base_imponible"] or 0,
                    "iva": factura["iva"] or 0,
                    "irpf": factura["irpf"] or 0,
                    "total": factura["total"] or 0,
                    "estado": factura["estado"],
                    "tipo_factura": factura["tipo_factura"] or "ordinaria",
                    "factura_rectificada_id": factura["factura_rectificada_id"] or "",
                    "hash_factura": factura["hash_factura"] or "",
                    "hash_anterior": factura["hash_anterior"] or "",
                    "verifactu_estado": factura["verifactu_estado"] or "",
                    "propuesta_id": factura["propuesta_id"] or "",
                    "expediente_id": factura["expediente_id"] or "",
                    "pdf_path": pdf_paths_por_factura.get(factura["id"], ""),
                }
            )
        zip_file.writestr(
            "facturas_emitidas.csv",
            escribir_csv(
                [
                    "fecha",
                    "numero_factura",
                    "cliente",
                    "nif_cif",
                    "base_imponible",
                    "iva",
                    "irpf",
                    "total",
                    "estado",
                    "tipo_factura",
                    "factura_rectificada_id",
                    "hash_factura",
                    "hash_anterior",
                    "verifactu_estado",
                    "propuesta_id",
                    "expediente_id",
                    "pdf_path",
                ],
                facturas_rows,
            ),
        )

        for gasto in resumen["gastos"]:
            gastos_rows.append(
                {
                    "fecha": gasto["fecha"],
                    "proveedor": gasto["proveedor"],
                    "nif_proveedor": gasto["nif_proveedor"] or "",
                    "numero_factura": gasto["numero_factura"] or "",
                    "concepto": gasto["concepto"],
                    "categoria": gasto["categoria"] or "",
                    "base_imponible": gasto["base_imponible"] or 0,
                    "iva_porcentaje": gasto["iva_porcentaje"] or 0,
                    "iva_importe": gasto["iva_importe"] or 0,
                    "total": gasto["total"] or 0,
                    "archivo_path": adjuntos_por_gasto.get(gasto["id"], ""),
                }
            )
        zip_file.writestr(
            "gastos_deducibles.csv",
            escribir_csv(
                [
                    "fecha",
                    "proveedor",
                    "nif_proveedor",
                    "numero_factura",
                    "concepto",
                    "categoria",
                    "base_imponible",
                    "iva_porcentaje",
                    "iva_importe",
                    "total",
                    "archivo_path",
                ],
                gastos_rows,
            ),
        )

    return ruta_zip
