from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection

router = APIRouter()

LEAD_ESTADOS = (
    "nuevo",
    "pendiente",
    "contactado",
    "email_enviado",
    "respondio",
    "reunion",
    "colaborador",
    "pendiente_respuesta",
    "propuesta_enviada",
    "aceptado",
    "rechazado",
    "descartado",
    "cerrado",
)
LEAD_TIPOS_PROSPECCION = (
    ("administrador_fincas", "Administrador de fincas"),
    ("abogado", "Abogado"),
    ("arquitecto", "Arquitecto"),
    ("inmobiliaria", "Inmobiliaria"),
    ("aseguradora", "Aseguradora"),
    ("empresa", "Empresa"),
    ("otro", "Otro"),
)
LEAD_TIPOS_PROSPECCION_VALUES = tuple(value for value, _label in LEAD_TIPOS_PROSPECCION)
LEAD_FECHA_OPTIONS = (
    ("", "Cualquier fecha"),
    ("hoy", "Hoy"),
    ("7", "Últimos 7 días"),
    ("30", "Últimos 30 días"),
)
LEADS_LIST_LIMIT = 100
WORKBENCH_LIMIT = 50
CONTACTO_TIPOS = ("llamada", "email", "whatsapp", "reunion", "nota")
TAREA_ESTADOS = ("pendiente", "hecha", "cancelada")


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


def limpiar_email(valor: str | None) -> str:
    return limpiar_texto(valor).lower()


def limpiar_telefono(valor: str | None) -> str:
    return "".join(char for char in limpiar_texto(valor) if char.isdigit() or char == "+")


def label_estado(valor: str | None) -> str:
    texto = limpiar_texto(valor).replace("_", " ")
    return texto.capitalize() if texto else "Sin estado"


def label_tipo_prospeccion(valor: str | None) -> str:
    tipo = limpiar_texto(valor)
    labels = dict(LEAD_TIPOS_PROSPECCION)
    return labels.get(tipo, tipo.replace("_", " ").capitalize() if tipo else "Sin tipo")


def lead_estado_badge_class(valor: str | None) -> str:
    estado = limpiar_texto(valor)
    if estado in {"nuevo", "pendiente", "contactado", "email_enviado", "pendiente_respuesta"}:
        return "estado-badge estado-pendiente"
    if estado in {"respondio", "reunion", "colaborador", "aceptado"}:
        return "estado-badge estado-enviada"
    if estado in {"rechazado", "descartado", "cerrado"}:
        return "estado-badge estado-rechazada"
    return "estado-badge estado-borrador"


def tipo_desde_request(valor: str | None) -> str:
    tipo = limpiar_texto(valor)
    return tipo if tipo in LEAD_TIPOS_PROSPECCION_VALUES else ""


def fecha_desde_request(valor: str | None) -> str:
    fecha = limpiar_texto(valor)
    return fecha if fecha in {key for key, _label in LEAD_FECHA_OPTIONS} else ""


def append_fecha_condition(condiciones: list[str], fecha: str) -> None:
    fecha_expr = "COALESCE(l.updated_at, l.created_at)"
    if fecha == "hoy":
        condiciones.append(f"DATE({fecha_expr}) = DATE('now')")
    elif fecha == "7":
        condiciones.append(f"DATE({fecha_expr}) >= DATE('now', '-7 days')")
    elif fecha == "30":
        condiciones.append(f"DATE({fecha_expr}) >= DATE('now', '-30 days')")


def normalizar_url(valor: str | None) -> str:
    url = limpiar_texto(valor)
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return f"https://{url}"


def extraer_web_desde_notas(notas: str | None) -> str:
    for linea in (notas or "").splitlines():
        texto = linea.strip()
        if texto.lower().startswith("web:"):
            return normalizar_url(texto.split(":", 1)[1])
    return ""


def validar_lead_payload(lead: dict) -> str:
    if not limpiar_texto(lead.get("nombre")):
        return "El nombre es obligatorio."
    if limpiar_texto(lead.get("estado")) not in LEAD_ESTADOS:
        return "El estado indicado no es válido."
    return ""


