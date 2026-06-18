import io
import logging
from email import policy
from email.parser import BytesParser

import pytest


def test_email_modules_import_with_isolated_environment(isolated_import):
    router = isolated_import("app.routers.emails")
    sender = isolated_import("app.services.email_sender")

    assert router.router is not None
    assert sender.smtp_configurado() is False


def test_crear_mensaje_email_builds_multipart_with_demo_attachment(isolated_import):
    sender = isolated_import("app.services.email_sender")

    sender.SMTP_FROM_NAME = "Sistema Pericial Test"
    sender.SMTP_FROM_EMAIL = "no-reply@example.test"
    message = sender.crear_mensaje_email(
        "destino@example.test",
        "Asunto smoke",
        "Texto plano",
        "<p>Texto html</p>",
        adjuntos=[
            {
                "contenido": b"demo temporal",
                "maintype": "text",
                "subtype": "plain",
                "filename": "demo.txt",
            }
        ],
    )

    assert message["To"] == "destino@example.test"
    assert message["Subject"] == "Asunto smoke"
    assert "no-reply@example.test" in message["From"]
    assert message.is_multipart()
    assert any(part.get_filename() == "demo.txt" for part in message.walk())


def test_mime_generado_es_estandar_para_dkim(isolated_import):
    sender = isolated_import("app.services.email_sender")
    templates = isolated_import("app.services.email_templates")

    sender.SMTP_FROM_NAME = "Carlos Blanco"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    body_text = templates.construir_email_texto(
        "Buenos días,\n\nEste es un email de diagnóstico MIME.",
        footer_text="",
    )
    body_html = templates.construir_email_html(
        "Diagnóstico MIME",
        templates.texto_a_html("Buenos días,\n\nEste es un email de diagnóstico MIME."),
        footer_text="",
    )
    message = sender.crear_mensaje_email(
        "destino@example.test",
        "Diagnóstico MIME",
        body_text,
        body_html,
    )

    raw = sender.generar_mime_bytes(message)
    raw_text = raw.decode("utf-8")
    root_headers = raw_text.split("\r\n\r\n", 1)[0]
    parsed = BytesParser(policy=policy.default).parsebytes(raw)
    parts = list(parsed.walk())

    assert b"\r\n" in raw
    assert "\n" not in raw_text.replace("\r\n", "")
    assert root_headers.count("MIME-Version:") == 1
    assert root_headers.count("Content-Type:") == 1
    assert parsed["From"] == "Carlos Blanco <contacto@carlosblancoperito.es>"
    assert parsed["To"] == "destino@example.test"
    assert parsed["Subject"] == "Diagnóstico MIME"
    assert parsed["Date"]
    assert parsed["Message-ID"]
    assert parsed["Message-ID"].endswith("@carlosblancoperito.es>")
    assert any(part.get_content_type() == "text/plain" for part in parts)
    assert any(part.get_content_type() == "text/html" for part in parts)
    assert "info@carlosblancoperito.es" not in raw_text
    assert raw_text.count("contacto@carlosblancoperito.es") == 3
    assert raw_text.count("Carlos Blanco") >= 2
    assert body_text.count("Arquitecto Técnico · Perito Judicial") == 1


def test_detectar_carpeta_enviados_imap_prefiere_candidatas(isolated_import):
    sender = isolated_import("app.services.email_sender")

    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren) "." "INBOX"',
                b'(\\HasNoChildren \\UnMarked \\Sent) "." INBOX.Sent',
                b'(\\HasNoChildren) "." Sent',
            ]
        )
        == "INBOX.Sent"
    )
    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren) "/" "INBOX"',
                b'(\\HasNoChildren) "/" "Archive"',
                b'(\\HasNoChildren) "/" "Enviados"',
            ]
        )
        == "Enviados"
    )
    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren \\Sent) "/" "Correo enviado"',
                b'(\\HasNoChildren) "/" "Archive"',
            ]
        )
        == "Correo enviado"
    )
    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren) "." "INBOX"',
                b'(\\HasNoChildren) "." "INBOX.Sent"',
            ]
        )
        == "INBOX.Sent"
    )
    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren) "/" "INBOX"',
                b'(\\HasNoChildren) "/" "INBOX/Sent Items"',
            ]
        )
        == "INBOX/Sent Items"
    )
    assert (
        sender.detectar_carpeta_enviados_imap(
            [
                b'(\\HasNoChildren) "." .',
                b'(\\HasNoChildren) "." "Archive"',
            ]
        )
        == ""
    )


