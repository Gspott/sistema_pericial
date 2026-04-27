from datetime import date

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.database import get_connection
from app.services.verifactu import preparar_registro_verifactu

router = APIRouter()

FACTURA_ESTADOS = ("borrador", "emitida", "cobrada", "anulada")
CONFIG_FISCAL_DEFAULTS = {
    "nombre_fiscal": "",
    "nif_cif": "",
    "direccion": "",
    "codigo_postal": "",
    "ciudad": "",
    "provincia": "",
    "email": "",
    "telefono": "",
    "iva_defecto": 21,
    "irpf_defecto": 0,
    "serie_factura": "F",
    "tipo_emisor": "autonomo",
    "es_nuevo_autonomo": 0,
    "aplicar_irpf_por_defecto": 1,
}


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


def parse_optional_int(valor: str | None) -> int | None:
    valor_limpio = limpiar_texto(valor)
    if not valor_limpio:
        return None
    try:
        return int(valor_limpio)
    except ValueError:
        return None


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


def get_owned_factura(cur, factura_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT f.*,
               c.nombre AS cliente_nombre,
               c.apellidos AS cliente_apellidos,
               c.razon_social AS cliente_razon_social,
               c.nif_cif AS cliente_nif_cif,
               c.email AS cliente_email,
               c.telefono AS cliente_telefono,
               c.tipo_cliente AS cliente_tipo_cliente,
               c.direccion AS cliente_direccion,
               c.codigo_postal AS cliente_codigo_postal,
               c.ciudad AS cliente_ciudad,
               c.provincia AS cliente_provincia,
               p.numero_propuesta,
               e.numero_expediente
        FROM facturas_emitidas f
        LEFT JOIN clientes c ON c.id = f.cliente_id
        LEFT JOIN propuestas p ON p.id = f.propuesta_id
        LEFT JOIN expedientes e ON e.id = f.expediente_id
        WHERE f.id = ? AND f.owner_user_id = ?
        """,
        (factura_id, owner_user_id),
    ).fetchone()


def get_owned_cliente(cur, cliente_id: int, owner_user_id: int):
    return cur.execute(
        "SELECT * FROM clientes WHERE id = ? AND owner_user_id = ?",
        (cliente_id, owner_user_id),
    ).fetchone()


def get_owned_propuesta(cur, propuesta_id: int, owner_user_id: int):
    return cur.execute(
        "SELECT * FROM propuestas WHERE id = ? AND owner_user_id = ?",
        (propuesta_id, owner_user_id),
    ).fetchone()


def get_owned_expediente(cur, expediente_id: int, owner_user_id: int):
    return cur.execute(
        "SELECT * FROM expedientes WHERE id = ? AND owner_user_id = ?",
        (expediente_id, owner_user_id),
    ).fetchone()


def obtener_configuracion_fiscal(cur, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM configuracion_fiscal
        WHERE owner_user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (owner_user_id,),
    ).fetchone()


def configuracion_fiscal_para_formulario(config):
    data = dict(CONFIG_FISCAL_DEFAULTS)
    if config:
        data.update(dict(config))
    return data


def normalizar_tipo_cliente(valor: str | None) -> str:
    return limpiar_texto(valor).lower()


def calcular_irpf_sugerido(cliente, configuracion_fiscal) -> float:
    if not cliente or not configuracion_fiscal:
        return 0.0

    aplicar = int(configuracion_fiscal["aplicar_irpf_por_defecto"] or 0)
    if not aplicar:
        return 0.0

    if normalizar_tipo_cliente(configuracion_fiscal["tipo_emisor"]) == "sociedad":
        return 0.0

    claves = cliente.keys() if hasattr(cliente, "keys") else cliente
    tipo_key = "tipo_cliente" if "tipo_cliente" in claves else "cliente_tipo_cliente"
    tipo_cliente = normalizar_tipo_cliente(cliente[tipo_key])
    if tipo_cliente not in {"empresa", "autonomo", "entidad"}:
        return 0.0

    return 7.0 if int(configuracion_fiscal["es_nuevo_autonomo"] or 0) else 15.0


def obtener_lineas_factura(cur, factura_id: int):
    return cur.execute(
        """
        SELECT *
        FROM factura_lineas
        WHERE factura_id = ?
        ORDER BY orden ASC, id ASC
        """,
        (factura_id,),
    ).fetchall()


def obtener_cobros_factura(cur, factura_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM cobros
        WHERE factura_id = ? AND owner_user_id = ?
        ORDER BY fecha ASC, id ASC
        """,
        (factura_id, owner_user_id),
    ).fetchall()


def registrar_evento_factura(
    cur,
    factura_id: int,
    owner_user_id: int,
    tipo: str,
    descripcion: str = "",
):
    cur.execute(
        """
        INSERT INTO factura_eventos (
            factura_id, tipo, descripcion, owner_user_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (factura_id, tipo, limpiar_texto(descripcion), owner_user_id),
    )


def obtener_eventos_factura(cur, factura_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM factura_eventos
        WHERE factura_id = ? AND owner_user_id = ?
        ORDER BY id DESC
        """,
        (factura_id, owner_user_id),
    ).fetchall()


