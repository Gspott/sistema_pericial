from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import logging
import re

from app.database import get_connection
from app.services.crm_templates import obtener_plantilla_comercial, plantilla_para_tipo
from app.services.email_sender import crear_mensaje_email, enviar_mensaje_email
from app.services.email_templates import construir_email_html_base, construir_firma_texto, texto_a_html
from app.utils.timezone import datetime_local_madrid_minutes, now_madrid_iso, today_madrid

logger = logging.getLogger(__name__)

EMAIL_PROGRAMADO_ESTADO = "programado"
EMAIL_ERROR_ESTADO = "error"
SEGUIMIENTO_PRESENTACION_TIPO = "seguimiento_presentacion"
SEGUIMIENTO_PRESENTACION_TITULO = "Seguimiento presentación comercial"
REVISION_POST_SEGUIMIENTO_TIPO = "revision_post_seguimiento"
REVISION_POST_SEGUIMIENTO_TITULO = "Revisión tras seguimiento comercial"
PRESENTACION_ADMINISTRADORES_FILENAME = "carlos-blanco-presentacion-administradores.png"
PRESENTACION_ADMINISTRADORES_CID = "carlos-blanco-presentacion-administradores@sistema-pericial"
PRESENTACION_ADMINISTRADORES_PATH = (
    Path(__file__).resolve().parents[2] / "static" / "crm" / PRESENTACION_ADMINISTRADORES_FILENAME
)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def limpiar_texto(valor: str | None) -> str:
    return (valor or "").strip()


def _email_valido(valor: str) -> bool:
    return bool(EMAIL_RE.match(valor))


def _extraer_valor_metadata(error_mensaje: str | None, clave: str) -> str:
    prefijo = f"{clave}="
    for parte in (error_mensaje or "").split(";"):
        parte_limpia = parte.strip()
        if parte_limpia.startswith(prefijo):
            return limpiar_texto(parte_limpia[len(prefijo) :])
    return ""


def _metadata_error_programado(error_mensaje: str | None, error: str) -> str:
    base = limpiar_texto(error_mensaje)
    partes = [base] if base else []
    partes.append(f"error_envio={limpiar_texto(error)[:220]}")
    partes.append(f"error_en={now_madrid_iso(timespec='minutes')}")
    return "; ".join(partes)


def _fecha_programada_vencida(fecha_programada: str, ahora: str) -> bool:
    fecha = limpiar_texto(fecha_programada)
    return bool(fecha and fecha <= ahora)


def _imagen_presentacion_administradores() -> dict | None:
    if not PRESENTACION_ADMINISTRADORES_PATH.exists():
        return None
    return {
        "contenido": PRESENTACION_ADMINISTRADORES_PATH.read_bytes(),
        "maintype": "image",
        "subtype": "png",
        "filename": PRESENTACION_ADMINISTRADORES_FILENAME,
        "cid": f"<{PRESENTACION_ADMINISTRADORES_CID}>",
    }


def _es_presentacion_administradores(plantilla) -> bool:
    return plantilla.slug == "presentacion_administrador_fincas"


def _cuerpo_texto_salida(cuerpo: str) -> str:
    return "\n\n".join([limpiar_texto(cuerpo), construir_firma_texto()])


def _crear_mensaje_crm_con_plantilla(destinatario: str, asunto: str, cuerpo: str, plantilla):
    imagen_presentacion = _imagen_presentacion_administradores() if _es_presentacion_administradores(plantilla) else None
    imagen_html = ""
    if imagen_presentacion:
        imagen_html = (
            f'<div style="margin:22px 0 18px;">'
            f'<img src="cid:{PRESENTACION_ADMINISTRADORES_CID}" '
            f'alt="Presentación profesional Carlos Blanco" '
            f'style="display:block;width:100%;max-width:620px;height:auto;border:1px solid #e4e0d8;border-radius:6px;">'
            f"</div>"
        )
    body_html = construir_email_html_base(asunto, f"{texto_a_html(cuerpo)}\n{imagen_html}", footer_text="")
    adjuntos = [imagen_presentacion] if imagen_presentacion else None
    imagenes_inline = [imagen_presentacion] if imagen_presentacion else None
    return crear_mensaje_email(
        destinatario,
        asunto,
        _cuerpo_texto_salida(cuerpo),
        body_html,
        adjuntos=adjuntos,
        imagenes_inline=imagenes_inline,
    )


