from datetime import date

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection

router = APIRouter()

PROPUESTA_ESTADOS = ("borrador", "enviada", "aceptada", "rechazada", "caducada")


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


def get_owned_lead(cur, lead_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM leads
        WHERE id = ? AND owner_user_id = ?
        """,
        (lead_id, owner_user_id),
    ).fetchone()


def get_owned_cliente(cur, cliente_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM clientes
        WHERE id = ? AND owner_user_id = ?
        """,
        (cliente_id, owner_user_id),
    ).fetchone()


def get_owned_propuesta(cur, propuesta_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT p.*,
               l.nombre AS lead_nombre,
               l.email AS lead_email,
               l.telefono AS lead_telefono,
               c.nombre AS cliente_nombre,
               c.apellidos AS cliente_apellidos,
               c.razon_social AS cliente_razon_social,
               c.email AS cliente_email,
               c.telefono AS cliente_telefono
        FROM propuestas p
        LEFT JOIN leads l ON l.id = p.lead_id
        LEFT JOIN clientes c ON c.id = p.cliente_id
        WHERE p.id = ? AND p.owner_user_id = ?
        """,
        (propuesta_id, owner_user_id),
    ).fetchone()


def obtener_lineas_propuesta(cur, propuesta_id: int):
    return cur.execute(
        """
        SELECT *
        FROM propuesta_lineas
        WHERE propuesta_id = ?
        ORDER BY orden ASC, id ASC
        """,
        (propuesta_id,),
    ).fetchall()


def recalcular_totales_propuesta(cur, propuesta_id: int):
    lineas = obtener_lineas_propuesta(cur, propuesta_id)
    base_imponible = 0.0
    iva = 0.0
    total = 0.0

    for linea in lineas:
        cantidad = float(linea["cantidad"] or 0)
        precio_unitario = float(linea["precio_unitario"] or 0)
        iva_porcentaje = float(linea["iva_porcentaje"] or 0)
        base_linea = cantidad * precio_unitario
        iva_linea = base_linea * iva_porcentaje / 100
        total_linea = base_linea + iva_linea

        cur.execute(
            """
            UPDATE propuesta_lineas
            SET total = ?
            WHERE id = ?
            """,
            (total_linea, linea["id"]),
        )

        base_imponible += base_linea
        iva += iva_linea
        total += total_linea

    cur.execute(
        """
        UPDATE propuestas
        SET base_imponible = ?, iva = ?, total = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (base_imponible, iva, total, propuesta_id),
    )