def obtener_rectificativas_factura(cur, factura_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT id, numero_factura, estado, fecha, total, motivo_rectificacion
        FROM facturas_emitidas
        WHERE factura_rectificada_id = ? AND owner_user_id = ?
        ORDER BY id DESC
        """,
        (factura_id, owner_user_id),
    ).fetchall()


def obtener_factura_referencia(cur, factura_id: int | None, owner_user_id: int):
    if not factura_id:
        return None
    return cur.execute(
        """
        SELECT id, numero_factura, estado, fecha, total
        FROM facturas_emitidas
        WHERE id = ? AND owner_user_id = ?
        """,
        (factura_id, owner_user_id),
    ).fetchone()


def calcular_linea(cantidad: float, precio_unitario: float, iva_porcentaje: float, irpf_porcentaje: float):
    subtotal = cantidad * precio_unitario
    iva_importe = subtotal * iva_porcentaje / 100
    irpf_importe = subtotal * irpf_porcentaje / 100
    total = subtotal + iva_importe - irpf_importe
    return subtotal, iva_importe, irpf_importe, total


def recalcular_totales_factura(cur, factura_id: int):
    lineas = obtener_lineas_factura(cur, factura_id)
    base_imponible = sum(float(linea["subtotal"] or 0) for linea in lineas)
    iva = sum(float(linea["iva_importe"] or 0) for linea in lineas)
    irpf = sum(float(linea["irpf_importe"] or 0) for linea in lineas)
    total = base_imponible + iva - irpf
    cur.execute(
        """
        UPDATE facturas_emitidas
        SET base_imponible = ?, iva = ?, irpf = ?, total = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (base_imponible, iva, irpf, total, factura_id),
    )


def nombre_cliente(cliente) -> str:
    if not cliente:
        return "Sin cliente"
    claves = cliente.keys() if hasattr(cliente, "keys") else cliente
    razon_social_key = "razon_social" if "razon_social" in claves else "cliente_razon_social"
    nombre_key = "nombre" if "nombre" in claves else "cliente_nombre"
    apellidos_key = "apellidos" if "apellidos" in claves else "cliente_apellidos"
    razon_social = limpiar_texto(cliente[razon_social_key])
    if razon_social:
        return razon_social
    partes = [limpiar_texto(cliente[nombre_key]), limpiar_texto(cliente[apellidos_key])]
    return " ".join(parte for parte in partes if parte) or "Sin cliente"


def cargar_contexto_formulario(cur, owner_user_id: int):
    clientes = cur.execute(
        """
        SELECT id, nombre, apellidos, razon_social
        FROM clientes
        WHERE owner_user_id = ?
        ORDER BY id DESC
        """,
        (owner_user_id,),
    ).fetchall()
    propuestas = cur.execute(
        """
        SELECT id, numero_propuesta
        FROM propuestas
        WHERE owner_user_id = ?
        ORDER BY id DESC
        """,
        (owner_user_id,),
    ).fetchall()
    expedientes = cur.execute(
        """
        SELECT id, numero_expediente, cliente
        FROM expedientes
        WHERE owner_user_id = ?
        ORDER BY id DESC
        """,
        (owner_user_id,),
    ).fetchall()
    return clientes, propuestas, expedientes


def siguiente_numero_factura(cur, serie: str) -> str:
    serie_limpia = limpiar_texto(serie) or "F"
    year = date.today().year
    prefijo = f"{serie_limpia}-{year}-"
    row = cur.execute(
        """
        SELECT numero_factura
        FROM facturas_emitidas
        WHERE numero_factura LIKE ?
        ORDER BY numero_factura DESC
        LIMIT 1
        """,
        (f"{prefijo}%",),
    ).fetchone()

    siguiente = 1
    if row and row["numero_factura"]:
        partes = row["numero_factura"].split("-")
        if len(partes) == 3 and partes[2].isdigit():
            siguiente = int(partes[2]) + 1
    return f"{prefijo}{siguiente:04d}"


def suma_cobros(cobros) -> float:
    return sum(float(cobro["importe"] or 0) for cobro in cobros)


