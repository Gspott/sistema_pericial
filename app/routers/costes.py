import json
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.config import UPLOAD_DIR
from app.database import get_connection
from app.services.bc3_parser import parsear_bc3
from app.services.costes_ocr import extraer_coste_desde_imagen
from app.utils.timezone import now_madrid_iso

router = APIRouter()

UPLOAD_CAPTURAS_PATH = Path(UPLOAD_DIR) / "costes" / "capturas"
UPLOAD_BC3_PATH = Path(UPLOAD_DIR) / "costes" / "bc3"
CAPTURA_EXT_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
BC3_EXT_PERMITIDAS = {".bc3", ".txt"}
TIPOS_CONCEPTO = ("partida", "mano_obra", "material", "maquinaria", "auxiliar")
TIPOS_DESCOMPUESTO = (
    "mano_obra",
    "material",
    "maquinaria",
    "porcentaje",
    "auxiliar",
    "partida",
)
ESTADOS_CONCEPTO = ("borrador", "validado")
ESTADOS_CAPTURA = ("pendiente_revision", "revisada", "descartada")
TOLERANCIA_VALIDACION = 0.02


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
    return request.app.state.templates.TemplateResponse(request, template_name, data)


def limpiar_texto(valor: str | None) -> str:
    return (valor or "").strip()


def existe_conflicto_updated_at(valor_actual: str | None, valor_cliente: str | None) -> bool:
    actual = limpiar_texto(valor_actual)
    cliente = limpiar_texto(valor_cliente)
    return bool(actual and cliente and actual != cliente)


def respuesta_autosave_conflicto(updated_at: str | None = None) -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "conflict": True,
            "updated_at": limpiar_texto(updated_at),
            "message": "Otro proceso ha modificado el registro.",
        },
        status_code=409,
    )


def parse_float(valor: str | None, default: float = 0.0) -> float:
    texto = limpiar_texto(valor)
    if not texto:
        return default
    try:
        return float(texto.replace(",", "."))
    except ValueError:
        return default


def parse_int(valor: str | None) -> int | None:
    texto = limpiar_texto(valor)
    if not texto:
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def format_money(valor: float | int | None) -> str:
    return f"{float(valor or 0):.2f}"


def label_estado(valor: str | None) -> str:
    texto = limpiar_texto(valor).replace("_", " ")
    return texto.capitalize() if texto else "Borrador"


def estado_badge_class(valor: str | None) -> str:
    return "estado-badge estado-enviada" if valor == "validado" else "estado-badge estado-borrador"


def redirect_costes(path: str, mensaje: str = "", error: str = "", aviso: str = ""):
    params = []
    if mensaje:
        params.append(f"mensaje={quote(mensaje)}")
    if error:
        params.append(f"error={quote(error)}")
    if aviso:
        params.append(f"aviso={quote(aviso)}")
    separator = "&" if "?" in path else "?"
    url = f"{path}{separator}{'&'.join(params)}" if params else path
    return RedirectResponse(url=url, status_code=303)


def resolver_ruta_upload_relativa(ruta_relativa: str | None) -> Path:
    ruta_limpia = limpiar_texto(ruta_relativa)
    if not ruta_limpia:
        raise ValueError("La captura no tiene archivo asociado.")
    ruta = Path(ruta_limpia)
    if ruta.is_absolute() or ".." in ruta.parts:
        raise ValueError("Ruta de captura no permitida.")
    base_uploads = Path(UPLOAD_DIR).resolve()
    destino = (base_uploads / ruta).resolve()
    if base_uploads not in destino.parents and destino != base_uploads:
        raise ValueError("Ruta de captura fuera de uploads.")
    return destino


def obtener_bases(cur):
    return cur.execute(
        """
        SELECT id, nombre, provincia, fecha_base, version
        FROM costes_bases
        ORDER BY nombre COLLATE NOCASE, id DESC
        """
    ).fetchall()


def obtener_captura(cur, captura_id: int):
    return cur.execute(
        """
        SELECT
            cc.*,
            cf.descripcion AS fuente_descripcion,
            cf.observaciones AS fuente_observaciones,
            cf.archivo_original,
            cf.base_id,
            cb.nombre AS base_nombre,
            c.codigo AS concepto_codigo,
            c.resumen AS concepto_resumen
        FROM costes_capturas cc
        LEFT JOIN costes_fuentes cf ON cf.id = cc.fuente_id
        LEFT JOIN costes_bases cb ON cb.id = cf.base_id
        LEFT JOIN costes_conceptos c ON c.id = cc.concepto_id
        WHERE cc.id = ?
        """,
        (captura_id,),
    ).fetchone()


def obtener_capitulos(cur, base_id: int | None = None):
    params: list[object] = []
    filtros = []
    if base_id:
        filtros.append("base_id = ?")
        params.append(base_id)
    where_sql = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    return cur.execute(
        f"""
        SELECT id, base_id, codigo, nombre
        FROM costes_capitulos
        {where_sql}
        ORDER BY base_id, orden, codigo COLLATE NOCASE, nombre COLLATE NOCASE
        """,
        params,
    ).fetchall()


def obtener_concepto(cur, concepto_id: int):
    return cur.execute(
        """
        SELECT c.*, b.nombre AS base_nombre, b.origen AS base_origen, b.version AS base_version
        FROM costes_conceptos c
        JOIN costes_bases b ON b.id = c.base_id
        WHERE c.id = ?
        """,
        (concepto_id,),
    ).fetchone()


def obtener_fuentes_concepto(cur, concepto):
    if concepto is None:
        return []
    return cur.execute(
        """
        SELECT
            cf.id, cf.tipo_fuente, cf.descripcion, cf.archivo_original,
            cf.url_origen, cf.observaciones, cf.created_at,
            cc.id AS captura_id,
            cc.estado AS captura_estado
        FROM costes_fuentes cf
        LEFT JOIN costes_capturas cc ON cc.fuente_id = cf.id
        WHERE
            cf.concepto_id = ?
            OR cc.concepto_id = ?
            OR (
                cf.base_id = ?
                AND cf.tipo_fuente = 'bc3'
            )
        ORDER BY
            CASE
                WHEN cf.concepto_id = ? THEN 0
                WHEN cc.concepto_id = ? THEN 1
                ELSE 2
            END,
            cf.created_at DESC,
            cf.id DESC
        LIMIT 6
        """,
        (
            concepto["id"],
            concepto["id"],
            concepto["base_id"],
            concepto["id"],
            concepto["id"],
        ),
    ).fetchall()


def obtener_descompuestos(cur, concepto_id: int):
    return cur.execute(
        """
        SELECT *
        FROM costes_descompuestos
        WHERE concepto_padre_id = ?
        ORDER BY orden, id
        """,
        (concepto_id,),
    ).fetchall()


