import sqlite3
from datetime import date
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.database import get_connection
from app.routers.facturacion import calcular_resumen_iva, obtener_trimestre_actual

router = APIRouter()

DASHBOARD_LIMIT = 6
OPERATIVE_LIMIT = 8
PERIODO_OPTIONS = (
    ("hoy", "Hoy"),
    ("7", "7 días"),
    ("30", "30 días"),
)
TIPO_OPTIONS = (
    ("todos", "Todo"),
    ("leads", "Leads"),
    ("propuestas", "Propuestas"),
    ("emails", "Emails"),
    ("expedientes", "Expedientes"),
)
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
PROSPECCION_PENDIENTE_ESTADOS = ("nuevo", "pendiente", "contactado", "email_enviado")
PROSPECCION_RESPONDIO_ESTADOS = ("respondio", "pendiente_respuesta")
TAREA_ESTADOS = ("pendiente", "hecha", "cancelada")
PROPUESTA_ESTADOS = ("borrador", "enviada", "aceptada", "rechazada", "caducada")
EMAIL_ESTADOS = ("enviado", "error")
LEAD_PIPELINE_ESTADOS = (
    ("nuevo", "Lead nuevo"),
    ("contactado", "Lead contactado"),
    ("pendiente_respuesta", "Lead pendiente respuesta"),
)
PROPUESTA_PIPELINE_ESTADOS = (
    ("borrador", "Propuesta borrador"),
    ("enviada", "Propuesta enviada"),
    ("aceptada", "Propuesta aceptada"),
)


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


def label_estado(valor: str | None) -> str:
    texto = (valor or "").strip().replace("_", " ")
    return texto.capitalize() if texto else "Sin estado"


def estado_badge_class(valor: str | None) -> str:
    estado = (valor or "").strip().replace("_", "-")
    return f"estado-badge estado-{estado}" if estado else "estado-badge"


def leads_por_origen_like(cur, owner_user_id: int, patron: str) -> int:
    return scalar_safe(
        cur,
        """
        SELECT COUNT(*)
        FROM leads
        WHERE owner_user_id = ?
          AND lower(COALESCE(origen, '')) LIKE ?
        """,
        (owner_user_id, patron),
    )


def leads_por_estados(cur, owner_user_id: int, estados: tuple[str, ...]) -> int:
    if not estados:
        return 0
    placeholders = ", ".join("?" for _estado in estados)
    return scalar_safe(
        cur,
        f"""
        SELECT COUNT(*)
        FROM leads
        WHERE owner_user_id = ?
          AND estado IN ({placeholders})
        """,
        (owner_user_id,) + estados,
    )


def contacto_principal(row) -> str:
    if row is None:
        return "Sin contacto"
    cliente_partes = [
        (row["cliente_nombre"] or "").strip(),
        (row["cliente_apellidos"] or "").strip(),
    ]
    cliente = " ".join(parte for parte in cliente_partes if parte).strip()
    if cliente:
        return cliente
    return (row["email"] or row["telefono"] or "Sin contacto").strip()


def relacion_email(row) -> str:
    tipo = (row["referencia_entidad_tipo"] or "").strip()
    entidad_id = row["referencia_entidad_id"]
    if not tipo:
        return "Sin relación"
    if entidad_id:
        return f"{label_estado(tipo)} #{entidad_id}"
    return label_estado(tipo)


def relacion_email_href(row) -> str:
    tipo = (row["referencia_entidad_tipo"] or "").strip().lower()
    entidad_id = row["referencia_entidad_id"]
    if not tipo or not entidad_id:
        return ""
    if tipo in {"propuesta", "propuestas"}:
        return f"/propuestas/{entidad_id}"
    if tipo in {"lead", "leads"}:
        return f"/leads/{entidad_id}"
    if tipo in {"expediente", "expedientes"}:
        return f"/detalle-expediente/{entidad_id}"
    if tipo in {"cliente", "clientes"}:
        return f"/clientes/{entidad_id}"
    return ""


def estado_expediente(row) -> str:
    if row is None or "estado" not in row.keys():
        return ""
    return (row["estado"] or "").strip()


def filtro_query(filters: dict, **updates) -> str:
    data = {
        "periodo": filters["periodo"],
        "tipo": filters["tipo"],
        "estado": filters["estado"],
    }
    data.update(updates)
    clean = {key: value for key, value in data.items() if value}
    return urlencode(clean)


