from fastapi.testclient import TestClient


def _crear_usuario(cur, suffix: str = "") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", f"autosave_estancias_{suffix}", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int) -> TestClient:
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_contexto_estancias_cuadrantes(cur, user_id: int, suffix: str = "") -> dict:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"EXP-AUTOSAVE-EST-{suffix}",
            "patologias",
            "particular",
            f"Cliente Estancias {suffix}",
            f"Calle Estancias {suffix}",
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
            "2026-06-19",
            "Tecnico Smoke",
            "Visita con estancias y cuadrantes.",
        ),
    )
    visita_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO estancias (
            visita_id, nombre, tipo_estancia, ventilacion, planta,
            acabado_pavimento, acabado_paramento, acabado_techo, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "Salon",
            "Salón",
            "Sí",
            "",
            "Tarima",
            "Pintura",
            "Yeso",
            "Observacion de estancia inicial.",
        ),
    )
    estancia_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO biblioteca_patologias (
            nombre, categoria, elemento_afectado, rol_patologia, activo
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Humedad puntual", "humedades", "paramento", "efecto", 1),
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
            "Humedad puntual",
            "Registro vinculable para cuadrante.",
            "",
            "paramento",
            "Junto a ventana",
            "efecto",
        ),
    )
    registro_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO mapas_patologia (
            visita_id, titulo, descripcion, ambito_mapa,
            filas, columnas, imagen_base, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "Mapa salon",
            "Descripcion del mapa.",
            "unidad",
            2,
            2,
            "",
            "Observaciones del mapa.",
        ),
    )
    mapa_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO cuadrantes_mapa_patologia (
            mapa_id, codigo_cuadrante, descripcion,
            patologia_detectada, patologia_id, gravedad, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            mapa_id,
            "A1",
            "Descripcion inicial del cuadrante.",
            "Humedad puntual",
            registro_id,
            "media",
            "Observacion inicial del cuadrante.",
        ),
    )
    cuadrante_id = cur.lastrowid
    return {
        "visita_id": visita_id,
        "estancia_id": estancia_id,
        "registro_id": registro_id,
        "mapa_id": mapa_id,
        "cuadrante_id": cuadrante_id,
    }


def test_autosave_estancias_cuadrantes_renderiza_contrato(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "render")
        contexto = _crear_contexto_estancias_cuadrantes(cur, user_id, "render")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(f"/editar-estancia/{contexto['estancia_id']}")
    assert response.status_code == 200
    html = response.text
    assert "/static/js/autosave.js" in html
    assert "data-autosave-form" in html
    assert f"/estancias/{contexto['estancia_id']}/autosave" in html
    assert "Listo para editar" in html
    assert 'name="updated_at"' in html

    response = client.get(
        f"/editar-cuadrante-mapa-patologia/{contexto['cuadrante_id']}"
    )
    assert response.status_code == 200
    html = response.text
    assert "/static/js/autosave.js" in html
    assert "data-autosave-form" in html
    assert (
        f"/mapas-patologia/cuadrantes/{contexto['cuadrante_id']}/autosave"
        in html
    )
    assert "Listo para editar" in html
    assert 'name="updated_at"' in html

    response = client.get(f"/editar-mapa-patologia/{contexto['mapa_id']}")
    assert response.status_code == 200
    assert "data-autosave-form" not in response.text


def test_autosave_estancia_guarda_recarga_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "estancia")
        contexto = _crear_contexto_estancias_cuadrantes(cur, user_id, "estancia")
        conn.commit()
        estancia = cur.execute(
            "SELECT * FROM estancias WHERE id = ?",
            (contexto["estancia_id"],),
        ).fetchone()
        token_inicial = main_module.token_autosave_estancia(estancia)
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/estancias/{contexto['estancia_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "nombre": "Salon autosave",
            "tipo_estancia": "Salón",
            "ventilacion": "No",
            "planta": "",
            "acabado_pavimento": "Gres",
            "acabado_paramento": "Pintura revisada",
            "acabado_techo": "Escayola",
            "observaciones": "Observacion de estancia autosave persistida.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(f"/editar-estancia/{contexto['estancia_id']}")
    assert response.status_code == 200
    assert "Observacion de estancia autosave persistida." in response.text

    response = client.post(
        f"/estancias/{contexto['estancia_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "nombre": "Intento conflictivo",
            "tipo_estancia": "Salón",
            "ventilacion": "No",
            "planta": "",
            "acabado_pavimento": "Gres",
            "acabado_paramento": "Pintura revisada",
            "acabado_techo": "Escayola",
            "observaciones": "No debe sobrescribir silenciosamente.",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True


def test_autosave_cuadrante_guarda_recarga_y_detecta_conflicto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "cuadrante")
        contexto = _crear_contexto_estancias_cuadrantes(cur, user_id, "cuadrante")
        conn.commit()
        cuadrante = cur.execute(
            "SELECT * FROM cuadrantes_mapa_patologia WHERE id = ?",
            (contexto["cuadrante_id"],),
        ).fetchone()
        token_inicial = main_module.token_autosave_cuadrante_mapa_patologia(cuadrante)
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/mapas-patologia/cuadrantes/{contexto['cuadrante_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "descripcion": "Descripcion autosave del cuadrante.",
            "patologia_detectada": "",
            "patologia_ref": f"interior:{contexto['registro_id']}",
            "gravedad": "alta",
            "observaciones": "Observacion de cuadrante autosave persistida.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]

    response = client.get(
        f"/editar-cuadrante-mapa-patologia/{contexto['cuadrante_id']}"
    )
    assert response.status_code == 200
    assert "Observacion de cuadrante autosave persistida." in response.text
    assert "Descripcion autosave del cuadrante." in response.text

    response = client.post(
        f"/mapas-patologia/cuadrantes/{contexto['cuadrante_id']}/autosave",
        data={
            "updated_at": token_inicial,
            "descripcion": "Intento conflictivo",
            "patologia_detectada": "Humedad puntual",
            "patologia_ref": f"interior:{contexto['registro_id']}",
            "gravedad": "alta",
            "observaciones": "No debe sobrescribir silenciosamente.",
        },
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True
