from fastapi.testclient import TestClient


def _crear_usuario(cur, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", f"autosave_crm_costes_{suffix}", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int) -> TestClient:
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_lead(cur, user_id: int, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO leads (
            nombre, email, telefono, origen, servicio_solicitado,
            mensaje, estado, prioridad, notas, updated_at, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"Administrador Autosave {suffix}",
            f"autosave-{suffix}@example.test",
            "600000000",
            "captacion manual",
            "Administrador de fincas",
            "Lead smoke autosave.",
            "nuevo",
            "media",
            "Notas CRM iniciales.",
            "2026-06-19 10:00:00",
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_coste(cur, suffix: str = "") -> dict:
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, fecha_base, provincia, origen, version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"Base autosave {suffix}",
            "Base temporal para smoke autosave.",
            "2026-06-19",
            "Madrid",
            "manual",
            "1",
        ),
    )
    base_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_conceptos (
            base_id, codigo, tipo, unidad, resumen, descripcion,
            precio, moneda, fecha_base, provincia, estado, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            base_id,
            f"AUTOSAVE-{suffix}",
            "partida",
            "ud",
            "Partida autosave",
            "Descripcion inicial de coste.",
            120.0,
            "EUR",
            "2026-06-19",
            "Madrid",
            "borrador",
            "2026-06-19 10:00:00",
        ),
    )
    return {"base_id": base_id, "concepto_id": cur.lastrowid}


def test_autosave_crm_notas_guarda_recarga_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "crm")
        lead_id = _crear_lead(cur, user_id, "crm")
        conn.commit()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        updated_at_inicial = lead["updated_at"]
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/crm/prospeccion?lead_id={lead_id}")
    assert response.status_code == 200
    assert "/static/js/autosave.js" in response.text
    assert "data-autosave-form" in response.text
    assert f"/crm/prospeccion/leads/{lead_id}/notas/autosave" in response.text
    assert "Notas del lead" in response.text

    response = client.post(
        f"/crm/prospeccion/leads/{lead_id}/notas/autosave",
        data={
            "updated_at": updated_at_inicial,
            "notas": "Notas CRM autosave persistidas.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(f"/crm/prospeccion?lead_id={lead_id}")
    assert response.status_code == 200
    assert "Notas CRM autosave persistidas." in response.text

    response = client.post(
        f"/crm/prospeccion/leads/{lead_id}/notas/autosave",
        data={
            "updated_at": updated_at_inicial,
            "notas": "No debe sobrescribir silenciosamente.",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True


def test_autosave_costes_partida_guarda_recarga_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "costes")
        contexto = _crear_coste(cur, "costes")
        conn.commit()
        concepto = cur.execute(
            "SELECT * FROM costes_conceptos WHERE id = ?",
            (contexto["concepto_id"],),
        ).fetchone()
        updated_at_inicial = concepto["updated_at"]
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/costes/{contexto['concepto_id']}")
    assert response.status_code == 200
    assert "/static/js/autosave.js" in response.text
    assert "data-autosave-form" in response.text
    assert f"/costes/{contexto['concepto_id']}/autosave" in response.text

    response = client.post(
        f"/costes/{contexto['concepto_id']}/autosave",
        data={
            "updated_at": updated_at_inicial,
            "base_id": str(contexto["base_id"]),
            "capitulo_id": "",
            "codigo": "AUTOSAVE-costes",
            "tipo": "partida",
            "unidad": "ud",
            "resumen": "Partida autosave",
            "descripcion": "Descripcion de coste autosave persistida.",
            "precio": "120.00",
            "moneda": "EUR",
            "fecha_base": "2026-06-19",
            "provincia": "Madrid",
            "estado": "borrador",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(f"/costes/{contexto['concepto_id']}")
    assert response.status_code == 200
    assert "Descripcion de coste autosave persistida." in response.text

    response = client.post(
        f"/costes/{contexto['concepto_id']}/autosave",
        data={
            "updated_at": updated_at_inicial,
            "base_id": str(contexto["base_id"]),
            "capitulo_id": "",
            "codigo": "AUTOSAVE-costes",
            "tipo": "partida",
            "unidad": "ud",
            "resumen": "Partida autosave",
            "descripcion": "No debe sobrescribir silenciosamente.",
            "precio": "120.00",
            "moneda": "EUR",
            "fecha_base": "2026-06-19",
            "provincia": "Madrid",
            "estado": "borrador",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True