def obtener_trimestre_actual():
    hoy = date.today()
    trimestre = ((hoy.month - 1) // 3) + 1
    return hoy.year, trimestre


def obtener_rango_trimestre(year: int, trimestre: int):
    mes_inicio = (trimestre - 1) * 3 + 1
    mes_fin = mes_inicio + 2
    fecha_inicio = date(year, mes_inicio, 1)
    if mes_fin == 12:
        fecha_fin = date(year, 12, 31)
    else:
        fecha_fin = date(year, mes_fin + 1, 1).replace(day=1)
        fecha_fin = date.fromordinal(fecha_fin.toordinal() - 1)
    return fecha_inicio.isoformat(), fecha_fin.isoformat()


def calcular_resumen_iva(owner_user_id: int, year: int, trimestre: int):
    fecha_inicio, fecha_fin = obtener_rango_trimestre(year, trimestre)
    conn = get_connection()
    cur = conn.cursor()
    try:
        facturas = cur.execute(
            """
            SELECT f.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
                   c.razon_social AS cliente_razon_social,
                   c.nif_cif AS cliente_nif_cif
            FROM facturas_emitidas f
            LEFT JOIN clientes c ON c.id = f.cliente_id
            WHERE f.owner_user_id = ?
              AND f.estado IN ('emitida', 'cobrada')
              AND f.fecha BETWEEN ? AND ?
            ORDER BY f.fecha ASC, f.id ASC
            """,
            (owner_user_id, fecha_inicio, fecha_fin),
        ).fetchall()
        gastos = cur.execute(
            """
            SELECT *
            FROM gastos
            WHERE owner_user_id = ?
              AND deducible = 1
              AND fecha BETWEEN ? AND ?
            ORDER BY fecha ASC, id ASC
            """,
            (owner_user_id, fecha_inicio, fecha_fin),
        ).fetchall()
    finally:
        conn.close()

    bases_facturas = sum(float(factura["base_imponible"] or 0) for factura in facturas)
    iva_repercutido = sum(float(factura["iva"] or 0) for factura in facturas)
    total_facturado = sum(float(factura["total"] or 0) for factura in facturas)
    bases_gastos = sum(float(gasto["base_imponible"] or 0) for gasto in gastos)
    iva_soportado = sum(float(gasto["iva_importe"] or 0) for gasto in gastos)
    total_gastos = sum(float(gasto["total"] or 0) for gasto in gastos)

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "facturas": facturas,
        "gastos": gastos,
        "bases_facturas": bases_facturas,
        "iva_repercutido": iva_repercutido,
        "total_facturado": total_facturado,
        "bases_gastos": bases_gastos,
        "iva_soportado": iva_soportado,
        "total_gastos": total_gastos,
        "resultado_estimado": iva_repercutido - iva_soportado,
    }


@router.get("/facturacion", response_class=HTMLResponse)
def index_facturacion(request: Request):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        resumen = cur.execute(
            """
            SELECT
                COUNT(*) AS total_facturas,
                SUM(CASE WHEN estado = 'borrador' THEN 1 ELSE 0 END) AS borradores,
                SUM(CASE WHEN estado = 'emitida' THEN 1 ELSE 0 END) AS emitidas,
                SUM(CASE WHEN estado = 'cobrada' THEN 1 ELSE 0 END) AS cobradas,
                COALESCE(SUM(total), 0) AS total_importe
            FROM facturas_emitidas
            WHERE owner_user_id = ?
            """,
            (current_user["id"],),
        ).fetchone()
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/index.html",
        {"resumen": resumen, "format_money": format_money},
    )


@router.get("/facturacion/configuracion", response_class=HTMLResponse)
def editar_configuracion_fiscal(request: Request):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        config = obtener_configuracion_fiscal(cur, current_user["id"])
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/configuracion.html",
        {
            "config": configuracion_fiscal_para_formulario(config),
            "error": "",
        },
    )


