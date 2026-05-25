import io
import logging

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