def periodo_desde_request(request: Request) -> str:
    valor = (request.query_params.get("periodo") or "7").strip()
    return valor if valor in {key for key, _label in PERIODO_OPTIONS} else "7"


def tipo_desde_request(request: Request) -> str:
    valor = (request.query_params.get("tipo") or "todos").strip()
    return valor if valor in {key for key, _label in TIPO_OPTIONS} else "todos"


def estado_desde_request(request: Request) -> str:
    valor = (request.query_params.get("estado") or "").strip()
    estados = set(LEAD_ESTADOS + TAREA_ESTADOS + PROPUESTA_ESTADOS + EMAIL_ESTADOS)
    return valor if valor in estados else ""


def periodo_condition(column_expr: str, periodo: str) -> tuple[str, tuple]:
    if periodo == "hoy":
        return f"DATE({column_expr}) = DATE(?)", ("now",)
    if periodo == "30":
        return f"DATE({column_expr}) >= DATE(?, '-30 days')", ("now",)
    return f"DATE({column_expr}) >= DATE(?, '-7 days')", ("now",)


def proximidad_tarea_condition(periodo: str) -> tuple[str, tuple]:
    if periodo == "hoy":
        return "DATE(lt.fecha_programada) <= DATE(?)", ("now",)
    if periodo == "30":
        return "DATE(lt.fecha_programada) <= DATE(?, '+30 days')", ("now",)
    return "DATE(lt.fecha_programada) <= DATE(?, '+7 days')", ("now",)


def estado_options_para_tipo(tipo: str) -> list[tuple[str, str]]:
    if tipo == "leads":
        estados = LEAD_ESTADOS + TAREA_ESTADOS
    elif tipo == "propuestas":
        estados = PROPUESTA_ESTADOS
    elif tipo == "emails":
        estados = EMAIL_ESTADOS
    elif tipo == "expedientes":
        estados = ()
    else:
        estados = LEAD_ESTADOS + TAREA_ESTADOS + PROPUESTA_ESTADOS + EMAIL_ESTADOS
    vistos = set()
    opciones = [("", "Cualquier estado")]
    for estado in estados:
        if estado not in vistos:
            opciones.append((estado, label_estado(estado)))
            vistos.add(estado)
    return opciones


def contar_por_estado(cur, tabla: str, owner_user_id: int, estados: tuple[str, ...]) -> dict[str, int]:
    return {
        estado: scalar_safe(
            cur,
            f"SELECT COUNT(*) FROM {tabla} WHERE owner_user_id = ? AND estado = ?",
            (owner_user_id, estado),
        )
        for estado in estados
    }


def construir_pipeline(cur, owner_user_id: int) -> list[dict]:
    lead_counts = contar_por_estado(
        cur,
        "leads",
        owner_user_id,
        tuple(estado for estado, _label in LEAD_PIPELINE_ESTADOS),
    )
    propuesta_counts = contar_por_estado(
        cur,
        "propuestas",
        owner_user_id,
        tuple(estado for estado, _label in PROPUESTA_PIPELINE_ESTADOS),
    )
    etapas = [
        {
            "clave": f"lead_{estado}",
            "label": label,
            "total": lead_counts.get(estado, 0),
            "href": f"/leads?estado={estado}",
        }
        for estado, label in LEAD_PIPELINE_ESTADOS
    ]
    etapas.extend(
        {
            "clave": f"propuesta_{estado}",
            "label": label,
            "total": propuesta_counts.get(estado, 0),
            "href": f"/propuestas?estado={estado}",
        }
        for estado, label in PROPUESTA_PIPELINE_ESTADOS
    )
    etapas.append(
        {
            "clave": "expediente_creado",
            "label": "Expediente creado",
            "total": scalar_safe(
                cur,
                "SELECT COUNT(*) FROM expedientes WHERE owner_user_id = ?",
                (owner_user_id,),
            ),
            "href": "/expedientes",
        }
    )
    return etapas


def cargar_tareas_operativas(cur, owner_user_id: int, filters: dict) -> list:
    condition, params = proximidad_tarea_condition(filters["periodo"])
    estado_sql = ""
    estado_params = ()
    if filters["estado"] in TAREA_ESTADOS:
        estado_sql = "AND lt.estado = ?"
        estado_params = (filters["estado"],)
    elif filters["estado"]:
        return []
    return fetchall_safe(
        cur,
        f"""
        SELECT lt.*, l.nombre AS lead_nombre
        FROM lead_tareas lt
        LEFT JOIN leads l ON l.id = lt.lead_id AND l.owner_user_id = lt.owner_user_id
        WHERE lt.owner_user_id = ?
          AND {condition}
          {estado_sql}
        ORDER BY
            CASE lt.estado WHEN 'pendiente' THEN 0 WHEN 'hecha' THEN 1 ELSE 2 END,
            lt.fecha_programada ASC,
            lt.id ASC
        LIMIT ?
        """,
        (owner_user_id,) + params + estado_params + (DASHBOARD_LIMIT,),
    )


