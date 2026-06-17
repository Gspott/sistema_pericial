from datetime import date, datetime, timedelta
import re
from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection
from app.services import email_sender
from app.services.email_log import registrar_email_enviado
from app.services.email_sender import crear_mensaje_email, enviar_mensaje_email
from app.services.email_templates import construir_email_html_base, construir_firma_texto, contexto_identidad_email, texto_a_html
from app.services.crm_templates import (
    construir_email_comercial,
    obtener_plantilla_comercial,
    plantilla_para_tipo,
    plantilla_seguimiento_para_tipo,
    plantillas_disponibles,
    renderizar_plantilla_comercial,
    variables_para_lead,
)

router = APIRouter()

TIPOS_LEAD = (
    ("administrador_fincas", "Administrador de fincas"),
    ("abogado", "Abogado"),
    ("particular", "Particular"),
    ("comunidad", "Comunidad"),
    ("empresa", "Empresa"),
    ("aseguradora", "Aseguradora"),
    ("otros", "Otros"),
)
TIPOS_LEAD_LABELS = dict(TIPOS_LEAD)
LEAD_ESTADOS = (
    "nuevo",
    "contactado",
    "pendiente_respuesta",
    "seguimiento_enviado",
    "propuesta_enviada",
    "aceptado",
    "rechazado",
    "cerrado",
)
EMAIL_FILTROS = ("con_email", "sin_email")
SEGUIMIENTO_PRESENTACION_TIPO = "seguimiento_presentacion"
SEGUIMIENTO_PRESENTACION_TITULO = "Seguimiento presentación comercial"
REVISION_POST_SEGUIMIENTO_TIPO = "revision_post_seguimiento"
REVISION_POST_SEGUIMIENTO_TITULO = "Revisión tras seguimiento comercial"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_PROGRAMADO_ESTADO = "programado"
EMAIL_CANCELADO_ESTADO = "cancelado"


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


def _email_valido(valor: str) -> bool:
    return not valor or bool(EMAIL_RE.match(valor))


def _normalizar_tipo(tipo: str) -> str:
    tipo_limpio = limpiar_texto(tipo)
    return tipo_limpio if tipo_limpio in TIPOS_LEAD_LABELS else "otros"


def _extraer_metadata(notas: str | None, clave: str) -> str:
    prefijo = f"{clave}:"
    for linea in (notas or "").splitlines():
        if linea.lower().startswith(prefijo.lower()):
            return limpiar_texto(linea.split(":", 1)[1])
    return ""


def _componer_notas_lead(persona_contacto: str, localidad: str, tipo_profesion: str, notas: str) -> str:
    bloques = []
    if persona_contacto:
        bloques.append(f"Persona de contacto: {persona_contacto}")
    if localidad:
        bloques.append(f"Localidad: {localidad}")
    if tipo_profesion:
        bloques.append(f"Tipo/profesión: {TIPOS_LEAD_LABELS.get(tipo_profesion, tipo_profesion)}")
    if notas:
        bloques.append(notas)
    return "\n".join(bloques)


def _redirect_workbench(mensaje: str = "", error: str = "", lead_id: int | None = None, **extra) -> RedirectResponse:
    params = {clave: valor for clave, valor in extra.items() if limpiar_texto(str(valor))}
    if mensaje:
        params["mensaje"] = mensaje
    if error:
        params["error"] = error
    if lead_id:
        params["lead_id"] = str(lead_id)
    qs = urlencode(params)
    url = "/crm/prospeccion"
    if qs:
        url = f"{url}?{qs}"
    return RedirectResponse(url=url, status_code=303)


def _redirect_agenda(mensaje: str = "", error: str = "", email_id: int | None = None) -> RedirectResponse:
    params = {}
    if mensaje:
        params["mensaje"] = mensaje
    if error:
        params["error"] = error
    if email_id:
        params["email_id"] = str(email_id)
    qs = urlencode(params)
    url = "/crm/prospeccion/agenda"
    if qs:
        url = f"{url}?{qs}"
    return RedirectResponse(url=url, status_code=303)


def _extraer_valor_error_mensaje(error_mensaje: str | None, clave: str) -> str:
    prefijo = f"{clave}="
    for parte in (error_mensaje or "").split(";"):
        parte_limpia = parte.strip()
        if parte_limpia.startswith(prefijo):
            return limpiar_texto(parte_limpia[len(prefijo) :])
    return ""


def _metadata_programado(fecha_programada: str, plantilla_slug: str = "", extra: str = "") -> str:
    partes = [f"programado_para={limpiar_texto(fecha_programada)}"]
    if plantilla_slug:
        partes.append(f"plantilla={limpiar_texto(plantilla_slug)}")
    if extra:
        partes.append(limpiar_texto(extra))
    return "; ".join(partes)


def _texto_busqueda(lead) -> str:
    return " ".join(
        limpiar_texto(lead[campo]).lower()
        for campo in ("nombre", "origen", "servicio_solicitado", "mensaje", "notas")
        if campo in lead.keys()
    )


def inferir_tipo_lead(lead) -> str:
    texto = _texto_busqueda(lead)
    if any(patron in texto for patron in ("administrador de fincas", "administradora de fincas", "administradores de fincas")):
        return "administrador_fincas"
    if "administrador" in texto and "finca" in texto:
        return "administrador_fincas"
    if "abogado" in texto or "abogada" in texto or "despacho" in texto:
        return "abogado"
    if "aseguradora" in texto or "seguro" in texto or "compañia" in texto or "compania" in texto:
        return "aseguradora"
    if "comunidad" in texto or "comunidades" in texto or "propietarios" in texto:
        return "comunidad"
    if "empresa" in texto or "sociedad" in texto or "sl" in texto or "s.l" in texto:
        return "empresa"
    if "particular" in texto or "vivienda" in texto:
        return "particular"
    return "otros"


def _contiene_localidad(lead, localidad: str) -> bool:
    localidad_limpia = limpiar_texto(localidad).lower()
    if not localidad_limpia:
        return True
    return localidad_limpia in _texto_busqueda(lead)


def _sin_accion_comercial(lead) -> bool:
    return (lead["contactos_count"] or 0) == 0 and (lead["emails_enviados_count"] or 0) == 0


def _seguimiento_pendiente(lead) -> bool:
    return bool(lead["proxima_tarea_titulo"])


