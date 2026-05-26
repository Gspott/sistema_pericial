from fastapi.testclient import TestClient


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", "valoracion_obs_form", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _campo_valor(campos, etiqueta: str) -> str:
    for campo in campos:
        if campo["label"] == etiqueta:
            return campo["value"]
    raise AssertionError(f"Campo no encontrado: {etiqueta}")


def test_valoracion_visita_observaciones_form_guarda_sin_tocar_legacy(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-OBS-001",
                "valoracion",
                "particular",
                "Cliente Valoracion Observaciones",
                "Calle Valoracion Observaciones 1",
                "Vivienda",
                user_id,
            ),
        )
        expediente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, identificacion_bien
            )
            VALUES (?, ?, ?)
            """,
            (
                expediente_id,
                "Compraventa",
                "Vivienda demo observaciones",
            ),
        )
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_id,
                "2026-05-25",
                "Tecnico Smoke",
                "Visita de valoracion.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, estado_inmueble, regimen_ocupacion,
                observaciones_valoracion
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Estado legacy",
                "Ocupacion legacy",
                "Observacion legacy",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(f"/visitas/{visita_id}/valoracion-observaciones")
    assert response.status_code == 200
    assert "Observaciones de valoración" in response.text
    assert "Legacy visita: Estado legacy" in response.text

    response = client.post(
        f"/visitas/{visita_id}/valoracion-observaciones",
        data={
            "estado_observado": "Buen estado observado",
            "reforma_observada": "Reforma parcial observada",
            "ocupacion_observada": "Libre observado",
            "observaciones_inspeccion_valoracion": "Inspeccion visual completa",
            "incidencias_valoracion": "Sin incidencias relevantes",
            "comprobaciones_fisicas": "Superficies no medidas in situ",
            "observaciones_portal": "Portal observado sin incidencias.",
            "observaciones_cuadro_contadores": "Cuadro de contadores accesible.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == (
        f"/nueva-visita/{expediente_id}?visita_id={visita_id}"
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        observaciones = cur.execute(
            """
            SELECT *
            FROM valoracion_visita_observaciones
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone()
        legacy = cur.execute(
            """
            SELECT *
            FROM valoracion_visita
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone()
    finally:
        conn.close()

    assert observaciones is not None
    assert observaciones["expediente_id"] == expediente_id
    assert observaciones["estado_observado"] == "Buen estado observado"
    assert observaciones["reforma_observada"] == "Reforma parcial observada"
    assert observaciones["ocupacion_observada"] == "Libre observado"
    assert observaciones["observaciones_portal"] == "Portal observado sin incidencias."
    assert (
        observaciones["observaciones_cuadro_contadores"]
        == "Cuadro de contadores accesible."
    )
    assert legacy["estado_inmueble"] == "Estado legacy"
    assert legacy["regimen_ocupacion"] == "Ocupacion legacy"

    contexto = build_informe_context(expediente_id)
    grupo_estado = next(
        grupo
        for grupo in contexto["valoracion"][0]["grupos"]
        if grupo["clave"] == "estado"
    )
    assert (
        _campo_valor(grupo_estado["campos"], "Estado actual del inmueble")
        == "Buen estado observado"
    )
    assert (
        _campo_valor(grupo_estado["campos"], "Régimen de ocupación")
        == "Libre observado"
    )
    assert (
        _campo_valor(grupo_estado["campos"], "Observaciones del portal")
        == "Portal observado sin incidencias."
    )
    assert (
        _campo_valor(
            grupo_estado["campos"],
            "Observaciones del cuadro de contadores",
        )
        == "Cuadro de contadores accesible."
    )


def test_detalle_expediente_muestra_cta_observaciones_solo_en_valoracion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-OBS-CTA",
                "valoracion",
                "particular",
                "Cliente CTA Valoracion",
                "Calle CTA Valoracion",
                user_id,
            ),
        )
        expediente_valoracion_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_valoracion_id,
                "2026-05-25",
                "Tecnico Smoke",
                "Visita valoracion CTA.",
            ),
        )
        visita_valoracion_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PAT-OBS-CTA",
                "patologias",
                "particular",
                "Cliente CTA Patologias",
                "Calle CTA Patologias",
                user_id,
            ),
        )
        expediente_patologias_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_patologias_id,
                "2026-05-25",
                "Tecnico Smoke",
                "Visita patologias CTA.",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response_valoracion = client.get(f"/detalle-expediente/{expediente_valoracion_id}")
    assert response_valoracion.status_code == 200
    assert "Observaciones de valoración" in response_valoracion.text
    assert (
        f"/visitas/{visita_valoracion_id}/valoracion-observaciones"
        in response_valoracion.text
    )

    response_patologias = client.get(f"/detalle-expediente/{expediente_patologias_id}")
    assert response_patologias.status_code == 200
    assert "Observaciones de valoración" not in response_patologias.text