def contar_usos_concepto_costes(cur, concepto_id: int) -> dict[str, int]:
    patologias = cur.execute(
        """
        SELECT COUNT(*)
        FROM patologia_costes
        WHERE concepto_id = ?
        """,
        (concepto_id,),
    ).fetchone()[0]
    actuaciones = cur.execute(
        """
        SELECT COUNT(*)
        FROM actuacion_partidas
        WHERE concepto_id = ?
        """,
        (concepto_id,),
    ).fetchone()[0]
    return {
        "patologias": int(patologias or 0),
        "actuaciones": int(actuaciones or 0),
    }


def calcular_resumen_descomposicion(concepto, descompuestos):
    suma = round(sum(float(item["importe"] or 0) for item in descompuestos), 2)
    precio = round(float(concepto["precio"] or 0), 2) if concepto else 0.0
    diferencia = round(precio - suma, 2)
    return {
        "suma": suma,
        "precio": precio,
        "diferencia": diferencia,
        "descuadre": abs(diferencia) > TOLERANCIA_VALIDACION,
        "tolerancia": TOLERANCIA_VALIDACION,
    }


def construir_concepto_payload(
    base_id: str | None,
    capitulo_id: str | None,
    codigo: str,
    tipo: str,
    unidad: str,
    resumen: str,
    descripcion: str,
    precio: str,
    moneda: str,
    fecha_base: str,
    provincia: str,
    estado: str,
):
    tipo_limpio = limpiar_texto(tipo) or "partida"
    estado_limpio = limpiar_texto(estado) or "borrador"
    return {
        "base_id": parse_int(base_id),
        "capitulo_id": parse_int(capitulo_id),
        "codigo": limpiar_texto(codigo),
        "tipo": tipo_limpio if tipo_limpio in TIPOS_CONCEPTO else "partida",
        "unidad": limpiar_texto(unidad),
        "resumen": limpiar_texto(resumen),
        "descripcion": limpiar_texto(descripcion),
        "precio": round(parse_float(precio, 0), 2),
        "moneda": limpiar_texto(moneda).upper() or "EUR",
        "fecha_base": limpiar_texto(fecha_base),
        "provincia": limpiar_texto(provincia),
        "estado": estado_limpio if estado_limpio in ESTADOS_CONCEPTO else "borrador",
    }


def validar_concepto_payload(payload: dict) -> str:
    if not payload["codigo"]:
        return "El código es obligatorio."
    if not payload["unidad"]:
        return "La unidad es obligatoria."
    if not payload["resumen"]:
        return "El resumen es obligatorio."
    if payload["precio"] < 0:
        return "El precio no puede ser negativo."
    return ""


def asegurar_base_para_payload(
    cur,
    payload: dict,
    base_nombre: str,
    base_descripcion: str,
):
    if payload["base_id"]:
        existe = cur.execute(
            "SELECT id FROM costes_bases WHERE id = ?",
            (payload["base_id"],),
        ).fetchone()
        if existe:
            return payload["base_id"]

    nombre = limpiar_texto(base_nombre) or "Base manual de costes"
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, fecha_base, provincia, origen, version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            limpiar_texto(base_descripcion),
            payload["fecha_base"],
            payload["provincia"],
            "manual",
            "costes-2a",
        ),
    )
    return cur.lastrowid


def validar_para_estado_validado(concepto, descompuestos) -> str:
    if not limpiar_texto(concepto["codigo"]):
        return "No se puede validar sin código."
    if not limpiar_texto(concepto["unidad"]):
        return "No se puede validar sin unidad."
    if not limpiar_texto(concepto["resumen"]):
        return "No se puede validar sin resumen."
    if float(concepto["precio"] or 0) <= 0:
        return "No se puede validar sin precio positivo."

    resumen_descomp = calcular_resumen_descomposicion(concepto, descompuestos)
    if resumen_descomp["descuadre"]:
        return (
            "No se puede validar: el precio y la suma de descompuestos "
            f"difieren en {format_money(resumen_descomp['diferencia'])} €."
        )
    return ""


def guardar_imagen_captura(archivo: UploadFile | None) -> str:
    if not archivo or not archivo.filename:
        raise ValueError("Selecciona una imagen.")

    extension = Path(archivo.filename).suffix.lower()
    if extension not in CAPTURA_EXT_PERMITIDAS:
        raise ValueError("Formato no permitido. Usa JPG, PNG o WEBP.")

    contenido = archivo.file.read()
    if not contenido:
        raise ValueError("La imagen está vacía.")

    UPLOAD_CAPTURAS_PATH.mkdir(parents=True, exist_ok=True)
    nombre = f"captura_costes_{uuid4().hex}{extension}"
    destino = UPLOAD_CAPTURAS_PATH / nombre
    destino.write_bytes(contenido)
    return f"costes/capturas/{nombre}"


def guardar_archivo_bc3(archivo: UploadFile | None) -> tuple[str, str]:
    if not archivo or not archivo.filename:
        raise ValueError("Selecciona un archivo BC3.")

    nombre_original = Path(archivo.filename).name
    extension = Path(nombre_original).suffix.lower()
    if extension not in BC3_EXT_PERMITIDAS:
        raise ValueError("Formato no permitido. Usa .bc3 o .txt para pruebas.")

    contenido = archivo.file.read()
    if not contenido:
        raise ValueError("El archivo BC3 está vacío.")

    UPLOAD_BC3_PATH.mkdir(parents=True, exist_ok=True)
    destino_nombre = f"costes_bc3_{uuid4().hex}{extension}"
    destino = UPLOAD_BC3_PATH / destino_nombre
    destino.write_bytes(contenido)
    return f"costes/bc3/{destino_nombre}", nombre_original


def _codigo_capitulo_para_concepto(capitulos_por_codigo: dict[str, int], codigo: str) -> int | None:
    candidatos = [
        codigo_capitulo
        for codigo_capitulo in capitulos_por_codigo
        if codigo.startswith(codigo_capitulo)
    ]
    if not candidatos:
        return None
    candidatos.sort(key=len, reverse=True)
    return capitulos_por_codigo[candidatos[0]]