def siguiente_numero_propuesta(cur) -> str:
    year = date.today().year
    prefijo = f"P-{year}-"
    ultima = cur.execute(
        """
        SELECT numero_propuesta
        FROM propuestas
        WHERE numero_propuesta LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"{prefijo}%",),
    ).fetchone()

    siguiente = 1
    if ultima and ultima["numero_propuesta"]:
        partes = ultima["numero_propuesta"].split("-")
        if len(partes) == 3 and partes[2].isdigit():
            siguiente = int(partes[2]) + 1

    return f"{prefijo}{siguiente:04d}"


def siguiente_numero_expediente(cur) -> str:
    sufijo_anio = date.today().strftime("%y")
    row = cur.execute(
        """
        SELECT MAX(CAST(SUBSTR(numero_expediente, 1, 3) AS INTEGER)) AS ultima_secuencia
        FROM expedientes
        WHERE numero_expediente GLOB ?
        """,
        (f"[0-9][0-9][0-9]-{sufijo_anio}",),
    ).fetchone()

    ultima_secuencia = row["ultima_secuencia"] or 0
    return f"{ultima_secuencia + 1:03d}-{sufijo_anio}"


def columnas_tabla(cur, tabla: str) -> set[str]:
    return {row["name"] for row in cur.execute(f"PRAGMA table_info({tabla})").fetchall()}


def nombre_cliente(cliente) -> str:
    razon_social = limpiar_texto(cliente["razon_social"])
    if razon_social:
        return razon_social
    partes = [
        limpiar_texto(cliente["nombre"]),
        limpiar_texto(cliente["apellidos"]),
    ]
    return " ".join(parte for parte in partes if parte) or "Cliente sin nombre"


def cargar_contexto_formulario(
    cur,
    owner_user_id: int,
    lead_id: int | None = None,
    cliente_id: int | None = None,
):
    leads = cur.execute(
        """
        SELECT id, nombre, email, telefono
        FROM leads
        WHERE owner_user_id = ?
        ORDER BY id DESC
        """,
        (owner_user_id,),
    ).fetchall()
    clientes = cur.execute(
        """
        SELECT id, nombre, apellidos, razon_social
        FROM clientes
        WHERE owner_user_id = ?
        ORDER BY id DESC
        """,
        (owner_user_id,),
    ).fetchall()
    lead = get_owned_lead(cur, lead_id, owner_user_id) if lead_id else None
    cliente = get_owned_cliente(cur, cliente_id, owner_user_id) if cliente_id else None
    return leads, clientes, lead, cliente


@router.get("/propuestas", response_class=HTMLResponse)
def listar_propuestas(request: Request, estado: str = Query("", max_length=30)):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    conn = get_connection()
    cur = conn.cursor()
    try:
        if estado_limpio in PROPUESTA_ESTADOS:
            propuestas = cur.execute(
                """
                SELECT p.*, l.nombre AS lead_nombre, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos
                FROM propuestas p
                LEFT JOIN leads l ON l.id = p.lead_id
                LEFT JOIN clientes c ON c.id = p.cliente_id
                WHERE p.owner_user_id = ? AND p.estado = ?
                ORDER BY p.id DESC
                """,
                (current_user["id"], estado_limpio),
            ).fetchall()
        else:
            propuestas = cur.execute(
                """
                SELECT p.*, l.nombre AS lead_nombre, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos
                FROM propuestas p
                LEFT JOIN leads l ON l.id = p.lead_id
                LEFT JOIN clientes c ON c.id = p.cliente_id
                WHERE p.owner_user_id = ?
                ORDER BY p.id DESC
                """,
                (current_user["id"],),
            ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "propuestas/listado.html",
        {
            "propuestas": propuestas,
            "estados_propuesta": PROPUESTA_ESTADOS,
            "estado_actual": estado_limpio if estado_limpio in PROPUESTA_ESTADOS else "",
            "format_money": format_money,
        },
    )


@router.get("/propuestas/nueva", response_class=HTMLResponse)
def nueva_propuesta(
    request: Request,
    lead_id: int | None = Query(None),
    cliente_id: int | None = Query(None),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        leads, clientes, lead, cliente = cargar_contexto_formulario(
            cur,
            current_user["id"],
            lead_id=lead_id,
            cliente_id=cliente_id,
        )
        if lead and not cliente and lead["cliente_id"]:
            cliente = get_owned_cliente(cur, lead["cliente_id"], current_user["id"])
            cliente_id = cliente["id"] if cliente else None
        propuesta = {
            "numero_propuesta": siguiente_numero_propuesta(cur),
            "lead_id": lead_id or "",
            "cliente_id": cliente_id or "",
            "fecha": str(date.today()),
            "estado": "borrador",
            "tipo_trabajo": lead["servicio_solicitado"] if lead else "",
            "direccion_inmueble": "",
            "alcance": "",
            "plazo_estimado": "",
            "condiciones": "",
        }
    finally:
        conn.close()

    return render_template(
        request,
        "propuestas/form.html",
        {
            "propuesta": propuesta,
            "form_action": "/propuestas/nueva",
            "titulo": "Nueva propuesta",
            "submit_label": "Guardar propuesta",
            "error": "",
            "estados_propuesta": PROPUESTA_ESTADOS,
            "leads": leads,
            "clientes": clientes,
            "lead_relacionado": lead,
            "cliente_relacionado": cliente,
        },
    )


@router.post("/propuestas/nueva")
def crear_propuesta(
    request: Request,
    numero_propuesta: str = Form(...),
    lead_id: str = Form(""),
    cliente_id: str = Form(""),
    fecha: str = Form(...),
    estado: str = Form("borrador"),
    tipo_trabajo: str = Form(""),
    direccion_inmueble: str = Form(""),
    alcance: str = Form(""),
    plazo_estimado: str = Form(""),
    condiciones: str = Form(""),
):
    current_user = get_current_user(request)
    lead_id_int = parse_optional_int(lead_id)
    cliente_id_int = parse_optional_int(cliente_id)
    propuesta = {
        "numero_propuesta": limpiar_texto(numero_propuesta),
        "lead_id": lead_id_int or "",
        "cliente_id": cliente_id_int or "",
        "fecha": limpiar_texto(fecha),
        "estado": limpiar_texto(estado) or "borrador",
        "tipo_trabajo": limpiar_texto(tipo_trabajo),
        "direccion_inmueble": limpiar_texto(direccion_inmueble),
        "alcance": limpiar_texto(alcance),
        "plazo_estimado": limpiar_texto(plazo_estimado),
        "condiciones": limpiar_texto(condiciones),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        leads, clientes, lead, cliente = cargar_contexto_formulario(
            cur,
            current_user["id"],
            lead_id=lead_id_int,
            cliente_id=cliente_id_int,
        )

        error = ""
        if not propuesta["numero_propuesta"]:
            error = "El número de propuesta es obligatorio."
        elif not propuesta["fecha"]:
            error = "La fecha es obligatoria."
        elif propuesta["estado"] not in PROPUESTA_ESTADOS:
            error = "El estado indicado no es válido."
        elif lead_id_int and lead is None:
            error = "El lead indicado no existe."
        elif cliente_id_int and cliente is None:
            error = "El cliente indicado no existe."

        if error:
            return render_template(
                request,
                "propuestas/form.html",
                {
                    "propuesta": propuesta,
                    "form_action": "/propuestas/nueva",
                    "titulo": "Nueva propuesta",
                    "submit_label": "Guardar propuesta",
                    "error": error,
                    "estados_propuesta": PROPUESTA_ESTADOS,
                    "leads": leads,
                    "clientes": clientes,
                    "lead_relacionado": lead,
                    "cliente_relacionado": cliente,
                },
            )

        cur.execute(
            """
            INSERT INTO propuestas (
                numero_propuesta, lead_id, cliente_id, fecha, estado, tipo_trabajo,
                direccion_inmueble, alcance, plazo_estimado, condiciones, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta["numero_propuesta"],
                lead_id_int,
                cliente_id_int,
                propuesta["fecha"],
                propuesta["estado"],
                propuesta["tipo_trabajo"],
                propuesta["direccion_inmueble"],
                propuesta["alcance"],
                propuesta["plazo_estimado"],
                propuesta["condiciones"],
                current_user["id"],
            ),
        )
        propuesta_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.get("/propuestas/{propuesta_id}", response_class=HTMLResponse)