@router.post("/facturacion/configuracion")
def guardar_configuracion_fiscal(
    request: Request,
    nombre_fiscal: str = Form(""),
    nif_cif: str = Form(""),
    direccion: str = Form(""),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    iva_defecto: str = Form("21"),
    serie_factura: str = Form("F"),
    tipo_emisor: str = Form("autonomo"),
    es_nuevo_autonomo: str = Form("0"),
    aplicar_irpf_por_defecto: str = Form("0"),
):
    current_user = get_current_user(request)
    config_form = {
        "nombre_fiscal": limpiar_texto(nombre_fiscal),
        "nif_cif": limpiar_texto(nif_cif),
        "direccion": limpiar_texto(direccion),
        "codigo_postal": limpiar_texto(codigo_postal),
        "ciudad": limpiar_texto(ciudad),
        "provincia": limpiar_texto(provincia),
        "email": limpiar_texto(email),
        "telefono": limpiar_texto(telefono),
        "iva_defecto": parse_float(iva_defecto, 21),
        "serie_factura": limpiar_texto(serie_factura) or "F",
        "tipo_emisor": normalizar_tipo_cliente(tipo_emisor)
        if normalizar_tipo_cliente(tipo_emisor) in {"autonomo", "sociedad"}
        else "autonomo",
        "es_nuevo_autonomo": 1 if limpiar_texto(es_nuevo_autonomo) == "1" else 0,
        "aplicar_irpf_por_defecto": 1
        if limpiar_texto(aplicar_irpf_por_defecto) == "1"
        else 0,
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        if config:
            cur.execute(
                """
                UPDATE configuracion_fiscal
                SET nombre_fiscal = ?, nif_cif = ?, direccion = ?, codigo_postal = ?,
                    ciudad = ?, provincia = ?, email = ?, telefono = ?,
                    iva_defecto = ?, serie_factura = ?, tipo_emisor = ?,
                    es_nuevo_autonomo = ?, aplicar_irpf_por_defecto = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (
                    config_form["nombre_fiscal"],
                    config_form["nif_cif"],
                    config_form["direccion"],
                    config_form["codigo_postal"],
                    config_form["ciudad"],
                    config_form["provincia"],
                    config_form["email"],
                    config_form["telefono"],
                    config_form["iva_defecto"],
                    config_form["serie_factura"],
                    config_form["tipo_emisor"],
                    config_form["es_nuevo_autonomo"],
                    config_form["aplicar_irpf_por_defecto"],
                    config["id"],
                    current_user["id"],
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO configuracion_fiscal (
                    nombre_fiscal, nif_cif, direccion, codigo_postal, ciudad,
                    provincia, email, telefono, iva_defecto, serie_factura,
                    tipo_emisor, es_nuevo_autonomo, aplicar_irpf_por_defecto,
                    owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    config_form["nombre_fiscal"],
                    config_form["nif_cif"],
                    config_form["direccion"],
                    config_form["codigo_postal"],
                    config_form["ciudad"],
                    config_form["provincia"],
                    config_form["email"],
                    config_form["telefono"],
                    config_form["iva_defecto"],
                    config_form["serie_factura"],
                    config_form["tipo_emisor"],
                    config_form["es_nuevo_autonomo"],
                    config_form["aplicar_irpf_por_defecto"],
                    current_user["id"],
                ),
            )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url="/facturacion", status_code=303)


@router.get("/facturacion/facturas", response_class=HTMLResponse)
def listar_facturas(request: Request, estado: str = Query("", max_length=30)):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    conn = get_connection()
    cur = conn.cursor()
    try:
        params = [current_user["id"]]
        filtro_estado = ""
        if estado_limpio in FACTURA_ESTADOS:
            filtro_estado = " AND f.estado = ?"
            params.append(estado_limpio)
        facturas = cur.execute(
            f"""
            SELECT f.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
                   c.razon_social AS cliente_razon_social
            FROM facturas_emitidas f
            LEFT JOIN clientes c ON c.id = f.cliente_id
            WHERE f.owner_user_id = ?{filtro_estado}
            ORDER BY f.id DESC
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/facturas_listado.html",
        {
            "facturas": facturas,
            "estado_actual": estado_limpio if estado_limpio in FACTURA_ESTADOS else "",
            "estados_factura": FACTURA_ESTADOS,
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
        },
    )


@router.get("/facturacion/iva", response_class=HTMLResponse)
def resumen_iva(
    request: Request,
    year: int | None = Query(None),
    trimestre: int | None = Query(None),
):
    current_user = get_current_user(request)
    year_actual, trimestre_actual = obtener_trimestre_actual()
    year_resuelto = year or year_actual
    trimestre_resuelto = trimestre if trimestre in (1, 2, 3, 4) else trimestre_actual
    resumen = calcular_resumen_iva(
        current_user["id"],
        year_resuelto,
        trimestre_resuelto,
    )

    return render_template(
        request,
        "facturacion/iva.html",
        {
            "year": year_resuelto,
            "trimestre": trimestre_resuelto,
            "resumen": resumen,
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
        },
    )


@router.get("/facturacion/exportar-trimestre", response_class=HTMLResponse)
def exportar_trimestre_form(
    request: Request,
    year: int | None = Query(None),
    trimestre: int | None = Query(None),
):
    get_current_user(request)
    year_actual, trimestre_actual = obtener_trimestre_actual()
    return render_template(
        request,
        "facturacion/exportar_trimestre.html",
        {
            "year": year or year_actual,
            "trimestre": trimestre if trimestre in (1, 2, 3, 4) else trimestre_actual,
        },
    )


@router.post("/facturacion/exportar-trimestre")
def exportar_trimestre(
    request: Request,
    year: int = Form(...),
    trimestre: int = Form(...),
):
    from app.services.exportaciones import crear_exportacion_trimestral

    current_user = get_current_user(request)
    if trimestre not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="Trimestre no válido")
    ruta_zip = crear_exportacion_trimestral(current_user["id"], year, trimestre)
    return FileResponse(
        path=str(ruta_zip),
        filename=ruta_zip.name,
        media_type="application/zip",
    )


