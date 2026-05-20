import mimetypes
import re
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.database import get_connection
from app.services.email_log import registrar_email_enviado
from app.services.email_sender import crear_mensaje_email, enviar_mensaje_email
from app.services.email_templates import (
    construir_email_html,
    construir_email_texto,
    texto_a_html,
)

router = APIRouter()

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_ADJUNTO_BYTES = 10 * 1024 * 1024
EMAIL_ESTADOS = ("enviado", "error")
MAX_CONTACTOS_SUGERIDOS = 8


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


def es_email_valido(valor: str) -> bool:
    return bool(EMAIL_REGEX.match(valor))


def limpiar_nombre_adjunto(filename: str) -> str:
    nombre = Path(filename).name.strip()
    return nombre or "adjunto"


def preparar_adjunto(adjunto: UploadFile | None) -> dict | None:
    if not adjunto or not adjunto.filename:
        return None

    contenido = adjunto.file.read(MAX_ADJUNTO_BYTES + 1)
    if len(contenido) > MAX_ADJUNTO_BYTES:
        raise ValueError("El adjunto supera el límite de 10 MB.")

    filename = limpiar_nombre_adjunto(adjunto.filename)
    content_type = adjunto.content_type or mimetypes.guess_type(filename)[0]
    if content_type and "/" in content_type:
        maintype, subtype = content_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"

    return {
        "contenido": contenido,
        "maintype": maintype,
        "subtype": subtype,
        "filename": filename,
    }


def _nombre_contacto(*partes: str | None) -> str:
    return " ".join(limpiar_texto(parte) for parte in partes if limpiar_texto(parte))


def _agregar_contacto(contactos: list[dict], vistos: set[str], nombre: str, email: str, origen: str) -> None:
    email_limpio = limpiar_texto(email)
    if not email_limpio or not es_email_valido(email_limpio):
        return
    clave = email_limpio.lower()
    if clave in vistos:
        nombre_limpio = limpiar_texto(nombre)
        for contacto in contactos:
            if contacto["email"].lower() == clave and contacto["nombre"] == contacto["email"] and nombre_limpio:
                contacto["nombre"] = nombre_limpio
                contacto["origen"] = origen
                break
        return
    vistos.add(clave)
    contactos.append(
        {
            "nombre": limpiar_texto(nombre) or email_limpio,
            "email": email_limpio,
            "origen": origen,
        }
    )


@router.get("/emails", response_class=HTMLResponse)
def listar_emails(request: Request, estado: str = Query("", max_length=20)):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    estado_actual = estado_limpio if estado_limpio in EMAIL_ESTADOS else ""

    conn = get_connection()
    cur = conn.cursor()
    try:
        if estado_actual:
            emails = cur.execute(
                """
                SELECT *
                FROM emails_enviados
                WHERE owner_user_id = ? AND estado = ?
                ORDER BY fecha_envio DESC, id DESC
                LIMIT 200
                """,
                (current_user["id"], estado_actual),
            ).fetchall()
        else:
            emails = cur.execute(
                """
                SELECT *
                FROM emails_enviados
                WHERE owner_user_id = ?
                ORDER BY fecha_envio DESC, id DESC
                LIMIT 200
                """,
                (current_user["id"],),
            ).fetchall()
    finally:
        conn.close()

    return render_template(
        request,
        "emails/listado.html",
        {
            "emails": emails,
            "estados_email": EMAIL_ESTADOS,
            "estado_actual": estado_actual,
        },
    )


@router.get("/emails/contactos")
def buscar_contactos_email(request: Request, q: str = Query("", max_length=80)):
    current_user = get_current_user(request)
    termino = limpiar_texto(q)
    if len(termino) < 2:
        return JSONResponse([])

    patron = f"%{termino.lower()}%"
    contactos: list[dict] = []
    vistos: set[str] = set()
    conn = get_connection()
    cur = conn.cursor()
    try:
        for row in cur.execute(
            """
            SELECT destinatario AS email, MAX(fecha_envio) AS ultima_fecha
            FROM emails_enviados
            WHERE owner_user_id = ?
              AND destinatario IS NOT NULL
              AND destinatario <> ''
              AND lower(destinatario) LIKE ?
            GROUP BY lower(destinatario)
            ORDER BY ultima_fecha DESC
            LIMIT 12
            """,
            (current_user["id"], patron),
        ).fetchall():
            _agregar_contacto(contactos, vistos, row["email"], row["email"], "email enviado")

        for row in cur.execute(
            """
            SELECT nombre, apellidos, razon_social, email
            FROM clientes
            WHERE owner_user_id = ?
              AND email IS NOT NULL
              AND email <> ''
              AND (
                lower(email) LIKE ?
                OR lower(nombre) LIKE ?
                OR lower(COALESCE(apellidos, '')) LIKE ?
                OR lower(COALESCE(razon_social, '')) LIKE ?
              )
            ORDER BY id DESC
            LIMIT 12
            """,
            (current_user["id"], patron, patron, patron, patron),
        ).fetchall():
            nombre = limpiar_texto(row["razon_social"]) or _nombre_contacto(row["nombre"], row["apellidos"])
            _agregar_contacto(contactos, vistos, nombre, row["email"], "cliente")

        for row in cur.execute(
            """
            SELECT nombre, email
            FROM leads
            WHERE owner_user_id = ?
              AND email IS NOT NULL
              AND email <> ''
              AND (lower(email) LIKE ? OR lower(nombre) LIKE ?)
            ORDER BY id DESC
            LIMIT 12
            """,
            (current_user["id"], patron, patron),
        ).fetchall():
            _agregar_contacto(contactos, vistos, row["nombre"], row["email"], "lead")

        for row in cur.execute(
            """
            SELECT c.nombre AS cliente_nombre,
                   c.apellidos AS cliente_apellidos,
                   c.razon_social AS cliente_razon_social,
                   c.email AS cliente_email,
                   l.nombre AS lead_nombre,
                   l.email AS lead_email
            FROM propuestas p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN leads l ON l.id = p.lead_id
            WHERE p.owner_user_id = ?
              AND (
                lower(COALESCE(c.email, '')) LIKE ?
                OR lower(COALESCE(l.email, '')) LIKE ?
                OR lower(COALESCE(c.nombre, '')) LIKE ?
                OR lower(COALESCE(c.apellidos, '')) LIKE ?
                OR lower(COALESCE(c.razon_social, '')) LIKE ?
                OR lower(COALESCE(l.nombre, '')) LIKE ?
              )
            ORDER BY p.id DESC
            LIMIT 12
            """,
            (current_user["id"], patron, patron, patron, patron, patron, patron),
        ).fetchall():
            if row["cliente_email"]:
                nombre = limpiar_texto(row["cliente_razon_social"]) or _nombre_contacto(
                    row["cliente_nombre"], row["cliente_apellidos"]
                )
                _agregar_contacto(contactos, vistos, nombre, row["cliente_email"], "propuesta")
            if row["lead_email"]:
                _agregar_contacto(contactos, vistos, row["lead_nombre"], row["lead_email"], "propuesta")
    finally:
        conn.close()

    return JSONResponse(contactos[:MAX_CONTACTOS_SUGERIDOS])


