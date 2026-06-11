from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Actuaciones", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente_y_coste(cur, owner_id: int):
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
            "EXP-COSTES-EXP-1",
            "patologias",
            "particular",
            "Cliente actuaciones",
            "Calle Actuaciones 1",
            "28000",
            "Madrid",
            "Madrid",
            "Vivienda",
            "Actuaciones de reparación.",
            "Daños por filtraciones.",
            "Obra de cubierta.",
            "Indicios demo.",
            "Reparación por actuaciones.",
            owner_id,
        ),
    )
    expediente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, fecha_base, provincia, origen, version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "Base actuaciones",
            "Base temporal para actuaciones.",
            "2026-06-05",
            "Madrid",
            "manual",
            "costes-exp-1",
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
            "ACT.001",
            "partida",
            "m2",
            "Pintura de paramentos afectados",
            "Aplicación de pintura plástica en paramentos interiores.",
            12.5,
            "EUR",
            "2026-06-05",
            "Madrid",
            "validado",
        ),
    )
    concepto_id = cur.lastrowid
    return expediente_id, concepto_id


def _crear_actuacion_con_partida(cur, expediente_id: int, concepto_id: int):
    cur.execute(
        """
        INSERT INTO actuaciones_reparacion (
            expediente_id, titulo, descripcion, observaciones, orden, updated_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            expediente_id,
            "Pintura de paramentos afectados",
            "Repaso y pintado de paramentos interiores dañados.",
            "Medición agrupada por actuaciones.",
            1,
        ),
    )
    actuacion_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO actuacion_partidas (
            actuacion_id, concepto_id, descripcion_snapshot,
            unidad_snapshot, precio_unitario_snapshot, cantidad, importe, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            actuacion_id,
            concepto_id,
            "Pintura snapshot por actuación",
            "m2",
            12.5,
            4,
            50,
        ),
    )
    return actuacion_id, cur.lastrowid


def _crear_patologia_coste_fallback(cur, expediente_id: int, concepto_id: int):
    cur.execute(
        """
        INSERT INTO visitas (
            expediente_id, fecha, tecnico, observaciones_visita
        )
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, "2026-06-05", "Tecnico", "Visita para fallback."),
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
            "Dormitorio",
            "dormitorio",
            "Natural",
            "1",
            "Tarima",
            "Pintura",
            "Yeso",
            "Estancia fallback.",
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
            "Mancha por filtración",
            "Patología para fallback económico.",
            "",
            "pared",
            "Junto a ventana",
            "",
        ),
    )
    patologia_id = cur.lastrowid
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
            "Partida fallback por patología",
            2,
            "m2",
            12.5,
            25,
            "incluido",
            "Debe usarse solo si no hay actuaciones.",
        ),
    )
    return patologia_id


