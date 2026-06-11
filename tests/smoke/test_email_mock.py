import io
import logging
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Email", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


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


def test_email_presentacion_desde_lead_crea_seguimiento_y_dashboard(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.routers import emails as emails_router

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "email_presentacion_owner")
        other_id = _crear_usuario(cur, "email_presentacion_other")
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, origen, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Administrador seguimiento",
                "seguimiento@example.test",
                "administrador_fincas",
                "pendiente",
                owner_id,
            ),
        )
        lead_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, origen, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Lead ajeno email",
                "ajeno-email@example.test",
                "administrador_fincas",
                "pendiente",
                other_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    def fake_send(message, contexto="email"):
        assert message["To"] == "seguimiento@example.test"

    monkeypatch.setattr(emails_router, "enviar_mensaje_email", fake_send)
    client = _autenticar_cliente(main_module, owner_id)

    response = client.get(f"/emails/nuevo?lead_id={lead_id}")
    assert response.status_code == 200
    assert "Email asociado a lead" in response.text
    assert f'name="lead_id" value="{lead_id}"' in response.text

    response = client.post(
        "/emails/nuevo",
        data={
            "destinatario": "seguimiento@example.test",
            "asunto": "Presentación servicios periciales",
            "cuerpo": "Hola, presento servicios periciales.",
            "lead_id": str(lead_id),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    fecha_esperada = (date.today() + timedelta(days=emails_router.PROSPECCION_SEGUIMIENTO_DIAS)).isoformat()
    conn = get_connection()
    try:
        lead = conn.execute(
            """
            SELECT estado
            FROM leads
            WHERE id = ? AND owner_user_id = ?
            """,
            (lead_id, owner_id),
        ).fetchone()
        tarea = conn.execute(
            """
            SELECT *
            FROM lead_tareas
            WHERE lead_id = ? AND owner_user_id = ?
            """,
            (lead_id, owner_id),
        ).fetchone()
        email = conn.execute(
            """
            SELECT *
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead'
              AND referencia_entidad_id = ?
              AND owner_user_id = ?
            """,
            (lead_id, owner_id),
        ).fetchone()
    finally:
        conn.close()

    assert lead["estado"] == "email_enviado"
    assert tarea["tipo"] == "seguimiento"
    assert tarea["estado"] == "pendiente"
    assert tarea["fecha_programada"] == fecha_esperada
    assert email["estado"] == "enviado"

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Seguimientos próximos" in dashboard.text
    assert "Seguimiento tras email de presentación" in dashboard.text
    assert "Administrador seguimiento" in dashboard.text
    assert "Lead ajeno email" not in dashboard.text
