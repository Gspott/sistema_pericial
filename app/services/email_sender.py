import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.config import (
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def smtp_configurado() -> bool:
    return all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL])


def crear_mensaje_email(
    destinatario: str,
    asunto: str,
    body_text: str,
    body_html: str,
    adjuntos: list[dict] | None = None,
) -> EmailMessage:
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
    mensaje["To"] = destinatario
    mensaje.set_content(body_text)
    mensaje.add_alternative(body_html, subtype="html")

    for adjunto in adjuntos or []:
        mensaje.add_attachment(
            adjunto["contenido"],
            maintype=adjunto.get("maintype", "application"),
            subtype=adjunto.get("subtype", "octet-stream"),
            filename=adjunto["filename"],
        )

    return mensaje


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
        SMTP_FROM_EMAIL,
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
            SMTP_FROM_EMAIL,
        )
        raise