def test_parsear_linea_list_imap_respeta_separador_y_utf7(isolated_import):
    sender = isolated_import("app.services.email_sender")

    carpeta = sender.parsear_linea_list_imap(b'(\\HasNoChildren) "." "INBOX.Sent"')
    assert carpeta["nombre"] == "INBOX.Sent"
    assert carpeta["separador"] == "."
    assert carpeta["atributos"] == ["\\HasNoChildren"]

    carpeta_raiola = sender.parsear_linea_list_imap(b'(\\HasNoChildren \\UnMarked \\Sent) "." INBOX.Sent')
    assert carpeta_raiola["nombre"] == "INBOX.Sent"
    assert carpeta_raiola["separador"] == "."
    assert carpeta_raiola["atributos"] == ["\\HasNoChildren", "\\UnMarked", "\\Sent"]

    carpeta_sent = sender.parsear_linea_list_imap(b'(\\HasNoChildren \\Sent) "/" "Sent"')
    assert carpeta_sent["nombre"] == "Sent"
    assert carpeta_sent["separador"] == "/"
    assert carpeta_sent["atributos"] == ["\\HasNoChildren", "\\Sent"]

    carpeta_sent_items = sender.parsear_linea_list_imap(b'(\\HasNoChildren) "/" "Sent Items"')
    assert carpeta_sent_items["nombre"] == "Sent Items"
    assert carpeta_sent_items["separador"] == "/"

    carpeta_enviados = sender.parsear_linea_list_imap(b'(\\HasNoChildren \\Sent) "." INBOX.Enviados')
    assert carpeta_enviados["nombre"] == "INBOX.Enviados"
    assert carpeta_enviados["separador"] == "."
    assert carpeta_enviados["atributos"] == ["\\HasNoChildren", "\\Sent"]

    carpeta_utf7 = sender.parsear_linea_list_imap(b'(\\HasNoChildren) "/" "Enviados &AMk-"')
    assert carpeta_utf7["nombre"] == "Enviados É"


