from fastapi.testclient import TestClient


def _crear_usuario(cur, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", f"autosave_propuestas_{suffix}", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int) -> TestClient:
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_propuesta(cur, user_id: int, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO propuestas (
            numero_propuesta, fecha, estado, tipo_trabajo, direccion_inmueble,
            alcance, plazo_estimado, base_imponible, iva_porcentaje,
            importe_iva, total_propuesta, iva, total, condiciones,
            updated_at, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"P-AUTOSAVE-{suffix}",
            "2026-06-19",
            "borrador",
            "Informe pericial",
            "Calle Prueba 1",
            "Alcance inicial de propuesta.",
            "10 dias",
            100.0,
            21.0,
            21.0,
            121.0,
            21.0,
            121.0,
            "Condiciones iniciales.",
            "2026-06-19 10:00:00",
            user_id,
        ),
    )
    return cur.lastrowid


def _payload_propuesta(updated_at: str, alcance: str, condiciones: str) -> dict:
    return {
        "updated_at": updated_at,
        "numero_propuesta": "P-AUTOSAVE-propuestas",
        "lead_id": "",
        "cliente_id": "",
        "fecha": "2026-06-19",
        "tipo_trabajo": "Informe pericial",
        "direccion_inmueble": "Calle Prueba 1",
        "alcance": alcance,
        "plazo_estimado": "10 dias",
        "base_imponible": "100.00",
        "iva_porcentaje": "21.00",
        "importe_iva": "21.00",
        "total_propuesta": "121.00",
        "condiciones": condiciones,
    }


def test_autosave_propuesta_guarda_recarga_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "propuestas")
        propuesta_id = _crear_propuesta(cur, user_id, "propuestas")
        conn.commit()
        propuesta = cur.execute(
            "SELECT * FROM propuestas WHERE id = ?",
            (propuesta_id,),
        ).fetchone()
        updated_at_inicial = propuesta["updated_at"]
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/propuestas/{propuesta_id}/editar")
    assert response.status_code == 200
    assert "/static/js/autosave.js" in response.text
    assert "data-autosave-form" in response.text
    assert f"/propuestas/{propuesta_id}/autosave" in response.text
    assert "Listo para editar" in response.text
    assert f'id="propuesta_updated_at_{propuesta_id}"' in response.text

    response = client.get("/propuestas/nueva")
    assert response.status_code == 200
    assert "data-autosave-form" not in response.text

    alcance_autosave = "Alcance largo persistido por autosave."
    condiciones_autosave = "Condiciones largas persistidas por autosave."
    response = client.post(
        f"/propuestas/{propuesta_id}/autosave",
        data=_payload_propuesta(
            updated_at_inicial,
            alcance_autosave,
            condiciones_autosave,
        ),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(f"/propuestas/{propuesta_id}/editar")
    assert response.status_code == 200
    assert alcance_autosave in response.text
    assert condiciones_autosave in response.text

    response = client.post(
        f"/propuestas/{propuesta_id}/autosave",
        data=_payload_propuesta(
            updated_at_inicial,
            "No debe sobrescribir silenciosamente.",
            "Tampoco debe sobrescribir condiciones.",
        ),
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True


def test_guardado_manual_propuesta_respeta_conflicto_updated_at(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "manual")
        propuesta_id = _crear_propuesta(cur, user_id, "manual")
        conn.commit()
        propuesta = cur.execute(
            "SELECT * FROM propuestas WHERE id = ?",
            (propuesta_id,),
        ).fetchone()
        updated_at_inicial = propuesta["updated_at"]
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/autosave",
        data=_payload_propuesta(
            updated_at_inicial,
            "Alcance previo guardado por autosave.",
            "Condiciones previas guardadas por autosave.",
        ),
    )
    assert response.status_code == 200

    response = client.post(
        f"/propuestas/{propuesta_id}/editar",
        data=_payload_propuesta(
            updated_at_inicial,
            "Intento manual con token antiguo.",
            "Intento manual con token antiguo.",
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Otro proceso ha modificado el registro." in response.text

    response = client.get(f"/propuestas/{propuesta_id}/editar")
    assert response.status_code == 200
    assert "Alcance previo guardado por autosave." in response.text
    assert "Intento manual con token antiguo." not in response.text
