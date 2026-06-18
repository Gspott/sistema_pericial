import imaplib
import logging
import re
import smtplib
import time
from base64 import b64decode
from email import policy
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from app.config import (
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from app.services.email_templates import CORPORATE_EMAIL, CORPORATE_NAME

logger = logging.getLogger(__name__)

CARPETAS_ENVIADOS_CANDIDATAS = (
    "Sent",
    "Sent Items",
    "Enviados",
    "INBOX.Sent",
    "INBOX.Enviados",
    "INBOX.Sent Items",
)


def _remitente_email() -> str:
    return (SMTP_FROM_EMAIL or "").strip() or CORPORATE_EMAIL


def _remitente_nombre() -> str:
    return (SMTP_FROM_NAME or "").strip() or CORPORATE_NAME


def smtp_configurado() -> bool:
    return all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, _remitente_email()])


def _message_id_domain() -> str:
    email = _remitente_email()
    if "@" not in email:
        return ""
    return email.rsplit("@", 1)[1]


def crear_mensaje_email(
    destinatario: str,
    asunto: str,
    body_text: str,
    body_html: str,
    adjuntos: list[dict] | None = None,
    imagenes_inline: list[dict] | None = None,
) -> EmailMessage:
    mensaje = EmailMessage(policy=policy.SMTP)
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((_remitente_nombre(), _remitente_email()))
    mensaje["To"] = destinatario
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=_message_id_domain() or None)
    mensaje.set_content(body_text)
    mensaje.add_alternative(body_html, subtype="html")
    html_part = mensaje.get_body(preferencelist=("html",))
    for imagen in imagenes_inline or []:
        if html_part is None:
            break
        html_part.add_related(
            imagen["contenido"],
            maintype=imagen.get("maintype", "image"),
            subtype=imagen.get("subtype", "png"),
            cid=imagen["cid"],
            filename=imagen.get("filename"),
        )

    for adjunto in adjuntos or []:
        mensaje.add_attachment(
            adjunto["contenido"],
            maintype=adjunto.get("maintype", "application"),
            subtype=adjunto.get("subtype", "octet-stream"),
            filename=adjunto["filename"],
        )

    return mensaje


def generar_mime_bytes(mensaje: EmailMessage) -> bytes:
    """Serializa el mensaje como lo espera SMTP, con CRLF y sin enviar."""
    return mensaje.as_bytes(policy=policy.SMTP)


def _imap_port() -> int:
    return 993 if SMTP_PORT == 465 else 143


def _imap_usa_ssl() -> bool:
    return SMTP_PORT == 465


def _decodificar_linea_imap(linea: bytes | str) -> str:
    if isinstance(linea, bytes):
        return linea.decode("utf-8", errors="replace")
    return linea


def _decodificar_utf7_imap(valor: str) -> str:
    def reemplazar(match: re.Match) -> str:
        contenido = match.group(1)
        if contenido == "":
            return "&"
        normalizado = contenido.replace(",", "/")
        padding = "=" * (-len(normalizado) % 4)
        try:
            return b64decode(normalizado + padding).decode("utf-16-be")
        except Exception:
            return match.group(0)

    return re.sub(r"&([^-]*)-", reemplazar, valor)


def parsear_linea_list_imap(linea: bytes | str) -> dict:
    texto = _decodificar_linea_imap(linea).strip()
    atributos = []
    match_atributos = re.match(r"\((.*?)\)", texto)
    resto = texto
    if match_atributos:
        atributos = match_atributos.group(1).split()
        resto = texto[match_atributos.end() :].strip()

    match_resto = re.match(
        r'(?:"(?P<sep_q>(?:[^"\\]|\\.)*)"|(?P<sep>\S+))\s+(?:"(?P<name_q>(?:[^"\\]|\\.)*)"|(?P<name>\S+))\s*$',
        resto,
    )
    if match_resto:
        separador = (match_resto.group("sep_q") or match_resto.group("sep") or "").replace('\\"', '"')
        nombre = (match_resto.group("name_q") or match_resto.group("name") or "").replace('\\"', '"')
    else:
        quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', resto)
        separador = quoted[0].replace('\\"', '"') if quoted else ""
        nombre = quoted[-1].replace('\\"', '"') if len(quoted) >= 2 else ""
        if not nombre:
            partes = resto.rsplit(" ", 1)
            nombre = partes[-1].strip('"') if partes else ""

    return {
        "raw": texto,
        "atributos": atributos,
        "separador": separador,
        "nombre": _decodificar_utf7_imap(nombre),
    }