def _ultima_accion(lead) -> str:
    if lead["ultimo_email_fecha"] and lead["ultimo_contacto_fecha"]:
        return max(lead["ultimo_email_fecha"], lead["ultimo_contacto_fecha"])
    return lead["ultimo_email_fecha"] or lead["ultimo_contacto_fecha"] or ""


def _lead_view(lead) -> dict:
    tipo = inferir_tipo_lead(lead)
    plantilla = plantilla_para_tipo(tipo)
    plantilla_seguimiento = plantilla_seguimiento_para_tipo(tipo)
    tiene_presentacion_enviada = (lead["emails_presentacion_count"] or 0) > 0
    tiene_seguimiento_pendiente = bool(lead["seguimiento_tarea_id"])
    persona_contacto = _extraer_metadata(lead["notas"], "Persona de contacto") or lead["nombre"]
    localidad = _extraer_metadata(lead["notas"], "Localidad")
    proxima_tarea_fecha = lead["proxima_tarea_fecha"]
    return {
        "id": lead["id"],
        "nombre": lead["nombre"],
        "persona_contacto": persona_contacto,
        "tipo": tipo,
        "tipo_label": TIPOS_LEAD_LABELS[tipo],
        "email": lead["email"],
        "telefono": lead["telefono"],
        "localidad": localidad,
        "fuente": lead["origen"],
        "estado": lead["estado"],
        "prioridad": lead["prioridad"],
        "sin_accion": _sin_accion_comercial(lead),
        "ultima_accion": _ultima_accion(lead),
        "proxima_tarea": lead["proxima_tarea_titulo"],
        "proxima_tarea_fecha": proxima_tarea_fecha,
        "seguimiento_tarea_id": lead["seguimiento_tarea_id"],
        "tiene_seguimiento_pendiente": tiene_seguimiento_pendiente,
        "tiene_presentacion_enviada": tiene_presentacion_enviada,
        "puede_enviar_seguimiento": tiene_seguimiento_pendiente or tiene_presentacion_enviada,
        "propuestas_enviadas": lead["propuestas_enviadas"] or 0,
        "emails_programados": lead["emails_programados_count"] or 0,
        "seguimiento_vencido": bool(proxima_tarea_fecha and proxima_tarea_fecha <= date.today().isoformat()),
        "plantilla_presentacion": plantilla.nombre,
        "plantilla_seguimiento": plantilla_seguimiento.nombre,
    }


def _query_string(filtros: dict, **overrides) -> str:
    valores = {**filtros, **overrides}
    return urlencode({clave: valor for clave, valor in valores.items() if limpiar_texto(str(valor))})


def _obtener_leads_workbench(cur, owner_user_id: int):
    return cur.execute(
        """
        SELECT l.*,
               (
                   SELECT COUNT(*)
                   FROM lead_contactos lc
                   WHERE lc.lead_id = l.id AND lc.owner_user_id = l.owner_user_id
               ) AS contactos_count,
               (
                   SELECT COUNT(*)
                   FROM emails_enviados ee
                   WHERE ee.owner_user_id = l.owner_user_id
                     AND ee.estado = 'enviado'
                     AND (
                         (ee.referencia_entidad_tipo = 'lead' AND ee.referencia_entidad_id = l.id)
                         OR (l.email IS NOT NULL AND l.email <> '' AND lower(ee.destinatario) = lower(l.email))
                     )
               ) AS emails_enviados_count,
               (
                   SELECT COUNT(*)
                   FROM emails_enviados ee
                   WHERE ee.owner_user_id = l.owner_user_id
                     AND ee.estado = 'enviado'
                     AND ee.tipo = 'presentacion_comercial'
                     AND ee.referencia_entidad_tipo = 'lead'
                     AND ee.referencia_entidad_id = l.id
               ) AS emails_presentacion_count,
               (
                   SELECT COUNT(*)
                   FROM emails_enviados ee
                   WHERE ee.owner_user_id = l.owner_user_id
                     AND ee.estado = 'programado'
                     AND ee.referencia_entidad_tipo = 'lead'
                     AND ee.referencia_entidad_id = l.id
               ) AS emails_programados_count,
               (
                   SELECT MAX(fecha)
                   FROM lead_contactos lc
                   WHERE lc.lead_id = l.id AND lc.owner_user_id = l.owner_user_id
               ) AS ultimo_contacto_fecha,
               (
                   SELECT MAX(fecha_envio)
                   FROM emails_enviados ee
                   WHERE ee.owner_user_id = l.owner_user_id
                     AND (
                         (ee.referencia_entidad_tipo = 'lead' AND ee.referencia_entidad_id = l.id)
                         OR (l.email IS NOT NULL AND l.email <> '' AND lower(ee.destinatario) = lower(l.email))
                     )
               ) AS ultimo_email_fecha,
               (
                   SELECT lt.titulo
                   FROM lead_tareas lt
                   WHERE lt.lead_id = l.id
                     AND lt.owner_user_id = l.owner_user_id
                     AND lt.estado = 'pendiente'
                   ORDER BY COALESCE(lt.fecha_programada, '') ASC, lt.id ASC
                   LIMIT 1
               ) AS proxima_tarea_titulo,
               (
                   SELECT lt.fecha_programada
                   FROM lead_tareas lt
                   WHERE lt.lead_id = l.id
                     AND lt.owner_user_id = l.owner_user_id
                     AND lt.estado = 'pendiente'
                   ORDER BY COALESCE(lt.fecha_programada, '') ASC, lt.id ASC
                   LIMIT 1
               ) AS proxima_tarea_fecha,
               (
                   SELECT lt.id
                   FROM lead_tareas lt
                   WHERE lt.lead_id = l.id
                     AND lt.owner_user_id = l.owner_user_id
                     AND lt.estado = 'pendiente'
                     AND lt.tipo = 'seguimiento_presentacion'
                   ORDER BY COALESCE(lt.fecha_programada, '') ASC, lt.id ASC
                   LIMIT 1
               ) AS seguimiento_tarea_id,
               (
                   SELECT COUNT(*)
                   FROM propuestas p
                   WHERE p.lead_id = l.id
                     AND p.owner_user_id = l.owner_user_id
                     AND p.estado = 'enviada'
               ) AS propuestas_enviadas
        FROM leads l
        WHERE l.owner_user_id = ?
        ORDER BY
            CASE COALESCE(l.prioridad, '')
                WHEN 'alta' THEN 0
                WHEN 'media' THEN 1
                WHEN 'baja' THEN 2
                ELSE 3
            END,
            l.id DESC
        """,
        (owner_user_id,),
    ).fetchall()