def detalle_propuesta(
    request: Request,
    propuesta_id: int,
    print: int = Query(0),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        lineas = obtener_lineas_propuesta(cur, propuesta_id)
    finally:
        conn.close()

    return render_template(
        request,
        "propuestas/detalle.html",
        {
            "propuesta": propuesta,
            "lineas": lineas,
            "estados_propuesta": PROPUESTA_ESTADOS,
            "format_money": format_money,
            "print_mode": bool(print),
        },
    )


@router.get("/propuestas/{propuesta_id}/editar", response_class=HTMLResponse)
def editar_propuesta(request: Request, propuesta_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        leads, clientes, lead, cliente = cargar_contexto_formulario(
            cur,
            current_user["id"],
            lead_id=propuesta["lead_id"],
            cliente_id=propuesta["cliente_id"],
        )
    finally:
        conn.close()

    return render_template(
        request,
        "propuestas/form.html",
        {
            "propuesta": dict(propuesta),
            "form_action": f"/propuestas/{propuesta_id}/editar",
            "titulo": "Editar propuesta",
            "submit_label": "Guardar cambios",
            "error": "",
            "estados_propuesta": PROPUESTA_ESTADOS,
            "leads": leads,
            "clientes": clientes,
            "lead_relacionado": lead,
            "cliente_relacionado": cliente,
        },
    )


@router.post("/propuestas/{propuesta_id}/editar")
def actualizar_propuesta(
    request: Request,
    propuesta_id: int,
    numero_propuesta: str = Form(...),
    lead_id: str = Form(""),
    cliente_id: str = Form(""),
    fecha: str = Form(...),
    tipo_trabajo: str = Form(""),
    direccion_inmueble: str = Form(""),
    alcance: str = Form(""),
    plazo_estimado: str = Form(""),
    condiciones: str = Form(""),
):
    current_user = get_current_user(request)
    lead_id_int = parse_optional_int(lead_id)
    cliente_id_int = parse_optional_int(cliente_id)
    propuesta = {
        "id": propuesta_id,
        "numero_propuesta": limpiar_texto(numero_propuesta),
        "lead_id": lead_id_int or "",
        "cliente_id": cliente_id_int or "",
        "fecha": limpiar_texto(fecha),
        "tipo_trabajo": limpiar_texto(tipo_trabajo),
        "direccion_inmueble": limpiar_texto(direccion_inmueble),
        "alcance": limpiar_texto(alcance),
        "plazo_estimado": limpiar_texto(plazo_estimado),
        "condiciones": limpiar_texto(condiciones),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta_existente = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta_existente:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        leads, clientes, lead, cliente = cargar_contexto_formulario(
            cur,
            current_user["id"],
            lead_id=lead_id_int,
            cliente_id=cliente_id_int,
        )

        error = ""
        if not propuesta["numero_propuesta"]:
            error = "El número de propuesta es obligatorio."
        elif not propuesta["fecha"]:
            error = "La fecha es obligatoria."
        elif lead_id_int and lead is None:
            error = "El lead indicado no existe."
        elif cliente_id_int and cliente is None:
            error = "El cliente indicado no existe."

        if error:
            propuesta["estado"] = propuesta_existente["estado"]
            return render_template(
                request,
                "propuestas/form.html",
                {
                    "propuesta": propuesta,
                    "form_action": f"/propuestas/{propuesta_id}/editar",
                    "titulo": "Editar propuesta",
                    "submit_label": "Guardar cambios",
                    "error": error,
                    "estados_propuesta": PROPUESTA_ESTADOS,
                    "leads": leads,
                    "clientes": clientes,
                    "lead_relacionado": lead,
                    "cliente_relacionado": cliente,
                },
            )

        cur.execute(
            """
            UPDATE propuestas
            SET numero_propuesta = ?, lead_id = ?, cliente_id = ?, fecha = ?,
                tipo_trabajo = ?, direccion_inmueble = ?, alcance = ?,
                plazo_estimado = ?, condiciones = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                propuesta["numero_propuesta"],
                lead_id_int,
                cliente_id_int,
                propuesta["fecha"],
                propuesta["tipo_trabajo"],
                propuesta["direccion_inmueble"],
                propuesta["alcance"],
                propuesta["plazo_estimado"],
                propuesta["condiciones"],
                propuesta_id,
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/lineas")
def crear_linea_propuesta(
    request: Request,
    propuesta_id: int,
    concepto: str = Form(...),
    descripcion: str = Form(""),
    cantidad: str = Form("1"),
    precio_unitario: str = Form("0"),
    iva_porcentaje: str = Form("21"),
):
    current_user = get_current_user(request)
    concepto_limpio = limpiar_texto(concepto)
    if not concepto_limpio:
        return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)

    cantidad_valor = parse_float(cantidad, default=1.0)
    precio_unitario_valor = parse_float(precio_unitario, default=0.0)
    iva_porcentaje_valor = parse_float(iva_porcentaje, default=21.0)
    base_linea = cantidad_valor * precio_unitario_valor
    total_linea = base_linea + (base_linea * iva_porcentaje_valor / 100)

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        siguiente_orden = cur.execute(
            """
            SELECT COALESCE(MAX(orden), 0) + 1
            FROM propuesta_lineas
            WHERE propuesta_id = ?
            """,
            (propuesta_id,),
        ).fetchone()[0]

        cur.execute(
            """
            INSERT INTO propuesta_lineas (
                propuesta_id, concepto, descripcion, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                concepto_limpio,
                limpiar_texto(descripcion),
                cantidad_valor,
                precio_unitario_valor,
                iva_porcentaje_valor,
                total_linea,
                siguiente_orden,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/estado")
def actualizar_estado_propuesta(
    request: Request,
    propuesta_id: int,
    estado: str = Form(...),
):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    if estado_limpio not in PROPUESTA_ESTADOS:
        return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        fecha_envio = propuesta["fecha_envio"]
        fecha_aceptacion = propuesta["fecha_aceptacion"]
        if estado_limpio == "enviada" and not fecha_envio:
            fecha_envio = str(date.today())
        if estado_limpio == "aceptada" and not fecha_aceptacion:
            fecha_aceptacion = str(date.today())

        cur.execute(
            """
            UPDATE propuestas
            SET estado = ?, fecha_envio = ?, fecha_aceptacion = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (estado_limpio, fecha_envio, fecha_aceptacion, propuesta_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/crear-expediente")
def crear_expediente_desde_propuesta(request: Request, propuesta_id: int):
    current_user = get_current_user(request)
    expediente_id = None

    for _ in range(3):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
            if not propuesta:
                raise HTTPException(status_code=404, detail="Propuesta no encontrada")
            if propuesta["expediente_id"]:
                expediente_id = propuesta["expediente_id"]
                conn.rollback()
                break
            if propuesta["estado"] != "aceptada":
                raise HTTPException(
                    status_code=400,
                    detail="Solo se puede crear expediente desde una propuesta aceptada.",
                )

            cliente = None
            if propuesta["cliente_id"]:
                cliente = get_owned_cliente(
                    cur, propuesta["cliente_id"], current_user["id"]
                )
                if not cliente:
                    raise HTTPException(status_code=400, detail="Cliente no válido.")
            elif propuesta["lead_id"]:
                lead = get_owned_lead(cur, propuesta["lead_id"], current_user["id"])
                if not lead:
                    raise HTTPException(status_code=400, detail="Lead no válido.")

                cur.execute(
                    """
                    INSERT INTO clientes (
                        nombre, email, telefono, origen, owner_user_id
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        limpiar_texto(lead["nombre"]) or "Cliente sin nombre",
                        limpiar_texto(lead["email"]),
                        limpiar_texto(lead["telefono"]),
                        "lead",
                        current_user["id"],
                    ),
                )
                cliente_id = cur.lastrowid
                cur.execute(
                    """
                    UPDATE propuestas
                    SET cliente_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND owner_user_id = ?
                    """,
                    (cliente_id, propuesta_id, current_user["id"]),
                )

                if "cliente_id" in columnas_tabla(cur, "leads"):
                    cur.execute(
                        """
                        UPDATE leads
                        SET cliente_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND owner_user_id = ?
                        """,
                        (cliente_id, propuesta["lead_id"], current_user["id"]),
                    )

                cliente = get_owned_cliente(cur, cliente_id, current_user["id"])
            else:
                raise HTTPException(
                    status_code=400,
                    detail="La propuesta no tiene cliente ni lead asociado.",
                )

            numero_expediente = siguiente_numero_expediente(cur)
            existe = cur.execute(
                "SELECT id FROM expedientes WHERE numero_expediente = ?",
                (numero_expediente,),
            ).fetchone()
            if existe:
                conn.rollback()
                continue

            cur.execute(
                """
                INSERT INTO expedientes (
                    numero_expediente,
                    cliente,
                    direccion,
                    tipo_informe,
                    objeto_pericia,
                    owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    numero_expediente,
                    nombre_cliente(cliente),
                    limpiar_texto(propuesta["direccion_inmueble"]) or "Pendiente",
                    limpiar_texto(propuesta["tipo_trabajo"]),
                    limpiar_texto(propuesta["alcance"]),
                    current_user["id"],
                ),
            )
            expediente_id = cur.lastrowid
            cur.execute(
                """
                UPDATE propuestas
                SET expediente_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ?
                """,
                (expediente_id, propuesta_id, current_user["id"]),
            )
            conn.commit()
            break
        except HTTPException:
            conn.rollback()
            raise
        finally:
            conn.close()

    if expediente_id is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar un número de expediente único.",
        )

    return RedirectResponse(url=f"/detalle-expediente/{expediente_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/generar-pdf")
def generar_pdf_propuesta(request: Request, propuesta_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        pdf_path = f"/propuestas/{propuesta_id}?print=1"
        cur.execute(
            """
            UPDATE propuestas
            SET pdf_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (pdf_path, propuesta_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}?print=1", status_code=303)
