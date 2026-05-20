import logging
import re
import smtplib
from decimal import Decimal, ROUND_HALF_UP
from email.message import EmailMessage
from email.utils import formataddr
from datetime import date
from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

from app.config import (
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from app.database import get_connection
from app.services.propuestas_catalogo import (
    SERVICIOS_CATALOGO,
    SERVICIOS_CATALOGO_OPCIONES,
)

router = APIRouter()
logger = logging.getLogger(__name__)

PROPUESTA_ESTADOS = ("borrador", "enviada", "aceptada", "rechazada", "caducada")
SERVICIO_CATEGORIAS = (
    ("", "Sin categoría"),
    ("estudio_documental", "Estudio preliminar y análisis documental"),
    ("visita_tecnica", "Visita técnica"),
    ("informe_pericial", "Redacción de informe pericial"),
    ("ratificacion_judicial", "Ratificación judicial"),
    ("desplazamientos", "Desplazamientos y dietas"),
    ("extras", "Servicios adicionales"),
)
SERVICIO_CATEGORIA_LABELS = dict(SERVICIO_CATEGORIAS)


def construir_catalogo_preview():
    return {
        clave: {
            "clave": clave,
            "concepto": servicio.get("concepto", ""),
            "categoria": SERVICIO_CATEGORIA_LABELS.get(
                servicio.get("categoria_servicio", ""),
                servicio.get("categoria_servicio", ""),
            ),
            "descripcion": servicio.get("descripcion", ""),
            "incluye": servicio.get("incluye", ""),
            "no_incluye": servicio.get("no_incluye", ""),
            "condiciones": servicio.get("condiciones", ""),
        }
        for clave, servicio in SERVICIOS_CATALOGO.items()
    }


RATIFICACION_JUDICIAL_PRESET = {
    "categoria_servicio": "ratificacion_judicial",
    "concepto": "Ratificación judicial",
    "descripcion": "Asistencia del perito para ratificación del informe pericial en sede judicial.",
    "incluye": "Preparación previa y asistencia a una única vista o señalamiento.",
    "no_incluye": "Suspensiones, nuevos señalamientos, ampliaciones, desplazamientos, dietas, reuniones adicionales ni nueva documentación no prevista.",
    "condiciones": "Cualquier suspensión judicial, nueva vista o actuación adicional será presupuestada aparte.",
    "cantidad": 1.0,
    "iva_porcentaje": 21.0,
}
DESPLAZAMIENTO_TEXTOS = {
    "incluye": "Desplazamiento profesional asociado a las actuaciones descritas en esta propuesta.",
    "no_incluye": "Peajes, aparcamientos, dietas, pernoctas u otros gastos extraordinarios salvo indicación expresa.",
    "condiciones": "Los desplazamientos adicionales, actuaciones fuera de la zona prevista o dietas se presupuestarán aparte.",
}
URGENCIA_TEXTOS = {
    "condiciones": "Recargo asociado a la priorización del encargo y reducción de plazos respecto del flujo ordinario de trabajo.",
}
COMPLEJIDAD_NIVELES = {
    "baja": "baja",
    "media": "media",
    "alta": "alta",
}
COMPLEJIDAD_TEXTOS = {
    "incluye": "Ajuste de honorarios por mayor dedicación técnica, revisión documental o análisis adicional dentro del alcance de la propuesta.",
    "no_incluye": "Trabajos fuera del alcance, nueva documentación no prevista, visitas adicionales, ensayos, catas o contrainformes independientes.",
    "condiciones": "El suplemento responde al nivel de complejidad estimado con la información disponible al presupuestar el encargo.",
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


def parse_float_no_negativo(valor: str | None) -> float | None:
    valor_limpio = limpiar_texto(valor)
    if not valor_limpio:
        return None
    try:
        numero = float(valor_limpio.replace(",", "."))
    except ValueError:
        return None
    return numero if numero >= 0 else None


def normalizar_categoria_servicio(valor: str | None) -> str:
    categoria = limpiar_texto(valor)
    return categoria if categoria in SERVICIO_CATEGORIA_LABELS else ""


def format_money(valor: float | int | None) -> str:
    return f"{float(valor or 0):.2f}"


def redondear_importe(valor: float | int | str | Decimal) -> float:
    return float(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calcular_honorarios(base_imponible: float, iva_porcentaje: float):
    base = redondear_importe(max(base_imponible, 0))
    iva_pct = redondear_importe(max(iva_porcentaje, 0))
    importe_iva = redondear_importe(base * iva_pct / 100)
    total_propuesta = redondear_importe(base + importe_iva)
    return base, iva_pct, importe_iva, total_propuesta


def calcular_importes_linea(cantidad: float, precio_unitario: float, iva_porcentaje: float):
    base_linea = redondear_importe(cantidad * precio_unitario)
    iva_linea = redondear_importe(base_linea * iva_porcentaje / 100)
    total_linea = redondear_importe(base_linea + iva_linea)
    return base_linea, iva_linea, total_linea


def inferir_linea_base_propuesta(tipo_trabajo: str | None) -> dict:
    tipo = limpiar_texto(tipo_trabajo).lower()
    if "tasaci" in tipo or "valoraci" in tipo:
        return {
            "categoria_servicio": "informe_pericial",
            "concepto": "Informe de valoración inmobiliaria",
            "descripcion": "Elaboración de informe de valoración conforme al objeto del encargo.",
        }
    if "inspecci" in tipo or "inspeccion" in tipo:
        return {
            "categoria_servicio": "visita_tecnica",
            "concepto": "Inspección técnica de vivienda",
            "descripcion": "Inspección técnica y emisión de resumen o informe de observaciones.",
        }
    if "informe" in tipo:
        return {
            "categoria_servicio": "informe_pericial",
            "concepto": "Redacción de informe pericial",
            "descripcion": "Elaboración de informe pericial técnico conforme al objeto del encargo.",
        }
    return {
        "categoria_servicio": "extras",
        "concepto": "Honorarios profesionales",
        "descripcion": "Honorarios profesionales correspondientes al objeto de la propuesta.",
    }


def crear_linea_base_inicial_propuesta(cur, propuesta_id: int, propuesta: dict):
    base_imponible = redondear_importe(propuesta["base_imponible"] or 0)
    if base_imponible <= 0:
        return

    iva_porcentaje = redondear_importe(propuesta["iva_porcentaje"] or 0)
    _, _, total_linea = calcular_importes_linea(1.0, base_imponible, iva_porcentaje)
    linea_base = inferir_linea_base_propuesta(propuesta["tipo_trabajo"])

    cur.execute(
        """
        INSERT INTO propuesta_lineas (
            propuesta_id, categoria_servicio, concepto, descripcion, incluye,
            no_incluye, condiciones, cantidad, precio_unitario,
            iva_porcentaje, total, orden
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            propuesta_id,
            linea_base["categoria_servicio"],
            linea_base["concepto"],
            linea_base["descripcion"],
            "",
            "",
            "",
            1.0,
            base_imponible,
            iva_porcentaje,
            total_linea,
            1,
        ),
    )
    recalcular_totales_propuesta(cur, propuesta_id)


def construir_mailto_propuesta(request: Request, propuesta) -> str:
    email = obtener_email_propuesta(propuesta)
    if not email:
        return ""

    url_imprimir = str(
        request.url_for("imprimir_propuesta", propuesta_id=propuesta["id"])
    )
    asunto = f"Propuesta {propuesta['numero_propuesta']} - Servicios profesionales"
    cuerpo = f"""Hola,

Te remito la propuesta de servicios profesionales correspondiente.

Puedes revisar la propuesta en el siguiente enlace:

{url_imprimir}

Para aceptar la propuesta, es suficiente con responder a este correo indicando:

“Acepto la propuesta enviada.”

Quedo a tu disposición para cualquier aclaración.

Un saludo,
Carlos Blanco
Arquitecto Técnico
623 829 228"""

    return (
        f"mailto:{quote(email)}"
        f"?subject={quote(asunto)}"
        f"&body={quote(cuerpo)}"
    )


def limpiar_nombre_pdf(valor: str | None) -> str:
    nombre = re.sub(r"[^A-Za-z0-9_.-]+", "-", limpiar_texto(valor))
    return nombre.strip("-") or "propuesta"


def obtener_email_propuesta(propuesta) -> str:
    return limpiar_texto(propuesta["cliente_email"] or propuesta["lead_email"])


def nombre_archivo_pdf_propuesta(propuesta) -> str:
    return f"Propuesta-{limpiar_nombre_pdf(propuesta['numero_propuesta'])}.pdf"


def generar_pdf_propuesta_bytes(request: Request, propuesta, lineas=None) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Playwright no está instalado. Actualiza dependencias para generar PDFs.",
        ) from exc

    html = request.app.state.templates.env.get_template(
        "propuestas/imprimir.html"
    ).render(
        {
            "request": request,
            "current_user": getattr(request.state, "current_user", None),
            "propuesta": propuesta,
            "lineas": lineas or [],
            "servicio_categoria_labels": SERVICIO_CATEGORIA_LABELS,
            "format_money": format_money,
            "mailto_url": "",
        }
    )

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                margin={
                    "top": "16mm",
                    "right": "16mm",
                    "bottom": "16mm",
                    "left": "16mm",
                },
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar el PDF de la propuesta.",
        ) from exc

    return pdf_bytes


def enviar_email_propuesta(destinatario: str, propuesta, pdf_bytes: bytes):
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL]):
        raise RuntimeError("smtp_not_configured")

    asunto = f"Propuesta {propuesta['numero_propuesta']} - Servicios profesionales"
    body_text = """Hola,

Te remito adjunta la propuesta de servicios profesionales correspondiente.

Para aceptar la propuesta, es suficiente con responder a este correo indicando:

“Acepto la propuesta enviada.”

Quedo a tu disposición para cualquier aclaración.

Un saludo,
Carlos Blanco
Arquitecto Técnico
623 829 228
contacto@carlosblancoperito.es

Documento adjunto en PDF."""

    body_html = """\
<!doctype html>
<html lang="es">
<body style="margin:0;padding:0;background:#f7f5f0;font-family:Arial,Helvetica,sans-serif;color:#10233f;">
  <div style="width:100%;background:#f7f5f0;padding:24px 12px;">
    <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #e4e0d8;border-radius:8px;overflow:hidden;">
      <div style="background:#10233f;color:#ffffff;padding:24px 28px;border-bottom:4px solid #b89b68;">
        <div style="font-size:22px;font-weight:700;line-height:1.2;">Carlos Blanco</div>
        <div style="font-size:14px;line-height:1.5;color:#f7f5f0;">Arquitecto Técnico</div>
        <div style="margin-top:14px;font-size:16px;font-weight:700;color:#b89b68;">Propuesta de servicios profesionales</div>
      </div>
      <div style="padding:28px;">
        <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">Hola,</p>
        <p style="margin:0 0 18px;font-size:15px;line-height:1.6;">Te remito adjunta la propuesta de servicios profesionales correspondiente.</p>
        <div style="margin:22px 0;padding:18px;border:1px solid #e4e0d8;border-left:4px solid #b89b68;background:#f7f5f0;border-radius:6px;">
          <div style="margin-bottom:8px;font-size:13px;font-weight:700;color:#10233f;">Para aceptar la propuesta, responde indicando:</div>
          <div style="font-size:17px;font-weight:700;color:#10233f;">“Acepto la propuesta enviada.”</div>
        </div>
        <p style="margin:0 0 24px;font-size:15px;line-height:1.6;">Quedo a tu disposición para cualquier aclaración.</p>
        <div style="padding-top:18px;border-top:1px solid #e4e0d8;font-size:14px;line-height:1.6;color:#10233f;">
          <div style="font-weight:700;">Carlos Blanco</div>
          <div>Arquitecto Técnico</div>
          <div>623 829 228</div>
          <div>contacto@carlosblancoperito.es</div>
        </div>
      </div>
      <div style="padding:14px 28px;background:#f7f5f0;border-top:1px solid #e4e0d8;font-size:12px;line-height:1.5;color:#6f6a60;">
        Documento adjunto en PDF.
      </div>
    </div>
  </div>
</body>
</html>"""

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
    mensaje["To"] = destinatario
    mensaje.set_content(body_text)
    mensaje.add_alternative(body_html, subtype="html")
    mensaje.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=nombre_archivo_pdf_propuesta(propuesta),
    )

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(mensaje)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(mensaje)
    except Exception:
        logger.exception(
            "Error SMTP enviando propuesta %s a %s con host=%s puerto=%s usuario=%s remitente=%s",
            propuesta["numero_propuesta"],
            destinatario,
            SMTP_HOST,
            SMTP_PORT,
            SMTP_USER,
            SMTP_FROM_EMAIL,
        )
        raise


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


def get_owned_linea_propuesta(cur, propuesta_id: int, linea_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT pl.*
        FROM propuesta_lineas pl
        INNER JOIN propuestas p ON p.id = pl.propuesta_id
        WHERE pl.id = ? AND pl.propuesta_id = ? AND p.owner_user_id = ?
        """,
        (linea_id, propuesta_id, owner_user_id),
    ).fetchone()


def recalcular_totales_propuesta(cur, propuesta_id: int):
    lineas = obtener_lineas_propuesta(cur, propuesta_id)
    base_imponible = 0.0
    iva = 0.0
    total = 0.0

    for linea in lineas:
        cantidad = float(linea["cantidad"] or 0)
        precio_unitario = float(linea["precio_unitario"] or 0)
        iva_porcentaje = float(linea["iva_porcentaje"] or 0)
        base_linea, iva_linea, total_linea = calcular_importes_linea(
            cantidad, precio_unitario, iva_porcentaje
        )

        cur.execute(
            """
            UPDATE propuesta_lineas
            SET total = ?
            WHERE id = ?
            """,
            (total_linea, linea["id"]),
        )

        base_imponible = redondear_importe(base_imponible + base_linea)
        iva = redondear_importe(iva + iva_linea)
        total = redondear_importe(total + total_linea)

    base_imponible = redondear_importe(base_imponible)
    iva = redondear_importe(iva)
    total = redondear_importe(total)

    cur.execute(
        """
        UPDATE propuestas
        SET base_imponible = ?, importe_iva = ?, total_propuesta = ?,
            iva = ?, total = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (base_imponible, iva, total, iva, total, propuesta_id),
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
            "base_imponible": 0,
            "iva_porcentaje": 21,
            "importe_iva": 0,
            "total_propuesta": 0,
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
    base_imponible: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    condiciones: str = Form(""),
):
    current_user = get_current_user(request)
    lead_id_int = parse_optional_int(lead_id)
    cliente_id_int = parse_optional_int(cliente_id)
    base, iva_pct, importe_iva, total_propuesta = calcular_honorarios(
        parse_float(base_imponible, 0),
        parse_float(iva_porcentaje, 21),
    )
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
        "base_imponible": base,
        "iva_porcentaje": iva_pct,
        "importe_iva": importe_iva,
        "total_propuesta": total_propuesta,
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
                direccion_inmueble, alcance, plazo_estimado, base_imponible,
                iva_porcentaje, importe_iva, total_propuesta, iva, total,
                condiciones, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                propuesta["base_imponible"],
                propuesta["iva_porcentaje"],
                propuesta["importe_iva"],
                propuesta["total_propuesta"],
                propuesta["importe_iva"],
                propuesta["total_propuesta"],
                propuesta["condiciones"],
                current_user["id"],
            ),
        )
        propuesta_id = cur.lastrowid
        crear_linea_base_inicial_propuesta(cur, propuesta_id, propuesta)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.get("/propuestas/{propuesta_id}", response_class=HTMLResponse)
def detalle_propuesta(
    request: Request,
    propuesta_id: int,
    print: int = Query(0),
    mensaje: str = Query(""),
    error: str = Query(""),
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
            "servicio_categorias": SERVICIO_CATEGORIAS,
            "servicio_categoria_labels": SERVICIO_CATEGORIA_LABELS,
            "servicios_catalogo": SERVICIOS_CATALOGO_OPCIONES,
            "servicios_catalogo_preview": construir_catalogo_preview(),
            "format_money": format_money,
            "print_mode": bool(print),
            "mailto_url": construir_mailto_propuesta(request, propuesta),
            "email_disponible": bool(obtener_email_propuesta(propuesta)),
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
        },
    )


@router.get("/propuestas/{propuesta_id}/imprimir", response_class=HTMLResponse)
def imprimir_propuesta(request: Request, propuesta_id: int):
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
        "propuestas/imprimir.html",
        {
            "propuesta": propuesta,
            "lineas": lineas,
            "servicio_categoria_labels": SERVICIO_CATEGORIA_LABELS,
            "format_money": format_money,
            "mailto_url": construir_mailto_propuesta(request, propuesta),
            "email_disponible": bool(obtener_email_propuesta(propuesta)),
        },
    )


@router.get("/propuestas/{propuesta_id}/pdf")
def descargar_pdf_propuesta(request: Request, propuesta_id: int):
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

    pdf_bytes = generar_pdf_propuesta_bytes(request, propuesta, lineas=lineas)
    filename = nombre_archivo_pdf_propuesta(propuesta)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/propuestas/{propuesta_id}/enviar-email")
def enviar_propuesta_email(request: Request, propuesta_id: int):
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

    destinatario = obtener_email_propuesta(propuesta)
    if not destinatario:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('La propuesta no tiene email de cliente o lead.')}",
            status_code=303,
        )

    try:
        pdf_bytes = generar_pdf_propuesta_bytes(request, propuesta, lineas=lineas)
        enviar_email_propuesta(destinatario, propuesta, pdf_bytes)
    except RuntimeError:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('No está configurado el envío de email.')}",
            status_code=303,
        )
    except HTTPException as exc:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote(str(exc.detail))}",
            status_code=303,
        )
    except Exception:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('No se pudo enviar la propuesta por email.')}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Propuesta enviada correctamente por email.')}",
        status_code=303,
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
        tiene_lineas = bool(obtener_lineas_propuesta(cur, propuesta_id))
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
            "tiene_lineas": tiene_lineas,
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
    base_imponible: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    condiciones: str = Form(""),
):
    current_user = get_current_user(request)
    lead_id_int = parse_optional_int(lead_id)
    cliente_id_int = parse_optional_int(cliente_id)
    base, iva_pct, importe_iva, total_propuesta = calcular_honorarios(
        parse_float(base_imponible, 0),
        parse_float(iva_porcentaje, 21),
    )
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
        "base_imponible": base,
        "iva_porcentaje": iva_pct,
        "importe_iva": importe_iva,
        "total_propuesta": total_propuesta,
        "condiciones": limpiar_texto(condiciones),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta_existente = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta_existente:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")
        tiene_lineas = bool(obtener_lineas_propuesta(cur, propuesta_id))
        if tiene_lineas:
            propuesta["base_imponible"] = propuesta_existente["base_imponible"]
            propuesta["iva_porcentaje"] = propuesta_existente["iva_porcentaje"]
            propuesta["importe_iva"] = propuesta_existente["importe_iva"]
            propuesta["total_propuesta"] = propuesta_existente["total_propuesta"]

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
                    "tiene_lineas": tiene_lineas,
                },
            )

        cur.execute(
            """
            UPDATE propuestas
            SET numero_propuesta = ?, lead_id = ?, cliente_id = ?, fecha = ?,
                tipo_trabajo = ?, direccion_inmueble = ?, alcance = ?,
                plazo_estimado = ?, base_imponible = ?, iva_porcentaje = ?,
                importe_iva = ?, total_propuesta = ?, iva = ?, total = ?,
                condiciones = ?, updated_at = CURRENT_TIMESTAMP
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
                propuesta["base_imponible"],
                propuesta["iva_porcentaje"],
                propuesta["importe_iva"],
                propuesta["total_propuesta"],
                propuesta["importe_iva"],
                propuesta["total_propuesta"],
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
    categoria_servicio: str = Form(""),
    concepto: str = Form(...),
    descripcion: str = Form(""),
    incluye: str = Form(""),
    no_incluye: str = Form(""),
    condiciones: str = Form(""),
    cantidad: str = Form("1"),
    precio_unitario: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    orden: str = Form(""),
):
    current_user = get_current_user(request)
    concepto_limpio = limpiar_texto(concepto)
    if not concepto_limpio:
        return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)

    categoria_limpia = normalizar_categoria_servicio(categoria_servicio)
    cantidad_valor = parse_float_no_negativo(cantidad)
    precio_unitario_valor = parse_float_no_negativo(precio_unitario)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if cantidad_valor is None or precio_unitario_valor is None or iva_porcentaje_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Cantidad, precio unitario e IVA deben ser valores válidos y no negativos.')}",
            status_code=303,
        )
    _, _, total_linea = calcular_importes_linea(
        cantidad_valor, precio_unitario_valor, iva_porcentaje_valor
    )

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
        orden_valor = parse_optional_int(orden) or siguiente_orden

        cur.execute(
            """
            INSERT INTO propuesta_lineas (
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                categoria_limpia,
                concepto_limpio,
                limpiar_texto(descripcion),
                limpiar_texto(incluye),
                limpiar_texto(no_incluye),
                limpiar_texto(condiciones),
                cantidad_valor,
                precio_unitario_valor,
                iva_porcentaje_valor,
                total_linea,
                orden_valor,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/lineas/catalogo")
def crear_linea_catalogo_propuesta(
    request: Request,
    propuesta_id: int,
    servicio_catalogo: str = Form(...),
    cantidad: str = Form("1"),
    precio_unitario: str = Form("0"),
    iva_porcentaje: str = Form("21"),
):
    current_user = get_current_user(request)
    servicio = SERVICIOS_CATALOGO.get(limpiar_texto(servicio_catalogo))
    if not servicio:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Selecciona un servicio del catálogo válido.')}",
            status_code=303,
        )

    cantidad_valor = parse_float_no_negativo(cantidad)
    precio_unitario_valor = parse_float_no_negativo(precio_unitario)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if (
        cantidad_valor is None
        or precio_unitario_valor is None
        or iva_porcentaje_valor is None
        or cantidad_valor <= 0
        or precio_unitario_valor <= 0
    ):
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Cantidad y precio deben ser positivos, e IVA debe ser válido y no negativo.')}",
            status_code=303,
        )

    _, _, total_linea = calcular_importes_linea(
        cantidad_valor, precio_unitario_valor, iva_porcentaje_valor
    )

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
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                servicio["categoria_servicio"],
                servicio["concepto"],
                servicio["descripcion"],
                servicio["incluye"],
                servicio["no_incluye"],
                servicio["condiciones"],
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

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Servicio del catálogo añadido como línea independiente.')}",
        status_code=303,
    )


@router.post("/propuestas/{propuesta_id}/lineas/ratificacion-judicial")
def crear_ratificacion_judicial_propuesta(
    request: Request,
    propuesta_id: int,
    precio_unitario: str = Form(...),
):
    current_user = get_current_user(request)
    precio_unitario_valor = parse_float_no_negativo(precio_unitario)
    if precio_unitario_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Indica un importe válido y no negativo para la ratificación judicial.')}",
            status_code=303,
        )

    preset = RATIFICACION_JUDICIAL_PRESET
    _, _, total_linea = calcular_importes_linea(
        preset["cantidad"], precio_unitario_valor, preset["iva_porcentaje"]
    )

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
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                preset["categoria_servicio"],
                preset["concepto"],
                preset["descripcion"],
                preset["incluye"],
                preset["no_incluye"],
                preset["condiciones"],
                preset["cantidad"],
                precio_unitario_valor,
                preset["iva_porcentaje"],
                total_linea,
                siguiente_orden,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Ratificación judicial añadida como línea independiente.')}",
        status_code=303,
    )


@router.post("/propuestas/{propuesta_id}/lineas/desplazamiento")
def crear_desplazamiento_propuesta(
    request: Request,
    propuesta_id: int,
    concepto: str = Form("Desplazamiento"),
    km: str = Form(...),
    precio_km: str = Form(...),
    iva_porcentaje: str = Form("21"),
):
    current_user = get_current_user(request)
    concepto_limpio = limpiar_texto(concepto) or "Desplazamiento"
    km_valor = parse_float_no_negativo(km)
    precio_km_valor = parse_float_no_negativo(precio_km)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if km_valor is None or precio_km_valor is None or iva_porcentaje_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Indica km, precio por km e IVA válidos y no negativos para el desplazamiento.')}",
            status_code=303,
        )

    _, _, total_linea = calcular_importes_linea(
        km_valor, precio_km_valor, iva_porcentaje_valor
    )
    descripcion = (
        f"Cálculo de desplazamiento: {format_money(km_valor)} km x "
        f"{format_money(precio_km_valor)} €/km."
    )

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
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                "desplazamientos",
                concepto_limpio,
                descripcion,
                DESPLAZAMIENTO_TEXTOS["incluye"],
                DESPLAZAMIENTO_TEXTOS["no_incluye"],
                DESPLAZAMIENTO_TEXTOS["condiciones"],
                km_valor,
                precio_km_valor,
                iva_porcentaje_valor,
                total_linea,
                siguiente_orden,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Desplazamiento añadido como línea independiente.')}",
        status_code=303,
    )


@router.post("/propuestas/{propuesta_id}/lineas/recargo-urgencia")
def crear_recargo_urgencia_propuesta(
    request: Request,
    propuesta_id: int,
    porcentaje: str = Form(...),
    iva_porcentaje: str = Form("21"),
):
    current_user = get_current_user(request)
    porcentaje_valor = parse_float_no_negativo(porcentaje)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if porcentaje_valor is None or iva_porcentaje_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Indica porcentaje de urgencia e IVA válidos y no negativos.')}",
            status_code=303,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        base_sin_iva = redondear_importe(propuesta["base_imponible"] or 0)
        if base_sin_iva <= 0:
            return RedirectResponse(
                url=f"/propuestas/{propuesta_id}?error={quote('No se puede calcular urgencia sin base imponible previa.')}",
                status_code=303,
            )

        importe_recargo = redondear_importe(base_sin_iva * porcentaje_valor / 100)
        _, _, total_linea = calcular_importes_linea(
            1.0, importe_recargo, iva_porcentaje_valor
        )
        descripcion = (
            f"Recargo del {format_money(porcentaje_valor)} % aplicado sobre "
            f"base imponible sin IVA de {format_money(base_sin_iva)} €."
        )

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
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                "extras",
                "Recargo por urgencia",
                descripcion,
                "",
                "",
                URGENCIA_TEXTOS["condiciones"],
                1.0,
                importe_recargo,
                iva_porcentaje_valor,
                total_linea,
                siguiente_orden,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Recargo por urgencia añadido como línea independiente.')}",
        status_code=303,
    )


@router.post("/propuestas/{propuesta_id}/lineas/suplemento-complejidad")
def crear_suplemento_complejidad_propuesta(
    request: Request,
    propuesta_id: int,
    complejidad: str = Form(...),
    porcentaje: str = Form(...),
    iva_porcentaje: str = Form("21"),
):
    current_user = get_current_user(request)
    complejidad_limpia = limpiar_texto(complejidad).lower()
    if complejidad_limpia not in COMPLEJIDAD_NIVELES:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Selecciona una complejidad válida.')}",
            status_code=303,
        )

    porcentaje_valor = parse_float_no_negativo(porcentaje)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if porcentaje_valor is None or iva_porcentaje_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Indica porcentaje de complejidad e IVA válidos y no negativos.')}",
            status_code=303,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        propuesta = get_owned_propuesta(cur, propuesta_id, current_user["id"])
        if not propuesta:
            raise HTTPException(status_code=404, detail="Propuesta no encontrada")

        base_sin_iva = redondear_importe(propuesta["base_imponible"] or 0)
        if base_sin_iva <= 0:
            return RedirectResponse(
                url=f"/propuestas/{propuesta_id}?error={quote('No se puede calcular complejidad sin base imponible previa.')}",
                status_code=303,
            )

        importe_suplemento = redondear_importe(
            base_sin_iva * porcentaje_valor / 100
        )
        _, _, total_linea = calcular_importes_linea(
            1.0, importe_suplemento, iva_porcentaje_valor
        )
        nivel = COMPLEJIDAD_NIVELES[complejidad_limpia]
        descripcion = (
            f"Suplemento por complejidad {nivel}: "
            f"{format_money(porcentaje_valor)} % aplicado sobre base imponible "
            f"sin IVA de {format_money(base_sin_iva)} €."
        )

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
                propuesta_id, categoria_servicio, concepto, descripcion, incluye,
                no_incluye, condiciones, cantidad, precio_unitario,
                iva_porcentaje, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                propuesta_id,
                "extras",
                "Suplemento por complejidad",
                descripcion,
                COMPLEJIDAD_TEXTOS["incluye"],
                COMPLEJIDAD_TEXTOS["no_incluye"],
                COMPLEJIDAD_TEXTOS["condiciones"],
                1.0,
                importe_suplemento,
                iva_porcentaje_valor,
                total_linea,
                siguiente_orden,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/propuestas/{propuesta_id}?mensaje={quote('Suplemento por complejidad añadido como línea independiente.')}",
        status_code=303,
    )


@router.post("/propuestas/{propuesta_id}/lineas/{linea_id}/editar")
def editar_linea_propuesta(
    request: Request,
    propuesta_id: int,
    linea_id: int,
    categoria_servicio: str = Form(""),
    concepto: str = Form(...),
    descripcion: str = Form(""),
    incluye: str = Form(""),
    no_incluye: str = Form(""),
    condiciones: str = Form(""),
    cantidad: str = Form("1"),
    precio_unitario: str = Form("0"),
    iva_porcentaje: str = Form("21"),
    orden: str = Form("0"),
):
    current_user = get_current_user(request)
    concepto_limpio = limpiar_texto(concepto)
    if not concepto_limpio:
        return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)

    categoria_limpia = normalizar_categoria_servicio(categoria_servicio)
    cantidad_valor = parse_float_no_negativo(cantidad)
    precio_unitario_valor = parse_float_no_negativo(precio_unitario)
    iva_porcentaje_valor = parse_float_no_negativo(iva_porcentaje)
    if cantidad_valor is None or precio_unitario_valor is None or iva_porcentaje_valor is None:
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Cantidad, precio unitario e IVA deben ser valores válidos y no negativos.')}",
            status_code=303,
        )
    _, _, total_linea = calcular_importes_linea(
        cantidad_valor, precio_unitario_valor, iva_porcentaje_valor
    )
    orden_valor = parse_optional_int(orden) or 0

    conn = get_connection()
    cur = conn.cursor()
    try:
        linea = get_owned_linea_propuesta(
            cur, propuesta_id, linea_id, current_user["id"]
        )
        if not linea:
            raise HTTPException(status_code=404, detail="Línea no encontrada")

        cur.execute(
            """
            UPDATE propuesta_lineas
            SET categoria_servicio = ?, concepto = ?, descripcion = ?,
                incluye = ?, no_incluye = ?, condiciones = ?, cantidad = ?,
                precio_unitario = ?, iva_porcentaje = ?, total = ?, orden = ?
            WHERE id = ? AND propuesta_id = ?
            """,
            (
                categoria_limpia,
                concepto_limpio,
                limpiar_texto(descripcion),
                limpiar_texto(incluye),
                limpiar_texto(no_incluye),
                limpiar_texto(condiciones),
                cantidad_valor,
                precio_unitario_valor,
                iva_porcentaje_valor,
                total_linea,
                orden_valor,
                linea_id,
                propuesta_id,
            ),
        )
        recalcular_totales_propuesta(cur, propuesta_id)
        conn.commit()
    finally:
        conn.close()

    return RedirectResponse(url=f"/propuestas/{propuesta_id}", status_code=303)


@router.post("/propuestas/{propuesta_id}/lineas/{linea_id}/eliminar")
def eliminar_linea_propuesta(
    request: Request,
    propuesta_id: int,
    linea_id: int,
    confirmar_eliminar: str = Form(""),
):
    current_user = get_current_user(request)
    if limpiar_texto(confirmar_eliminar) != "on":
        return RedirectResponse(
            url=f"/propuestas/{propuesta_id}?error={quote('Confirma el borrado de la línea antes de eliminarla.')}",
            status_code=303,
        )

    conn = get_connection()
    cur = conn.cursor()
    try:
        linea = get_owned_linea_propuesta(
            cur, propuesta_id, linea_id, current_user["id"]
        )
        if not linea:
            raise HTTPException(status_code=404, detail="Línea no encontrada")

        cur.execute(
            """
            DELETE FROM propuesta_lineas
            WHERE id = ? AND propuesta_id = ?
            """,
            (linea_id, propuesta_id),
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