def _aplicar_filtros(leads, filtros: dict):
    resultado = []
    for lead in leads:
        tipo = inferir_tipo_lead(lead)
        if filtros["tipo"] and filtros["tipo"] != tipo:
            continue
        if filtros["estado"] and filtros["estado"] != lead["estado"]:
            continue
        if filtros["email"] == "con_email" and not limpiar_texto(lead["email"]):
            continue
        if filtros["email"] == "sin_email" and limpiar_texto(lead["email"]):
            continue
        if filtros["sin_accion"] and not _sin_accion_comercial(lead):
            continue
        if filtros["seguimiento"] and not _seguimiento_pendiente(lead):
            continue
        if filtros["localidad"] and not _contiene_localidad(lead, filtros["localidad"]):
            continue
        if filtros["fuente"] and filtros["fuente"].lower() not in limpiar_texto(lead["origen"]).lower():
            continue
        resultado.append(lead)
    return resultado


def _metricas(leads) -> dict:
    return {
        "total": len(leads),
        "administradores": sum(1 for lead in leads if inferir_tipo_lead(lead) == "administrador_fincas"),
        "sin_accion": sum(1 for lead in leads if _sin_accion_comercial(lead)),
        "presentacion_enviada": sum(1 for lead in leads if (lead["emails_enviados_count"] or 0) > 0),
        "seguimientos": sum(1 for lead in leads if _seguimiento_pendiente(lead)),
        "propuestas_enviadas": sum(int(lead["propuestas_enviadas"] or 0) for lead in leads),
    }


def _acciones_prioritarias(leads) -> dict:
    hoy = date.today().isoformat()
    return {
        "admins_sin_accion": sum(
            1 for lead in leads if inferir_tipo_lead(lead) == "administrador_fincas" and _sin_accion_comercial(lead)
        ),
        "seguimiento_vencido": sum(
            1 for lead in leads if lead["proxima_tarea_fecha"] and lead["proxima_tarea_fecha"] <= hoy
        ),
        "presentacion_sin_respuesta": sum(
            1
            for lead in leads
            if (lead["emails_presentacion_count"] or 0) > 0 and lead["estado"] == "pendiente_respuesta"
        ),
        "sin_email": sum(1 for lead in leads if not limpiar_texto(lead["email"])),
        "pendientes_revisar": sum(
            1 for lead in leads if lead["estado"] in {"nuevo", "pendiente_respuesta", "seguimiento_enviado"}
        ),
    }


def _plantillas_para_tipo(tipo: str):
    disponibles = [
        plantilla
        for plantilla in plantillas_disponibles()
        if plantilla.tipo_lead == tipo or plantilla.tipo_lead == "administrador_fincas"
    ]
    return disponibles or [plantilla_para_tipo(tipo)]


def _plantilla_panel(slug: str, tipo: str):
    plantilla = obtener_plantilla_comercial(slug) if slug else None
    if plantilla:
        return plantilla
    return plantilla_para_tipo(tipo)


def _renderizar_preview_email(lead, current_user, slug: str = "") -> dict:
    tipo = inferir_tipo_lead(lead)
    plantilla = _plantilla_panel(slug, tipo)
    variables = variables_para_lead(lead, current_user)
    variables.update(
        {
            "nombre_contacto": _extraer_metadata(lead["notas"], "Persona de contacto")
            or limpiar_texto(lead["nombre"])
            or variables["nombre_contacto"],
            "empresa": limpiar_texto(lead["nombre"]) or variables["empresa"],
            "localidad": _extraer_metadata(lead["notas"], "Localidad"),
        }
    )
    asunto, cuerpo = renderizar_plantilla_comercial(plantilla, variables)
    return {
        "plantilla": plantilla,
        "asunto": asunto,
        "cuerpo": cuerpo,
    }


def _historial_lead(cur, lead_id: int, owner_user_id: int) -> dict:
    emails = cur.execute(
        """
        SELECT fecha_envio, tipo, asunto, estado, error_mensaje
        FROM emails_enviados
        WHERE referencia_entidad_tipo = 'lead'
          AND referencia_entidad_id = ?
          AND owner_user_id = ?
        ORDER BY fecha_envio DESC, id DESC
        LIMIT 5
        """,
        (lead_id, owner_user_id),
    ).fetchall()
    contactos = cur.execute(
        """
        SELECT fecha, tipo, resumen, resultado
        FROM lead_contactos
        WHERE lead_id = ? AND owner_user_id = ?
        ORDER BY fecha DESC, id DESC
        LIMIT 5
        """,
        (lead_id, owner_user_id),
    ).fetchall()
    tareas = cur.execute(
        """
        SELECT titulo, tipo, fecha_programada, estado
        FROM lead_tareas
        WHERE lead_id = ? AND owner_user_id = ?
        ORDER BY COALESCE(fecha_programada, '') ASC, id DESC
        LIMIT 5
        """,
        (lead_id, owner_user_id),
    ).fetchall()
    return {"emails": emails, "contactos": contactos, "tareas": tareas}


def _obtener_emails_programados(cur, owner_user_id: int):
    return cur.execute(
        """
        SELECT ee.*,
               l.nombre AS lead_nombre,
               l.email AS lead_email,
               l.telefono AS lead_telefono,
               l.origen AS lead_origen,
               l.servicio_solicitado AS lead_servicio_solicitado,
               l.estado AS lead_estado,
               l.notas AS lead_notas
        FROM emails_enviados ee
        LEFT JOIN leads l
          ON l.id = ee.referencia_entidad_id
         AND ee.referencia_entidad_tipo = 'lead'
         AND l.owner_user_id = ee.owner_user_id
        WHERE ee.owner_user_id = ?
          AND ee.estado = ?
        ORDER BY
          COALESCE(
            NULLIF(
              substr(
                ee.error_mensaje,
                instr(ee.error_mensaje, 'programado_para=') + length('programado_para='),
                16
              ),
              ''
            ),
            ee.fecha_envio
          ) ASC,
          ee.id ASC
        """,
        (owner_user_id, EMAIL_PROGRAMADO_ESTADO),
    ).fetchall()