def importar_bc3_en_base(
    cur,
    base_id: int,
    fuente_id: int,
    resultado_bc3: dict,
    fecha_base: str,
    provincia: str,
) -> dict:
    advertencias = list(resultado_bc3.get("advertencias") or [])
    conceptos_por_codigo = {
        item["codigo"]: item
        for item in resultado_bc3.get("conceptos") or []
        if limpiar_texto(item.get("codigo"))
    }
    codigos_hijos = {
        limpiar_texto(item.get("codigo_hijo"))
        for item in resultado_bc3.get("descompuestos") or []
    }
    capitulos_por_codigo: dict[str, int] = {}
    conceptos_insertados: dict[str, int] = {}
    conceptos_saltados = 0
    capitulos_creados = 0

    for codigo, concepto in conceptos_por_codigo.items():
        precio = float(concepto.get("precio") or 0)
        unidad = limpiar_texto(concepto.get("unidad"))
        es_capitulo = not unidad and precio == 0 and codigo not in codigos_hijos
        if not es_capitulo:
            continue
        existente = cur.execute(
            """
            SELECT id
            FROM costes_capitulos
            WHERE base_id = ? AND codigo = ?
            """,
            (base_id, codigo),
        ).fetchone()
        if existente:
            capitulos_por_codigo[codigo] = existente["id"]
            continue
        cur.execute(
            """
            INSERT INTO costes_capitulos (
                base_id, codigo, nombre, descripcion, orden
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                base_id,
                codigo,
                limpiar_texto(concepto.get("resumen")) or codigo,
                limpiar_texto(concepto.get("descripcion")),
                capitulos_creados + 1,
            ),
        )
        capitulos_por_codigo[codigo] = cur.lastrowid
        capitulos_creados += 1

    for codigo, concepto in conceptos_por_codigo.items():
        precio = float(concepto.get("precio") or 0)
        unidad = limpiar_texto(concepto.get("unidad"))
        if not unidad and precio == 0 and codigo in capitulos_por_codigo:
            continue
        existente = cur.execute(
            """
            SELECT id
            FROM costes_conceptos
            WHERE base_id = ? AND codigo = ?
            """,
            (base_id, codigo),
        ).fetchone()
        if existente:
            conceptos_saltados += 1
            advertencias.append(f"Concepto duplicado saltado en la base: {codigo}")
            continue
        cur.execute(
            """
            INSERT INTO costes_conceptos (
                base_id, capitulo_id, codigo, tipo, unidad, resumen,
                descripcion, precio, moneda, fecha_base, provincia, estado,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'borrador', CURRENT_TIMESTAMP)
            """,
            (
                base_id,
                _codigo_capitulo_para_concepto(capitulos_por_codigo, codigo),
                codigo,
                limpiar_texto(concepto.get("tipo")) or "partida",
                unidad,
                limpiar_texto(concepto.get("resumen")) or codigo,
                limpiar_texto(concepto.get("descripcion")),
                round(precio, 2),
                limpiar_texto(concepto.get("moneda")).upper() or "EUR",
                limpiar_texto(fecha_base),
                limpiar_texto(provincia),
            ),
        )
        conceptos_insertados[codigo] = cur.lastrowid

    descompuestos_insertados = 0
    for item in resultado_bc3.get("descompuestos") or []:
        codigo_padre = limpiar_texto(item.get("codigo_padre"))
        codigo_hijo = limpiar_texto(item.get("codigo_hijo"))
        concepto_padre_id = conceptos_insertados.get(codigo_padre)
        if not concepto_padre_id:
            if codigo_padre in conceptos_por_codigo:
                advertencias.append(f"Descompuesto de {codigo_padre} saltado: partida padre duplicada o no importada.")
            else:
                advertencias.append(f"Descompuesto saltado: no existe padre {codigo_padre}.")
            continue
        hijo = conceptos_por_codigo.get(codigo_hijo) or {}
        rendimiento = float(item.get("rendimiento") or 0)
        precio_unitario = item.get("precio_unitario")
        if precio_unitario is None:
            precio_unitario = float(hijo.get("precio") or 0)
        importe = item.get("importe")
        if importe is None:
            importe = round(float(precio_unitario or 0) * rendimiento, 2)
        concepto_hijo_id = conceptos_insertados.get(codigo_hijo)
        cur.execute(
            """
            INSERT INTO costes_descompuestos (
                concepto_padre_id, concepto_hijo_id, codigo, tipo, unidad,
                resumen, precio_unitario, rendimiento, importe, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concepto_padre_id,
                concepto_hijo_id,
                codigo_hijo,
                limpiar_texto(hijo.get("tipo")) or "material",
                limpiar_texto(hijo.get("unidad")),
                limpiar_texto(hijo.get("resumen")) or codigo_hijo,
                round(float(precio_unitario or 0), 4),
                round(rendimiento, 4),
                round(float(importe or 0), 2),
                int(item.get("orden") or descompuestos_insertados + 1),
            ),
        )
        descompuestos_insertados += 1

    primer_concepto_id = next(iter(conceptos_insertados.values()), None)
    if primer_concepto_id:
        cur.execute(
            """
            UPDATE costes_fuentes
            SET concepto_id = ?
            WHERE id = ?
            """,
            (primer_concepto_id, fuente_id),
        )

    return {
        "base_id": base_id,
        "fuente_id": fuente_id,
        "capitulos_creados": capitulos_creados,
        "conceptos_importados": len(conceptos_insertados),
        "conceptos_saltados": conceptos_saltados,
        "descompuestos_importados": descompuestos_insertados,
        "advertencias": advertencias,
        "estadisticas": resultado_bc3.get("estadisticas") or {},
    }


def construir_descompuestos_desde_form(
    codigos: list[str],
    tipos: list[str],
    unidades: list[str],
    resumenes: list[str],
    precios_unitarios: list[str],
    rendimientos: list[str],
    importes: list[str],
    ordenes: list[str],
) -> list[dict]:
    total_lineas = max(
        len(codigos),
        len(tipos),
        len(unidades),
        len(resumenes),
        len(precios_unitarios),
        len(rendimientos),
        len(importes),
        len(ordenes),
        0,
    )
    descompuestos = []
    for index in range(total_lineas):
        codigo = limpiar_texto(codigos[index] if index < len(codigos) else "")
        tipo = limpiar_texto(tipos[index] if index < len(tipos) else "")
        unidad = limpiar_texto(unidades[index] if index < len(unidades) else "")
        resumen = limpiar_texto(resumenes[index] if index < len(resumenes) else "")
        precio_unitario = round(
            parse_float(precios_unitarios[index] if index < len(precios_unitarios) else "", 0),
            4,
        )
        rendimiento = round(
            parse_float(rendimientos[index] if index < len(rendimientos) else "", 0),
            4,
        )
        importe_texto = importes[index] if index < len(importes) else ""
        importe_calculado = round(precio_unitario * rendimiento, 2)
        importe = round(parse_float(importe_texto, importe_calculado), 2)
        orden = parse_int(ordenes[index] if index < len(ordenes) else "") or index + 1
        if not any([codigo, unidad, resumen, precio_unitario, rendimiento, importe]):
            continue
        descompuestos.append(
            {
                "codigo": codigo,
                "tipo": tipo if tipo in TIPOS_DESCOMPUESTO else "material",
                "unidad": unidad,
                "resumen": resumen,
                "precio_unitario": precio_unitario,
                "rendimiento": rendimiento,
                "importe": importe,
                "orden": orden,
            }
        )
    return descompuestos


