from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Asistente", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_propuesta_con_linea(cur, user_id: int, numero: str, precio: float = 100) -> int:
    from app.routers.propuestas import recalcular_totales_propuesta

    cur.execute(
        """
        INSERT INTO clientes (nombre, tipo_cliente, owner_user_id)
        VALUES (?, ?, ?)
        """,
        (f"Cliente {numero}", "particular", user_id),
    )
    cliente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, cliente, direccion, owner_user_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (f"EXP-{numero}", f"Cliente {numero}", f"Calle {numero}", user_id),
    )
    expediente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO propuestas (
            numero_propuesta, cliente_id, expediente_id, fecha, estado,
            tipo_trabajo, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            cliente_id,
            expediente_id,
            "2026-06-01",
            "aceptada",
            "Informe pericial",
            user_id,
        ),
    )
    propuesta_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO propuesta_lineas (
            propuesta_id, categoria_servicio, concepto, descripcion,
            cantidad, precio_unitario, iva_porcentaje, orden
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            propuesta_id,
            "informe_pericial",
            "Informe pericial",
            "Redaccion de informe pericial.",
            1,
            precio,
            21,
            1,
        ),
    )
    recalcular_totales_propuesta(cur, propuesta_id)
    return propuesta_id


def _crear_factura_vinculada(
    cur,
    user_id: int,
    propuesta_id: int,
    estado: str,
    total: float,
    numero: str | None = "F-TEST-0001",
) -> int:
    propuesta = cur.execute(
        "SELECT cliente_id, expediente_id FROM propuestas WHERE id = ?",
        (propuesta_id,),
    ).fetchone()
    cur.execute(
        """
        INSERT INTO facturas_emitidas (
            numero_factura, serie, fecha, fecha_emision, estado, cliente_id,
            propuesta_id, expediente_id, concepto_general, base_imponible,
            iva, total, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            "F",
            "2026-06-05",
            "2026-06-05" if estado != "borrador" else None,
            estado,
            propuesta["cliente_id"],
            propuesta_id,
            propuesta["expediente_id"],
            "Factura vinculada de prueba",
            total / 1.21,
            total - (total / 1.21),
            total,
            user_id,
        ),
    )
    return cur.lastrowid


def _facturas_propuesta(cur, propuesta_id: int):
    return cur.execute(
        """
        SELECT *
        FROM facturas_emitidas
        WHERE propuesta_id = ?
        ORDER BY id ASC
        """,
        (propuesta_id,),
    ).fetchall()


def test_asistente_crea_borrador_total_sin_emitir(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_total")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-001")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "total", "porcentaje": "50", "importe": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        factura = _facturas_propuesta(conn.cursor(), propuesta_id)[0]
    finally:
        conn.close()

    assert factura["estado"] == "borrador"
    assert factura["numero_factura"] is None
    assert factura["fecha_emision"] is None
    assert factura["hash_factura"] is None
    assert factura["total"] == 121


def test_asistente_crea_borrador_anticipo_50(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_anticipo")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-002", 200)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "anticipo_porcentaje", "porcentaje": "50", "importe": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        factura = _facturas_propuesta(conn.cursor(), propuesta_id)[0]
    finally:
        conn.close()

    assert factura["estado"] == "borrador"
    assert factura["tipo_factura"] == "anticipo"
    assert factura["total"] == 121


def test_asistente_crea_borrador_importe_libre(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_libre")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-003", 200)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "importe_libre", "porcentaje": "50", "importe": "121"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        factura = _facturas_propuesta(conn.cursor(), propuesta_id)[0]
    finally:
        conn.close()

    assert factura["estado"] == "borrador"
    assert factura["total"] == 121


def test_asistente_crea_borrador_final_pendiente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_final")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-004", 200)
        factura_emitida_id = _crear_factura_vinculada(
            cur,
            user_id,
            propuesta_id,
            "emitida",
            121,
            "F-AST-004",
        )
        factura_emitida_previa = cur.execute(
            "SELECT * FROM facturas_emitidas WHERE id = ?",
            (factura_emitida_id,),
        ).fetchone()
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "final_pendiente", "porcentaje": "50", "importe": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        facturas = _facturas_propuesta(cur, propuesta_id)
        factura_emitida_despues = cur.execute(
            "SELECT * FROM facturas_emitidas WHERE id = ?",
            (factura_emitida_id,),
        ).fetchone()
    finally:
        conn.close()

    borrador = [factura for factura in facturas if factura["estado"] == "borrador"][0]
    assert borrador["tipo_factura"] == "final"
    assert borrador["total"] == 121
    assert factura_emitida_despues["estado"] == factura_emitida_previa["estado"]
    assert factura_emitida_despues["numero_factura"] == factura_emitida_previa["numero_factura"]
    assert factura_emitida_despues["hash_factura"] == factura_emitida_previa["hash_factura"]


def test_asistente_no_cuenta_facturas_anuladas(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_anulada")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-005", 200)
        _crear_factura_vinculada(cur, user_id, propuesta_id, "anulada", 121, "F-AST-005")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "final_pendiente", "porcentaje": "50", "importe": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        facturas = _facturas_propuesta(conn.cursor(), propuesta_id)
    finally:
        conn.close()

    borrador = [factura for factura in facturas if factura["estado"] == "borrador"][0]
    assert borrador["total"] == 242


def test_asistente_avisa_con_borrador_existente_y_no_crea_otro(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "asistente_borrador_existente")
        propuesta_id = _crear_propuesta_con_linea(cur, user_id, "P-AST-006")
        borrador_id = _crear_factura_vinculada(
            cur,
            user_id,
            propuesta_id,
            "borrador",
            121,
            None,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    page = client.get(f"/propuestas/{propuesta_id}/crear-factura-asistente")
    assert page.status_code == 200
    assert "Ya existe un borrador vinculado" in page.text
    assert f"/facturacion/facturas/{borrador_id}" in page.text

    response = client.post(
        f"/propuestas/{propuesta_id}/crear-factura-asistente",
        data={"modo": "total", "porcentaje": "50", "importe": ""},
    )
    assert response.status_code == 200
    assert "Abre el borrador existente" in response.text

    conn = get_connection()
    try:
        facturas = _facturas_propuesta(conn.cursor(), propuesta_id)
    finally:
        conn.close()

    assert len(facturas) == 1
    assert facturas[0]["id"] == borrador_id