def _get_owned_email_programado(cur, email_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT ee.*,
               l.nombre AS lead_nombre,
               l.email AS lead_email,
               l.telefono AS lead_telefono,
               l.origen AS lead_origen,
               l.servicio_solicitado AS lead_servicio_solicitado,
               l.estado AS lead_estado,
               l.notas AS lead_notas
        FROM emails_enviados ee
        LEFT JOIN leads l
          ON l.id = ee.referencia_entidad_id
         AND ee.referencia_entidad_tipo = 'lead'
         AND l.owner_user_id = ee.owner_user_id
        WHERE ee.id = ?
          AND ee.owner_user_id = ?
        """,
        (email_id, owner_user_id),
    ).fetchone()


def _email_programado_view(email) -> dict:
    plantilla_slug = _extraer_valor_error_mensaje(email["error_mensaje"], "plantilla")
    fecha_programada = _extraer_valor_error_mensaje(email["error_mensaje"], "programado_para")
    plantilla = obtener_plantilla_comercial(plantilla_slug) if plantilla_slug else None
    return {
        "id": email["id"],
        "destinatario": email["destinatario"],
        "lead_id": email["referencia_entidad_id"] if email["referencia_entidad_tipo"] == "lead" else None,
        "lead_nombre": email["lead_nombre"] or "",
        "lead_email": email["lead_email"] or "",
        "lead_telefono": email["lead_telefono"] or "",
        "lead_estado": email["lead_estado"] or "",
        "lead_notas": email["lead_notas"] or "",
        "plantilla_slug": plantilla_slug,
        "plantilla_nombre": plantilla.nombre if plantilla else plantilla_slug,
        "tipo": email["tipo"],
        "asunto": email["asunto"],
        "cuerpo": email["cuerpo_texto"] or "",
        "fecha_programada": fecha_programada,
        "estado": email["estado"],
        "tiene_destinatario": bool(limpiar_texto(email["destinatario"])),
        "tiene_lead": bool(email["referencia_entidad_tipo"] == "lead" and email["referencia_entidad_id"] and email["lead_nombre"]),
        "es_seguimiento": _email_programado_es_seguimiento(email),
    }


def _email_programado_es_seguimiento(email) -> bool:
    plantilla_slug = _extraer_valor_error_mensaje(email["error_mensaje"], "plantilla")
    return limpiar_texto(email["tipo"]).startswith("seguimiento_") or _es_plantilla_seguimiento(plantilla_slug)


def _tipo_confirmado_desde_programado(email) -> str:
    return "seguimiento_comercial" if _email_programado_es_seguimiento(email) else "presentacion_comercial"


def _aplicar_estado_post_envio_programado(cur, email, owner_user_id: int) -> None:
    lead_id = email["referencia_entidad_id"] if email["referencia_entidad_tipo"] == "lead" else None
    if not lead_id:
        return
    lead = _get_owned_lead(cur, lead_id, owner_user_id)
    if not lead:
        return
    if _email_programado_es_seguimiento(email):
        tarea_seguimiento = _get_tarea_seguimiento_pendiente(cur, lead_id, owner_user_id)
        _registrar_contacto_email(
            cur,
            lead_id,
            owner_user_id,
            "Email programado de seguimiento confirmado y enviado.",
            "Seguimiento enviado",
            "Revisión comercial en 30 días.",
        )
        if tarea_seguimiento:
            _marcar_tarea_hecha(cur, tarea_seguimiento["id"], lead_id, owner_user_id)
        _crear_tarea_revision_post_seguimiento_si_no_existe(cur, lead_id, owner_user_id)
        nuevo_estado = "seguimiento_enviado"
    else:
        _registrar_contacto_presentacion(cur, lead_id, owner_user_id)
        _crear_tarea_seguimiento_si_no_existe(cur, lead_id, owner_user_id)
        nuevo_estado = "pendiente_respuesta"
    cur.execute(
        """
        UPDATE leads
        SET estado = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND owner_user_id = ?
        """,
        (nuevo_estado, lead_id, owner_user_id),
    )


def _get_owned_lead(cur, lead_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM leads
        WHERE id = ? AND owner_user_id = ?
        """,
        (lead_id, owner_user_id),
    ).fetchone()


def _crear_tarea_seguimiento_si_no_existe(cur, lead_id: int, owner_user_id: int) -> bool:
    existente = cur.execute(
        """
        SELECT id
        FROM lead_tareas
        WHERE lead_id = ?
          AND owner_user_id = ?
          AND estado = 'pendiente'
          AND tipo = ?
        LIMIT 1
        """,
        (lead_id, owner_user_id, SEGUIMIENTO_PRESENTACION_TIPO),
    ).fetchone()
    if existente:
        return False

    fecha_programada = (date.today() + timedelta(days=10)).isoformat()
    cur.execute(
        """
        INSERT INTO lead_tareas (
            lead_id, titulo, tipo, fecha_programada, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            SEGUIMIENTO_PRESENTACION_TITULO,
            SEGUIMIENTO_PRESENTACION_TIPO,
            fecha_programada,
            "Seguimiento automático tras presentación comercial.",
            owner_user_id,
        ),
    )
    return True


def _crear_tarea_revision_post_seguimiento_si_no_existe(cur, lead_id: int, owner_user_id: int) -> bool:
    existente = cur.execute(
        """
        SELECT id
        FROM lead_tareas
        WHERE lead_id = ?
          AND owner_user_id = ?
          AND estado = 'pendiente'
          AND tipo = ?
        LIMIT 1
        """,
        (lead_id, owner_user_id, REVISION_POST_SEGUIMIENTO_TIPO),
    ).fetchone()
    if existente:
        return False

    fecha_programada = (date.today() + timedelta(days=30)).isoformat()
    cur.execute(
        """
        INSERT INTO lead_tareas (
            lead_id, titulo, tipo, fecha_programada, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            REVISION_POST_SEGUIMIENTO_TITULO,
            REVISION_POST_SEGUIMIENTO_TIPO,
            fecha_programada,
            "Revisión automática tras email de seguimiento comercial.",
            owner_user_id,
        ),
    )
    return True


def _get_tarea_seguimiento_pendiente(cur, lead_id: int, owner_user_id: int):
    return cur.execute(
        """
        SELECT *
        FROM lead_tareas
        WHERE lead_id = ?
          AND owner_user_id = ?
          AND estado = 'pendiente'
          AND tipo = ?
        ORDER BY COALESCE(fecha_programada, '') ASC, id ASC
        LIMIT 1
        """,
        (lead_id, owner_user_id, SEGUIMIENTO_PRESENTACION_TIPO),
    ).fetchone()