@router.get("/costes", response_class=HTMLResponse)
def listar_costes(
    request: Request,
    q: str = Query(""),
    estado: str = Query(""),
    base_id: str = Query(""),
    mensaje: str = Query(""),
    error: str = Query(""),
):
    get_current_user(request)
    q_limpia = limpiar_texto(q)
    estado_limpio = limpiar_texto(estado)
    base_id_int = parse_int(base_id)
    condiciones = []
    params: list[object] = []

    if q_limpia:
        condiciones.append(
            """
            (
                lower(c.codigo) LIKE ?
                OR lower(c.resumen) LIKE ?
                OR lower(COALESCE(c.descripcion, '')) LIKE ?
            )
            """
        )
        patron = f"%{q_limpia.lower()}%"
        params.extend([patron, patron, patron])
    if estado_limpio in ESTADOS_CONCEPTO:
        condiciones.append("c.estado = ?")
        params.append(estado_limpio)
    else:
        estado_limpio = ""
    if base_id_int:
        condiciones.append("c.base_id = ?")
        params.append(base_id_int)

    where_sql = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    conn = get_connection()
    try:
        cur = conn.cursor()
        bases = obtener_bases(cur)
        conceptos = cur.execute(
            f"""
            SELECT
                c.id, c.codigo, c.tipo, c.unidad, c.resumen, c.descripcion,
                c.precio, c.moneda, c.fecha_base, c.provincia, c.estado,
                b.nombre AS base_nombre
            FROM costes_conceptos c
            JOIN costes_bases b ON b.id = c.base_id
            {where_sql}
            ORDER BY c.updated_at DESC, c.created_at DESC, c.codigo COLLATE NOCASE
            LIMIT 200
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    concepto_ids = [concepto["id"] for concepto in conceptos]
    usos_por_concepto: dict[int, dict[str, int]] = {
        concepto_id: {"patologias": 0, "actuaciones": 0}
        for concepto_id in concepto_ids
    }
    if concepto_ids:
        placeholders = ",".join("?" for _ in concepto_ids)
        conn = get_connection()
        try:
            cur = conn.cursor()
            for row in cur.execute(
                f"""
                SELECT concepto_id, COUNT(*) AS total
                FROM patologia_costes
                WHERE concepto_id IN ({placeholders})
                GROUP BY concepto_id
                """,
                concepto_ids,
            ).fetchall():
                usos_por_concepto[row["concepto_id"]]["patologias"] = int(row["total"] or 0)
            for row in cur.execute(
                f"""
                SELECT concepto_id, COUNT(*) AS total
                FROM actuacion_partidas
                WHERE concepto_id IN ({placeholders})
                GROUP BY concepto_id
                """,
                concepto_ids,
            ).fetchall():
                usos_por_concepto[row["concepto_id"]]["actuaciones"] = int(row["total"] or 0)
        finally:
            conn.close()

    return render_template(
        request,
        "costes/listado.html",
        {
            "conceptos": conceptos,
            "usos_por_concepto": usos_por_concepto,
            "bases": bases,
            "filters": {"q": q_limpia, "estado": estado_limpio, "base_id": base_id_int or ""},
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
            "format_money": format_money,
            "label_estado": label_estado,
            "estado_badge_class": estado_badge_class,
        },
    )


@router.get("/costes/capturas", response_class=HTMLResponse)
def listar_capturas_costes(
    request: Request,
    estado: str = Query(""),
    mensaje: str = Query(""),
    error: str = Query(""),
):
    get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    condiciones = []
    params: list[object] = []
    if estado_limpio in ESTADOS_CAPTURA:
        condiciones.append("cc.estado = ?")
        params.append(estado_limpio)
    else:
        estado_limpio = ""
    where_sql = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    conn = get_connection()
    try:
        cur = conn.cursor()
        capturas = cur.execute(
            f"""
            SELECT
                cc.id, cc.fuente_id, cc.concepto_id, cc.archivo_imagen,
                cc.estado, cc.created_at, cc.updated_at,
                cf.descripcion AS fuente_descripcion,
                c.codigo AS concepto_codigo,
                c.resumen AS concepto_resumen
            FROM costes_capturas cc
            LEFT JOIN costes_fuentes cf ON cf.id = cc.fuente_id
            LEFT JOIN costes_conceptos c ON c.id = cc.concepto_id
            {where_sql}
            ORDER BY cc.created_at DESC, cc.id DESC
            LIMIT 100
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "costes/capturas_listado.html",
        {
            "capturas": capturas,
            "filters": {"estado": estado_limpio},
            "estados_captura": ESTADOS_CAPTURA,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
            "label_estado": label_estado,
        },
    )


@router.get("/costes/capturas/nueva", response_class=HTMLResponse)
def nueva_captura_costes(request: Request, error: str = Query("")):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        bases = obtener_bases(cur)
    finally:
        conn.close()

    return render_template(
        request,
        "costes/captura_form.html",
        {
            "bases": bases,
            "error": limpiar_texto(error),
        },
    )