def cargar_leads_filtrados(cur, owner_user_id: int, filters: dict) -> list:
    condition, params = periodo_condition("COALESCE(l.updated_at, l.created_at)", filters["periodo"])
    estado_sql = ""
    estado_params = ()
    if filters["estado"] in LEAD_ESTADOS:
        estado_sql = "AND l.estado = ?"
        estado_params = (filters["estado"],)
    elif filters["estado"]:
        return []
    return fetchall_safe(
        cur,
        f"""
        SELECT l.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
               MAX(lc.fecha) AS ultima_actividad
        FROM leads l
        LEFT JOIN clientes c
          ON c.id = l.cliente_id AND c.owner_user_id = l.owner_user_id
        LEFT JOIN lead_contactos lc
          ON lc.lead_id = l.id AND lc.owner_user_id = l.owner_user_id
        WHERE l.owner_user_id = ?
          AND {condition}
          {estado_sql}
        GROUP BY l.id
        ORDER BY COALESCE(MAX(lc.fecha), l.updated_at, l.created_at) DESC, l.id DESC
        LIMIT ?
        """,
        (owner_user_id,) + params + estado_params + (OPERATIVE_LIMIT,),
    )


def cargar_propuestas_filtradas(cur, owner_user_id: int, filters: dict) -> list:
    fecha_expr = "COALESCE(p.fecha_envio, p.fecha_aceptacion, p.updated_at, p.fecha)"
    condition, params = periodo_condition(fecha_expr, filters["periodo"])
    estado_sql = ""
    estado_params = ()
    if filters["estado"] in PROPUESTA_ESTADOS:
        estado_sql = "AND p.estado = ?"
        estado_params = (filters["estado"],)
    elif filters["estado"]:
        return []
    return fetchall_safe(
        cur,
        f"""
        SELECT p.*, l.nombre AS lead_nombre, c.nombre AS cliente_nombre,
               c.apellidos AS cliente_apellidos
        FROM propuestas p
        LEFT JOIN leads l ON l.id = p.lead_id AND l.owner_user_id = p.owner_user_id
        LEFT JOIN clientes c ON c.id = p.cliente_id AND c.owner_user_id = p.owner_user_id
        WHERE p.owner_user_id = ?
          AND {condition}
          {estado_sql}
        ORDER BY {fecha_expr} DESC, p.id DESC
        LIMIT ?
        """,
        (owner_user_id,) + params + estado_params + (OPERATIVE_LIMIT,),
    )


def cargar_emails_filtrados(cur, owner_user_id: int, filters: dict) -> list:
    condition, params = periodo_condition("ee.fecha_envio", filters["periodo"])
    estado_sql = ""
    estado_params = ()
    if filters["estado"] in EMAIL_ESTADOS:
        estado_sql = "AND ee.estado = ?"
        estado_params = (filters["estado"],)
    elif filters["estado"]:
        return []
    return fetchall_safe(
        cur,
        f"""
        SELECT ee.*
        FROM emails_enviados ee
        WHERE ee.owner_user_id = ?
          AND {condition}
          {estado_sql}
        ORDER BY ee.fecha_envio DESC, ee.id DESC
        LIMIT ?
        """,
        (owner_user_id,) + params + estado_params + (OPERATIVE_LIMIT,),
    )