@router.get("/emails/nuevo", response_class=HTMLResponse)
def nuevo_email(request: Request, mensaje: str = "", error: str = ""):
    get_current_user(request)
    return render_template(
        request,
        "emails/form.html",
        {
            "titulo": "Nuevo email corporativo",
            "form_action": "/emails/nuevo",
            "form_data": {},
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
        },
    )


@router.post("/emails/nuevo", response_class=HTMLResponse)
def enviar_email_corporativo(
    request: Request,
    destinatario: str = Form(""),
    asunto: str = Form(""),
    cuerpo: str = Form(""),
    adjunto: UploadFile | None = File(None),
):
    current_user = get_current_user(request)
    destinatario_limpio = limpiar_texto(destinatario)
    asunto_limpio = limpiar_texto(asunto)
    cuerpo_limpio = limpiar_texto(cuerpo)
    form_data = {
        "destinatario": destinatario_limpio,
        "asunto": asunto_limpio,
        "cuerpo": cuerpo_limpio,
    }

    if not destinatario_limpio or not es_email_valido(destinatario_limpio):
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": "Indica un destinatario válido.",
            },
        )
    if not asunto_limpio:
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": "El asunto es obligatorio.",
            },
        )
    if not cuerpo_limpio:
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": "El cuerpo del email es obligatorio.",
            },
        )

    try:
        adjunto_preparado = preparar_adjunto(adjunto)
    except ValueError as exc:
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": str(exc),
            },
        )

    body_text = construir_email_texto(cuerpo_limpio, footer_text="")
    body_html = construir_email_html(
        asunto_limpio,
        texto_a_html(cuerpo_limpio),
        footer_text="",
    )
    mensaje_email = crear_mensaje_email(
        destinatario_limpio,
        asunto_limpio,
        body_text,
        body_html,
        adjuntos=[adjunto_preparado] if adjunto_preparado else None,
    )

    try:
        enviar_mensaje_email(mensaje_email, contexto="email corporativo")
    except RuntimeError as exc:
        registrar_email_enviado(
            tipo="manual",
            destinatario=destinatario_limpio,
            asunto=asunto_limpio,
            cuerpo_texto=cuerpo_limpio,
            nombre_adjunto=adjunto_preparado["filename"] if adjunto_preparado else None,
            tiene_adjunto=bool(adjunto_preparado),
            estado="error",
            error_mensaje=str(exc),
            owner_user_id=current_user["id"],
        )
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": "No está configurado el envío de email.",
            },
        )
    except Exception as exc:
        registrar_email_enviado(
            tipo="manual",
            destinatario=destinatario_limpio,
            asunto=asunto_limpio,
            cuerpo_texto=cuerpo_limpio,
            nombre_adjunto=adjunto_preparado["filename"] if adjunto_preparado else None,
            tiene_adjunto=bool(adjunto_preparado),
            estado="error",
            error_mensaje=str(exc),
            owner_user_id=current_user["id"],
        )
        return render_template(
            request,
            "emails/form.html",
            {
                "titulo": "Nuevo email corporativo",
                "form_action": "/emails/nuevo",
                "form_data": form_data,
                "mensaje": "",
                "error": "No se pudo enviar el email corporativo.",
            },
        )

    registrar_email_enviado(
        tipo="manual",
        destinatario=destinatario_limpio,
        asunto=asunto_limpio,
        cuerpo_texto=cuerpo_limpio,
        nombre_adjunto=adjunto_preparado["filename"] if adjunto_preparado else None,
        tiene_adjunto=bool(adjunto_preparado),
        estado="enviado",
        owner_user_id=current_user["id"],
    )

    return RedirectResponse(
        url=f"/emails/nuevo?mensaje={quote('Email corporativo enviado correctamente.')}",
        status_code=303,
    )
