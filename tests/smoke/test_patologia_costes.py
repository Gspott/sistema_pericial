from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "PatologiaCostes", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_patologia_y_coste(cur, owner_id: int):
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario, cliente,
            direccion, codigo_postal, ciudad, provincia, tipo_inmueble,
            objeto_pericia, descripcion_dano, causa_probable,
            pruebas_indicios, propuesta_reparacion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EXP-COSTES-4A-001",
            "patologias",
            "particular",
            "Cliente costes 4A",
            "Calle Costes 4A 1",
            "28000",
            "Madrid",
            "Madrid",
            "Vivienda",
            "Vinculación controlada de costes.",
            "Daño demo.",
            "Causa demo.",
            "Indicios demo.",
            "Reparación demo.",
            owner_id,
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
        (expediente_id, "2026-06-05", "Tecnico", "Visita costes 4A."),
    )
    visita_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO estancias (
            visita_id, nombre, tipo_estancia, ventilacion, planta,
            acabado_pavimento, acabado_paramento, acabado_techo,
            observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "Salon",
            "salon",
            "Natural",
            "1",
            "Ceramico",
            "Pintura",
            "Yeso",
            "Estancia demo.",
        ),
    )
    estancia_id = cur.lastrowid
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
            "Humedad demo",
            "Patología para costes.",
            "",
            "paramento",
            "Zona inferior",
            "",
        ),
    )
    patologia_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, fecha_base, provincia, origen, version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Base costes 4A",
            "Base temporal para vinculación.",
            "2026-06-05",
            "Madrid",
            "manual",
            "costes-4a",
        ),
    )
    base_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_conceptos (
            base_id, codigo, tipo, unidad, resumen, descripcion,
            precio, moneda, fecha_base, provincia, estado, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            base_id,
            "REP.001",
            "partida",
            "m2",
            "Reparación de revestimiento",
            "Partida validada para subsanación.",
            25.5,
            "EUR",
            "2026-06-05",
            "Madrid",
            "validado",
        ),
    )
    concepto_id = cur.lastrowid
    return expediente_id, patologia_id, concepto_id