def test_enviar_mensaje_email_guarda_misma_copia_mime_en_imap_con_adjuntos(isolated_import, monkeypatch):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "mail.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    sender.SMTP_FROM_NAME = "Carlos Blanco"
    message = sender.crear_mensaje_email(
        "destino@example.test",
        "Asunto con adjunto",
        "Texto plano",
        "<p>Texto html</p>",
        adjuntos=[
            {
                "contenido": b"adjunto demo",
                "maintype": "text",
                "subtype": "plain",
                "filename": "demo.txt",
            }
        ],
    )

    class FakeSMTP:
        sent_message = None

        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, user, password):
            assert user == "usuario@example.test"
            assert password == "super-secret-password"

        def send_message(self, message):
            FakeSMTP.sent_message = message
            return {}

    class FakeIMAP:
        appended = None
        selected_mailbox = None

        def __init__(self, host, port, timeout=None):
            assert host == "mail.example.test"
            assert port == 993
            assert timeout == 20

        def login(self, user, password):
            assert user == "usuario@example.test"
            assert password == "super-secret-password"
            return "OK", []

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "Sent"', b'(\\HasNoChildren) "/" "INBOX"']

        def append(self, mailbox, flags, date_time, message_bytes):
            FakeIMAP.selected_mailbox = mailbox
            FakeIMAP.appended = message_bytes
            assert flags == "\\Seen"
            assert date_time is not None
            return "OK", [b"APPENDUID 1 2"]

        def status(self, mailbox, query):
            assert mailbox == "Sent"
            assert query == "(MESSAGES UIDNEXT)"
            return "OK", [b"Sent (MESSAGES 12 UIDNEXT 99)"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(sender.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(sender.imaplib, "IMAP4_SSL", FakeIMAP)

    sender.enviar_mensaje_email(message, contexto="smoke imap copy")

    assert FakeSMTP.sent_message is message
    assert FakeIMAP.selected_mailbox == "Sent"
    assert FakeIMAP.appended == sender.generar_mime_bytes(message)
    parsed = BytesParser(policy=policy.default).parsebytes(FakeIMAP.appended)
    assert any(part.get_filename() == "demo.txt" for part in parsed.walk())
    assert any(part.get_content_type() == "text/plain" for part in parsed.walk())
    assert any(part.get_content_type() == "text/html" for part in parsed.walk())


def test_guardar_en_enviados_imap_devuelve_resultado_estructurado(isolated_import, monkeypatch):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "mail.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    sender.SMTP_FROM_NAME = "Carlos Blanco"
    message = sender.crear_mensaje_email("destino@example.test", "Asunto", "Texto", "<p>Texto</p>")

    class FakeIMAP:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, user, password):
            return "OK", []

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "Enviados"']

        def append(self, mailbox, flags, date_time, message_bytes):
            return "OK", [b"APPENDUID 1 7"]

        def status(self, mailbox, query):
            return "OK", [b"Enviados (MESSAGES 7 UIDNEXT 8)"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(sender.imaplib, "IMAP4_SSL", FakeIMAP)

    resultado = sender.guardar_en_enviados_imap(message)

    assert resultado["ok"] is True
    assert resultado["conexion_ok"] is True
    assert resultado["login_ok"] is True
    assert resultado["append_ok"] is True
    assert resultado["carpeta"] == "Enviados"
    assert resultado["error"] == ""


def test_enviar_mensaje_email_no_falla_si_imap_no_tiene_carpeta(isolated_import, monkeypatch, caplog):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "mail.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    sender.SMTP_FROM_NAME = "Carlos Blanco"
    message = sender.crear_mensaje_email("destino@example.test", "Asunto", "Texto", "<p>Texto</p>")

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, user, password):
            return None

        def send_message(self, message):
            return {}

    class FakeIMAP:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, user, password):
            return "OK", []

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Archive"']

        def append(self, mailbox, flags, date_time, message_bytes):
            raise AssertionError("No debe intentar append sin carpeta de enviados")

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(sender.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(sender.imaplib, "IMAP4_SSL", FakeIMAP)

    with caplog.at_level(logging.WARNING, logger=sender.logger.name):
        sender.enviar_mensaje_email(message, contexto="smoke imap sin carpeta")

    assert "No se encontro carpeta IMAP de enviados" in caplog.text
    assert "super-secret-password" not in caplog.text


def test_enviar_mensaje_email_no_falla_si_imap_append_falla(isolated_import, monkeypatch, caplog):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "mail.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    sender.SMTP_FROM_NAME = "Carlos Blanco"
    message = sender.crear_mensaje_email("destino@example.test", "Asunto", "Texto", "<p>Texto</p>")

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, user, password):
            return None

        def send_message(self, message):
            return {}

    class FakeIMAP:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, user, password):
            return "OK", []

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "Enviados"']

        def append(self, mailbox, flags, date_time, message_bytes):
            raise RuntimeError("imap_append_failure")

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(sender.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(sender.imaplib, "IMAP4_SSL", FakeIMAP)

    with caplog.at_level(logging.WARNING, logger=sender.logger.name):
        sender.enviar_mensaje_email(message, contexto="smoke imap fallo")

    assert "Email enviado por SMTP pero no copiado en IMAP" in caplog.text
    assert "imap_append_failure" in caplog.text
    assert "super-secret-password" not in caplog.text


def test_guardar_en_enviados_imap_devuelve_error_estructurado_si_append_falla(isolated_import, monkeypatch):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "mail.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    sender.SMTP_FROM_NAME = "Carlos Blanco"
    message = sender.crear_mensaje_email("destino@example.test", "Asunto", "Texto", "<p>Texto</p>")

    class FakeIMAP:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, user, password):
            return "OK", []

        def list(self):
            return "OK", [b'(\\HasNoChildren) "/" "Sent"']

        def append(self, mailbox, flags, date_time, message_bytes):
            return "NO", [b"Permission denied"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr(sender.imaplib, "IMAP4_SSL", FakeIMAP)

    resultado = sender.guardar_en_enviados_imap(message)

    assert resultado["ok"] is False
    assert resultado["conexion_ok"] is True
    assert resultado["login_ok"] is True
    assert resultado["append_ok"] is False
    assert resultado["carpeta"] == "Sent"
    assert "APPEND status=NO" in resultado["error"]


def test_preparar_adjunto_uses_uploaded_content_without_real_file_paths(isolated_import):
    router = isolated_import("app.routers.emails")
    fake_upload = type(
        "FakeUpload",
        (),
        {
            "filename": "../recibos/reales/demo.pdf",
            "content_type": "application/pdf",
            "file": io.BytesIO(b"%PDF demo temporal"),
        },
    )()

    adjunto = router.preparar_adjunto(fake_upload)

    assert adjunto == {
        "contenido": b"%PDF demo temporal",
        "maintype": "application",
        "subtype": "pdf",
        "filename": "demo.pdf",
    }


def test_enviar_mensaje_email_without_config_never_opens_smtp(isolated_import, monkeypatch):
    sender = isolated_import("app.services.email_sender")
    message = sender.crear_mensaje_email(
        "destino@example.test",
        "Asunto",
        "Texto",
        "<p>Texto</p>",
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("SMTP real no debe abrirse")

    monkeypatch.setattr(sender.smtplib, "SMTP", fail_if_called)
    monkeypatch.setattr(sender.smtplib, "SMTP_SSL", fail_if_called)

    with pytest.raises(RuntimeError, match="smtp_not_configured"):
        sender.enviar_mensaje_email(message, contexto="smoke email")


def test_enviar_mensaje_email_smtp_failure_does_not_log_password(
    isolated_import,
    monkeypatch,
    caplog,
):
    sender = isolated_import("app.services.email_sender")
    sender.SMTP_HOST = "smtp.example.test"
    sender.SMTP_PORT = 465
    sender.SMTP_USER = "usuario@example.test"
    sender.SMTP_PASSWORD = "super-secret-password"
    sender.SMTP_FROM_EMAIL = "origen@example.test"
    sender.SMTP_FROM_NAME = "Sistema Pericial Test"
    message = sender.crear_mensaje_email(
        "destino@example.test",
        "Asunto",
        "Texto",
        "<p>Texto</p>",
    )

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, user, password):
            assert user == "usuario@example.test"
            assert password == "super-secret-password"

        def send_message(self, message):
            raise RuntimeError("smtp_failure_simulado")

    monkeypatch.setattr(sender.smtplib, "SMTP_SSL", FakeSMTP)

    with caplog.at_level(logging.INFO, logger=sender.logger.name):
        with pytest.raises(RuntimeError, match="smtp_failure_simulado"):
            sender.enviar_mensaje_email(message, contexto="smoke email")

    assert "super-secret-password" not in caplog.text
