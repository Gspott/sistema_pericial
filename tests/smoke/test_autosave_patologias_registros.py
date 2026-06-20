from pathlib import Path

from fastapi.testclient import TestClient


def _crear_usuario(cur, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", f"autosave_patologias_{suffix}", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int) -> TestClient:
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_contexto_patologias(cur, user_id: int, suffix: str = "") -> dict:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"EXP-AUTOSAVE-PAT-{suffix}",
            "patologias",
            "particular",
            f"Cliente Patologias {suffix}",
            f"Calle Patologias {suffix}",
            user_id,
        ),
    )
    expediente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO visitas (
            expediente_id, fecha, tecnico, observaciones_visita
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            expediente_id,
            "2026-06-18",
            "Tecnico Smoke",
            "Visita con registros de patologias.",
        ),
    )
    visita_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO estancias (
            visita_id, nombre, tipo_estancia, planta, observaciones
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (visita_id, "Salon", "salon", "1", "Estancia para autosave."),
    )
    estancia_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO biblioteca_patologias (
            nombre, categoria, elemento_afectado, rol_patologia, activo
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Humedad por capilaridad", "humedades", "paramento", "efecto", 1),
    )
    cur.execute(
        """
        INSERT INTO biblioteca_patologias (
            nombre, categoria, elemento_afectado, rol_patologia, activo
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Fisura vertical", "fisuras", "paramento", "mixta", 1),
    )
    cur.execute(
        """
        INSERT INTO registros_patologias (
            visita_id, estancia_id, elemento, patologia, observaciones,
            foto, localizacion_dano, detalle_localizacion,
            rol_patologia_observado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            estancia_id,
            "paramento",
            "Humedad por capilaridad",
            "Observacion interior inicial.",
            "",
            "paramento",
            "Encuentro con rodapie",
            "efecto",
        ),
    )
    registro_interior_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO registros_patologias_exteriores (
            visita_id, zona_exterior, elemento_exterior,
            localizacion_dano_exterior, patologia, observaciones, foto
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "fachada",
            "revestimiento",
            "vertical",
            "Fisura vertical",
            "Observacion exterior inicial.",
            "",
        ),
    )
    registro_exterior_id = cur.lastrowid
    return {
        "expediente_id": expediente_id,
        "visita_id": visita_id,
        "estancia_id": estancia_id,
        "interior_id": registro_interior_id,
        "exterior_id": registro_exterior_id,
    }


def test_autosave_patologias_registros_renderiza_contrato(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "render")
        contexto = _crear_contexto_patologias(cur, user_id, "render")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(f"/editar-registro/{contexto['interior_id']}")
    assert response.status_code == 200
    html = response.text
    assert "/static/js/autosave.js" in html
    assert "data-autosave-form" in html
    assert f"/patologias/registros/{contexto['interior_id']}/autosave" in html
    assert "Listo para editar" in html
    assert 'name="updated_at"' in html

    response = client.get(f"/editar-registro-exterior/{contexto['exterior_id']}")
    assert response.status_code == 200
    html = response.text
    assert "/static/js/autosave.js" in html
    assert "data-autosave-form" in html
    assert (
        f"/patologias/registros-exteriores/{contexto['exterior_id']}/autosave"
        in html
    )
    assert "Listo para editar" in html
    assert 'name="updated_at"' in html

    js = Path("static/js/autosave.js").read_text(encoding="utf-8")
    assert "Cambios pendientes" in js
    assert "Guardando" in js
    assert "Error al guardar" in js
    assert "beforeunload" in js


def test_autosave_patologia_interior_guarda_recarga_y_detecta_conflicto(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "interior")
        contexto = _crear_contexto_patologias(cur, user_id, "interior")
        conn.commit()
        registro = cur.execute(
            "SELECT * FROM registros_patologias WHERE id = ?",
            (contexto["interior_id"],),
        ).fetchone()
        token_inicial = main_module.token_autosave_registro_patologia(registro)
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/patologias/registros/{contexto['interior_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "estancia_id": str(contexto["estancia_id"]),
            "elemento": "paramento",
            "localizacion_dano": "techo",
            "detalle_localizacion": "Junta superior revisada",
            "rol_patologia_observado": "causa",
            "patologia": "Fisura vertical",
            "observaciones": "Observacion interior autosave persistida.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]
    assert payload["message"] == "Guardado correctamente"

    response = client.get(f"/editar-registro/{contexto['interior_id']}")
    assert response.status_code == 200
    assert "Observacion interior autosave persistida." in response.text

    response = client.post(
        f"/patologias/registros/{contexto['interior_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "estancia_id": str(contexto["estancia_id"]),
            "elemento": "paramento",
            "localizacion_dano": "techo",
            "detalle_localizacion": "Intento conflictivo",
            "rol_patologia_observado": "causa",
            "patologia": "Fisura vertical",
            "observaciones": "No debe sobrescribir silenciosamente.",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True
    assert payload["updated_at"]


def test_autosave_patologia_exterior_guarda_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "exterior")
        contexto = _crear_contexto_patologias(cur, user_id, "exterior")
        conn.commit()
        registro = cur.execute(
            "SELECT * FROM registros_patologias_exteriores WHERE id = ?",
            (contexto["exterior_id"],),
        ).fetchone()
        token_inicial = main_module.token_autosave_registro_patologia_exterior(registro)
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/patologias/registros-exteriores/{contexto['exterior_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "zona_exterior": "cubierta",
            "elemento_exterior": "impermeabilizacion",
            "localizacion_dano_exterior": "horizontal",
            "patologia": "Humedad por capilaridad",
            "observaciones": "Observacion exterior autosave persistida.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(f"/editar-registro-exterior/{contexto['exterior_id']}")
    assert response.status_code == 200
    assert "Observacion exterior autosave persistida." in response.text

    response = client.post(
        f"/patologias/registros-exteriores/{contexto['exterior_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "zona_exterior": "cubierta",
            "elemento_exterior": "impermeabilizacion",
            "localizacion_dano_exterior": "horizontal",
            "patologia": "Humedad por capilaridad",
            "observaciones": "No debe sobrescribir silenciosamente.",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True
