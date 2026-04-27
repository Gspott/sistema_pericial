import sqlite3
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.database import get_connection
from app.routers.facturacion import calcular_resumen_iva, obtener_trimestre_actual
from app.services.backups import listar_backups

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


def format_money(valor: float | int | None) -> str:
    return f"{float(valor or 0):.2f}"


def fetchone_safe(cur, query: str, params=(), default=None):
    try:
        return cur.execute(query, params).fetchone()
    except sqlite3.OperationalError:
        return default


def fetchall_safe(cur, query: str, params=()):
    try:
        return cur.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        return []


def scalar_safe(cur, query: str, params=(), default=0):
    row = fetchone_safe(cur, query, params)
    if row is None:
        return default
    return row[0] if row[0] is not None else default


def nombre_cliente(factura) -> str:
    razon_social = (factura["cliente_razon_social"] or "").strip()
    if razon_social:
        return razon_social
    partes = [
        (factura["cliente_nombre"] or "").strip(),
        (factura["cliente_apellidos"] or "").strip(),
    ]
    return " ".join(parte for parte in partes if parte) or "Sin cliente"


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    current_user = get_current_user(request)
    owner_user_id = current_user["id"]
    hoy = date.today().isoformat()
    year_actual, trimestre_actual = obtener_trimestre_actual()

    conn = get_connection()
    cur = conn.cursor()
    try:
        leads = {
            "nuevos": scalar_safe(
                cur,
                "SELECT COUNT(*) FROM leads WHERE owner_user_id = ? AND estado = 'nuevo'",
                (owner_user_id,),
            ),
            "contactados": scalar_safe(
                cur,
                "SELECT COUNT(*) FROM leads WHERE owner_user_id = ? AND estado = 'contactado'",
                (owner_user_id,),
            ),
            "pendientes_respuesta": scalar_safe(
                cur,
                "SELECT COUNT(*) FROM leads WHERE owner_user_id = ? AND estado = 'pendiente_respuesta'",
                (owner_user_id,),
            ),
            "tareas_hoy": fetchall_safe(
                cur,
                """
                SELECT lt.*, l.nombre AS lead_nombre
                FROM lead_tareas lt
                LEFT JOIN leads l ON l.id = lt.lead_id
                WHERE lt.owner_user_id = ?
                  AND lt.estado = 'pendiente'
                  AND DATE(lt.fecha_programada) <= DATE(?)
                ORDER BY lt.fecha_programada ASC, lt.id ASC
                LIMIT 5
                """,
                (owner_user_id, hoy),
            ),
        }

        propuestas = {
            "enviadas": scalar_safe(
                cur,
                "SELECT COUNT(*) FROM propuestas WHERE owner_user_id = ? AND estado = 'enviada'",
                (owner_user_id,),
            ),
            "aceptadas_sin_expediente": scalar_safe(
                cur,
                """
                SELECT COUNT(*)
                FROM propuestas
                WHERE owner_user_id = ? AND estado = 'aceptada' AND expediente_id IS NULL
                """,
                (owner_user_id,),
            ),
            "borradores": fetchall_safe(
                cur,
                """
                SELECT *
                FROM propuestas
                WHERE owner_user_id = ? AND estado = 'borrador'
                ORDER BY id DESC
                LIMIT 5
                """,
                (owner_user_id,),
            ),
        }

        expedientes = {
            "ultimos": fetchall_safe(
                cur,
                """
                SELECT *
                FROM expedientes
                WHERE owner_user_id = ?
                ORDER BY id DESC
                LIMIT 5
                """,
                (owner_user_id,),
            ),
            "sin_factura": fetchall_safe(
                cur,
                """
                SELECT e.*
                FROM expedientes e
                LEFT JOIN facturas_emitidas f
                  ON f.expediente_id = e.id AND f.owner_user_id = e.owner_user_id
                WHERE e.owner_user_id = ? AND f.id IS NULL
                ORDER BY e.id DESC
                LIMIT 5
                """,
                (owner_user_id,),
            ),
            "desde_propuestas": fetchall_safe(
                cur,
                """
                SELECT e.*, p.numero_propuesta
                FROM expedientes e
                INNER JOIN propuestas p ON p.expediente_id = e.id
                WHERE e.owner_user_id = ?
                ORDER BY e.id DESC
                LIMIT 5
                """,
                (owner_user_id,),
            ),
        }

        facturas_borrador = fetchall_safe(
            cur,
            """
            SELECT f.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
                   c.razon_social AS cliente_razon_social
            FROM facturas_emitidas f
            LEFT JOIN clientes c ON c.id = f.cliente_id
            WHERE f.owner_user_id = ? AND f.estado = 'borrador'
            ORDER BY f.id DESC
            LIMIT 5
            """,
            (owner_user_id,),
        )
        facturas_pendientes = fetchall_safe(
            cur,
            """
            SELECT f.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
                   c.razon_social AS cliente_razon_social
            FROM facturas_emitidas f
            LEFT JOIN clientes c ON c.id = f.cliente_id
            WHERE f.owner_user_id = ? AND f.estado = 'emitida'
            ORDER BY f.fecha ASC, f.id ASC
            LIMIT 5
            """,
            (owner_user_id,),
        )
        total_pendiente = scalar_safe(
            cur,
            """
            SELECT COALESCE(SUM(total), 0)
            FROM facturas_emitidas
            WHERE owner_user_id = ? AND estado = 'emitida'
            """,
            (owner_user_id,),
        )

        gastos_ultimos = fetchall_safe(
            cur,
            """
            SELECT *
            FROM gastos
            WHERE owner_user_id = ?
            ORDER BY fecha DESC, id DESC
            LIMIT 5
            """,
            (owner_user_id,),
        )
    finally:
        conn.close()

    resumen_iva = calcular_resumen_iva(owner_user_id, year_actual, trimestre_actual)
    backups = listar_backups()[:3]

    return render_template(
        request,
        "dashboard.html",
        {
            "leads": leads,
            "propuestas": propuestas,
            "expedientes": expedientes,
            "facturas_borrador": facturas_borrador,
            "facturas_pendientes": facturas_pendientes,
            "total_pendiente": total_pendiente,
            "resumen_iva": resumen_iva,
            "year_actual": year_actual,
            "trimestre_actual": trimestre_actual,
            "gastos_ultimos": gastos_ultimos,
            "backups": backups,
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
        },
    )