@router.get("/facturacion/facturas/nueva", response_class=HTMLResponse)
def nueva_factura(
    request: Request,
    cliente_id: int | None = Query(None),
    propuesta_id: int | None = Query(None),
    expediente_id: int | None = Query(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"]) if propuesta_id else None
        expediente = get_owned_expediente(cur, expediente_id, current_user["id"]) if expediente_id else None
        if propuesta and propuesta["cliente_id"]:
            cliente_id = propuesta["cliente_id"]
        clientes, propuestas, expedientes = cargar_contexto_formulario(cur, current_user["id"])
        config_form = configuracion_fiscal_para_formulario(config)
        cliente = get_owned_cliente(cur, cliente_id, current_user["id"]) if cliente_id else None
        irpf_sugerido = calcular_irpf_sugerido(cliente, config)
        factura = {
            "fecha": str(date.today()),
            "serie": config_form["serie_factura"] or "F",
            "estado": "borrador",
            "cliente_id": cliente_id or "",
            "propuesta_id": propuesta_id or "",
            "expediente_id": expediente_id or "",
            "concepto_general": propuesta["tipo_trabajo"] if propuesta else expediente["numero_expediente"] if expediente else "",
            "irpf_porcentaje_defecto": irpf_sugerido,
            "notas": "",
        }
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/factura_form.html",
        {
            "factura": factura,
            "clientes": clientes,
            "propuestas": propuestas,
            "expedientes": expedientes,
            "form_action": "/facturacion/facturas/nueva",
            "titulo": "Nueva factura",
            "submit_label": "Guardar borrador",
            "error": "",
        },
    )


@router.post("/facturacion/facturas/nueva")
def crear_factura(
    request: Request,
    fecha: str = Form(...),
    serie: str = Form("F"),
    cliente_id: str = Form(""),
    propuesta_id: str = Form(""),
    expediente_id: str = Form(""),
    concepto_general: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    cliente_id_int = parse_optional_int(cliente_id)
    propuesta_id_int = parse_optional_int(propuesta_id)
    expediente_id_int = parse_optional_int(expediente_id)
    factura = {
        "fecha": limpiar_texto(fecha),
        "serie": limpiar_texto(serie) or "F",
        "cliente_id": cliente_id_int or "",
        "propuesta_id": propuesta_id_int or "",
        "expediente_id": expediente_id_int or "",
        "concepto_general": limpiar_texto(concepto_general),
        "notas": limpiar_texto(notas),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        clientes, propuestas, expedientes = cargar_contexto_formulario(cur, current_user["id"])
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        cliente = get_owned_cliente(cur, cliente_id_int, current_user["id"]) if cliente_id_int else None
        irpf_sugerido = calcular_irpf_sugerido(cliente, config)
        factura["irpf_porcentaje_defecto"] = irpf_sugerido
        error = ""
        if not factura["fecha"]:
            error = "La fecha es obligatoria."
        elif cliente_id_int and not cliente:
            error = "El cliente indicado no existe."
        elif propuesta_id_int and not get_owned_propuesta(cur, propuesta_id_int, current_user["id"]):
            error = "La propuesta indicada no existe."
        elif expediente_id_int and not get_owned_expediente(cur, expediente_id_int, current_user["id"]):
            error = "El expediente indicado no existe."

        if error:
            return render_template(
                request,
                "facturacion/factura_form.html",
                {
                    "factura": factura,
                    "clientes": clientes,
                    "propuestas": propuestas,
                    "expedientes": expedientes,
                    "form_action": "/facturacion/facturas/nueva",
                    "titulo": "Nueva factura",
                    "submit_label": "Guardar borrador",
                    "error": error,
                },
            )

        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                serie, fecha, estado, cliente_id, propuesta_id, expediente_id,
                concepto_general, irpf_porcentaje_defecto, notas, tipo_factura,
                owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factura["serie"],
                factura["fecha"],
                "borrador",
                cliente_id_int,
                propuesta_id_int,
                expediente_id_int,
                factura["concepto_general"],
                irpf_sugerido,
                factura["notas"],
                "ordinaria",
                current_user["id"],
            ),
        )
        factura_id = cur.lastrowid
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "creada",
            "Factura creada en borrador.",
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.get("/facturacion/facturas/{factura_id}", response_class=HTMLResponse)
def detalle_factura(request: Request, factura_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        lineas = obtener_lineas_factura(cur, factura_id)
        cobros = obtener_cobros_factura(cur, factura_id, current_user["id"])
        eventos = obtener_eventos_factura(cur, factura_id, current_user["id"])
        rectificativas = obtener_rectificativas_factura(
            cur, factura_id, current_user["id"]
        )
        factura_rectificada = obtener_factura_referencia(
            cur, factura["factura_rectificada_id"], current_user["id"]
        )
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        config_form = configuracion_fiscal_para_formulario(config)
        irpf_sugerido = factura["irpf_porcentaje_defecto"]
        if irpf_sugerido is None and factura["estado"] == "borrador":
            irpf_sugerido = calcular_irpf_sugerido(factura, config)
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/factura_detalle.html",
        {
            "factura": factura,
            "lineas": lineas,
            "cobros": cobros,
            "eventos": eventos,
            "rectificativas": rectificativas,
            "factura_rectificada": factura_rectificada,
            "iva_defecto": config_form["iva_defecto"] or 21,
            "irpf_defecto": irpf_sugerido or 0,
            "configuracion_fiscal_completa": bool(config),
            "total_cobrado": suma_cobros(cobros),
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
        },
    )


@router.get("/facturacion/facturas/{factura_id}/editar", response_class=HTMLResponse)
def editar_factura(request: Request, factura_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] != "borrador":
            raise HTTPException(
                status_code=400,
                detail="Factura emitida: bloqueada para edición fiscal.",
            )
        clientes, propuestas, expedientes = cargar_contexto_formulario(cur, current_user["id"])
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/factura_form.html",
        {
            "factura": dict(factura),
            "clientes": clientes,
            "propuestas": propuestas,
            "expedientes": expedientes,
            "form_action": f"/facturacion/facturas/{factura_id}/editar",
            "titulo": "Editar factura",
            "submit_label": "Guardar cambios",
            "error": "",
        },
    )