def _marcar_tarea_hecha(cur, tarea_id: int, lead_id: int, owner_user_id: int) -> None:
    cur.execute(
        """
        UPDATE lead_tareas
        SET estado = 'hecha', completed_at = CURRENT_TIMESTAMP
        WHERE id = ? AND lead_id = ? AND owner_user_id = ?
        """,
        (tarea_id, lead_id, owner_user_id),
    )


def _registrar_contacto_presentacion(cur, lead_id: int, owner_user_id: int) -> None:
    cur.execute(
        """
        INSERT INTO lead_contactos (
            lead_id, fecha, tipo, resumen, resultado, siguiente_accion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "email",
            "Presentación comercial enviada.",
            "Pendiente de respuesta",
            "Seguimiento en 10 días.",
            owner_user_id,
        ),
    )


def _registrar_contacto_email(
    cur,
    lead_id: int,
    owner_user_id: int,
    resumen: str,
    resultado: str,
    siguiente_accion: str,
) -> None:
    cur.execute(
        """
        INSERT INTO lead_contactos (
            lead_id, fecha, tipo, resumen, resultado, siguiente_accion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead_id,
            datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "email",
            resumen,
            resultado,
            siguiente_accion,
            owner_user_id,
        ),
    )


def _preparar_mensaje_comercial(destinatario: str, tipo_lead: str, lead, current_user, proposito: str):
    email_comercial = construir_email_comercial(tipo_lead, lead, current_user, proposito=proposito)
    plantilla = email_comercial["plantilla"]
    asunto = email_comercial["asunto"]
    cuerpo = email_comercial["cuerpo"]
    body_html = construir_email_html_base(asunto, texto_a_html(cuerpo), footer_text="")
    mensaje_email = crear_mensaje_email(destinatario, asunto, _cuerpo_texto_salida(cuerpo), body_html)
    return plantilla, asunto, cuerpo, mensaje_email


def _cuerpo_texto_salida(cuerpo: str) -> str:
    return "\n\n".join([limpiar_texto(cuerpo), construir_firma_texto()])


def _identidad_email_preview() -> dict:
    return contexto_identidad_email(email_sender.SMTP_FROM_NAME, email_sender.SMTP_FROM_EMAIL)


def _es_plantilla_seguimiento(slug: str) -> bool:
    plantilla = obtener_plantilla_comercial(slug)
    return bool(plantilla and plantilla.slug.startswith("seguimiento_"))


@router.get("/crm/prospeccion", response_class=HTMLResponse)
def prospeccion_workbench(
    request: Request,
    lead_id: int = Query(0),
    plantilla: str = Query("", max_length=80),
    tipo: str = Query("", max_length=40),
    estado: str = Query("", max_length=40),
    email: str = Query("", max_length=20),
    sin_accion: int = Query(0),
    seguimiento: int = Query(0),
    localidad: str = Query("", max_length=80),
    fuente: str = Query("", max_length=80),
    mensaje: str = Query("", max_length=160),
    error: str = Query("", max_length=160),
):
    current_user = get_current_user(request)
    filtros = {
        "tipo": tipo if tipo in TIPOS_LEAD_LABELS else "",
        "estado": estado if estado in LEAD_ESTADOS else "",
        "email": email if email in EMAIL_FILTROS else "",
        "sin_accion": 1 if sin_accion else 0,
        "seguimiento": 1 if seguimiento else 0,
        "localidad": limpiar_texto(localidad),
        "fuente": limpiar_texto(fuente),
    }

    conn = get_connection()
    cur = conn.cursor()
    try:
        leads_base = _obtener_leads_workbench(cur, current_user["id"])
    finally:
        conn.close()

    leads_filtrados = _aplicar_filtros(leads_base, filtros)
    selected_row = None
    if lead_id:
        selected_row = next((lead for lead in leads_base if lead["id"] == lead_id), None)
    if selected_row is None and leads_filtrados:
        selected_row = leads_filtrados[0]

    selected_lead = _lead_view(selected_row) if selected_row else None
    preview_email = _renderizar_preview_email(selected_row, current_user, plantilla) if selected_row else None
    plantillas_panel = _plantillas_para_tipo(inferir_tipo_lead(selected_row)) if selected_row else []

    conn = get_connection()
    cur = conn.cursor()
    try:
        historial = _historial_lead(cur, selected_row["id"], current_user["id"]) if selected_row else None
    finally:
        conn.close()

    return render_template(
        request,
        "crm/prospeccion.html",
        {
            "leads": [_lead_view(lead) for lead in leads_filtrados],
            "metricas": _metricas(leads_base),
            "acciones_prioritarias": _acciones_prioritarias(leads_base),
            "selected_lead": selected_lead,
            "preview_email": preview_email,
            "plantillas_panel": plantillas_panel,
            "plantilla_actual": preview_email["plantilla"].slug if preview_email else "",
            "historial": historial,
            "email_identidad": _identidad_email_preview(),
            "tipos_lead": TIPOS_LEAD,
            "estados_lead": LEAD_ESTADOS,
            "email_filtros": EMAIL_FILTROS,
            "filtros": filtros,
            "lead_id": selected_row["id"] if selected_row else 0,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
            "query_string": _query_string,
        },
    )