@router.post("/costes/capturas/nueva")
def crear_captura_costes(
    request: Request,
    base_id: str = Form(""),
    descripcion: str = Form(""),
    provincia: str = Form(""),
    fecha_base: str = Form(""),
    observaciones: str = Form(""),
    archivo: UploadFile | None = File(None),
):
    get_current_user(request)
    try:
        archivo_relativo = guardar_imagen_captura(archivo)
    except ValueError as exc:
        return redirect_costes("/costes/capturas/nueva", error=str(exc))

    base_id_int = parse_int(base_id)
    datos_extraidos = {
        "ocr": False,
        "modo": "revision_manual",
        "provincia": limpiar_texto(provincia),
        "fecha_base": limpiar_texto(fecha_base),
    }

    conn = get_connection()
    try:
        cur = conn.cursor()
        if base_id_int and not cur.execute(
            "SELECT id FROM costes_bases WHERE id = ?",
            (base_id_int,),
        ).fetchone():
            base_id_int = None
        cur.execute(
            """
            INSERT INTO costes_fuentes (
                base_id, tipo_fuente, descripcion, archivo_original,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                base_id_int,
                "pantallazo",
                limpiar_texto(descripcion) or "Pantallazo pendiente de revisión",
                archivo_relativo,
                limpiar_texto(observaciones),
            ),
        )
        fuente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO costes_capturas (
                fuente_id, archivo_imagen, estado, datos_extraidos_json,
                updated_at
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                fuente_id,
                archivo_relativo,
                "pendiente_revision",
                json.dumps(datos_extraidos, sort_keys=True),
            ),
        )
        captura_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/capturas/{captura_id}",
        mensaje="Captura creada. Revisa manualmente antes de guardar.",
    )


@router.get("/costes/capturas/{captura_id}", response_class=HTMLResponse)
def revisar_captura_costes(
    request: Request,
    captura_id: int,
    mensaje: str = Query(""),
    error: str = Query(""),
):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        captura = obtener_captura(cur, captura_id)
        if captura is None:
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        bases = obtener_bases(cur)
        capitulos = obtener_capitulos(cur, captura["base_id"])
        datos = {}
        if captura["datos_extraidos_json"]:
            try:
                datos = json.loads(captura["datos_extraidos_json"])
            except json.JSONDecodeError:
                datos = {}
        datos_parseados = datos.get("datos_parseados") or {}
        if not datos_parseados and any(datos.get(clave) for clave in ("fecha_base", "provincia")):
            datos_parseados = {
                "fecha_base": datos.get("fecha_base") or "",
                "provincia": datos.get("provincia") or "",
            }
        descompuestos_sugeridos = list(datos_parseados.get("descompuestos") or [])
        while len(descompuestos_sugeridos) < 3:
            descompuestos_sugeridos.append({})
        confianza_ocr = datos.get("confianza") or {}
        campos_detectados = (
            datos.get("campos_detectados")
            or confianza_ocr.get("campos_detectados")
            or {}
        )
    finally:
        conn.close()

    return render_template(
        request,
        "costes/captura_revision.html",
        {
            "captura": captura,
            "bases": bases,
            "capitulos": capitulos,
            "datos": datos,
            "datos_parseados": datos_parseados,
            "descompuestos_sugeridos": descompuestos_sugeridos,
            "advertencias_ocr": datos.get("advertencias") or [],
            "texto_detectado": datos.get("texto_detectado") or datos.get("texto_ocr") or "",
            "ocr_disponible": bool(datos.get("ocr_disponible")),
            "confianza_ocr": confianza_ocr,
            "campos_detectados": campos_detectados,
            "version_parser": datos.get("version_parser") or "",
            "tipos_descompuesto": TIPOS_DESCOMPUESTO,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
        },
    )


@router.post("/costes/capturas/{captura_id}/extraer")
def extraer_captura_costes(request: Request, captura_id: int):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        captura = obtener_captura(cur, captura_id)
        if captura is None:
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        try:
            ruta_imagen = resolver_ruta_upload_relativa(captura["archivo_imagen"])
        except ValueError as exc:
            return redirect_costes(f"/costes/capturas/{captura_id}", error=str(exc))

        resultado = extraer_coste_desde_imagen(ruta_imagen)
        resultado["modo"] = "ocr_local_asistido"
        cur.execute(
            """
            UPDATE costes_capturas
            SET datos_extraidos_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json.dumps(resultado, ensure_ascii=False, sort_keys=True), captura_id),
        )
        conn.commit()
    finally:
        conn.close()

    mensaje = "Extracción local preparada para revisión manual."
    if not resultado.get("ocr_disponible"):
        mensaje = "OCR local no disponible; continúa con revisión manual."
    return redirect_costes(f"/costes/capturas/{captura_id}", mensaje=mensaje)