def insertar_lead(cur, lead: dict, owner_user_id: int) -> int:
    cur.execute(
        """
        INSERT INTO leads (
            nombre, email, telefono, origen, servicio_solicitado, mensaje,
            estado, prioridad, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead["nombre"],
            lead["email"],
            lead["telefono"],
            lead["origen"],
            lead["servicio_solicitado"],
            lead["mensaje"],
            lead["estado"],
            lead["prioridad"],
            lead["notas"],
            owner_user_id,
        ),
    )
    return cur.lastrowid


def detectar_duplicados_lead(cur, owner_user_id: int, lead: dict) -> list[dict]:
    condiciones = []
    parametros = [owner_user_id]
    email = limpiar_email(lead.get("email"))
    telefono = limpiar_telefono(lead.get("telefono"))
    nombre = limpiar_texto(lead.get("nombre")).lower()
    if email:
        condiciones.append("lower(COALESCE(email, '')) = ?")
        parametros.append(email)
    if telefono:
        condiciones.append(
            "REPLACE(REPLACE(REPLACE(COALESCE(telefono, ''), ' ', ''), '-', ''), '.', '') = ?"
        )
        parametros.append(telefono)
    if nombre:
        condiciones.append("lower(COALESCE(nombre, '')) = ?")
        parametros.append(nombre)
    if not condiciones:
        return []
    rows = cur.execute(
        f"""
        SELECT id, nombre, email, telefono, origen, estado, created_at
        FROM leads
        WHERE owner_user_id = ?
          AND ({" OR ".join(condiciones)})
        ORDER BY id DESC
        LIMIT 8
        """,
        tuple(parametros),
    ).fetchall()
    return [dict(row) for row in rows]


def construir_lead_desde_workbench(
    empresa: str,
    contacto: str,
    email: str,
    telefono: str,
    localidad: str,
    tipo: str,
    web: str,
    observaciones: str,
) -> dict:
    empresa_limpia = limpiar_texto(empresa)
    contacto_limpio = limpiar_texto(contacto)
    localidad_limpia = limpiar_texto(localidad)
    tipo_limpio = tipo_desde_request(tipo) or "administrador_fincas"
    web_limpia = normalizar_url(web)
    mensaje_partes = [
        f"Contacto: {contacto_limpio}" if contacto_limpio else "",
        f"Localidad: {localidad_limpia}" if localidad_limpia else "",
    ]
    notas_partes = [
        "Origen: Workbench de prospeccion",
        f"Localidad: {localidad_limpia}" if localidad_limpia else "",
        f"Web: {web_limpia}" if web_limpia else "",
        limpiar_texto(observaciones),
    ]
    return {
        "nombre": empresa_limpia or contacto_limpio,
        "email": limpiar_email(email),
        "telefono": limpiar_telefono(telefono),
        "origen": tipo_limpio,
        "servicio_solicitado": "Prospeccion",
        "mensaje": "\n".join(parte for parte in mensaje_partes if parte),
        "estado": "pendiente",
        "prioridad": "prospeccion",
        "notas": "\n".join(parte for parte in notas_partes if parte),
        "empresa": empresa_limpia,
        "contacto": contacto_limpio,
        "localidad": localidad_limpia,
        "web": web_limpia,
        "observaciones": limpiar_texto(observaciones),
    }


def get_owned_lead(cur, lead_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT l.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos
        FROM leads l
        LEFT JOIN clientes c ON c.id = l.cliente_id
        WHERE l.id = ? AND l.owner_user_id = ?
        """,
        (lead_id, owner_user_id),
    ).fetchone()


