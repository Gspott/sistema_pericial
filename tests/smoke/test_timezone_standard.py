from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str = "timezone_smoke") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Timezone", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_timezone_helper_interpreta_current_timestamp_sqlite_como_utc(isolated_import):
    timezone_utils = isolated_import("app.utils.timezone")

    assert timezone_utils.format_datetime_madrid("2026-06-19 10:15:00") == "19/06/2026 12:15"
    assert timezone_utils.format_datetime_madrid("2026-01-19 10:15:00") == "19/01/2026 11:15"
    assert timezone_utils.format_datetime_madrid("2026-06-19T10:15:00Z") == "19/06/2026 12:15"
    assert timezone_utils.format_datetime_madrid("2026-06-19") == "19/06/2026"


def test_email_listado_muestra_fecha_envio_current_timestamp_en_hora_madrid(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO emails_enviados (
                fecha_envio, tipo, destinatario, asunto, cuerpo_texto,
                estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-19 10:15:00",
                "manual",
                "destino@example.test",
                "Smoke timezone",
                "Cuerpo",
                "enviado",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get("/emails")

    assert response.status_code == 200
    assert "19/06/2026 12:15" in response.text
    assert "2026-06-19 10:15:00" not in response.text
