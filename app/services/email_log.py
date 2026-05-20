import logging

from app.database import get_connection

logger = logging.getLogger(__name__)

MAX_CUERPO_TEXTO = 1000
MAX_ERROR_MENSAJE = 500


def _limitar_texto(valor: str | None, max_len: int) -> str:
    texto = (valor or "").strip()
    if len(texto) <= max_len:
        return texto
    return texto[: max_len - 3].rstrip() + "..."


def registrar_email_enviado(
    *,
    tipo: str,
    destinatario: str,
    asunto: str,
    cuerpo_texto: str | None = None,
    nombre_adjunto: str | None = None,
    tiene_adjunto: bool = False,
    estado: str = "enviado",
    error_mensaje: str | None = None,
    referencia_entidad_tipo: str | None = None,
    referencia_entidad_id: int | None = None,
    owner_user_id: int | None = None,
) -> None:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO emails_enviados (
                tipo, destinatario, asunto, cuerpo_texto, nombre_adjunto,
                tiene_adjunto, estado, error_mensaje, referencia_entidad_tipo,
                referencia_entidad_id, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tipo,
                destinatario,
                asunto,
                _limitar_texto(cuerpo_texto, MAX_CUERPO_TEXTO),
                nombre_adjunto,
                1 if tiene_adjunto else 0,
                estado,
                _limitar_texto(error_mensaje, MAX_ERROR_MENSAJE),
                referencia_entidad_tipo,
                referencia_entidad_id,
                owner_user_id,
            ),
        )
        conn.commit()
    except Exception:
        logger.exception("No se pudo registrar el email enviado en el log interno.")
    finally:
        if conn is not None:
            conn.close()