def _extraer_nombre_carpeta_imap(linea: bytes | str) -> str:
    return parsear_linea_list_imap(linea)["nombre"]


def _normalizar_carpeta(valor: str) -> str:
    return valor.strip().strip('"').lower()


def detectar_carpeta_enviados_imap(listado: list[bytes | str]) -> str:
    info = detectar_carpeta_enviados_imap_info(listado)
    return info["nombre"] if info else ""


def detectar_carpeta_enviados_imap_info(listado: list[bytes | str]) -> dict:
    carpetas = [parsear_linea_list_imap(linea) for linea in listado or []]
    carpetas_validas = [carpeta for carpeta in carpetas if carpeta["nombre"] and carpeta["nombre"] != carpeta["separador"]]
    for carpeta in carpetas_validas:
        atributos = {atributo.lower() for atributo in carpeta["atributos"]}
        if "\\sent" in atributos or "\\sentmail" in atributos:
            return carpeta

    por_nombre = {_normalizar_carpeta(carpeta["nombre"]): carpeta for carpeta in carpetas_validas}
    separadores = [carpeta["separador"] for carpeta in carpetas_validas if carpeta["separador"]]
    candidatas = list(CARPETAS_ENVIADOS_CANDIDATAS)
    for separador in separadores:
        candidatas.extend(
            [
                f"INBOX{separador}Sent",
                f"INBOX{separador}Enviados",
                f"INBOX{separador}Sent Items",
            ]
        )

    for candidata in candidatas:
        carpeta = por_nombre.get(_normalizar_carpeta(candidata))
        if carpeta:
            return carpeta

    return {}


def _resultado_imap(**kwargs) -> dict:
    resultado = {
        "ok": False,
        "conexion_ok": False,
        "login_ok": False,
        "append_ok": False,
        "host": SMTP_HOST,
        "puerto": _imap_port(),
        "usuario": SMTP_USER,
        "ssl": _imap_usa_ssl(),
        "starttls": not _imap_usa_ssl(),
        "carpetas": [],
        "carpeta_enviados_detectada": "",
        "carpeta": "",
        "append_status": "",
        "append_response": "",
        "status_response": "",
        "error": "",
    }
    resultado.update(kwargs)
    return resultado