def test_actuaciones_reparacion_tablas_idempotentes(isolated_import):
    isolated_import("app.main")

    from app import database

    database.init_db()
    database.init_db()

    conn = database.get_connection()
    try:
        cur = conn.cursor()
        columnas_actuaciones = {
            row["name"]
            for row in cur.execute(
                "PRAGMA table_info(actuaciones_reparacion)"
            ).fetchall()
        }
        columnas_partidas = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(actuacion_partidas)").fetchall()
        }
        indices = {
            row["name"]
            for row in cur.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                  AND (
                    name LIKE 'idx_actuaciones_reparacion_%'
                    OR name LIKE 'idx_actuacion_partidas_%'
                  )
                """
            ).fetchall()
        }
    finally:
        conn.close()

    assert {
        "id",
        "expediente_id",
        "titulo",
        "descripcion",
        "observaciones",
        "orden",
        "created_at",
        "updated_at",
    } <= columnas_actuaciones
    assert {
        "id",
        "actuacion_id",
        "concepto_id",
        "descripcion_snapshot",
        "unidad_snapshot",
        "precio_unitario_snapshot",
        "cantidad",
        "importe",
        "created_at",
        "updated_at",
    } <= columnas_partidas
    assert {
        "idx_actuaciones_reparacion_expediente_id",
        "idx_actuaciones_reparacion_orden",
        "idx_actuacion_partidas_actuacion_id",
        "idx_actuacion_partidas_concepto_id",
    } <= indices


def test_anexo_economico_actuaciones_solo_con_flag(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_exp_2_owner")
        expediente_id, concepto_id = _crear_expediente_y_coste(cur, owner_id)
        _crear_actuacion_con_partida(cur, expediente_id, concepto_id)
        conn.commit()
    finally:
        conn.close()

    template = main_module.templates.env.get_template("informes/imprimir.html")
    contexto_sin_flag = build_informe_context(expediente_id)
    html_sin_flag = template.render({"request": None, "modo_pdf": False, **contexto_sin_flag})
    assert contexto_sin_flag["anexo_economico_reparacion"]["tiene_costes"] is True
    assert contexto_sin_flag["anexo_economico_reparacion"]["modo"] == "actuaciones"
    assert contexto_sin_flag["anexo_economico_reparacion"]["incluido"] is False
    assert "Anexo económico de reparación" not in html_sin_flag

    contexto_con_flag = build_informe_context(
        expediente_id,
        incluir_anexo_economico_reparacion=True,
    )
    html_con_flag = template.render({"request": None, "modo_pdf": False, **contexto_con_flag})
    anexo = contexto_con_flag["anexo_economico_reparacion"]
    assert anexo["incluido"] is True
    assert anexo["modo"] == "actuaciones"
    assert anexo["total_pem"] == 50
    assert "La valoración económica se estructura por actuaciones de reparación" in html_con_flag
    assert "Pintura de paramentos afectados" in html_con_flag
    assert "Pintura snapshot por actuación" in html_con_flag
    assert "Total PEM de reparación" in html_con_flag
    assert "50.00 €" in html_con_flag


def test_anexo_economico_prioriza_actuaciones_sobre_patologias(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import (
        build_informe_context,
        generar_informe_docx_editable_bytes,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_exp_2_prioridad_owner")
        expediente_id, concepto_id = _crear_expediente_y_coste(cur, owner_id)
        _crear_actuacion_con_partida(cur, expediente_id, concepto_id)
        _crear_patologia_coste_fallback(cur, expediente_id, concepto_id)
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(
        expediente_id,
        incluir_anexo_economico_reparacion=True,
    )
    template = main_module.templates.env.get_template("informes/imprimir.html")
    html = template.render({"request": None, "modo_pdf": False, **contexto})
    anexo = contexto["anexo_economico_reparacion"]

    assert anexo["incluido"] is True
    assert anexo["modo"] == "actuaciones"
    assert anexo["total_pem"] == 50
    assert "Pintura snapshot por actuación" in html
    assert "Partida fallback por patología" not in html

    docx_bytes = generar_informe_docx_editable_bytes(
        expediente_id,
        incluir_anexo_economico_reparacion=True,
    )
    assert docx_bytes.startswith(b"PK")


def test_actuaciones_reparacion_flujo_snapshot_total_y_borrados(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_exp_1_owner")
        expediente_id, concepto_id = _crear_expediente_y_coste(cur, owner_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get(f"/expedientes/{expediente_id}/actuaciones-reparacion")
    assert response.status_code == 200
    assert "Actuaciones de reparación" in response.text
    assert "Total PEM del expediente" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/actuaciones-reparacion",
        data={
            "titulo": "Pintura de paramentos afectados",
            "descripcion": "Pintura tras filtraciones.",
            "observaciones": "Medición por estancias.",
            "orden": "2",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        actuacion = conn.execute(
            "SELECT * FROM actuaciones_reparacion WHERE expediente_id = ?",
            (expediente_id,),
        ).fetchone()
        assert actuacion is not None
        actuacion_id = actuacion["id"]
        assert actuacion["titulo"] == "Pintura de paramentos afectados"
        assert actuacion["orden"] == 2
    finally:
        conn.close()

    response = client.get(
        f"/expedientes/{expediente_id}/actuaciones-reparacion"
        f"?actuacion_id={actuacion_id}&q=ACT.001"
    )
    assert response.status_code == 200
    assert "ACT.001" in response.text

    response = client.post(
        f"/actuaciones-reparacion/{actuacion_id}/partidas",
        data={
            "concepto_id": str(concepto_id),
            "cantidad": "3",
            "q": "ACT.001",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        partida = conn.execute(
            "SELECT * FROM actuacion_partidas WHERE actuacion_id = ?",
            (actuacion_id,),
        ).fetchone()
        assert partida is not None
        partida_id = partida["id"]
        assert partida["concepto_id"] == concepto_id
        assert partida["descripcion_snapshot"] == (
            "Aplicación de pintura plástica en paramentos interiores."
        )
        assert partida["unidad_snapshot"] == "m2"
        assert partida["precio_unitario_snapshot"] == 12.5
        assert partida["cantidad"] == 3
        assert partida["importe"] == 37.5
        conn.execute(
            """
            UPDATE costes_conceptos
            SET precio = 99, unidad = 'ud', descripcion = 'Biblioteca alterada'
            WHERE id = ?
            """,
            (concepto_id,),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.post(
        f"/actuacion-partidas/{partida_id}/actualizar",
        data={"cantidad": "4"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        partida = conn.execute(
            "SELECT * FROM actuacion_partidas WHERE id = ?",
            (partida_id,),
        ).fetchone()
        assert partida["unidad_snapshot"] == "m2"
        assert partida["precio_unitario_snapshot"] == 12.5
        assert partida["cantidad"] == 4
        assert partida["importe"] == 50
        presupuesto = main_module.preparar_actuaciones_reparacion_expediente(
            conn.cursor(),
            expediente_id,
        )
        assert presupuesto["actuaciones"][0]["subtotal"] == 50
        assert presupuesto["total_pem"] == 50
    finally:
        conn.close()

    response = client.get(f"/expedientes/{expediente_id}/actuaciones-reparacion")
    assert response.status_code == 200
    assert "50,00 €" in response.text
    assert "Informe con anexo económico" in response.text
    assert "Biblioteca alterada" not in response.text

    response = client.get(f"/detalle-expediente/{expediente_id}")
    assert response.status_code == 200
    assert "Actuaciones de reparación" in response.text
    assert "Ver informe con anexo económico" in response.text

    response = client.post(
        f"/actuacion-partidas/{partida_id}/borrar",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        total_partidas = conn.execute(
            "SELECT COUNT(*) FROM actuacion_partidas WHERE actuacion_id = ?",
            (actuacion_id,),
        ).fetchone()[0]
        assert total_partidas == 0
    finally:
        conn.close()

    response = client.post(
        f"/actuaciones-reparacion/{actuacion_id}/borrar",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        total_actuaciones = conn.execute(
            "SELECT COUNT(*) FROM actuaciones_reparacion WHERE expediente_id = ?",
            (expediente_id,),
        ).fetchone()[0]
        assert total_actuaciones == 0
    finally:
        conn.close()
