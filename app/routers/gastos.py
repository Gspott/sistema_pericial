import os
import shutil
from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import UPLOAD_DIR
from app.database import get_connection

router = APIRouter()

EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif"}
UPLOAD_PATH = Path(UPLOAD_DIR)


def get_current_user(request: Request):
    current_user = getattr(request.state, "current_user", None)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return current_user


def render_template(request: Request, template_name: str, context: dict | None = None):
    data = {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
    }
    if context:
        data.update(context)
    return request.app.state.templates.TemplateResponse(template_name, data)


def limpiar_texto(valor: str | None) -> str:
    return (valor or "").strip()


def parse_float(valor: str | None, default: float = 0.0) -> float:
    valor_limpio = limpiar_texto(valor)
    if not valor_limpio:
        return default
    try:
        return float(valor_limpio.replace(",", "."))
    except ValueError:
        return default


def format_money(valor: float | int | None) -> str:
    return f"{float(valor or 0):.2f}"


def calcular_importes(base_imponible: float, iva_porcentaje: float):
    iva_importe = base_imponible * iva_porcentaje / 100
    total = base_imponible + iva_importe
    return iva_importe, total


def get_owned_gasto(cur, gasto_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM gastos
        WHERE id = ? AND owner_user_id = ?
        """,
        (gasto_id, owner_user_id),
    ).fetchone()


def guardar_archivo_gasto(archivo: UploadFile | None) -> str | None:
    if not archivo or not archivo.filename:
        return None

    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no permitido. Usa PDF, JPG, PNG o HEIC.",
        )

    UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"gasto_{uuid4().hex}{extension}"
    ruta_destino = UPLOAD_PATH / nombre_archivo
    with ruta_destino.open("wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    return nombre_archivo


def borrar_archivo_gasto(nombre_archivo: str | None):
    nombre_limpio = limpiar_texto(nombre_archivo)
    if not nombre_limpio or Path(nombre_limpio).name != nombre_limpio:
        return

    ruta = UPLOAD_PATH / nombre_limpio
    try:
        if ruta.exists() and ruta.is_file():
            ruta.unlink()
    except OSError:
        pass


def preparar_gasto_form(
    fecha: str,
    proveedor: str,
    nif_proveedor: str,
    numero_factura: str,
    concepto: str,
    categoria: str,
    base_imponible: str,
    iva_porcentaje: str,
    deducible: str,
    notas: str,
    gasto_id: int | None = None,
    archivo_path: str = "",
):
    base = parse_float(base_imponible, 0)
    iva_pct = parse_float(iva_porcentaje, 21)
    iva_importe, total = calcular_importes(base, iva_pct)
    return {
        "id": gasto_id,
        "fecha": limpiar_texto(fecha),
        "proveedor": limpiar_texto(proveedor),
        "nif_proveedor": limpiar_texto(nif_proveedor),
        "numero_factura": limpiar_texto(numero_factura),
        "concepto": limpiar_texto(concepto),
        "categoria": limpiar_texto(categoria),
        "base_imponible": base,
        "iva_porcentaje": iva_pct,
        "iva_importe": iva_importe,
        "total": total,
        "deducible": 1 if limpiar_texto(deducible) == "1" else 0,
        "archivo_path": limpiar_texto(archivo_path),
        "notas": limpiar_texto(notas),
    }


def validar_gasto(gasto: dict) -> str:
    if not gasto["fecha"]:
        return "La fecha es obligatoria."
    if not gasto["proveedor"]:
        return "El proveedor es obligatorio."
    if not gasto["concepto"]:
        return "El concepto es obligatorio."
    return ""


@router.get("/gastos", response_class=HTMLResponse)
def listar_gastos(
    request: Request,
    year: int | None = Query(None),
    trimestre: int | None = Query(None),
    deducible: str = Query(""),
):
    current_user = get_current_user(request)
    filtros = ["owner_user_id = ?"]
    params: list[object] = [current_user["id"]]

    if year:
        filtros.append("strftime('%Y', fecha) = ?")
        params.append(str(year))
    if trimestre in (1, 2, 3, 4):
        inicio = (trimestre - 1) * 3 + 1
        fin = inicio + 2
        filtros.append("CAST(strftime('%m', fecha) AS INTEGER) BETWEEN ? AND ?")
        params.extend([inicio, fin])
    if deducible in ("0", "1"):
        filtros.append("deducible = ?")
        params.append(int(deducible))

    conn = get_connection()
    cur = conn.cursor()
    try:
        gastos = cur.execute(
            f"""
            SELECT *
            FROM gastos
            WHERE {' AND '.join(filtros)}
            ORDER BY fecha DESC, id DESC
            """,
            params,
        ).fetchall()
        resumen = cur.execute(
            f"""
            SELECT
                COALESCE(SUM(base_imponible), 0) AS base,
                COALESCE(SUM(iva_importe), 0) AS iva,
                COALESCE(SUM(total), 0) AS total
            FROM gastos
            WHERE {' AND '.join(filtros)}
            """,
            params,
        ).fetchone()
    finally:
        conn.close()

    return render_template(
        request,
        "gastos/listado.html",
        {
            "gastos": gastos,
            "resumen": resumen,
            "year": year or "",
            "trimestre": trimestre or "",
            "deducible": deducible,
            "format_money": format_money,
        },
    )


@router.get("/gastos/nuevo", response_class=HTMLResponse)
def nuevo_gasto(request: Request):
    get_current_user(request)
    return render_template(
        request,
        "gastos/form.html",
        {
            "gasto": {
                "fecha": str(date.today()),
                "base_imponible": 0,
                "iva_porcentaje": 21,
                "iva_importe": 0,
                "total": 0,
                "deducible": 1,
            },
            "form_action": "/gastos/nuevo",
            "titulo": "Nuevo gasto",
            "submit_label": "Guardar gasto",
            "error": "",
            "format_money": format_money,
        },
    )


@router.post("/gastos/nuevo")
def crear_gasto(
    request: Request,
    fecha: str = Form(...),
    proveedor: str = Form(...),
    nif_proveedor: str = Form(""),
    numero_factura: str = Form(""),
    concepto: str = Form(...),
    categoria: str = Form(""),
    base_imponible: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    deducible: str = Form("0"),
    notas: str = Form(""),
    archivo: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    gasto = preparar_gasto_form(
        fecha,
        proveedor,
        nif_proveedor,
        numero_factura,
        concepto,
        categoria,
        base_imponible,
        iva_porcentaje,
        deducible,
        notas,
    )
    error = validar_gasto(gasto)
    if error:
        return render_template(
            request,
            "gastos/form.html",
            {
                "gasto": gasto,
                "form_action": "/gastos/nuevo",
                "titulo": "Nuevo gasto",
                "submit_label": "Guardar gasto",
                "error": error,
                "format_money": format_money,
            },
        )

    archivo_path = guardar_archivo_gasto(archivo)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO gastos (
                fecha, proveedor, nif_proveedor, numero_factura, concepto,
                categoria, base_imponible, iva_porcentaje, iva_importe, total,
                deducible, archivo_path, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                gasto["fecha"],
                gasto["proveedor"],
                gasto["nif_proveedor"],
                gasto["numero_factura"],
                gasto["concepto"],
                gasto["categoria"],
                gasto["base_imponible"],
                gasto["iva_porcentaje"],
                gasto["iva_importe"],
                gasto["total"],
                gasto["deducible"],
                archivo_path,
                gasto["notas"],
                current_user["id"],
            ),
        )
        gasto_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/gastos/{gasto_id}", status_code=303)


@router.get("/gastos/{gasto_id}", response_class=HTMLResponse)
def detalle_gasto(request: Request, gasto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        gasto = get_owned_gasto(cur, gasto_id, current_user["id"])
    finally:
        conn.close()

    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    return render_template(
        request,
        "gastos/detalle.html",
        {"gasto": gasto, "format_money": format_money},
    )


@router.get("/gastos/{gasto_id}/editar", response_class=HTMLResponse)
def editar_gasto(request: Request, gasto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        gasto = get_owned_gasto(cur, gasto_id, current_user["id"])
    finally:
        conn.close()

    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

    return render_template(
        request,
        "gastos/form.html",
        {
            "gasto": dict(gasto),
            "form_action": f"/gastos/{gasto_id}/editar",
            "titulo": "Editar gasto",
            "submit_label": "Guardar cambios",
            "error": "",
            "format_money": format_money,
        },
    )


@router.post("/gastos/{gasto_id}/editar")
def actualizar_gasto(
    request: Request,
    gasto_id: int,
    fecha: str = Form(...),
    proveedor: str = Form(...),
    nif_proveedor: str = Form(""),
    numero_factura: str = Form(""),
    concepto: str = Form(...),
    categoria: str = Form(""),
    base_imponible: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    deducible: str = Form("0"),
    notas: str = Form(""),
    archivo: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        gasto_existente = get_owned_gasto(cur, gasto_id, current_user["id"])
        if not gasto_existente:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")

        gasto = preparar_gasto_form(
            fecha,
            proveedor,
            nif_proveedor,
            numero_factura,
            concepto,
            categoria,
            base_imponible,
            iva_porcentaje,
            deducible,
            notas,
            gasto_id=gasto_id,
            archivo_path=gasto_existente["archivo_path"],
        )
        error = validar_gasto(gasto)
        if error:
            return render_template(
                request,
                "gastos/form.html",
                {
                    "gasto": gasto,
                    "form_action": f"/gastos/{gasto_id}/editar",
                    "titulo": "Editar gasto",
                    "submit_label": "Guardar cambios",
                    "error": error,
                    "format_money": format_money,
                },
            )

        archivo_path = gasto_existente["archivo_path"]
        nuevo_archivo = guardar_archivo_gasto(archivo)
        if nuevo_archivo:
            borrar_archivo_gasto(archivo_path)
            archivo_path = nuevo_archivo

        cur.execute(
            """
            UPDATE gastos
            SET fecha = ?, proveedor = ?, nif_proveedor = ?, numero_factura = ?,
                concepto = ?, categoria = ?, base_imponible = ?,
                iva_porcentaje = ?, iva_importe = ?, total = ?, deducible = ?,
                archivo_path = ?, notas = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                gasto["fecha"],
                gasto["proveedor"],
                gasto["nif_proveedor"],
                gasto["numero_factura"],
                gasto["concepto"],
                gasto["categoria"],
                gasto["base_imponible"],
                gasto["iva_porcentaje"],
                gasto["iva_importe"],
                gasto["total"],
                gasto["deducible"],
                archivo_path,
                gasto["notas"],
                gasto_id,
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/gastos/{gasto_id}", status_code=303)


@router.post("/gastos/{gasto_id}/eliminar")
def eliminar_gasto(request: Request, gasto_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        gasto = get_owned_gasto(cur, gasto_id, current_user["id"])
        if not gasto:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
        archivo_path = gasto["archivo_path"]
        cur.execute(
            "DELETE FROM gastos WHERE id = ? AND owner_user_id = ?",
            (gasto_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    borrar_archivo_gasto(archivo_path)
    return RedirectResponse(url="/gastos", status_code=303)
