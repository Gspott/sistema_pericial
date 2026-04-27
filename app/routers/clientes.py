from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection

router = APIRouter()


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


def get_owned_cliente(cur, cliente_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM clientes
        WHERE id = ? AND owner_user_id = ?
        """,
        (cliente_id, owner_user_id),
    ).fetchone()


@router.get("/clientes", response_class=HTMLResponse)
def listar_clientes(request: Request):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        clientes = cur.execute(
            """
            SELECT *
            FROM clientes
            WHERE owner_user_id = ?
            ORDER BY id DESC
            """,
            (current_user["id"],),
        ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "clientes/listado.html",
        {"clientes": clientes},
    )


@router.get("/clientes/nuevo", response_class=HTMLResponse)
def nuevo_cliente(request: Request):
    get_current_user(request)
    return render_template(
        request,
        "clientes/form.html",
        {
            "cliente": {},
            "form_action": "/clientes/nuevo",
            "titulo": "Nuevo cliente",
            "submit_label": "Guardar cliente",
            "error": "",
        },
    )


@router.post("/clientes/nuevo")
def crear_cliente(
    request: Request,
    nombre: str = Form(...),
    apellidos: str = Form(""),
    razon_social: str = Form(""),
    nif_cif: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    direccion: str = Form(""),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
    tipo_cliente: str = Form(""),
    origen: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    nombre_limpio = limpiar_texto(nombre)

    cliente = {
        "nombre": nombre_limpio,
        "apellidos": limpiar_texto(apellidos),
        "razon_social": limpiar_texto(razon_social),
        "nif_cif": limpiar_texto(nif_cif),
        "email": limpiar_texto(email),
        "telefono": limpiar_texto(telefono),
        "direccion": limpiar_texto(direccion),
        "codigo_postal": limpiar_texto(codigo_postal),
        "ciudad": limpiar_texto(ciudad),
        "provincia": limpiar_texto(provincia),
        "tipo_cliente": limpiar_texto(tipo_cliente),
        "origen": limpiar_texto(origen),
        "notas": limpiar_texto(notas),
    }

    if not nombre_limpio:
        return render_template(
            request,
            "clientes/form.html",
            {
                "cliente": cliente,
                "form_action": "/clientes/nuevo",
                "titulo": "Nuevo cliente",
                "submit_label": "Guardar cliente",
                "error": "El nombre es obligatorio.",
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO clientes (
                nombre, apellidos, razon_social, nif_cif, email, telefono,
                direccion, codigo_postal, ciudad, provincia, tipo_cliente,
                origen, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cliente["nombre"],
                cliente["apellidos"],
                cliente["razon_social"],
                cliente["nif_cif"],
                cliente["email"],
                cliente["telefono"],
                cliente["direccion"],
                cliente["codigo_postal"],
                cliente["ciudad"],
                cliente["provincia"],
                cliente["tipo_cliente"],
                cliente["origen"],
                cliente["notas"],
                current_user["id"],
            ),
        )
        cliente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/clientes/{cliente_id}", status_code=303)


@router.get("/clientes/{cliente_id}", response_class=HTMLResponse)
def detalle_cliente(request: Request, cliente_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cliente = get_owned_cliente(cur, cliente_id, current_user["id"])
        facturas = []
        if cliente:
            facturas = cur.execute(
                """
                SELECT id, numero_factura, fecha, estado, total
                FROM facturas_emitidas
                WHERE cliente_id = ? AND owner_user_id = ?
                ORDER BY id DESC
                """,
                (cliente_id, current_user["id"]),
            ).fetchall()
    finally:
        conn.close()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return render_template(
        request,
        "clientes/detalle.html",
        {
            "cliente": cliente,
            "facturas": facturas,
            "format_money": lambda valor: f"{float(valor or 0):.2f}",
        },
    )


@router.get("/clientes/{cliente_id}/editar", response_class=HTMLResponse)
def editar_cliente(request: Request, cliente_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cliente = get_owned_cliente(cur, cliente_id, current_user["id"])
    finally:
        conn.close()

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return render_template(
        request,
        "clientes/form.html",
        {
            "cliente": dict(cliente),
            "form_action": f"/clientes/{cliente_id}/editar",
            "titulo": "Editar cliente",
            "submit_label": "Guardar cambios",
            "error": "",
        },
    )


@router.post("/clientes/{cliente_id}/editar")
def actualizar_cliente(
    request: Request,
    cliente_id: int,
    nombre: str = Form(...),
    apellidos: str = Form(""),
    razon_social: str = Form(""),
    nif_cif: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    direccion: str = Form(""),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
    tipo_cliente: str = Form(""),
    origen: str = Form(""),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    nombre_limpio = limpiar_texto(nombre)
    cliente = {
        "id": cliente_id,
        "nombre": nombre_limpio,
        "apellidos": limpiar_texto(apellidos),
        "razon_social": limpiar_texto(razon_social),
        "nif_cif": limpiar_texto(nif_cif),
        "email": limpiar_texto(email),
        "telefono": limpiar_texto(telefono),
        "direccion": limpiar_texto(direccion),
        "codigo_postal": limpiar_texto(codigo_postal),
        "ciudad": limpiar_texto(ciudad),
        "provincia": limpiar_texto(provincia),
        "tipo_cliente": limpiar_texto(tipo_cliente),
        "origen": limpiar_texto(origen),
        "notas": limpiar_texto(notas),
    }

    if not nombre_limpio:
        return render_template(
            request,
            "clientes/form.html",
            {
                "cliente": cliente,
                "form_action": f"/clientes/{cliente_id}/editar",
                "titulo": "Editar cliente",
                "submit_label": "Guardar cambios",
                "error": "El nombre es obligatorio.",
            },
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        cliente_existente = get_owned_cliente(cur, cliente_id, current_user["id"])
        if not cliente_existente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cur.execute(
            """
            UPDATE clientes
            SET nombre = ?, apellidos = ?, razon_social = ?, nif_cif = ?, email = ?,
                telefono = ?, direccion = ?, codigo_postal = ?, ciudad = ?, provincia = ?,
                tipo_cliente = ?, origen = ?, notas = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (
                cliente["nombre"],
                cliente["apellidos"],
                cliente["razon_social"],
                cliente["nif_cif"],
                cliente["email"],
                cliente["telefono"],
                cliente["direccion"],
                cliente["codigo_postal"],
                cliente["ciudad"],
                cliente["provincia"],
                cliente["tipo_cliente"],
                cliente["origen"],
                cliente["notas"],
                cliente_id,
                current_user["id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/clientes/{cliente_id}", status_code=303)