@router.post("/facturacion/facturas/{factura_id}/editar")
def actualizar_factura(
    request: Request,
    factura_id: int,
    fecha: str = Form(...),
    serie: str = Form("F"),
    cliente_id: str = Form(""),
    propuesta_id: str = Form(""),
    expediente_id: str = Form(""),
    concepto_general: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    cliente_id_int = parse_optional_int(cliente_id)
    propuesta_id_int = parse_optional_int(propuesta_id)
    expediente_id_int = parse_optional_int(expediente_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] != "borrador":
            raise HTTPException(
                status_code=400,
                detail="Factura emitida: bloqueada para edición fiscal.",
            )

        clientes, propuestas, expedientes = cargar_contexto_formulario(cur, current_user["id"])
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        cliente = get_owned_cliente(cur, cliente_id_int, current_user["id"]) if cliente_id_int else None
        irpf_sugerido = calcular_irpf_sugerido(cliente, config)
        factura_form = {
            "id": factura_id,
            "fecha": limpiar_texto(fecha),
            "serie": limpiar_texto(serie) or "F",
            "estado": factura["estado"],
            "cliente_id": cliente_id_int or "",
            "propuesta_id": propuesta_id_int or "",
            "expediente_id": expediente_id_int or "",
            "concepto_general": limpiar_texto(concepto_general),
            "irpf_porcentaje_defecto": irpf_sugerido,
            "notas": limpiar_texto(notas),
        }
        error = ""
        if not factura_form["fecha"]:
            error = "La fecha es obligatoria."
        elif cliente_id_int and not cliente:
            error = "El cliente indicado no existe."
        elif propuesta_id_int and not get_owned_propuesta(cur, propuesta_id_int, current_user["id"]):
            error = "La propuesta indicada no existe."
        elif expediente_id_int and not get_owned_expediente(cur, expediente_id_int, current_user["id"]):
            error = "El expediente indicado no existe."

        if error:
            return render_template(
                request,
                "facturacion/factura_form.html",
                {
                    "factura": factura_form,
                    "clientes": clientes,
                    "propuestas": propuestas,
                    "expedientes": expedientes,
                    "form_action": f"/facturacion/facturas/{factura_id}/editar",
                    "titulo": "Editar factura",
                    "submit_label": "Guardar cambios",
                    "error": error,
                },
            )

        cur.execute(
            """
            UPDATE facturas_emitidas
            SET fecha = ?, serie = ?, cliente_id = ?, propuesta_id = ?, expediente_id = ?,
                concepto_general = ?, irpf_porcentaje_defecto = ?, notas = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                factura_form["fecha"],
                factura_form["serie"],
                cliente_id_int,
                propuesta_id_int,
                expediente_id_int,
                factura_form["concepto_general"],
                factura_form["irpf_porcentaje_defecto"],
                factura_form["notas"],
                factura_id,
                current_user["id"],
            ),
        )
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "editada",
            "Factura editada en borrador.",
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/lineas")
def crear_linea_factura(
    request: Request,
    factura_id: int,
    concepto: str = Form(...),
    descripcion: str = Form(""),
    cantidad: str = Form("1"),
    precio_unitario: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    irpf_porcentaje: str = Form(""),
):
    current_user = get_current_user(request)
    concepto_limpio = limpiar_texto(concepto)
    if not concepto_limpio:
        return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] != "borrador":
            raise HTTPException(status_code=400, detail="Solo se pueden editar líneas en borrador.")

        cantidad_valor = parse_float(cantidad, 1)
        precio_unitario_valor = parse_float(precio_unitario, 0)
        iva_porcentaje_valor = parse_float(iva_porcentaje, 21)
        if limpiar_texto(irpf_porcentaje):
            irpf_porcentaje_valor = parse_float(irpf_porcentaje, 0)
        else:
            config = obtener_configuracion_fiscal(cur, current_user["id"])
            irpf_porcentaje_valor = factura["irpf_porcentaje_defecto"]
            if irpf_porcentaje_valor is None:
                irpf_porcentaje_valor = calcular_irpf_sugerido(factura, config)
            irpf_porcentaje_valor = float(irpf_porcentaje_valor or 0)
        subtotal, iva_importe, irpf_importe, total = calcular_linea(
            cantidad_valor,
            precio_unitario_valor,
            iva_porcentaje_valor,
            irpf_porcentaje_valor,
        )
        siguiente_orden = cur.execute(
            """
            SELECT COALESCE(MAX(orden), 0) + 1
            FROM factura_lineas
            WHERE factura_id = ?
            """,
            (factura_id,),
        ).fetchone()[0]
        cur.execute(
            """
            INSERT INTO factura_lineas (
                factura_id, concepto, descripcion, cantidad, precio_unitario,
                iva_porcentaje, irpf_porcentaje, subtotal, iva_importe,
                irpf_importe, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factura_id,
                concepto_limpio,
                limpiar_texto(descripcion),
                cantidad_valor,
                precio_unitario_valor,
                iva_porcentaje_valor,
                irpf_porcentaje_valor,
                subtotal,
                iva_importe,
                irpf_importe,
                total,
                siguiente_orden,
            ),
        )
        recalcular_totales_factura(cur, factura_id)
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "linea_anadida",
            f"Línea añadida: {concepto_limpio}.",
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/emitir")
def emitir_factura(request: Request, factura_id: int):
    current_user = get_current_user(request)
    numero_factura = None

    for _ in range(3):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            factura = get_owned_factura(cur, factura_id, current_user["id"])
            if not factura:
                raise HTTPException(status_code=404, detail="Factura no encontrada")
            if factura["estado"] != "borrador":
                conn.rollback()
                return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)
            lineas = obtener_lineas_factura(cur, factura_id)
            if not factura["cliente_id"] or not lineas:
                raise HTTPException(
                    status_code=400,
                    detail="No se puede emitir una factura sin cliente y sin líneas.",
                )

            numero_factura = siguiente_numero_factura(cur, factura["serie"] or "F")
            existe = cur.execute(
                "SELECT id FROM facturas_emitidas WHERE numero_factura = ?",
                (numero_factura,),
            ).fetchone()
            if existe:
                conn.rollback()
                continue

            cur.execute(
                """
                UPDATE facturas_emitidas
                SET numero_factura = ?, estado = 'emitida', fecha_emision = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (numero_factura, str(date.today()), factura_id, current_user["id"]),
            )
            registro_tecnico = preparar_registro_verifactu(
                conn,
                factura_id,
                current_user["id"],
            )
            registrar_evento_factura(
                cur,
                factura_id,
                current_user["id"],
                "emitida",
                f"Factura emitida con número {numero_factura}.",
            )
            registrar_evento_factura(
                cur,
                factura_id,
                current_user["id"],
                "verifactu_generado",
                (
                    "Hash generado "
                    f"{registro_tecnico['hash_factura'][:12]}... "
                    "y preparación técnica sin envío AEAT."
                ),
            )
            conn.commit()
            break
        except HTTPException:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    if numero_factura is None:
        raise HTTPException(status_code=500, detail="No se pudo asignar número de factura.")
    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/generar-registro-tecnico")
def generar_registro_tecnico_factura(request: Request, factura_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("BEGIN IMMEDIATE")
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] not in ("emitida", "cobrada", "anulada"):
            raise HTTPException(
                status_code=400,
                detail="Solo se puede generar en facturas emitidas, cobradas o anuladas.",
            )
        if factura["hash_factura"]:
            raise HTTPException(
                status_code=400,
                detail="La factura ya tiene registro técnico generado.",
            )
        registro_tecnico = preparar_registro_verifactu(
            conn,
            factura_id,
            current_user["id"],
        )
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "verifactu_generado",
            (
                "Registro técnico generado manualmente "
                f"{registro_tecnico['hash_factura'][:12]}... "
                "sin envío AEAT."
            ),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/cobros")
def registrar_cobro_factura(
    request: Request,
    factura_id: int,
    fecha: str = Form(...),
    importe: str = Form(...),
    metodo: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    importe_valor = parse_float(importe, 0)
    if importe_valor <= 0:
        return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] not in ("emitida", "cobrada"):
            raise HTTPException(status_code=400, detail="Solo se pueden registrar cobros en facturas emitidas.")

        fecha_limpia = limpiar_texto(fecha) or str(date.today())
        cur.execute(
            """
            INSERT INTO cobros (
                factura_id, fecha, importe, metodo, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                factura_id,
                fecha_limpia,
                importe_valor,
                limpiar_texto(metodo),
                limpiar_texto(notas),
                current_user["id"],
            ),
        )
        cobros = obtener_cobros_factura(cur, factura_id, current_user["id"])
        total_cobrado = suma_cobros(cobros)
        nuevo_estado = "cobrada" if total_cobrado >= float(factura["total"] or 0) else "emitida"
        fecha_cobro = fecha_limpia if nuevo_estado == "cobrada" else None
        cur.execute(
            """
            UPDATE facturas_emitidas
            SET estado = ?, fecha_cobro = ?, metodo_cobro = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                nuevo_estado,
                fecha_cobro,
                limpiar_texto(metodo),
                factura_id,
                current_user["id"],
            ),
        )
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "cobro_registrado",
            f"Cobro registrado por {importe_valor:.2f}.",
        )
        if nuevo_estado == "cobrada" and factura["estado"] != "cobrada":
            registrar_evento_factura(
                cur,
                factura_id,
                current_user["id"],
                "cobrada",
                "Factura marcada como cobrada.",
            )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/notas")
def actualizar_notas_factura(
    request: Request,
    factura_id: int,
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    notas_limpias = limpiar_texto(notas)
    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        cur.execute(
            """
            UPDATE facturas_emitidas
            SET notas = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (notas_limpias, factura_id, current_user["id"]),
        )
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "nota",
            "Notas internas actualizadas.",
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/anular")
def anular_factura(
    request: Request,
    factura_id: int,
    motivo: str = Form(...),
):
    current_user = get_current_user(request)
    motivo_limpio = limpiar_texto(motivo)
    if not motivo_limpio:
        raise HTTPException(status_code=400, detail="El motivo de anulación es obligatorio.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] not in ("emitida", "cobrada"):
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden anular facturas emitidas o cobradas.",
            )
        cur.execute(
            """
            UPDATE facturas_emitidas
            SET estado = 'anulada', notas = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                f"{limpiar_texto(factura['notas'])}\nAnulación: {motivo_limpio}".strip(),
                factura_id,
                current_user["id"],
            ),
        )
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "anulacion_marcada",
            motivo_limpio,
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{factura_id}", status_code=303)


@router.post("/facturacion/facturas/{factura_id}/crear-rectificativa")
def crear_rectificativa_factura(
    request: Request,
    factura_id: int,
    motivo_rectificacion: str = Form(...),
):
    current_user = get_current_user(request)
    motivo_limpio = limpiar_texto(motivo_rectificacion)
    if not motivo_limpio:
        raise HTTPException(
            status_code=400,
            detail="El motivo de rectificación es obligatorio.",
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        if factura["estado"] not in ("emitida", "cobrada", "anulada"):
            raise HTTPException(
                status_code=400,
                detail="Solo se puede crear rectificativa desde una factura emitida, cobrada o anulada.",
            )
        lineas = obtener_lineas_factura(cur, factura_id)
        numero_origen = factura["numero_factura"] or f"#{factura_id}"
        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                serie, fecha, estado, cliente_id, propuesta_id, expediente_id,
                concepto_general, base_imponible, iva, irpf, total,
                irpf_porcentaje_defecto, notas, factura_rectificada_id,
                tipo_factura, motivo_rectificacion, owner_user_id
            )
            VALUES (?, ?, 'borrador', ?, ?, ?, ?, 0, 0, 0, 0, ?, ?, ?, 'rectificativa', ?, ?)
            """,
            (
                factura["serie"] or "F",
                str(date.today()),
                factura["cliente_id"],
                factura["propuesta_id"],
                factura["expediente_id"],
                f"Factura rectificativa de {numero_origen}",
                factura["irpf_porcentaje_defecto"] or 0,
                "",
                factura_id,
                motivo_limpio,
                current_user["id"],
            ),
        )
        rectificativa_id = cur.lastrowid
        registrar_evento_factura(
            cur,
            rectificativa_id,
            current_user["id"],
            "creada",
            f"Rectificativa creada desde factura {numero_origen}.",
        )

        for linea in lineas:
            cur.execute(
                """
                INSERT INTO factura_lineas (
                    factura_id, concepto, descripcion, cantidad, precio_unitario,
                    iva_porcentaje, irpf_porcentaje, subtotal, iva_importe,
                    irpf_importe, total, orden
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rectificativa_id,
                    linea["concepto"],
                    linea["descripcion"],
                    linea["cantidad"],
                    -float(linea["precio_unitario"] or 0),
                    linea["iva_porcentaje"],
                    linea["irpf_porcentaje"],
                    -float(linea["subtotal"] or 0),
                    -float(linea["iva_importe"] or 0),
                    -float(linea["irpf_importe"] or 0),
                    -float(linea["total"] or 0),
                    linea["orden"],
                ),
            )

        recalcular_totales_factura(cur, rectificativa_id)
        registrar_evento_factura(
            cur,
            factura_id,
            current_user["id"],
            "rectificativa_creada",
            f"Creada rectificativa #{rectificativa_id}. Motivo: {motivo_limpio}",
        )
        registrar_evento_factura(
            cur,
            rectificativa_id,
            current_user["id"],
            "rectificativa_creada",
            motivo_limpio,
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/facturacion/facturas/{rectificativa_id}", status_code=303)


@router.get("/facturacion/facturas/{factura_id}/imprimir", response_class=HTMLResponse)
def imprimir_factura(request: Request, factura_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        factura = get_owned_factura(cur, factura_id, current_user["id"])
        if not factura:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        lineas = obtener_lineas_factura(cur, factura_id)
        cobros = obtener_cobros_factura(cur, factura_id, current_user["id"])
        config = obtener_configuracion_fiscal(cur, current_user["id"])
        config_form = configuracion_fiscal_para_formulario(config)
    finally:
        conn.close()

    return render_template(
        request,
        "facturacion/factura_imprimir.html",
        {
            "factura": factura,
            "lineas": lineas,
            "cobros": cobros,
            "config": config_form,
            "total_cobrado": suma_cobros(cobros),
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
        },
    )