@router.post("/costes/capturas/{captura_id}")
def guardar_revision_captura_costes(
    request: Request,
    captura_id: int,
    base_id: str = Form(""),
    base_nombre: str = Form(""),
    base_descripcion: str = Form(""),
    capitulo_id: str = Form(""),
    codigo: str = Form(""),
    unidad: str = Form(""),
    resumen: str = Form(""),
    descripcion: str = Form(""),
    precio: str = Form("0"),
    moneda: str = Form("EUR"),
    fecha_base: str = Form(""),
    provincia: str = Form(""),
    descomp_codigo: list[str] = Form([]),
    descomp_tipo: list[str] = Form([]),
    descomp_unidad: list[str] = Form([]),
    descomp_resumen: list[str] = Form([]),
    descomp_precio_unitario: list[str] = Form([]),
    descomp_rendimiento: list[str] = Form([]),
    descomp_importe: list[str] = Form([]),
    descomp_orden: list[str] = Form([]),
):
    get_current_user(request)
    payload = construir_concepto_payload(
        base_id,
        capitulo_id,
        codigo,
        "partida",
        unidad,
        resumen,
        descripcion,
        precio,
        moneda,
        fecha_base,
        provincia,
        "borrador",
    )
    error = validar_concepto_payload(payload)
    if error:
        return redirect_costes(f"/costes/capturas/{captura_id}", error=error)

    descompuestos = construir_descompuestos_desde_form(
        descomp_codigo,
        descomp_tipo,
        descomp_unidad,
        descomp_resumen,
        descomp_precio_unitario,
        descomp_rendimiento,
        descomp_importe,
        descomp_orden,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        captura = obtener_captura(cur, captura_id)
        if captura is None:
            raise HTTPException(status_code=404, detail="Captura no encontrada")
        payload["base_id"] = asegurar_base_para_payload(
            cur,
            payload,
            base_nombre,
            base_descripcion,
        )
        cur.execute(
            """
            INSERT INTO costes_conceptos (
                base_id, capitulo_id, codigo, tipo, unidad, resumen,
                descripcion, precio, moneda, fecha_base, provincia, estado,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                payload["base_id"],
                payload["capitulo_id"],
                payload["codigo"],
                payload["tipo"],
                payload["unidad"],
                payload["resumen"],
                payload["descripcion"],
                payload["precio"],
                payload["moneda"],
                payload["fecha_base"],
                payload["provincia"],
                "borrador",
            ),
        )
        concepto_id = cur.lastrowid
        for item in descompuestos:
            cur.execute(
                """
                INSERT INTO costes_descompuestos (
                    concepto_padre_id, codigo, tipo, unidad, resumen,
                    precio_unitario, rendimiento, importe, orden
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    concepto_id,
                    item["codigo"],
                    item["tipo"],
                    item["unidad"],
                    item["resumen"],
                    item["precio_unitario"],
                    item["rendimiento"],
                    item["importe"],
                    item["orden"],
                ),
            )
        cur.execute(
            """
            UPDATE costes_capturas
            SET concepto_id = ?, estado = 'revisada', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (concepto_id, captura_id),
        )
        if captura["fuente_id"]:
            cur.execute(
                """
                UPDATE costes_fuentes
                SET concepto_id = ?
                WHERE id = ?
                """,
                (concepto_id, captura["fuente_id"]),
            )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/{concepto_id}",
        mensaje="Partida creada desde captura.",
    )


@router.get("/costes/bc3/importar", response_class=HTMLResponse)
def importar_bc3_form(request: Request, error: str = Query("")):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        bases = obtener_bases(cur)
    finally:
        conn.close()

    return render_template(
        request,
        "costes/bc3_importar.html",
        {
            "bases": bases,
            "error": limpiar_texto(error),
        },
    )


@router.post("/costes/bc3/importar", response_class=HTMLResponse)
def importar_bc3_post(
    request: Request,
    base_id: str = Form(""),
    base_nombre: str = Form(""),
    descripcion: str = Form(""),
    fecha_base: str = Form(""),
    provincia: str = Form(""),
    observaciones: str = Form(""),
    archivo: UploadFile | None = File(None),
):
    get_current_user(request)
    try:
        archivo_relativo, nombre_original = guardar_archivo_bc3(archivo)
    except ValueError as exc:
        return redirect_costes("/costes/bc3/importar", error=str(exc))

    ruta_archivo = resolver_ruta_upload_relativa(archivo_relativo)
    resultado_bc3 = parsear_bc3(ruta_archivo)
    base_id_int = parse_int(base_id)
    nombre_base = limpiar_texto(base_nombre) or Path(nombre_original).stem or "Base importada BC3"
    fecha_base_limpia = limpiar_texto(fecha_base)
    provincia_limpia = limpiar_texto(provincia)

    conn = get_connection()
    try:
        cur = conn.cursor()
        if base_id_int and not cur.execute(
            "SELECT id FROM costes_bases WHERE id = ?",
            (base_id_int,),
        ).fetchone():
            base_id_int = None
        if not base_id_int:
            cur.execute(
                """
                INSERT INTO costes_bases (
                    nombre, descripcion, fecha_base, provincia, origen, version
                )
                VALUES (?, ?, ?, ?, 'bc3', ?)
                """,
                (
                    nombre_base,
                    limpiar_texto(descripcion) or "Base importada desde archivo BC3/FIEBDC.",
                    fecha_base_limpia,
                    provincia_limpia,
                    "costes-3",
                ),
            )
            base_id_int = cur.lastrowid
        cur.execute(
            """
            INSERT INTO costes_fuentes (
                base_id, tipo_fuente, descripcion, archivo_original,
                observaciones
            )
            VALUES (?, 'bc3', ?, ?, ?)
            """,
            (
                base_id_int,
                limpiar_texto(descripcion) or f"Importación BC3: {nombre_original}",
                archivo_relativo,
                limpiar_texto(observaciones),
            ),
        )
        fuente_id = cur.lastrowid
        resultado_importacion = importar_bc3_en_base(
            cur,
            base_id_int,
            fuente_id,
            resultado_bc3,
            fecha_base_limpia,
            provincia_limpia,
        )
        conn.commit()
        base = cur.execute(
            "SELECT id, nombre FROM costes_bases WHERE id = ?",
            (base_id_int,),
        ).fetchone()
    finally:
        conn.close()

    return render_template(
        request,
        "costes/bc3_resultado.html",
        {
            "base": base,
            "archivo_original": nombre_original,
            "archivo_relativo": archivo_relativo,
            "resultado": resultado_importacion,
            "format_money": format_money,
        },
    )


@router.get("/costes/bc3/importaciones", response_class=HTMLResponse)
def listar_importaciones_bc3(
    request: Request,
    mensaje: str = Query(""),
    error: str = Query(""),
):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        importaciones = cur.execute(
            """
            SELECT
                cf.id, cf.base_id, cf.descripcion, cf.archivo_original,
                cf.observaciones, cf.created_at,
                cb.nombre AS base_nombre,
                (
                    SELECT COUNT(*)
                    FROM costes_conceptos c
                    WHERE c.base_id = cf.base_id
                ) AS conceptos_base
            FROM costes_fuentes cf
            LEFT JOIN costes_bases cb ON cb.id = cf.base_id
            WHERE cf.tipo_fuente = 'bc3'
            ORDER BY cf.created_at DESC, cf.id DESC
            LIMIT 100
            """
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "costes/bc3_importaciones.html",
        {
            "importaciones": importaciones,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
        },
    )


@router.get("/costes/bc3/importaciones/{fuente_id}", response_class=HTMLResponse)
def detalle_importacion_bc3(request: Request, fuente_id: int):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        fuente = cur.execute(
            """
            SELECT cf.*, cb.nombre AS base_nombre
            FROM costes_fuentes cf
            LEFT JOIN costes_bases cb ON cb.id = cf.base_id
            WHERE cf.id = ? AND cf.tipo_fuente = 'bc3'
            """,
            (fuente_id,),
        ).fetchone()
        if fuente is None:
            raise HTTPException(status_code=404, detail="Importación BC3 no encontrada")
        conceptos = cur.execute(
            """
            SELECT id, codigo, unidad, resumen, precio, estado
            FROM costes_conceptos
            WHERE base_id = ?
            ORDER BY codigo COLLATE NOCASE
            LIMIT 200
            """,
            (fuente["base_id"],),
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "costes/bc3_importacion_detalle.html",
        {
            "fuente": fuente,
            "conceptos": conceptos,
            "format_money": format_money,
            "label_estado": label_estado,
        },
    )


@router.get("/costes/nuevo", response_class=HTMLResponse)
def nuevo_coste(request: Request, error: str = Query("")):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        bases = obtener_bases(cur)
        capitulos = obtener_capitulos(cur)
    finally:
        conn.close()

    return render_template(
        request,
        "costes/form.html",
        {
            "concepto": {
                "base_id": bases[0]["id"] if bases else "",
                "capitulo_id": "",
                "codigo": "",
                "tipo": "partida",
                "unidad": "",
                "resumen": "",
                "descripcion": "",
                "precio": 0,
                "moneda": "EUR",
                "fecha_base": "",
                "provincia": "",
                "estado": "borrador",
            },
            "bases": bases,
            "capitulos": capitulos,
            "tipos_concepto": TIPOS_CONCEPTO,
            "estados_concepto": ESTADOS_CONCEPTO,
            "error": limpiar_texto(error),
        },
    )


@router.post("/costes/nuevo")
def crear_coste(
    request: Request,
    base_id: str = Form(""),
    base_nombre: str = Form(""),
    base_descripcion: str = Form(""),
    capitulo_id: str = Form(""),
    codigo: str = Form(""),
    tipo: str = Form("partida"),
    unidad: str = Form(""),
    resumen: str = Form(""),
    descripcion: str = Form(""),
    precio: str = Form("0"),
    moneda: str = Form("EUR"),
    fecha_base: str = Form(""),
    provincia: str = Form(""),
    estado: str = Form("borrador"),
):
    get_current_user(request)
    payload = construir_concepto_payload(
        base_id,
        capitulo_id,
        codigo,
        tipo,
        unidad,
        resumen,
        descripcion,
        precio,
        moneda,
        fecha_base,
        provincia,
        estado,
    )
    error = validar_concepto_payload(payload)
    if error:
        return redirect_costes("/costes/nuevo", error=error)

    conn = get_connection()
    try:
        cur = conn.cursor()
        payload["base_id"] = asegurar_base_para_payload(
            cur,
            payload,
            base_nombre,
            base_descripcion,
        )
        cur.execute(
            """
            INSERT INTO costes_conceptos (
                base_id, capitulo_id, codigo, tipo, unidad, resumen,
                descripcion, precio, moneda, fecha_base, provincia, estado,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                payload["base_id"],
                payload["capitulo_id"],
                payload["codigo"],
                payload["tipo"],
                payload["unidad"],
                payload["resumen"],
                payload["descripcion"],
                payload["precio"],
                payload["moneda"],
                payload["fecha_base"],
                payload["provincia"],
                payload["estado"],
            ),
        )
        concepto_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/{concepto_id}",
        mensaje="Partida creada.",
    )