def _email_programado_es_seguimiento(email) -> bool:
    plantilla_slug = _extraer_valor_metadata(email["error_mensaje"], "plantilla")
    tipo = limpiar_texto(email["tipo"])
    return tipo.startswith("seguimiento_") or plantilla_slug.startswith("seguimiento_")


def _tipo_confirmado_desde_programado(email) -> str:
    return "seguimiento_comercial" if _email_programado_es_seguimiento(email) else "presentacion_comercial"


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

    fecha_programada = (today_madrid() + timedelta(days=10)).isoformat()
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

    fecha_programada = (today_madrid() + timedelta(days=30)).isoformat()
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
            now_madrid_iso(timespec="minutes"),
            "email",
            resumen,
            resultado,
            siguiente_accion,
            owner_user_id,
        ),
    )


def _registrar_contacto_presentacion(cur, lead_id: int, owner_user_id: int) -> None:
    _registrar_contacto_email(
        cur,
        lead_id,
        owner_user_id,
        "Presentación comercial enviada.",
        "Pendiente de respuesta",
        "Seguimiento en 10 días.",
    )


def _registrar_metricas_contacto_lead(cur, lead_id: int, owner_user_id: int, tipo_contacto: str) -> None:
    campo_fecha = "fecha_segundo_contacto" if tipo_contacto == "seguimiento" else "fecha_primer_contacto"
    cur.execute(
        f"""
        UPDATE leads
        SET {campo_fecha} = COALESCE({campo_fecha}, ?),
            apertura_email = COALESCE(apertura_email, 'no_registrada'),
            respuesta_email = COALESCE(respuesta_email, 'pendiente'),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND owner_user_id = ?
        """,
        (now_madrid_iso(timespec="minutes"), lead_id, owner_user_id),
    )


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
            "Email programado de seguimiento enviado automáticamente.",
            "Seguimiento enviado",
            "Revisión comercial en 30 días.",
        )
        if tarea_seguimiento:
            _marcar_tarea_hecha(cur, tarea_seguimiento["id"], lead_id, owner_user_id)
        _crear_tarea_revision_post_seguimiento_si_no_existe(cur, lead_id, owner_user_id)
        _registrar_metricas_contacto_lead(cur, lead_id, owner_user_id, "seguimiento")
        nuevo_estado = "seguimiento_enviado"
    else:
        _registrar_contacto_presentacion(cur, lead_id, owner_user_id)
        _crear_tarea_seguimiento_si_no_existe(cur, lead_id, owner_user_id)
        _registrar_metricas_contacto_lead(cur, lead_id, owner_user_id, "presentacion")
        nuevo_estado = "pendiente_respuesta"
    cur.execute(
        """
        UPDATE leads
        SET estado = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND owner_user_id = ?
        """,
        (nuevo_estado, lead_id, owner_user_id),
    )


def _programado_view(email) -> dict:
    return {
        "id": email["id"],
        "destinatario": email["destinatario"],
        "asunto": email["asunto"],
        "tipo": email["tipo"],
        "estado": email["estado"],
        "owner_user_id": email["owner_user_id"],
        "lead_id": email["referencia_entidad_id"] if email["referencia_entidad_tipo"] == "lead" else None,
        "programado_para": _extraer_valor_metadata(email["error_mensaje"], "programado_para"),
        "plantilla": _extraer_valor_metadata(email["error_mensaje"], "plantilla"),
    }


def _obtener_programados_vencidos(cur, ahora: str, limit: int) -> list:
    programados = cur.execute(
        """
        SELECT *
        FROM emails_enviados
        WHERE estado = ?
        ORDER BY fecha_envio ASC, id ASC
        """,
        (EMAIL_PROGRAMADO_ESTADO,),
    ).fetchall()
    vencidos = [
        email
        for email in programados
        if _fecha_programada_vencida(_extraer_valor_metadata(email["error_mensaje"], "programado_para"), ahora)
    ]
    return vencidos[: max(1, limit)]