def test_patologia_costes_tabla_idempotente(isolated_import):
    isolated_import("app.main")

    from app import database

    database.init_db()
    database.init_db()

    conn = database.get_connection()
    try:
        cur = conn.cursor()
        columnas = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(patologia_costes)").fetchall()
        }
        indices = {
            row["name"]
            for row in cur.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index' AND name LIKE 'idx_patologia_costes_%'
                """
            ).fetchall()
        }
    finally:
        conn.close()

    assert {
        "id",
        "patologia_id",
        "concepto_id",
        "descripcion_actuacion",
        "cantidad",
        "unidad",
        "precio_unitario",
        "importe",
        "estado",
        "observaciones",
    } <= columnas
    assert {
        "idx_patologia_costes_patologia_id",
        "idx_patologia_costes_concepto_id",
        "idx_patologia_costes_estado",
    } <= indices


def test_patologia_costes_vincula_snapshot_recalcula_y_borra(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_4a_owner")
        _expediente_id, patologia_id, concepto_id = _crear_patologia_y_coste(cur, owner_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get(f"/editar-registro/{patologia_id}?cost_q=REP.001")
    assert response.status_code == 200
    assert "Coste de subsanación" in response.text
    assert "REP.001" in response.text

    response = client.post(
        f"/patologias/{patologia_id}/costes",
        data={
            "concepto_id": str(concepto_id),
            "cantidad": "2,5",
            "descripcion_actuacion": "Reparación medida en visita",
            "observaciones": "Snapshot inicial",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/editar-registro/{patologia_id}")

    conn = get_connection()
    try:
        vinculo = conn.execute(
            """
            SELECT *
            FROM patologia_costes
            WHERE patologia_id = ?
            """,
            (patologia_id,),
        ).fetchone()
        assert vinculo is not None
        assert vinculo["concepto_id"] == concepto_id
        assert vinculo["unidad"] == "m2"
        assert vinculo["precio_unitario"] == 25.5
        assert vinculo["cantidad"] == 2.5
        assert vinculo["importe"] == 63.75
        assert vinculo["estado"] == "incluido"
        vinculo_id = vinculo["id"]
    finally:
        conn.close()

    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE costes_conceptos
            SET precio = 99, unidad = 'ud'
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.post(
        f"/patologias/costes/{vinculo_id}/actualizar",
        data={
            "cantidad": "3",
            "descripcion_actuacion": "Reparación ajustada",
            "estado": "incluido",
            "observaciones": "Cantidad revisada",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        vinculo = conn.execute(
            "SELECT * FROM patologia_costes WHERE id = ?",
            (vinculo_id,),
        ).fetchone()
        assert vinculo["unidad"] == "m2"
        assert vinculo["precio_unitario"] == 25.5
        assert vinculo["cantidad"] == 3
        assert vinculo["importe"] == 76.5
        assert vinculo["observaciones"] == "Cantidad revisada"
    finally:
        conn.close()

    response = client.post(
        f"/patologias/costes/{vinculo_id}/borrar",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM patologia_costes WHERE patologia_id = ?",
            (patologia_id,),
        ).fetchone()[0]
        assert total == 0
    finally:
        conn.close()


def test_presupuesto_reparacion_expediente_agrupa_costes_y_total(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_4b_owner")
        expediente_id, patologia_id, concepto_id = _crear_patologia_y_coste(cur, owner_id)
        cur.execute(
            """
            INSERT INTO patologia_costes (
                patologia_id, concepto_id, descripcion_actuacion,
                cantidad, unidad, precio_unitario, importe, estado,
                observaciones, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                patologia_id,
                concepto_id,
                "Reparación presupuestada",
                2,
                "m2",
                25.5,
                51.0,
                "incluido",
                "Incluido en PEM",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get(f"/expedientes/{expediente_id}/presupuesto-reparacion")
    assert response.status_code == 200
    assert "Presupuesto de reparación" in response.text
    assert "Humedad demo" in response.text
    assert "Reparación presupuestada" in response.text
    assert "Subtotal patología" in response.text
    assert "51,00 €" in response.text
    assert "Total PEM reparación" in response.text

    response = client.get(f"/detalle-expediente/{expediente_id}")
    assert response.status_code == 200
    assert "Presupuesto de reparación" in response.text


def test_presupuesto_reparacion_expediente_sin_costes_muestra_vacio(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_4b_empty_owner")
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario, cliente,
                direccion, codigo_postal, ciudad, provincia, tipo_inmueble,
                objeto_pericia, descripcion_dano, causa_probable,
                pruebas_indicios, propuesta_reparacion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-COSTES-4B-VACIO",
                "patologias",
                "particular",
                "Cliente sin costes",
                "Calle Sin Costes 1",
                "28000",
                "Madrid",
                "Madrid",
                "Vivienda",
                "Presupuesto vacío.",
                "Daño sin coste.",
                "Causa.",
                "Indicios.",
                "Reparación pendiente.",
                owner_id,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get(f"/expedientes/{expediente_id}/presupuesto-reparacion")
    assert response.status_code == 200
    assert "Sin costes vinculados" in response.text
    assert "0,00 €" in response.text


def test_informe_anexo_economico_solo_con_flag_y_costes(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_4c_owner")
        expediente_id, patologia_id, concepto_id = _crear_patologia_y_coste(cur, owner_id)
        cur.execute(
            """
            INSERT INTO patologia_costes (
                patologia_id, concepto_id, descripcion_actuacion,
                cantidad, unidad, precio_unitario, importe, estado,
                observaciones, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                patologia_id,
                concepto_id,
                "Reparación para anexo",
                2,
                "m2",
                25.5,
                51.0,
                "incluido",
                "PEM orientativo",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    template = main_module.templates.env.get_template("informes/imprimir.html")
    contexto_sin_flag = build_informe_context(expediente_id)
    html_sin_flag = template.render({"request": None, "modo_pdf": False, **contexto_sin_flag})
    assert contexto_sin_flag["anexo_economico_reparacion"]["tiene_costes"] is True
    assert contexto_sin_flag["anexo_economico_reparacion"]["modo"] == "patologias"
    assert contexto_sin_flag["anexo_economico_reparacion"]["incluido"] is False
    assert "Anexo económico de reparación" not in html_sin_flag

    contexto_con_flag = build_informe_context(
        expediente_id,
        incluir_anexo_economico_reparacion=True,
    )
    html_con_flag = template.render({"request": None, "modo_pdf": False, **contexto_con_flag})
    assert contexto_con_flag["anexo_economico_reparacion"]["incluido"] is True
    assert contexto_con_flag["anexo_economico_reparacion"]["modo"] == "patologias"
    assert "Anexo económico de reparación" in html_con_flag
    assert "La valoración económica siguiente se realiza a efectos orientativos/periciales" in html_con_flag
    assert "Reparación para anexo" in html_con_flag
    assert "51.00 €" in html_con_flag
    assert "Total PEM de reparación" in html_con_flag


def test_informe_anexo_economico_no_aparece_sin_costes_aunque_haya_flag(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_4c_empty_owner")
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario, cliente,
                direccion, codigo_postal, ciudad, provincia, tipo_inmueble,
                objeto_pericia, descripcion_dano, causa_probable,
                pruebas_indicios, propuesta_reparacion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-COSTES-4C-VACIO",
                "patologias",
                "particular",
                "Cliente anexo vacío",
                "Calle Anexo Vacío 1",
                "28000",
                "Madrid",
                "Madrid",
                "Vivienda",
                "Anexo vacío.",
                "Daño.",
                "Causa.",
                "Indicios.",
                "Reparación pendiente.",
                owner_id,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(
        expediente_id,
        incluir_anexo_economico_reparacion=True,
    )
    template = main_module.templates.env.get_template("informes/imprimir.html")
    html = template.render({"request": None, "modo_pdf": False, **contexto})
    assert contexto["anexo_economico_reparacion"]["tiene_costes"] is False
    assert contexto["anexo_economico_reparacion"]["incluido"] is False
    assert "Anexo económico de reparación" not in html
