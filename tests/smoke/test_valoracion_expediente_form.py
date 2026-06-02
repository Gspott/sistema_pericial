from fastapi.testclient import TestClient


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", "valoracion_form", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_valoracion_expediente_form_guarda_modelo_nuevo_sin_migrar_legacy(isolated_import):
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
                "EXP-VAL-FORM-001",
                "valoracion",
                "particular",
                "Cliente Valoracion Form",
                "Calle Valoracion Form 1",
                "Vivienda",
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
                "2026-05-25",
                "Tecnico Smoke",
                "Visita legacy previa.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, identificacion_bien,
                superficie_valoracion
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Finalidad legacy previa",
                "Identificacion legacy previa",
                "80 m2 legacy",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(f"/expedientes/{expediente_id}/valoracion")
    assert response.status_code == 200
    assert "Datos de valoración" in response.text
    assert "Legacy visita: Finalidad legacy previa" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion",
        data={
            "finalidad_valoracion": "Compraventa modelo nuevo",
            "documentacion_utilizada": "Catastro y nota simple",
            "identificacion_bien": "Vivienda modelo nuevo form",
            "superficie_valoracion": "95 m2",
            "situacion_urbanistica": "Suelo urbano consolidado",
            "descripcion_entorno": "Entorno residencial consolidado",
            "criterios_metodo_valoracion": "Comparación",
            "condicionantes_limitaciones_valoracion": "Superficies no comprobadas",
            "metodo_comparacion_activo": "1",
            "metodo_coste_activo": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/detalle-expediente/{expediente_id}")

    conn = get_connection()
    try:
        cur = conn.cursor()
        valoracion = cur.execute(
            """
            SELECT *
            FROM valoracion_expediente
            WHERE expediente_id = ?
            """,
            (expediente_id,),
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

    assert valoracion is not None
    assert valoracion["finalidad_valoracion"] == "Compraventa modelo nuevo"
    assert valoracion["identificacion_bien"] == "Vivienda modelo nuevo form"
    assert valoracion["metodo_comparacion_activo"] == 1
    assert legacy["finalidad_valoracion"] == "Finalidad legacy previa"
    assert legacy["identificacion_bien"] == "Identificacion legacy previa"

    contexto = build_informe_context(expediente_id)
    grupo_encargo = next(
        grupo
        for grupo in contexto["valoracion"][0]["grupos"]
        if grupo["clave"] == "encargo"
    )
    finalidad = next(
        campo
        for campo in grupo_encargo["campos"]
        if campo["label"] == "Finalidad de la valoración"
    )
    assert finalidad["value"] == "Compraventa modelo nuevo"


def test_detalle_expediente_muestra_cta_solo_en_valoracion(isolated_import):
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
                "EXP-VAL-CTA",
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
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PAT-CTA",
                "patologias",
                "particular",
                "Cliente CTA Patologias",
                "Calle CTA Patologias",
                user_id,
            ),
        )
        expediente_patologias_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response_valoracion = client.get(f"/detalle-expediente/{expediente_valoracion_id}")
    assert response_valoracion.status_code == 200
    assert "Editar datos de valoración" in response_valoracion.text
    assert f"/expedientes/{expediente_valoracion_id}/valoracion" in response_valoracion.text
    assert "Workbench de valoración" in response_valoracion.text
    assert (
        f"/expediente/{expediente_valoracion_id}/valoracion/workbench"
        in response_valoracion.text
    )
    assert (
        "Análisis técnico de comparables, homogeneización y ponderación"
        in response_valoracion.text
    )
    response_workbench = client.get(
        f"/expediente/{expediente_valoracion_id}/valoracion/workbench"
    )
    assert response_workbench.status_code == 200
    assert "Workbench de valoración" in response_workbench.text

    response_patologias = client.get(f"/detalle-expediente/{expediente_patologias_id}")
    assert response_patologias.status_code == 200
    assert "Editar datos de valoración" not in response_patologias.text
    assert "Workbench de valoración" not in response_patologias.text