@router.get("/crm/prospeccion/agenda", response_class=HTMLResponse)
def prospeccion_agenda(
    request: Request,
    email_id: int = Query(0),
    mensaje: str = Query("", max_length=160),
    error: str = Query("", max_length=160),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        programados = _obtener_emails_programados(cur, current_user["id"])
        selected_row = None
        if email_id:
            selected_row = _get_owned_email_programado(cur, email_id, current_user["id"])
        if selected_row is None and programados:
            selected_row = programados[0]
        selected_email = _email_programado_view(selected_row) if selected_row else None
        historial = (
            _historial_lead(cur, selected_row["referencia_entidad_id"], current_user["id"])
            if selected_row
            and selected_row["referencia_entidad_tipo"] == "lead"
            and selected_row["referencia_entidad_id"]
            else None
        )
    finally:
        conn.close()

    return render_template(
        request,
        "crm/prospeccion_agenda.html",
        {
            "programados": [_email_programado_view(email) for email in programados],
            "selected_email": selected_email,
            "historial": historial,
            "mensaje": limpiar_texto(mensaje),
            "error": limpiar_texto(error),
        },
    )


@router.post("/crm/prospeccion/agenda/{email_id}/confirmar")
def confirmar_email_programado(
    request: Request,
    email_id: int,
    asunto: str = Form(...),
    cuerpo: str = Form(...),
):
    current_user = get_current_user(request)
    asunto_limpio = limpiar_texto(asunto)
    cuerpo_limpio = limpiar_texto(cuerpo)
    if not asunto_limpio or not cuerpo_limpio:
        return _redirect_agenda(error="Asunto y cuerpo son obligatorios para confirmar.", email_id=email_id)

    conn = get_connection()
    cur = conn.cursor()
    try:
        email_programado = _get_owned_email_programado(cur, email_id, current_user["id"])
        if not email_programado:
            raise HTTPException(status_code=404, detail="Email programado no encontrado")
        if email_programado["estado"] != EMAIL_PROGRAMADO_ESTADO:
            return _redirect_agenda(error="Este email ya no esta programado.", email_id=email_id)
        destinatario = limpiar_texto(email_programado["destinatario"])
        if not destinatario:
            return _redirect_agenda(error="El email programado no tiene destinatario.", email_id=email_id)
        if not _email_valido(destinatario):
            return _redirect_agenda(error="El destinatario no tiene un formato valido.", email_id=email_id)

        body_html = construir_email_html_base(asunto_limpio, texto_a_html(cuerpo_limpio), footer_text="")
        mensaje_email = crear_mensaje_email(destinatario, asunto_limpio, _cuerpo_texto_salida(cuerpo_limpio), body_html)
        tipo_confirmado = _tipo_confirmado_desde_programado(email_programado)
        enviar_mensaje_email(
            mensaje_email,
            contexto=f"agenda {tipo_confirmado} email_programado {email_id}",
        )
        cur.execute(
            """
            UPDATE emails_enviados
            SET estado = 'enviado',
                tipo = ?,
                asunto = ?,
                cuerpo_texto = ?,
                error_mensaje = NULL,
                fecha_envio = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ? AND estado = ?
            """,
            (
                tipo_confirmado,
                asunto_limpio,
                cuerpo_limpio,
                email_id,
                current_user["id"],
                EMAIL_PROGRAMADO_ESTADO,
            ),
        )
        _aplicar_estado_post_envio_programado(cur, email_programado, current_user["id"])
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except RuntimeError:
        conn.rollback()
        return _redirect_agenda(error="No esta configurado el envio de email.", email_id=email_id)
    except Exception:
        conn.rollback()
        return _redirect_agenda(error="No se pudo confirmar el envio programado.", email_id=email_id)
    finally:
        conn.close()

    return _redirect_agenda(mensaje="Email programado confirmado y enviado.")


@router.post("/crm/prospeccion/agenda/{email_id}/cancelar")
def cancelar_email_programado(request: Request, email_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        email_programado = _get_owned_email_programado(cur, email_id, current_user["id"])
        if not email_programado:
            raise HTTPException(status_code=404, detail="Email programado no encontrado")
        if email_programado["estado"] != EMAIL_PROGRAMADO_ESTADO:
            return _redirect_agenda(error="Este email ya no esta programado.", email_id=email_id)
        plantilla_slug = _extraer_valor_error_mensaje(email_programado["error_mensaje"], "plantilla")
        fecha_programada = _extraer_valor_error_mensaje(email_programado["error_mensaje"], "programado_para")
        cur.execute(
            """
            UPDATE emails_enviados
            SET estado = ?,
                error_mensaje = ?
            WHERE id = ? AND owner_user_id = ? AND estado = ?
            """,
            (
                EMAIL_CANCELADO_ESTADO,
                _metadata_programado(fecha_programada, plantilla_slug, f"cancelado_en={datetime.now().strftime('%Y-%m-%dT%H:%M')}"),
                email_id,
                current_user["id"],
                EMAIL_PROGRAMADO_ESTADO,
            ),
        )
        lead_id = email_programado["referencia_entidad_id"] if email_programado["referencia_entidad_tipo"] == "lead" else None
        if lead_id:
            _registrar_contacto_email(
                cur,
                lead_id,
                current_user["id"],
                "Email programado cancelado desde agenda.",
                "Programado cancelado",
                "",
            )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        return _redirect_agenda(error="No se pudo cancelar el email programado.", email_id=email_id)
    finally:
        conn.close()

    return _redirect_agenda(mensaje="Email programado cancelado.")


@router.post("/crm/prospeccion/agenda/{email_id}/reprogramar")
def reprogramar_email_programado(
    request: Request,
    email_id: int,
    fecha_programada: str = Form(...),
):
    current_user = get_current_user(request)
    fecha_limpia = limpiar_texto(fecha_programada)
    if not fecha_limpia:
        return _redirect_agenda(error="Indica fecha y hora para reprogramar.", email_id=email_id)
    conn = get_connection()
    cur = conn.cursor()
    try:
        email_programado = _get_owned_email_programado(cur, email_id, current_user["id"])
        if not email_programado:
            raise HTTPException(status_code=404, detail="Email programado no encontrado")
        if email_programado["estado"] != EMAIL_PROGRAMADO_ESTADO:
            return _redirect_agenda(error="Este email ya no esta programado.", email_id=email_id)
        plantilla_slug = _extraer_valor_error_mensaje(email_programado["error_mensaje"], "plantilla")
        cur.execute(
            """
            UPDATE emails_enviados
            SET estado = ?,
                error_mensaje = ?
            WHERE id = ? AND owner_user_id = ? AND estado = ?
            """,
            (
                EMAIL_PROGRAMADO_ESTADO,
                _metadata_programado(fecha_limpia, plantilla_slug),
                email_id,
                current_user["id"],
                EMAIL_PROGRAMADO_ESTADO,
            ),
        )
        lead_id = email_programado["referencia_entidad_id"] if email_programado["referencia_entidad_tipo"] == "lead" else None
        if lead_id:
            _registrar_contacto_email(
                cur,
                lead_id,
                current_user["id"],
                f"Email programado reprogramado para {fecha_limpia}.",
                "Programado",
                "Revisar envío programado.",
            )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        return _redirect_agenda(error="No se pudo reprogramar el email.", email_id=email_id)
    finally:
        conn.close()

    return _redirect_agenda(mensaje="Email reprogramado.", email_id=email_id)


@router.post("/crm/prospeccion/leads/rapido")
def crear_lead_rapido_workbench(
    request: Request,
    nombre: str = Form(...),
    persona_contacto: str = Form(""),
    tipo_profesion: str = Form("otros"),
    email: str = Form(""),
    telefono: str = Form(""),
    localidad: str = Form(""),
    fuente: str = Form("captacion manual"),
    notas: str = Form(""),
):
    current_user = get_current_user(request)
    nombre_limpio = limpiar_texto(nombre)
    email_limpio = limpiar_texto(email)
    tipo_limpio = _normalizar_tipo(tipo_profesion)
    if not nombre_limpio:
        return _redirect_workbench(error="El lead necesita al menos empresa o nombre.")
    if not _email_valido(email_limpio):
        return _redirect_workbench(error="El email no tiene un formato valido.")

    notas_compuestas = _componer_notas_lead(
        limpiar_texto(persona_contacto),
        limpiar_texto(localidad),
        tipo_limpio,
        limpiar_texto(notas),
    )
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, telefono, origen, servicio_solicitado,
                mensaje, estado, prioridad, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nombre_limpio,
                email_limpio,
                limpiar_texto(telefono),
                limpiar_texto(fuente) or "captacion manual",
                TIPOS_LEAD_LABELS[tipo_limpio],
                "Alta rápida desde Workbench de prospección.",
                "nuevo",
                "media",
                notas_compuestas,
                current_user["id"],
            ),
        )
        lead_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return _redirect_workbench(mensaje="Lead guardado. Formulario listo para otro.", lead_id=lead_id)