def cargar_expedientes_filtrados(cur, owner_user_id: int, filters: dict) -> list:
    if filters["estado"]:
        return []
    return fetchall_safe(
        cur,
        """
        SELECT *
        FROM expedientes
        WHERE owner_user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (owner_user_id, OPERATIVE_LIMIT),
    )


def construir_actividad_operativa(cur, owner_user_id: int, filters: dict) -> list[dict]:
    tipo = filters["tipo"]
    actividad = []
    if tipo in {"todos", "leads"}:
        for lead in cargar_leads_filtrados(cur, owner_user_id, filters):
            actividad.append(
                {
                    "tipo": "Lead",
                    "titulo": lead["nombre"],
                    "href": f"/leads/{lead['id']}",
                    "estado": lead["estado"],
                    "fecha": lead["ultima_actividad"] or lead["updated_at"] or lead["created_at"],
                    "detalle": f"{lead['origen'] or 'Sin origen'} · {contacto_principal(lead)}",
                    "accion_href": f"/propuestas/nueva?lead_id={lead['id']}",
                    "accion_label": "Crear propuesta",
                }
            )
    if tipo in {"todos", "propuestas"}:
        for propuesta in cargar_propuestas_filtradas(cur, owner_user_id, filters):
            contacto = propuesta["lead_nombre"] or propuesta["cliente_nombre"] or "Sin contacto"
            actividad.append(
                {
                    "tipo": "Propuesta",
                    "titulo": propuesta["numero_propuesta"],
                    "href": f"/propuestas/{propuesta['id']}",
                    "estado": propuesta["estado"],
                    "fecha": propuesta["fecha_envio"] or propuesta["fecha_aceptacion"] or propuesta["fecha"],
                    "detalle": contacto,
                    "accion_href": "",
                    "accion_label": "",
                }
            )
    if tipo in {"todos", "emails"}:
        for email in cargar_emails_filtrados(cur, owner_user_id, filters):
            actividad.append(
                {
                    "tipo": "Email",
                    "titulo": email["asunto"],
                    "href": relacion_email_href(email),
                    "estado": email["estado"],
                    "fecha": email["fecha_envio"],
                    "detalle": f"{email['destinatario']} · {relacion_email(email)}",
                    "accion_href": "",
                    "accion_label": "",
                }
            )
    if tipo in {"todos", "expedientes"}:
        for expediente in cargar_expedientes_filtrados(cur, owner_user_id, filters):
            actividad.append(
                {
                    "tipo": "Expediente",
                    "titulo": expediente["numero_expediente"],
                    "href": f"/detalle-expediente/{expediente['id']}",
                    "estado": estado_expediente(expediente),
                    "fecha": "",
                    "detalle": f"{expediente['cliente']} · {expediente['direccion']}",
                    "accion_href": "",
                    "accion_label": "",
                }
            )
    return actividad[:OPERATIVE_LIMIT]


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    current_user = get_current_user(request)
    owner_user_id = current_user["id"]
    hoy = date.today().isoformat()
    year_actual, trimestre_actual = obtener_trimestre_actual()
    filters = {
        "periodo": periodo_desde_request(request),
        "tipo": tipo_desde_request(request),
        "estado": estado_desde_request(request),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        tareas_operativas = cargar_tareas_operativas(cur, owner_user_id, filters)
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
            "administradores": leads_por_origen_like(cur, owner_user_id, "%administrador%"),
            "abogados": leads_por_origen_like(cur, owner_user_id, "%abogado%"),
            "pendientes_contacto": leads_por_estados(
                cur, owner_user_id, PROSPECCION_PENDIENTE_ESTADOS
            ),
            "respondidos": leads_por_estados(
                cur, owner_user_id, PROSPECCION_RESPONDIO_ESTADOS
            ),
            "reuniones": scalar_safe(
                cur,
                """
                SELECT COUNT(DISTINCT l.id)
                FROM leads l
                LEFT JOIN lead_contactos lc
                  ON lc.lead_id = l.id AND lc.owner_user_id = l.owner_user_id
                WHERE l.owner_user_id = ?
                  AND (
                    l.estado = 'reunion'
                    OR lower(COALESCE(lc.tipo, '')) = 'reunion'
                  )
                """,
                (owner_user_id,),
            ),
            "tareas_hoy": fetchall_safe(
                cur,
                """
                SELECT lt.*, l.nombre AS lead_nombre,
                       MAX(0, CAST(julianday(DATE(?)) - julianday(DATE(lt.fecha_programada)) AS INTEGER)) AS dias_retraso
                FROM lead_tareas lt
                LEFT JOIN leads l ON l.id = lt.lead_id
                WHERE lt.owner_user_id = ?
                  AND lt.estado = 'pendiente'
                  AND DATE(lt.fecha_programada) <= DATE(?)
                ORDER BY lt.fecha_programada ASC, lt.id ASC
                LIMIT 5
                """,
                (hoy, owner_user_id, hoy),
            ),
            "seguimientos_proximos": fetchall_safe(
                cur,
                """
                SELECT lt.*, l.nombre AS lead_nombre
                FROM lead_tareas lt
                LEFT JOIN leads l ON l.id = lt.lead_id
                WHERE lt.owner_user_id = ?
                  AND lt.estado = 'pendiente'
                  AND DATE(lt.fecha_programada) > DATE(?)
                ORDER BY lt.fecha_programada ASC, lt.id ASC
                LIMIT ?
                """,
                (owner_user_id, hoy, DASHBOARD_LIMIT),
            ),
            "recientes": fetchall_safe(
                cur,
                """
                SELECT l.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos,
                       MAX(lc.fecha) AS ultima_actividad
                FROM leads l
                LEFT JOIN clientes c
                  ON c.id = l.cliente_id AND c.owner_user_id = l.owner_user_id
                LEFT JOIN lead_contactos lc
                  ON lc.lead_id = l.id AND lc.owner_user_id = l.owner_user_id
                WHERE l.owner_user_id = ?
                GROUP BY l.id
                ORDER BY COALESCE(MAX(lc.fecha), l.updated_at, l.created_at) DESC, l.id DESC
                LIMIT ?
                """,
                (owner_user_id, DASHBOARD_LIMIT),
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
            "pendientes": fetchall_safe(
                cur,
                """
                SELECT p.*, l.nombre AS lead_nombre, c.nombre AS cliente_nombre,
                       c.apellidos AS cliente_apellidos
                FROM propuestas p
                LEFT JOIN leads l ON l.id = p.lead_id AND l.owner_user_id = p.owner_user_id
                LEFT JOIN clientes c ON c.id = p.cliente_id AND c.owner_user_id = p.owner_user_id
                WHERE p.owner_user_id = ?
                  AND (
                    p.estado IN ('borrador', 'enviada')
                    OR (p.estado = 'aceptada' AND p.expediente_id IS NULL)
                  )
                ORDER BY COALESCE(p.fecha_envio, p.fecha_aceptacion, p.updated_at, p.fecha) DESC, p.id DESC
                LIMIT ?
                """,
                (owner_user_id, DASHBOARD_LIMIT),
            ),
        }

        emails = {
            "recientes": fetchall_safe(
                cur,
                """
                SELECT *
                FROM emails_enviados
                WHERE owner_user_id = ?
                ORDER BY fecha_envio DESC, id DESC
                LIMIT ?
                """,
                (owner_user_id, DASHBOARD_LIMIT),
            )
        }

        campanas = {
            "prescriptores": fetchall_safe(
                cur,
                """
                SELECT l.*, c.nombre AS cliente_nombre, c.apellidos AS cliente_apellidos
                FROM leads l
                LEFT JOIN clientes c
                  ON c.id = l.cliente_id AND c.owner_user_id = l.owner_user_id
                WHERE l.owner_user_id = ?
                  AND (
                    lower(COALESCE(l.origen, '')) LIKE '%abogado%'
                    OR lower(COALESCE(l.origen, '')) LIKE '%administrador%'
                    OR lower(COALESCE(l.notas, '')) LIKE '%abogado%'
                    OR lower(COALESCE(l.notas, '')) LIKE '%administrador%'
                  )
                ORDER BY COALESCE(l.updated_at, l.created_at) DESC, l.id DESC
                LIMIT ?
                """,
                (owner_user_id, DASHBOARD_LIMIT),
            )
        }

        pipeline = construir_pipeline(cur, owner_user_id)
        actividad_operativa = construir_actividad_operativa(cur, owner_user_id, filters)

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

    return render_template(
        request,
        "dashboard.html",
        {
            "leads": leads,
            "propuestas": propuestas,
            "emails": emails,
            "campanas": campanas,
            "pipeline": pipeline,
            "actividad_operativa": actividad_operativa,
            "tareas_operativas": tareas_operativas,
            "filters": filters,
            "periodo_options": PERIODO_OPTIONS,
            "tipo_options": TIPO_OPTIONS,
            "estado_options": estado_options_para_tipo(filters["tipo"]),
            "expedientes": expedientes,
            "facturas_borrador": facturas_borrador,
            "facturas_pendientes": facturas_pendientes,
            "total_pendiente": total_pendiente,
            "resumen_iva": resumen_iva,
            "year_actual": year_actual,
            "trimestre_actual": trimestre_actual,
            "gastos_ultimos": gastos_ultimos,
            "format_money": format_money,
            "nombre_cliente": nombre_cliente,
            "label_estado": label_estado,
            "estado_badge_class": estado_badge_class,
            "contacto_principal": contacto_principal,
            "relacion_email": relacion_email,
            "relacion_email_href": relacion_email_href,
            "estado_expediente": estado_expediente,
            "filtro_query": filtro_query,
        },
    )