def _marcar_email_error(cur, email, error: str) -> None:
    cur.execute(
        """
        UPDATE emails_enviados
        SET estado = ?,
            error_mensaje = ?
        WHERE id = ? AND estado = ?
        """,
        (
            EMAIL_ERROR_ESTADO,
            _metadata_error_programado(email["error_mensaje"], error),
            email["id"],
            EMAIL_PROGRAMADO_ESTADO,
        ),
    )


def _enviar_email_programado(cur, email) -> dict:
    destinatario = limpiar_texto(email["destinatario"])
    asunto = limpiar_texto(email["asunto"])
    cuerpo = limpiar_texto(email["cuerpo_texto"])
    if not destinatario:
        raise ValueError("destinatario_vacio")
    if not _email_valido(destinatario):
        raise ValueError("destinatario_invalido")
    if not asunto or not cuerpo:
        raise ValueError("asunto_o_cuerpo_vacio")

    plantilla_slug = _extraer_valor_metadata(email["error_mensaje"], "plantilla")
    plantilla = obtener_plantilla_comercial(plantilla_slug) or plantilla_para_tipo("administrador_fincas")
    mensaje_email = _crear_mensaje_crm_con_plantilla(destinatario, asunto, cuerpo, plantilla)
    tipo_confirmado = _tipo_confirmado_desde_programado(email)
    enviar_mensaje_email(
        mensaje_email,
        contexto=f"scheduled {tipo_confirmado} email_programado {email['id']}",
    )
    nombre_adjunto = PRESENTACION_ADMINISTRADORES_FILENAME if _es_presentacion_administradores(plantilla) else None
    cur.execute(
        """
        UPDATE emails_enviados
        SET estado = 'enviado',
            tipo = ?,
            asunto = ?,
            cuerpo_texto = ?,
            nombre_adjunto = ?,
            tiene_adjunto = ?,
            error_mensaje = NULL,
            fecha_envio = CURRENT_TIMESTAMP
        WHERE id = ? AND owner_user_id = ? AND estado = ?
        """,
        (
            tipo_confirmado,
            asunto,
            cuerpo,
            nombre_adjunto,
            1 if nombre_adjunto else 0,
            email["id"],
            email["owner_user_id"],
            EMAIL_PROGRAMADO_ESTADO,
        ),
    )
    _aplicar_estado_post_envio_programado(cur, email, email["owner_user_id"])
    return {"id": email["id"], "destinatario": destinatario, "asunto": asunto, "tipo": tipo_confirmado}


def enviar_emails_programados_vencidos(
    *,
    dry_run: bool = False,
    limit: int = 10,
    ahora: str | None = None,
) -> dict:
    """Envia emails CRM programados cuya fecha ya vencio.

    El envio SMTP/IMAP queda delegado en `enviar_mensaje_email`. En `dry_run`
    solo lista candidatos y no modifica la base de datos.
    """
    limite = max(1, min(int(limit or 10), 100))
    ahora_ref = limpiar_texto(ahora) or datetime_local_madrid_minutes()
    resultado = {
        "dry_run": dry_run,
        "limit": limite,
        "ahora": ahora_ref,
        "candidatos": [],
        "enviados": [],
        "errores": [],
    }
    conn = get_connection()
    cur = conn.cursor()
    try:
        candidatos = _obtener_programados_vencidos(cur, ahora_ref, limite)
        resultado["candidatos"] = [_programado_view(email) for email in candidatos]
        if dry_run:
            return resultado

        for email in candidatos:
            try:
                enviado = _enviar_email_programado(cur, email)
                resultado["enviados"].append(enviado)
                conn.commit()
                logger.info("Email programado enviado automaticamente: id=%s", email["id"])
            except Exception as exc:
                conn.rollback()
                error = str(exc) or repr(exc)
                try:
                    _marcar_email_error(cur, email, error)
                    conn.commit()
                except Exception:
                    conn.rollback()
                    logger.exception("No se pudo registrar error del email programado id=%s", email["id"])
                resultado["errores"].append({"id": email["id"], "error": error})
                logger.warning("No se pudo enviar email programado id=%s: %s", email["id"], error, exc_info=True)
    finally:
        conn.close()
    return resultado
