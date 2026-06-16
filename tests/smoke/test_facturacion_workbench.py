from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str = "facturacion_workbench") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Workbench", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_cliente(cur, user_id: int, nombre: str) -> int:
    cur.execute(
        """
        INSERT INTO clientes (nombre, tipo_cliente, owner_user_id)
        VALUES (?, ?, ?)
        """,
        (nombre, "particular", user_id),
    )
    return cur.lastrowid


def _crear_expediente(cur, user_id: int, numero: str, cliente: str) -> int:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, cliente, direccion, owner_user_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (numero, cliente, f"Calle {numero}", user_id),
    )
    return cur.lastrowid


def _crear_propuesta(
    cur,
    user_id: int,
    cliente_id: int,
    expediente_id: int,
    numero: str,
    total: float,
) -> int:
    cur.execute(
        """
        INSERT INTO propuestas (
            numero_propuesta, cliente_id, expediente_id, fecha, estado,
            tipo_trabajo, base_imponible, iva, total_propuesta, total,
            owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            cliente_id,
            expediente_id,
            "2026-06-01",
            "aceptada",
            "Informe pericial",
            total / 1.21,
            total - (total / 1.21),
            total,
            total,
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_factura(
    cur,
    user_id: int,
    cliente_id: int,
    expediente_id: int,
    propuesta_id: int | None,
    numero: str,
    estado: str,
    total: float,
    fecha: str = "2026-06-05",
    tipo_factura: str = "ordinaria",
) -> int:
    cur.execute(
        """
        INSERT INTO facturas_emitidas (
            numero_factura, serie, fecha, fecha_emision, estado, cliente_id,
            propuesta_id, expediente_id, concepto_general, base_imponible,
            iva, total, tipo_factura, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            "F",
            fecha,
            fecha if estado != "borrador" else None,
            estado,
            cliente_id,
            propuesta_id,
            expediente_id,
            f"Factura {numero}",
            total / 1.21,
            total - (total / 1.21),
            total,
            tipo_factura,
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_cobro(cur, user_id: int, factura_id: int, importe: float, fecha: str = "2026-06-10"):
    cur.execute(
        """
        INSERT INTO cobros (
            factura_id, fecha, importe, metodo, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (factura_id, fecha, importe, "Transferencia", "", user_id),
    )


def _crear_dataset_workbench(cur, user_id: int):
    cliente_id = _crear_cliente(cur, user_id, "Cliente Workbench")

    expediente_sin_factura = _crear_expediente(cur, user_id, "ECO-001", "Cliente Workbench")
    _crear_propuesta(cur, user_id, cliente_id, expediente_sin_factura, "P-WB-001", 500)

    expediente_emitida = _crear_expediente(cur, user_id, "ECO-002", "Cliente Workbench")
    propuesta_emitida = _crear_propuesta(cur, user_id, cliente_id, expediente_emitida, "P-WB-002", 121)
    _crear_factura(cur, user_id, cliente_id, expediente_emitida, propuesta_emitida, "F-WB-002", "emitida", 121)

    expediente_parcial = _crear_expediente(cur, user_id, "ECO-003", "Cliente Workbench")
    propuesta_parcial = _crear_propuesta(cur, user_id, cliente_id, expediente_parcial, "P-WB-003", 242)
    factura_parcial = _crear_factura(cur, user_id, cliente_id, expediente_parcial, propuesta_parcial, "F-WB-003", "emitida", 242)
    _crear_cobro(cur, user_id, factura_parcial, 121)

    expediente_cobrada = _crear_expediente(cur, user_id, "ECO-004", "Cliente Workbench")
    propuesta_cobrada = _crear_propuesta(cur, user_id, cliente_id, expediente_cobrada, "P-WB-004", 363)
    factura_cobrada = _crear_factura(cur, user_id, cliente_id, expediente_cobrada, propuesta_cobrada, "F-WB-004", "cobrada", 363)
    _crear_cobro(cur, user_id, factura_cobrada, 363)

    expediente_vencida = _crear_expediente(cur, user_id, "ECO-005", "Cliente Workbench")
    propuesta_vencida = _crear_propuesta(cur, user_id, cliente_id, expediente_vencida, "P-WB-005", 484)
    _crear_factura(
        cur,
        user_id,
        cliente_id,
        expediente_vencida,
        propuesta_vencida,
        "F-WB-005",
        "emitida",
        484,
        fecha="2026-04-01",
    )

    expediente_rectificativa = _crear_expediente(cur, user_id, "ECO-006", "Cliente Workbench")
    propuesta_rectificativa = _crear_propuesta(cur, user_id, cliente_id, expediente_rectificativa, "P-WB-006", 500)
    _crear_factura(cur, user_id, cliente_id, expediente_rectificativa, propuesta_rectificativa, "F-WB-006", "emitida", 500)
    _crear_factura(
        cur,
        user_id,
        cliente_id,
        expediente_rectificativa,
        propuesta_rectificativa,
        "R-WB-006",
        "emitida",
        -100,
        tipo_factura="rectificativa",
    )

    expediente_anulada = _crear_expediente(cur, user_id, "ECO-007", "Cliente Workbench")
    propuesta_anulada = _crear_propuesta(cur, user_id, cliente_id, expediente_anulada, "P-WB-007", 700)
    _crear_factura(cur, user_id, cliente_id, expediente_anulada, propuesta_anulada, "F-WB-007", "anulada", 700)


def test_workbench_economico_renderiza_estados_y_acciones(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "facturacion_workbench_estados")
        _crear_dataset_workbench(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get("/facturacion/workbench")

    assert response.status_code == 200
    assert "Workbench económico" in response.text
    assert "Facturado mes" in response.text
    assert "Cobrado mes" in response.text
    assert "Pendiente total" in response.text
    assert "Vencido estimado" in response.text
    assert "P-WB-001" in response.text
    assert "Sin facturar" in response.text
    assert "Facturada" in response.text
    assert "Cobro parcial" in response.text
    assert "Cobrada" in response.text
    assert "Vencida" in response.text
    assert "/facturacion/facturas/nueva?propuesta_id=" in response.text
    assert "PDF cliente" in response.text
    assert "PDF interno" in response.text
    assert "Registrar cobro" in response.text
    assert "F-WB-007" not in response.text
    assert "400.00 €" in response.text


def test_workbench_economico_filtros(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "facturacion_workbench_filtros")
        _crear_dataset_workbench(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    parcial = client.get("/facturacion/workbench?filtro=cobro_parcial")
    assert parcial.status_code == 200
    assert "P-WB-003" in parcial.text
    assert "P-WB-004" not in parcial.text

    cobradas = client.get("/facturacion/workbench?filtro=cobradas")
    assert cobradas.status_code == 200
    assert "P-WB-004" in cobradas.text
    assert "P-WB-003" not in cobradas.text

    vencidas = client.get("/facturacion/workbench?filtro=vencidas")
    assert vencidas.status_code == 200
    assert "P-WB-005" in vencidas.text
    assert "P-WB-002" not in vencidas.text

    sin_facturar = client.get("/facturacion/workbench?filtro=sin_facturar")
    assert sin_facturar.status_code == 200
    assert "P-WB-001" in sin_facturar.text
    assert "P-WB-002" not in sin_facturar.text


def test_timeline_economico_aparece_en_propuesta_y_expediente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "facturacion_workbench_timeline")
        _crear_dataset_workbench(cur, user_id)
        propuesta = cur.execute(
            "SELECT id, expediente_id FROM propuestas WHERE numero_propuesta = ?",
            ("P-WB-003",),
        ).fetchone()
        propuesta_id = propuesta["id"]
        expediente_id = propuesta["expediente_id"]
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    propuesta_response = client.get(f"/propuestas/{propuesta_id}")
    assert propuesta_response.status_code == 200
    assert "Timeline económico" in propuesta_response.text
    assert "Cobro recibido" in propuesta_response.text
    assert "Pendiente económico estimado" in propuesta_response.text

    expediente_response = client.get(f"/detalle-expediente/{expediente_id}")
    assert expediente_response.status_code == 200
    assert "Timeline económico" in expediente_response.text
    assert "Cobro recibido" in expediente_response.text