@router.get("/costes/{concepto_id}", response_class=HTMLResponse)
def detalle_coste(
    request: Request,
    concepto_id: int,
    mensaje: str = Query(""),
    error: str = Query(""),
    aviso: str = Query(""),
):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        concepto = obtener_concepto(cur, concepto_id)
        if concepto is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        bases = obtener_bases(cur)
        capitulos = obtener_capitulos(cur, concepto["base_id"])
        descompuestos = obtener_descompuestos(cur, concepto_id)
        fuentes = obtener_fuentes_concepto(cur, concepto)
        resumen_descomp = calcular_resumen_descomposicion(concepto, descompuestos)
    finally:
        conn.close()

    return render_template(
        request,
        "costes/detalle.html",
        {
            "concepto": concepto,
            "bases": bases,
            "capitulos": capitulos,
            "descompuestos": descompuestos,
            "fuentes": fuentes,
            "resumen_descomp": resumen_descomp,
            "tipos_concepto": TIPOS_CONCEPTO,
            "tipos_descompuesto": TIPOS_DESCOMPUESTO,
            "estados_concepto": ESTADOS_CONCEPTO,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
            "aviso": limpiar_texto(aviso),
            "format_money": format_money,
            "label_estado": label_estado,
            "estado_badge_class": estado_badge_class,
        },
    )


