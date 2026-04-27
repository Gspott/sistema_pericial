from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection

router = APIRouter()

LEAD_ESTADOS = (
    "nuevo",
    "contactado",
    "pendiente_respuesta",
    "propuesta_enviada",
    "aceptado",
    "rechazado",
    "cerrado",
)
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
    return request.app.state.templates.TemplateResponse(template_name, data)


def limpiar_texto(valor: str | None) -> str:
    return (valor or "").strip()


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


@router.get("/leads", response_class=HTMLResponse)
def listar_leads(request: Request, estado: str = Query("", max_length=40)):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    conn = get_connection()
    cur = conn.cursor()
    try:
        if estado_limpio and estado_limpio in LEAD_ESTADOS:
            leads = cur.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ? AND estado = ?
                ORDER BY id DESC
                """,
                (current_user["id"], estado_limpio),
            ).fetchall()
        else:
            leads = cur.execute(
                """
                SELECT *
                FROM leads
                WHERE owner_user_id = ?
                ORDER BY id DESC
                """,
                (current_user["id"],),
            ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "leads/listado.html",
        {
            "leads": leads,
            "estado_actual": estado_limpio if estado_limpio in LEAD_ESTADOS else "",
            "estados_lead": LEAD_ESTADOS,
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
                "form_action": "/leads/nuevo",
                "titulo": "Nuevo lead",
                "submit_label": "Guardar lead",
                "error": error,
                "estados_lead": LEAD_ESTADOS,
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
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
                current_user["id"],
            ),
        )
        lead_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/leads/{lead_id}", status_code=303)


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
