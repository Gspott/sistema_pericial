from fastapi.testclient import TestClient


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", "valoracion_ajustes_form", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_ajustes_homogeneizacion_manual_guardan_coeficiente_sin_tocar_testigo_base(
    isolated_import,
):
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
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-AJUSTES-001",
                "valoracion",
                "particular",
                "Cliente ajustes",
                "Calle ajustes",
                user_id,
            ),
        )
        expediente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, fuente_testigo,
                superficie_construida, valor_unitario, validacion_estado,
                reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "Calle Testigo Ajustes",
                "Portal ajustes",
                100,
                2000,
                "validado",
                1,
            ),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json,
                notas_seleccion, valor_unitario_base
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                1,
                1,
                '{"direccion_testigo": "Calle Testigo Ajustes"}',
                "Seleccionado para ajustes.",
                2000,
            ),
        )
        vinculo_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes"
    )
    assert response.status_code == 200
    assert "Ajustes de testigo" in response.text
    assert "Calle Testigo Ajustes" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes",
        data={
            "ajuste_superficie_construida": "0.02",
            "ajuste_ubicacion": "0.03",
            "ajuste_antiguedad": "-0.01",
            "ajuste_calidades": "0.00",
            "ajuste_caracteristicas_constructivas": "0.04",
            "justificacion": "Ajustes manuales por comparación directa.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        ajuste = cur.execute(
            """
            SELECT *
            FROM valoracion_testigo_ajustes
            WHERE expediente_testigo_id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        vinculo = cur.execute(
            """
            SELECT *
            FROM valoracion_expediente_testigos
            WHERE id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        testigo_base = cur.execute(
            """
            SELECT *
            FROM testigos_valoracion
            WHERE id = ?
            """,
            (testigo_id,),
        ).fetchone()
    finally:
        conn.close()

    assert ajuste is not None
    assert ajuste["ajuste_superficie_construida"] == 0.02
    assert ajuste["ajuste_ubicacion"] == 0.03
    assert ajuste["ajuste_antiguedad"] == -0.01
    assert ajuste["ajuste_calidades"] == 0
    assert ajuste["ajuste_caracteristicas_constructivas"] == 0.04
    assert round(ajuste["coeficiente_total"], 2) == 1.08
    assert ajuste["justificacion"] == "Ajustes manuales por comparación directa."
    assert round(vinculo["valor_unitario_ajustado"], 2) == 2160
    assert testigo_base["valor_unitario"] == 2000

    contexto = build_informe_context(expediente_id)
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["origen"] == "modelo_nuevo"
    assert round(comparable["coeficiente_total"], 2) == 1.08
    assert round(comparable["valor_unitario_ajustado"], 2) == 2160
    assert comparable["ajustes"]["justificacion"] == (
        "Ajustes manuales por comparación directa."
    )

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes",
        data={
            "ajuste_superficie_construida": "0.25",
            "ajuste_ubicacion": "0",
            "ajuste_antiguedad": "0",
            "ajuste_calidades": "0",
            "ajuste_caracteristicas_constructivas": "0",
            "justificacion": "No debe guardarse.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 400

    conn = get_connection()
    try:
        cur = conn.cursor()
        ajuste_tras_error = cur.execute(
            """
            SELECT *
            FROM valoracion_testigo_ajustes
            WHERE expediente_testigo_id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        vinculo_tras_error = cur.execute(
            """
            SELECT *
            FROM valoracion_expediente_testigos
            WHERE id = ?
            """,
            (vinculo_id,),
        ).fetchone()
        testigo_base_tras_error = cur.execute(
            """
            SELECT *
            FROM testigos_valoracion
            WHERE id = ?
            """,
            (testigo_id,),
        ).fetchone()
    finally:
        conn.close()

    assert round(ajuste_tras_error["coeficiente_total"], 2) == 1.08
    assert ajuste_tras_error["justificacion"] == (
        "Ajustes manuales por comparación directa."
    )
    assert round(vinculo_tras_error["valor_unitario_ajustado"], 2) == 2160
    assert testigo_base_tras_error["valor_unitario"] == 2000