@router.post("/costes/{concepto_id}/autosave")
async def autosave_coste(request: Request, concepto_id: int):
    get_current_user(request)
    form = await request.form()
    payload = construir_concepto_payload(
        form.get("base_id"),
        form.get("capitulo_id"),
        form.get("codigo"),
        form.get("tipo"),
        form.get("unidad"),
        form.get("resumen"),
        form.get("descripcion"),
        form.get("precio"),
        form.get("moneda"),
        form.get("fecha_base"),
        form.get("provincia"),
        form.get("estado"),
    )
    error = validar_concepto_payload(payload)
    if error:
        return JSONResponse({"ok": False, "message": error}, status_code=400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        concepto_actual = obtener_concepto(cur, concepto_id)
        if concepto_actual is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        if existe_conflicto_updated_at(concepto_actual["updated_at"], form.get("updated_at")):
            return respuesta_autosave_conflicto(concepto_actual["updated_at"])
        if not payload["base_id"]:
            return JSONResponse(
                {"ok": False, "message": "Selecciona una base."},
                status_code=400,
            )
        estado_final = payload["estado"]
        cambio_relevante = (
            limpiar_texto(concepto_actual["codigo"]) != payload["codigo"]
            or round(float(concepto_actual["precio"] or 0), 2) != payload["precio"]
        )
        if concepto_actual["estado"] == "validado" and cambio_relevante:
            estado_final = "borrador"
        cur.execute(
            """
            UPDATE costes_conceptos
            SET base_id = ?, capitulo_id = ?, codigo = ?, tipo = ?,
                unidad = ?, resumen = ?, descripcion = ?, precio = ?,
                moneda = ?, fecha_base = ?, provincia = ?, estado = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload["base_id"],
                payload["capitulo_id"],
                payload["codigo"],
                payload["tipo"],
                payload["unidad"],
                payload["resumen"],
                payload["descripcion"],
                payload["precio"],
                payload["moneda"],
                payload["fecha_base"],
                payload["provincia"],
                estado_final,
                concepto_id,
            ),
        )
        actualizado = obtener_concepto(cur, concepto_id)
        conn.commit()
    finally:
        conn.close()

    return JSONResponse(
        {
            "ok": True,
            "updated_at": limpiar_texto(actualizado["updated_at"] if actualizado else ""),
            "saved_at": now_madrid_iso(),
            "message": "Guardado correctamente",
        }
    )


@router.post("/costes/{concepto_id}")
def actualizar_coste(
    request: Request,
    concepto_id: int,
    base_id: str = Form(""),
    capitulo_id: str = Form(""),
    codigo: str = Form(""),
    tipo: str = Form("partida"),
    unidad: str = Form(""),
    resumen: str = Form(""),
    descripcion: str = Form(""),
    precio: str = Form("0"),
    moneda: str = Form("EUR"),
    fecha_base: str = Form(""),
    provincia: str = Form(""),
    estado: str = Form("borrador"),
    updated_at: str = Form(""),
):
    get_current_user(request)
    payload = construir_concepto_payload(
        base_id,
        capitulo_id,
        codigo,
        tipo,
        unidad,
        resumen,
        descripcion,
        precio,
        moneda,
        fecha_base,
        provincia,
        estado,
    )
    error = validar_concepto_payload(payload)
    if error:
        return redirect_costes(f"/costes/{concepto_id}", error=error)

    conn = get_connection()
    try:
        cur = conn.cursor()
        concepto_actual = obtener_concepto(cur, concepto_id)
        if concepto_actual is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        if existe_conflicto_updated_at(concepto_actual["updated_at"], updated_at):
            return redirect_costes(
                f"/costes/{concepto_id}",
                error="Otro proceso ha modificado el registro.",
            )
        if not payload["base_id"]:
            return redirect_costes(f"/costes/{concepto_id}", error="Selecciona una base.")
        estado_final = payload["estado"]
        cambio_relevante = (
            limpiar_texto(concepto_actual["codigo"]) != payload["codigo"]
            or round(float(concepto_actual["precio"] or 0), 2) != payload["precio"]
        )
        aviso = ""
        if concepto_actual["estado"] == "validado" and cambio_relevante:
            estado_final = "borrador"
            aviso = (
                "La partida estaba validada. Al cambiar código o precio vuelve a borrador "
                "para revisar la descomposición."
            )
        cur.execute(
            """
            UPDATE costes_conceptos
            SET base_id = ?, capitulo_id = ?, codigo = ?, tipo = ?,
                unidad = ?, resumen = ?, descripcion = ?, precio = ?,
                moneda = ?, fecha_base = ?, provincia = ?, estado = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                payload["base_id"],
                payload["capitulo_id"],
                payload["codigo"],
                payload["tipo"],
                payload["unidad"],
                payload["resumen"],
                payload["descripcion"],
                payload["precio"],
                payload["moneda"],
                payload["fecha_base"],
                payload["provincia"],
                estado_final,
                concepto_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/{concepto_id}",
        mensaje="Partida actualizada.",
        aviso=aviso,
    )


@router.post("/costes/{concepto_id}/eliminar")
def eliminar_coste(request: Request, concepto_id: int):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        concepto = obtener_concepto(cur, concepto_id)
        if concepto is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")

        usos = contar_usos_concepto_costes(cur, concepto_id)
        if usos["patologias"] or usos["actuaciones"]:
            detalle = (
                f" Actuaciones vinculadas: {usos['actuaciones']}. "
                f"Patologías vinculadas: {usos['patologias']}."
            )
            return redirect_costes(
                "/costes",
                error="Esta partida está siendo utilizada y no puede eliminarse." + detalle,
            )

        cur.execute(
            """
            DELETE FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            """,
            (concepto_id,),
        )
        cur.execute(
            """
            UPDATE costes_descompuestos
            SET concepto_hijo_id = NULL
            WHERE concepto_hijo_id = ?
            """,
            (concepto_id,),
        )
        cur.execute("DELETE FROM costes_conceptos WHERE id = ?", (concepto_id,))
        conn.commit()
    finally:
        conn.close()

    return redirect_costes("/costes", mensaje="Partida eliminada.")


@router.post("/costes/{concepto_id}/descompuestos")
def crear_descompuesto(
    request: Request,
    concepto_id: int,
    codigo: str = Form(""),
    tipo: str = Form("material"),
    unidad: str = Form(""),
    resumen: str = Form(""),
    precio_unitario: str = Form("0"),
    rendimiento: str = Form("0"),
    importe: str = Form(""),
    orden: str = Form("0"),
):
    get_current_user(request)
    tipo_limpio = limpiar_texto(tipo)
    if tipo_limpio not in TIPOS_DESCOMPUESTO:
        tipo_limpio = "material"
    precio_unitario_num = round(parse_float(precio_unitario, 0), 4)
    rendimiento_num = round(parse_float(rendimiento, 0), 4)
    importe_limpio = limpiar_texto(importe)
    importe_calculado = round(precio_unitario_num * rendimiento_num, 2)
    importe_num = round(parse_float(importe_limpio, importe_calculado), 2)
    orden_num = parse_int(orden) or 0
    aviso = ""
    if importe_limpio and abs(importe_num - importe_calculado) > TOLERANCIA_VALIDACION:
        aviso = (
            "El importe informado no coincide con precio unitario x rendimiento "
            f"({format_money(importe_calculado)} €). Se ha respetado el importe manual."
        )

    conn = get_connection()
    try:
        cur = conn.cursor()
        if obtener_concepto(cur, concepto_id) is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        cur.execute(
            """
            INSERT INTO costes_descompuestos (
                concepto_padre_id, codigo, tipo, unidad, resumen,
                precio_unitario, rendimiento, importe, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concepto_id,
                limpiar_texto(codigo),
                tipo_limpio,
                limpiar_texto(unidad),
                limpiar_texto(resumen),
                precio_unitario_num,
                rendimiento_num,
                importe_num,
                orden_num,
            ),
        )
        cur.execute(
            """
            UPDATE costes_conceptos
            SET estado = 'borrador', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/{concepto_id}",
        mensaje="Descompuesto añadido.",
        aviso=aviso,
    )


@router.post("/costes/descompuestos/{descompuesto_id}/actualizar")
def actualizar_descompuesto(
    request: Request,
    descompuesto_id: int,
    codigo: str = Form(""),
    tipo: str = Form("material"),
    unidad: str = Form(""),
    resumen: str = Form(""),
    precio_unitario: str = Form("0"),
    rendimiento: str = Form("0"),
    importe: str = Form(""),
    orden: str = Form("0"),
):
    get_current_user(request)
    tipo_limpio = limpiar_texto(tipo)
    if tipo_limpio not in TIPOS_DESCOMPUESTO:
        tipo_limpio = "material"
    precio_unitario_num = round(parse_float(precio_unitario, 0), 4)
    rendimiento_num = round(parse_float(rendimiento, 0), 4)
    importe_limpio = limpiar_texto(importe)
    importe_calculado = round(precio_unitario_num * rendimiento_num, 2)
    importe_num = round(parse_float(importe_limpio, importe_calculado), 2)
    orden_num = parse_int(orden) or 0
    aviso = ""
    if importe_limpio and abs(importe_num - importe_calculado) > TOLERANCIA_VALIDACION:
        aviso = (
            "El importe informado no coincide con precio unitario x rendimiento "
            f"({format_money(importe_calculado)} €). Se ha respetado el importe manual."
        )

    conn = get_connection()
    try:
        cur = conn.cursor()
        descompuesto = cur.execute(
            """
            SELECT id, concepto_padre_id
            FROM costes_descompuestos
            WHERE id = ?
            """,
            (descompuesto_id,),
        ).fetchone()
        if descompuesto is None:
            raise HTTPException(status_code=404, detail="Descompuesto no encontrado")
        concepto_id = descompuesto["concepto_padre_id"]
        cur.execute(
            """
            UPDATE costes_descompuestos
            SET codigo = ?, tipo = ?, unidad = ?, resumen = ?,
                precio_unitario = ?, rendimiento = ?, importe = ?, orden = ?
            WHERE id = ?
            """,
            (
                limpiar_texto(codigo),
                tipo_limpio,
                limpiar_texto(unidad),
                limpiar_texto(resumen),
                precio_unitario_num,
                rendimiento_num,
                importe_num,
                orden_num,
                descompuesto_id,
            ),
        )
        cur.execute(
            """
            UPDATE costes_conceptos
            SET estado = 'borrador', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(
        f"/costes/{concepto_id}",
        mensaje="Descompuesto actualizado.",
        aviso=aviso,
    )


@router.post("/costes/descompuestos/{descompuesto_id}/borrar")
def borrar_descompuesto(request: Request, descompuesto_id: int):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        descompuesto = cur.execute(
            """
            SELECT id, concepto_padre_id
            FROM costes_descompuestos
            WHERE id = ?
            """,
            (descompuesto_id,),
        ).fetchone()
        if descompuesto is None:
            raise HTTPException(status_code=404, detail="Descompuesto no encontrado")
        concepto_id = descompuesto["concepto_padre_id"]
        cur.execute("DELETE FROM costes_descompuestos WHERE id = ?", (descompuesto_id,))
        cur.execute(
            """
            UPDATE costes_conceptos
            SET estado = 'borrador', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(f"/costes/{concepto_id}", mensaje="Descompuesto borrado.")


@router.post("/costes/{concepto_id}/validar")
def validar_coste(request: Request, concepto_id: int):
    get_current_user(request)
    conn = get_connection()
    try:
        cur = conn.cursor()
        concepto = obtener_concepto(cur, concepto_id)
        if concepto is None:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        descompuestos = obtener_descompuestos(cur, concepto_id)
        error = validar_para_estado_validado(concepto, descompuestos)
        if error:
            cur.execute(
                """
                UPDATE costes_conceptos
                SET estado = 'borrador', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (concepto_id,),
            )
            conn.commit()
            return redirect_costes(f"/costes/{concepto_id}", error=error)

        cur.execute(
            """
            UPDATE costes_conceptos
            SET estado = 'validado', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    return redirect_costes(f"/costes/{concepto_id}", mensaje="Partida validada.")