def get_owned_tarea(cur, tarea_id: int, lead_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM lead_tareas
        WHERE id = ? AND lead_id = ? AND owner_user_id = ?
        """,
        (tarea_id, lead_id, owner_user_id),
    ).fetchone()


def buscar_cliente_similar(cur, lead, owner_user_id: int):
    email = limpiar_texto(lead["email"])
    telefono = limpiar_texto(lead["telefono"])
    if email:
        cliente = cur.execute(
            """
            SELECT *
            FROM clientes
            WHERE owner_user_id = ? AND lower(email) = lower(?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (owner_user_id, email),
        ).fetchone()
        if cliente:
            return cliente
    if telefono:
        return cur.execute(
            """
            SELECT *
            FROM clientes
            WHERE owner_user_id = ? AND telefono = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (owner_user_id, telefono),
        ).fetchone()
    return None


@router.get("/leads", response_class=HTMLResponse)
def listar_leads(
    request: Request,
    tipo: str = Query("", max_length=60),
    estado: str = Query("", max_length=40),
    localidad: str = Query("", max_length=80),
    fecha: str = Query("", max_length=20),
):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    tipo_limpio = tipo_desde_request(tipo)
    localidad_limpia = limpiar_texto(localidad)
    fecha_limpia = fecha_desde_request(fecha)

    condiciones = ["l.owner_user_id = ?"]
    parametros: list = [current_user["id"]]
    if tipo_limpio:
        condiciones.append("l.origen = ?")
        parametros.append(tipo_limpio)
    if estado_limpio and estado_limpio in LEAD_ESTADOS:
        condiciones.append("l.estado = ?")
        parametros.append(estado_limpio)
    else:
        estado_limpio = ""
    if localidad_limpia:
        like = f"%{localidad_limpia.lower()}%"
        condiciones.append(
            """
            (
                lower(COALESCE(l.mensaje, '')) LIKE ?
                OR lower(COALESCE(l.notas, '')) LIKE ?
                OR lower(COALESCE(l.servicio_solicitado, '')) LIKE ?
                OR lower(COALESCE(c.direccion, '')) LIKE ?
                OR lower(COALESCE(c.ciudad, '')) LIKE ?
                OR lower(COALESCE(c.provincia, '')) LIKE ?
            )
            """
        )
        parametros.extend([like] * 6)
    append_fecha_condition(condiciones, fecha_limpia)

    where_sql = " AND ".join(condiciones)
    conn = get_connection()
    cur = conn.cursor()
    try:
        leads = cur.execute(
            f"""
            SELECT l.*, c.ciudad AS cliente_ciudad, c.provincia AS cliente_provincia
            FROM leads l
            LEFT JOIN clientes c
              ON c.id = l.cliente_id AND c.owner_user_id = l.owner_user_id
            WHERE {where_sql}
            ORDER BY COALESCE(l.updated_at, l.created_at) DESC, l.id DESC
            LIMIT ?
            """,
            tuple(parametros + [LEADS_LIST_LIMIT]),
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "leads/listado.html",
        {
            "leads": leads,
            "filters": {
                "tipo": tipo_limpio,
                "estado": estado_limpio,
                "localidad": localidad_limpia,
                "fecha": fecha_limpia,
            },
            "estados_lead": LEAD_ESTADOS,
            "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
            "tipos_prospeccion_values": LEAD_TIPOS_PROSPECCION_VALUES,
            "fecha_options": LEAD_FECHA_OPTIONS,
            "label_estado": label_estado,
            "label_tipo_prospeccion": label_tipo_prospeccion,
            "lead_estado_badge_class": lead_estado_badge_class,
            "leads_list_limit": LEADS_LIST_LIMIT,
        },
    )


@router.get("/leads/nuevo", response_class=HTMLResponse)
def nuevo_lead(request: Request):
    get_current_user(request)
    return render_template(
        request,
        "leads/form.html",
        {
            "lead": {},
            "form_action": "/leads/nuevo",
            "titulo": "Nuevo lead",
            "submit_label": "Guardar lead",
            "error": "",
            "estados_lead": LEAD_ESTADOS,
            "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
            "tipos_prospeccion_values": LEAD_TIPOS_PROSPECCION_VALUES,
        },
    )


@router.post("/leads/nuevo")
def crear_lead(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(""),
    telefono: str = Form(""),
    origen: str = Form(""),
    servicio_solicitado: str = Form(""),
    mensaje: str = Form(""),
    estado: str = Form("nuevo"),
    prioridad: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    nombre_limpio = limpiar_texto(nombre)
    estado_limpio = limpiar_texto(estado) or "nuevo"

    lead = {
        "nombre": nombre_limpio,
        "email": limpiar_texto(email),
        "telefono": limpiar_texto(telefono),
        "origen": limpiar_texto(origen),
        "servicio_solicitado": limpiar_texto(servicio_solicitado),
        "mensaje": limpiar_texto(mensaje),
        "estado": estado_limpio,
        "prioridad": limpiar_texto(prioridad),
        "notas": limpiar_texto(notas),
    }

    error = validar_lead_payload(lead)

    if error:
        return render_template(
            request,
            "leads/form.html",
            {
                "lead": lead,
                "form_action": "/leads/nuevo",
                "titulo": "Nuevo lead",
                "submit_label": "Guardar lead",
                "error": error,
                "estados_lead": LEAD_ESTADOS,
                "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
                "tipos_prospeccion_values": LEAD_TIPOS_PROSPECCION_VALUES,
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead_id = insertar_lead(cur, lead, current_user["id"])
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


def cargar_workbench_leads(
    cur,
    owner_user_id: int,
    tipo: str,
    localidad: str,
    vista: str,
) -> list[dict]:
    condiciones = ["l.owner_user_id = ?"]
    parametros: list = [owner_user_id]
    tipo_limpio = tipo_desde_request(tipo)
    localidad_limpia = limpiar_texto(localidad)
    if tipo_limpio:
        condiciones.append("l.origen = ?")
        parametros.append(tipo_limpio)
    if localidad_limpia:
        like = f"%{localidad_limpia.lower()}%"
        condiciones.append(
            """
            (
                lower(COALESCE(l.mensaje, '')) LIKE ?
                OR lower(COALESCE(l.notas, '')) LIKE ?
                OR lower(COALESCE(c.ciudad, '')) LIKE ?
                OR lower(COALESCE(c.provincia, '')) LIKE ?
            )
            """
        )
        parametros.extend([like] * 4)
    if vista == "pendientes":
        condiciones.append("l.estado IN ('nuevo', 'pendiente', 'contactado', 'email_enviado')")
    elif vista == "convertidos":
        condiciones.append("l.estado IN ('colaborador', 'aceptado')")
    elif vista in LEAD_ESTADOS:
        condiciones.append("l.estado = ?")
        parametros.append(vista)

    rows = cur.execute(
        f"""
        SELECT l.*, c.ciudad AS cliente_ciudad, c.provincia AS cliente_provincia
        FROM leads l
        LEFT JOIN clientes c
          ON c.id = l.cliente_id AND c.owner_user_id = l.owner_user_id
        WHERE {" AND ".join(condiciones)}
        ORDER BY COALESCE(l.updated_at, l.created_at) DESC, l.id DESC
        LIMIT ?
        """,
        tuple(parametros + [WORKBENCH_LIMIT]),
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["web"] = extraer_web_desde_notas(item.get("notas"))
        items.append(item)
    return items


@router.get("/leads/prospeccion", response_class=HTMLResponse)
def workbench_prospeccion(
    request: Request,
    tipo: str = Query("administrador_fincas", max_length=60),
    localidad: str = Query("", max_length=80),
    vista: str = Query("pendientes", max_length=40),
    creado: int = Query(0),
):
    current_user = get_current_user(request)
    tipo_limpio = tipo_desde_request(tipo) or "administrador_fincas"
    localidad_limpia = limpiar_texto(localidad)
    vista_limpia = limpiar_texto(vista) or "pendientes"
    if vista_limpia not in {"todos", "pendientes", "convertidos"} and vista_limpia not in LEAD_ESTADOS:
        vista_limpia = "pendientes"
    conn = get_connection()
    cur = conn.cursor()
    try:
        recientes = cargar_workbench_leads(
            cur, current_user["id"], tipo_limpio, localidad_limpia, vista_limpia
        )
    finally:
        conn.close()
    return render_template(
        request,
        "leads/workbench_prospeccion.html",
        {
            "lead": {
                "origen": tipo_limpio,
                "localidad": localidad_limpia,
            },
            "error": "",
            "duplicados": [],
            "creado": creado,
            "recientes": recientes,
            "filters": {
                "tipo": tipo_limpio,
                "localidad": localidad_limpia,
                "vista": vista_limpia,
            },
            "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
            "estados_lead": LEAD_ESTADOS,
            "label_estado": label_estado,
            "label_tipo_prospeccion": label_tipo_prospeccion,
            "lead_estado_badge_class": lead_estado_badge_class,
            "workbench_limit": WORKBENCH_LIMIT,
        },
    )


@router.post("/leads/prospeccion", response_class=HTMLResponse)
def crear_desde_workbench_prospeccion(
    request: Request,
    empresa: str = Form(""),
    contacto: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    localidad: str = Form(""),
    tipo: str = Form("administrador_fincas"),
    web: str = Form(""),
    observaciones: str = Form(""),
    confirmar_duplicado: str = Form(""),
):
    current_user = get_current_user(request)
    lead = construir_lead_desde_workbench(
        empresa, contacto, email, telefono, localidad, tipo, web, observaciones
    )
    error = validar_lead_payload(lead)
    tipo_limpio = tipo_desde_request(lead["origen"]) or "administrador_fincas"
    localidad_limpia = limpiar_texto(localidad)
    conn = get_connection()
    cur = conn.cursor()
    try:
        duplicados = detectar_duplicados_lead(cur, current_user["id"], lead)
        if error or (duplicados and confirmar_duplicado != "1"):
            recientes = cargar_workbench_leads(
                cur, current_user["id"], tipo_limpio, localidad_limpia, "pendientes"
            )
            return render_template(
                request,
                "leads/workbench_prospeccion.html",
                {
                    "lead": lead,
                    "error": error,
                    "duplicados": duplicados,
                    "creado": 0,
                    "recientes": recientes,
                    "filters": {
                        "tipo": tipo_limpio,
                        "localidad": localidad_limpia,
                        "vista": "pendientes",
                    },
                    "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
                    "estados_lead": LEAD_ESTADOS,
                    "label_estado": label_estado,
                    "label_tipo_prospeccion": label_tipo_prospeccion,
                    "lead_estado_badge_class": lead_estado_badge_class,
                    "workbench_limit": WORKBENCH_LIMIT,
                },
            )
        lead_id = insertar_lead(cur, lead, current_user["id"])
        conn.commit()
    finally:
        conn.close()
    query = urlencode({"tipo": tipo_limpio, "localidad": localidad_limpia, "creado": lead_id})
    return RedirectResponse(url=f"/leads/prospeccion?{query}", status_code=303)


@router.post("/leads/prospeccion/{lead_id}/revisado")
def marcar_lead_revisado_desde_workbench(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        cur.execute(
            """
            UPDATE leads
            SET estado = 'contactado', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (lead_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/leads/prospeccion", status_code=303)


@router.post("/leads/{lead_id}/convertir-cliente")
def convertir_lead_en_cliente(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        cliente_id = lead["cliente_id"]
        if cliente_id:
            cliente = cur.execute(
                """
                SELECT id
                FROM clientes
                WHERE id = ? AND owner_user_id = ?
                """,
                (cliente_id, current_user["id"]),
            ).fetchone()
            if cliente:
                return RedirectResponse(url=f"/clientes/{cliente_id}", status_code=303)

        cliente = buscar_cliente_similar(cur, lead, current_user["id"])
        if cliente:
            cliente_id = cliente["id"]
        else:
            notas = "\n".join(
                parte
                for parte in (
                    f"Convertido desde lead #{lead_id}.",
                    f"Servicio solicitado: {lead['servicio_solicitado']}" if limpiar_texto(lead["servicio_solicitado"]) else "",
                    f"Mensaje inicial: {lead['mensaje']}" if limpiar_texto(lead["mensaje"]) else "",
                    f"Notas lead: {lead['notas']}" if limpiar_texto(lead["notas"]) else "",
                )
                if parte
            )
            cur.execute(
                """
                INSERT INTO clientes (
                    nombre, email, telefono, origen, notas, owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    limpiar_texto(lead["nombre"]) or "Cliente sin nombre",
                    limpiar_texto(lead["email"]),
                    limpiar_texto(lead["telefono"]),
                    limpiar_texto(lead["origen"]) or "lead",
                    notas,
                    current_user["id"],
                ),
            )
            cliente_id = cur.lastrowid

        cur.execute(
            """
            UPDATE leads
            SET cliente_id = ?, estado = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (cliente_id, "aceptado", lead_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/clientes/{cliente_id}", status_code=303)


@router.get("/leads/{lead_id}", response_class=HTMLResponse)
def detalle_lead(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        contactos = cur.execute(
            """
            SELECT *
            FROM lead_contactos
            WHERE lead_id = ? AND owner_user_id = ?
            ORDER BY fecha DESC, id DESC
            """,
            (lead_id, current_user["id"]),
        ).fetchall()
        tareas = cur.execute(
            """
            SELECT *
            FROM lead_tareas
            WHERE lead_id = ? AND owner_user_id = ?
            ORDER BY
                CASE estado
                    WHEN 'pendiente' THEN 0
                    WHEN 'hecha' THEN 1
                    ELSE 2
                END,
                COALESCE(fecha_programada, '') ASC,
                id DESC
            """,
            (lead_id, current_user["id"]),
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "leads/detalle.html",
        {
            "lead": lead,
            "contactos": contactos,
            "tareas": tareas,
            "estados_lead": LEAD_ESTADOS,
            "tipos_contacto": CONTACTO_TIPOS,
            "label_estado": label_estado,
            "label_tipo_prospeccion": label_tipo_prospeccion,
            "lead_estado_badge_class": lead_estado_badge_class,
        },
    )


@router.get("/leads/{lead_id}/editar", response_class=HTMLResponse)
def editar_lead(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
    finally:
        conn.close()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    return render_template(
        request,
        "leads/form.html",
        {
            "lead": dict(lead),
            "form_action": f"/leads/{lead_id}/editar",
            "titulo": "Editar lead",
            "submit_label": "Guardar cambios",
            "error": "",
            "estados_lead": LEAD_ESTADOS,
            "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
            "tipos_prospeccion_values": LEAD_TIPOS_PROSPECCION_VALUES,
        },
    )


@router.post("/leads/{lead_id}/editar")
def actualizar_lead(
    request: Request,
    lead_id: int,
    nombre: str = Form(...),
    email: str = Form(""),
    telefono: str = Form(""),
    origen: str = Form(""),
    servicio_solicitado: str = Form(""),
    mensaje: str = Form(""),
    estado: str = Form("nuevo"),
    prioridad: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    nombre_limpio = limpiar_texto(nombre)
    estado_limpio = limpiar_texto(estado) or "nuevo"
    lead = {
        "id": lead_id,
        "nombre": nombre_limpio,
        "email": limpiar_texto(email),
        "telefono": limpiar_texto(telefono),
        "origen": limpiar_texto(origen),
        "servicio_solicitado": limpiar_texto(servicio_solicitado),
        "mensaje": limpiar_texto(mensaje),
        "estado": estado_limpio,
        "prioridad": limpiar_texto(prioridad),
        "notas": limpiar_texto(notas),
    }

    error = ""
    if not nombre_limpio:
        error = "El nombre es obligatorio."
    elif estado_limpio not in LEAD_ESTADOS:
        error = "El estado indicado no es válido."

    if error:
        return render_template(
            request,
            "leads/form.html",
            {
                "lead": lead,
                "form_action": f"/leads/{lead_id}/editar",
                "titulo": "Editar lead",
                "submit_label": "Guardar cambios",
                "error": error,
                "estados_lead": LEAD_ESTADOS,
                "tipos_prospeccion": LEAD_TIPOS_PROSPECCION,
                "tipos_prospeccion_values": LEAD_TIPOS_PROSPECCION_VALUES,
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead_existente = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead_existente:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        cur.execute(
            """
            UPDATE leads
            SET nombre = ?, email = ?, telefono = ?, origen = ?, servicio_solicitado = ?,
                mensaje = ?, estado = ?, prioridad = ?, notas = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                lead["nombre"],
                lead["email"],
                lead["telefono"],
                lead["origen"],
                lead["servicio_solicitado"],
                lead["mensaje"],
                lead["estado"],
                lead["prioridad"],
                lead["notas"],
                lead_id,
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@router.post("/leads/{lead_id}/contactos")
def crear_contacto_lead(
    request: Request,
    lead_id: int,
    fecha: str = Form(...),
    tipo: str = Form(...),
    resumen: str = Form(""),
    resultado: str = Form(""),
    siguiente_accion: str = Form(""),
):
    current_user = get_current_user(request)
    fecha_limpia = limpiar_texto(fecha)
    tipo_limpio = limpiar_texto(tipo)

    if not fecha_limpia or tipo_limpio not in CONTACTO_TIPOS:
        return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        cur.execute(
            """
            INSERT INTO lead_contactos (
                lead_id, fecha, tipo, resumen, resultado, siguiente_accion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                fecha_limpia,
                tipo_limpio,
                limpiar_texto(resumen),
                limpiar_texto(resultado),
                limpiar_texto(siguiente_accion),
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@router.post("/leads/{lead_id}/tareas")
def crear_tarea_lead(
    request: Request,
    lead_id: int,
    titulo: str = Form(...),
    tipo: str = Form(""),
    fecha_programada: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    titulo_limpio = limpiar_texto(titulo)
    if not titulo_limpio:
        return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                titulo_limpio,
                limpiar_texto(tipo),
                limpiar_texto(fecha_programada),
                limpiar_texto(notas),
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@router.post("/leads/{lead_id}/tareas/{tarea_id}/hecha")
def marcar_tarea_hecha(request: Request, lead_id: int, tarea_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        tarea = get_owned_tarea(cur, tarea_id, lead_id, current_user["id"])
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        cur.execute(
            """
            UPDATE lead_tareas
            SET estado = 'hecha', completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND lead_id = ? AND owner_user_id = ?
            """,
            (tarea_id, lead_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


@router.post("/leads/{lead_id}/tareas/{tarea_id}/cancelar")
def marcar_tarea_cancelada(request: Request, lead_id: int, tarea_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        tarea = get_owned_tarea(cur, tarea_id, lead_id, current_user["id"])
        if not tarea:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")

        cur.execute(
            """
            UPDATE lead_tareas
            SET estado = 'cancelada', completed_at = NULL
            WHERE id = ? AND lead_id = ? AND owner_user_id = ?
            """,
            (tarea_id, lead_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)