@router.post("/crm/prospeccion/leads/{lead_id}/enviar-editado")
def enviar_email_editado_workbench(
    request: Request,
    lead_id: int,
    plantilla_slug: str = Form(...),
    asunto: str = Form(...),
    cuerpo: str = Form(...),
):
    current_user = get_current_user(request)
    asunto_limpio = limpiar_texto(asunto)
    cuerpo_limpio = limpiar_texto(cuerpo)
    if not asunto_limpio or not cuerpo_limpio:
        return _redirect_workbench(error="Asunto y cuerpo son obligatorios para enviar.", lead_id=lead_id)

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        destinatario = limpiar_texto(lead["email"])
        if not destinatario:
            return _redirect_workbench(error="El lead no tiene email y no se puede enviar.", lead_id=lead_id)
        if not _email_valido(destinatario):
            return _redirect_workbench(error="El email del lead no tiene un formato valido.", lead_id=lead_id)

        plantilla = obtener_plantilla_comercial(plantilla_slug) or plantilla_para_tipo(inferir_tipo_lead(lead))
        es_seguimiento = _es_plantilla_seguimiento(plantilla.slug)
        body_html = construir_email_html_base(asunto_limpio, texto_a_html(cuerpo_limpio), footer_text="")
        mensaje_email = crear_mensaje_email(destinatario, asunto_limpio, _cuerpo_texto_salida(cuerpo_limpio), body_html)
        contexto = "seguimiento editado" if es_seguimiento else "presentacion editada"
        enviar_mensaje_email(mensaje_email, contexto=f"{contexto} lead {lead_id} plantilla {plantilla.slug}")

        registrar_email_enviado(
            tipo="seguimiento_comercial" if es_seguimiento else "presentacion_comercial",
            destinatario=destinatario,
            asunto=asunto_limpio,
            cuerpo_texto=cuerpo_limpio,
            estado="enviado",
            referencia_entidad_tipo="lead",
            referencia_entidad_id=lead_id,
            owner_user_id=current_user["id"],
        )
        if es_seguimiento:
            tarea_seguimiento = _get_tarea_seguimiento_pendiente(cur, lead_id, current_user["id"])
            _registrar_contacto_email(
                cur,
                lead_id,
                current_user["id"],
                "Seguimiento comercial enviado con texto revisado.",
                "Seguimiento enviado",
                "Revisión comercial en 30 días.",
            )
            if tarea_seguimiento:
                _marcar_tarea_hecha(cur, tarea_seguimiento["id"], lead_id, current_user["id"])
            _crear_tarea_revision_post_seguimiento_si_no_existe(cur, lead_id, current_user["id"])
            nuevo_estado = "seguimiento_enviado"
        else:
            _registrar_contacto_presentacion(cur, lead_id, current_user["id"])
            _crear_tarea_seguimiento_si_no_existe(cur, lead_id, current_user["id"])
            nuevo_estado = "pendiente_respuesta"
        cur.execute(
            """
            UPDATE leads
            SET estado = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (nuevo_estado, lead_id, current_user["id"]),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except RuntimeError:
        conn.rollback()
        return _redirect_workbench(error="No esta configurado el envio de email.", lead_id=lead_id)
    except Exception:
        conn.rollback()
        return _redirect_workbench(error="No se pudo enviar el email editado.", lead_id=lead_id)
    finally:
        conn.close()

    return _redirect_workbench(mensaje="Email enviado con texto revisado y seguimiento creado.", lead_id=lead_id)


@router.post("/crm/prospeccion/leads/{lead_id}/programar-email")
def programar_email_workbench(
    request: Request,
    lead_id: int,
    plantilla_slug: str = Form(...),
    asunto: str = Form(...),
    cuerpo: str = Form(...),
    fecha_programada: str = Form(...),
):
    current_user = get_current_user(request)
    asunto_limpio = limpiar_texto(asunto)
    cuerpo_limpio = limpiar_texto(cuerpo)
    fecha_limpia = limpiar_texto(fecha_programada)
    if not asunto_limpio or not cuerpo_limpio or not fecha_limpia:
        return _redirect_workbench(error="Asunto, cuerpo y fecha son obligatorios para programar.", lead_id=lead_id)

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        destinatario = limpiar_texto(lead["email"])
        if not destinatario:
            return _redirect_workbench(error="El lead no tiene email y no se puede programar.", lead_id=lead_id)
        if not _email_valido(destinatario):
            return _redirect_workbench(error="El email del lead no tiene un formato valido.", lead_id=lead_id)
        plantilla = obtener_plantilla_comercial(plantilla_slug) or plantilla_para_tipo(inferir_tipo_lead(lead))
        registrar_email_enviado(
            tipo="seguimiento_programado" if _es_plantilla_seguimiento(plantilla.slug) else "presentacion_programada",
            destinatario=destinatario,
            asunto=asunto_limpio,
            cuerpo_texto=cuerpo_limpio,
            estado=EMAIL_PROGRAMADO_ESTADO,
            error_mensaje=_metadata_programado(fecha_limpia, plantilla.slug),
            referencia_entidad_tipo="lead",
            referencia_entidad_id=lead_id,
            owner_user_id=current_user["id"],
        )
        _registrar_contacto_email(
            cur,
            lead_id,
            current_user["id"],
            f"Email comercial programado para {fecha_limpia}.",
            "Programado",
            "Revisar envío programado.",
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        return _redirect_workbench(error="No se pudo programar el email.", lead_id=lead_id)
    finally:
        conn.close()

    return _redirect_workbench(mensaje="Email marcado como programado. No se ha enviado automaticamente.", lead_id=lead_id)


@router.post("/crm/prospeccion/leads/{lead_id}/enviar-presentacion")
def enviar_presentacion_administradores(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        destinatario = limpiar_texto(lead["email"])
        if not destinatario:
            return RedirectResponse(
                url="/crm/prospeccion?error=El lead no tiene email y no se puede enviar la presentacion.",
                status_code=303,
            )

        plantilla, asunto, cuerpo, mensaje_email = _preparar_mensaje_comercial(
            destinatario,
            inferir_tipo_lead(lead),
            lead,
            current_user,
            proposito="presentacion",
        )

        enviar_mensaje_email(mensaje_email, contexto=f"presentacion lead {lead_id} plantilla {plantilla.slug}")

        registrar_email_enviado(
            tipo="presentacion_comercial",
            destinatario=destinatario,
            asunto=asunto,
            cuerpo_texto=cuerpo,
            estado="enviado",
            referencia_entidad_tipo="lead",
            referencia_entidad_id=lead_id,
            owner_user_id=current_user["id"],
        )
        _registrar_contacto_presentacion(cur, lead_id, current_user["id"])
        _crear_tarea_seguimiento_si_no_existe(cur, lead_id, current_user["id"])
        cur.execute(
            """
            UPDATE leads
            SET estado = 'pendiente_respuesta', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (lead_id, current_user["id"]),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except RuntimeError:
        conn.rollback()
        return RedirectResponse(
            url="/crm/prospeccion?error=No esta configurado el envio de email.",
            status_code=303,
        )
    except Exception:
        conn.rollback()
        return RedirectResponse(
            url="/crm/prospeccion?error=No se pudo enviar la presentacion.",
            status_code=303,
        )
    finally:
        conn.close()

    return RedirectResponse(
        url="/crm/prospeccion?mensaje=Presentacion enviada y seguimiento creado.",
        status_code=303,
    )


@router.post("/crm/prospeccion/leads/{lead_id}/enviar-seguimiento")
def enviar_seguimiento_administradores(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        destinatario = limpiar_texto(lead["email"])
        if not destinatario:
            return RedirectResponse(
                url="/crm/prospeccion?error=El lead no tiene email y no se puede enviar el seguimiento.",
                status_code=303,
            )

        tarea_seguimiento = _get_tarea_seguimiento_pendiente(cur, lead_id, current_user["id"])
        plantilla, asunto, cuerpo, mensaje_email = _preparar_mensaje_comercial(
            destinatario,
            inferir_tipo_lead(lead),
            lead,
            current_user,
            proposito="seguimiento_10d",
        )

        enviar_mensaje_email(mensaje_email, contexto=f"seguimiento lead {lead_id} plantilla {plantilla.slug}")

        registrar_email_enviado(
            tipo="seguimiento_comercial",
            destinatario=destinatario,
            asunto=asunto,
            cuerpo_texto=cuerpo,
            estado="enviado",
            referencia_entidad_tipo="lead",
            referencia_entidad_id=lead_id,
            owner_user_id=current_user["id"],
        )
        _registrar_contacto_email(
            cur,
            lead_id,
            current_user["id"],
            "Seguimiento comercial enviado.",
            "Seguimiento enviado",
            "Revisión comercial en 30 días.",
        )
        if tarea_seguimiento:
            _marcar_tarea_hecha(cur, tarea_seguimiento["id"], lead_id, current_user["id"])
        _crear_tarea_revision_post_seguimiento_si_no_existe(cur, lead_id, current_user["id"])
        cur.execute(
            """
            UPDATE leads
            SET estado = 'seguimiento_enviado', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (lead_id, current_user["id"]),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except RuntimeError:
        conn.rollback()
        return RedirectResponse(
            url="/crm/prospeccion?error=No esta configurado el envio de email.",
            status_code=303,
        )
    except Exception:
        conn.rollback()
        return RedirectResponse(
            url="/crm/prospeccion?error=No se pudo enviar el seguimiento.",
            status_code=303,
        )
    finally:
        conn.close()

    return RedirectResponse(
        url="/crm/prospeccion?mensaje=Seguimiento enviado y revision creada.",
        status_code=303,
    )


@router.post("/crm/prospeccion/leads/{lead_id}/registrar-llamada")
def registrar_llamada_workbench(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
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
                datetime.now().strftime("%Y-%m-%dT%H:%M"),
                "llamada",
                "Llamada registrada desde Workbench de prospección.",
                "Contactado",
                "",
                current_user["id"],
            ),
        )
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
    return RedirectResponse(url="/crm/prospeccion?mensaje=Llamada registrada.", status_code=303)


@router.post("/crm/prospeccion/leads/{lead_id}/crear-tarea")
def crear_tarea_rapida_workbench(request: Request, lead_id: int):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        _crear_tarea_seguimiento_si_no_existe(cur, lead_id, current_user["id"])
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/crm/prospeccion?mensaje=Tarea de seguimiento preparada.", status_code=303)


@router.post("/crm/prospeccion/leads/{lead_id}/estado")
def cambiar_estado_lead_workbench(
    request: Request,
    lead_id: int,
    estado: str = Form(...),
):
    current_user = get_current_user(request)
    estado_limpio = limpiar_texto(estado)
    if estado_limpio not in LEAD_ESTADOS:
        return RedirectResponse(url="/crm/prospeccion?error=Estado de lead no valido.", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    try:
        lead = _get_owned_lead(cur, lead_id, current_user["id"])
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        cur.execute(
            """
            UPDATE leads
            SET estado = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND owner_user_id = ?
            """,
            (estado_limpio, lead_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/crm/prospeccion?mensaje=Estado actualizado.", status_code=303)