def diagnosticar_imap_enviados(mensaje: EmailMessage | None = None, append_test: bool = False) -> dict:
    if not smtp_configurado():
        return _resultado_imap(error="smtp_not_configured")

    imap = None
    resultado = _resultado_imap()
    try:
        logger.info(
            "Diagnostico IMAP enviados: host=%s puerto=%s usuario=%s modo=%s",
            SMTP_HOST,
            _imap_port(),
            SMTP_USER,
            "SSL" if _imap_usa_ssl() else "STARTTLS",
        )
        if _imap_usa_ssl():
            imap = imaplib.IMAP4_SSL(SMTP_HOST, _imap_port(), timeout=20)
        else:
            imap = imaplib.IMAP4(SMTP_HOST, _imap_port(), timeout=20)
            imap.starttls()
        resultado["conexion_ok"] = True

        imap.login(SMTP_USER, SMTP_PASSWORD)
        resultado["login_ok"] = True
        status, listado = imap.list()
        if status != "OK":
            resultado["error"] = f"LIST status={status}"
            logger.warning("No se pudo listar carpetas IMAP: status=%s data=%s", status, listado)
            return resultado

        carpetas_info = [parsear_linea_list_imap(linea) for linea in (listado or [])]
        resultado["carpetas"] = carpetas_info
        logger.info("Carpetas IMAP detectadas: %s", [carpeta["nombre"] for carpeta in carpetas_info])

        carpeta_info = detectar_carpeta_enviados_imap_info(listado or [])
        carpeta = carpeta_info.get("nombre", "")
        resultado["carpeta_enviados_detectada"] = carpeta
        resultado["carpeta"] = carpeta
        logger.info("Carpeta IMAP de enviados candidata: %s", carpeta or "(no detectada)")
        if not carpeta:
            resultado["error"] = "sent_folder_not_found"
            logger.warning("No se encontro carpeta IMAP de enviados para guardar copia.")
            return resultado

        if not append_test:
            resultado["ok"] = True
            return resultado

        if mensaje is None:
            resultado["error"] = "append_requested_without_message"
            return resultado

        fecha_interna = imaplib.Time2Internaldate(time.time())
        status, data = imap.append(carpeta, "\\Seen", fecha_interna, generar_mime_bytes(mensaje))
        resultado["append_status"] = status
        resultado["append_response"] = repr(data)
        if status != "OK":
            resultado["error"] = f"APPEND status={status} data={data!r}"
            logger.warning("No se pudo guardar copia IMAP en carpeta %s: status=%s data=%s", carpeta, status, data)
            return resultado

        resultado["append_ok"] = True
        resultado["ok"] = True
        try:
            status_status, data_status = imap.status(carpeta, "(MESSAGES UIDNEXT)")
            resultado["status_response"] = f"{status_status} {data_status!r}"
            logger.info("STATUS IMAP tras APPEND carpeta=%s status=%s data=%s", carpeta, status_status, data_status)
        except Exception as exc:
            resultado["status_response"] = f"status_failed: {exc}"
            logger.info("No se pudo confirmar STATUS tras APPEND en %s: %s", carpeta, exc)

        logger.info("Copia IMAP guardada en carpeta %s append_response=%s", carpeta, data)
        return resultado
    except Exception as exc:
        resultado["error"] = repr(exc)
        logger.warning("No se pudo diagnosticar/guardar copia IMAP del email enviado: %s", exc, exc_info=True)
        return resultado
    finally:
        if imap is not None:
            try:
                imap.logout()
            except Exception:
                logger.debug("No se pudo cerrar sesion IMAP limpiamente.", exc_info=True)


def guardar_en_enviados_imap(mensaje: EmailMessage) -> dict:
    return diagnosticar_imap_enviados(mensaje, append_test=True)


def enviar_mensaje_email(mensaje: EmailMessage, contexto: str = "email") -> None:
    if not smtp_configurado():
        raise RuntimeError("smtp_not_configured")

    destinatario = mensaje.get("To", "")
    asunto = mensaje.get("Subject", "")
    logger.info(
        "Enviando %s a %s asunto=%s host=%s puerto=%s usuario=%s remitente=%s",
        contexto,
        destinatario,
        asunto,
        SMTP_HOST,
        SMTP_PORT,
        SMTP_USER,
        _remitente_email(),
    )

    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                rechazados = smtp.send_message(mensaje)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.starttls()
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                rechazados = smtp.send_message(mensaje)

        if rechazados:
            raise RuntimeError(f"smtp_rejected_recipients: {rechazados}")

        resultado_imap = guardar_en_enviados_imap(mensaje)
        if not resultado_imap["ok"]:
            logger.warning(
                "Email enviado por SMTP pero no copiado en IMAP: carpeta=%s error=%s host=%s puerto=%s usuario=%s",
                resultado_imap.get("carpeta") or resultado_imap.get("carpeta_enviados_detectada"),
                resultado_imap.get("error"),
                resultado_imap.get("host"),
                resultado_imap.get("puerto"),
                resultado_imap.get("usuario"),
            )

        logger.info(
            "Email enviado correctamente: %s a %s asunto=%s",
            contexto,
            destinatario,
            asunto,
        )
    except Exception:
        logger.exception(
            "Error SMTP enviando %s a %s con host=%s puerto=%s usuario=%s remitente=%s",
            contexto,
            mensaje.get("To", ""),
            SMTP_HOST,
            SMTP_PORT,
            SMTP_USER,
            _remitente_email(),
        )
        raise
