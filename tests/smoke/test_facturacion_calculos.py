from fastapi.testclient import TestClient


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Factura", "", "facturacion_smoke", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_factura_linea_and_totals_are_calculated_in_temp_db(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.routers.facturacion import calcular_linea, recalcular_totales_factura

    subtotal, iva_importe, irpf_importe, total = calcular_linea(
        cantidad=2,
        precio_unitario=100,
        iva_porcentaje=21,
        irpf_porcentaje=15,
    )

    assert subtotal == 200
    assert iva_importe == 42
    assert irpf_importe == 30
    assert total == 212

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                fecha, estado, concepto_general, owner_user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            ("2026-01-15", "borrador", "Factura demo smoke", 1),
        )
        factura_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO factura_lineas (
                factura_id, concepto, cantidad, precio_unitario,
                iva_porcentaje, irpf_porcentaje, subtotal,
                iva_importe, irpf_importe, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factura_id,
                "Honorarios demo",
                2,
                100,
                21,
                15,
                subtotal,
                iva_importe,
                irpf_importe,
                total,
                1,
            ),
        )
        recalcular_totales_factura(cur, factura_id)
        factura = cur.execute(
            "SELECT * FROM facturas_emitidas WHERE id = ?",
            (factura_id,),
        ).fetchone()
    finally:
        conn.close()

    assert factura["estado"] == "borrador"
    assert factura["base_imponible"] == 200
    assert factura["iva"] == 42
    assert factura["irpf"] == 30
    assert factura["total"] == 212


def test_factura_imprimir_muestra_resumen_de_pagos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.routers.facturacion import calcular_linea, recalcular_totales_factura

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO configuracion_fiscal (
                nombre_fiscal, nif_cif, direccion, codigo_postal, ciudad,
                provincia, email, telefono, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Carlos Blanco Segura",
                "44620303G",
                "Calle Demo 1",
                "46001",
                "Valencia",
                "Valencia",
                "contacto@example.test",
                "600000000",
                user_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO clientes (
                nombre, apellidos, nif_cif, tipo_cliente, email, direccion,
                codigo_postal, ciudad, provincia, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Leonor",
                "Camara Herrero",
                "22630070W",
                "particular",
                "cliente@example.test",
                "Calle Empedra 18",
                "46620",
                "Ayora",
                "Valencia",
                user_id,
            ),
        )
        cliente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            ("019-26", "Leonor Camara Herrero", "Calle Empedra 18", user_id),
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
                "P-2026-0016",
                cliente_id,
                expediente_id,
                "2026-05-01",
                "aceptada",
                "Informe pericial por danos de agua",
                user_id,
            ),
        )
        propuesta_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                numero_factura, serie, fecha, estado, cliente_id, propuesta_id,
                expediente_id, concepto_general, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "F-2026-0001",
                "F",
                "2026-06-01",
                "emitida",
                cliente_id,
                propuesta_id,
                expediente_id,
                "Informe pericial expediente 019-26",
                "Pago realizado el 01/06/2026.",
                user_id,
            ),
        )
        factura_id = cur.lastrowid
        for orden, (concepto, cantidad, precio) in enumerate(
            (
                ("Redaccion de informe pericial", 1, 700),
                ("Desplazamiento", 270, 0.26),
            ),
            start=1,
        ):
            subtotal, iva_importe, irpf_importe, total = calcular_linea(
                cantidad=cantidad,
                precio_unitario=precio,
                iva_porcentaje=21,
                irpf_porcentaje=0,
            )
            cur.execute(
                """
                INSERT INTO factura_lineas (
                    factura_id, concepto, cantidad, precio_unitario,
                    iva_porcentaje, irpf_porcentaje, subtotal, iva_importe,
                    irpf_importe, total, orden
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    factura_id,
                    concepto,
                    cantidad,
                    precio,
                    21,
                    0,
                    subtotal,
                    iva_importe,
                    irpf_importe,
                    total,
                    orden,
                ),
            )
        recalcular_totales_factura(cur, factura_id)
        cur.execute(
            """
            INSERT INTO cobros (
                factura_id, fecha, importe, metodo, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                factura_id,
                "2026-06-01",
                465.97,
                "Transferencia",
                "Pago realizado el 01/06/2026",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/facturacion/facturas/{factura_id}/imprimir")

    assert response.status_code == 200
    assert "F-2026-0001" in response.text
    assert "Leonor Camara Herrero" in response.text
    assert "Total factura" in response.text
    assert "931,94 €" in response.text
    assert "Pagos recibidos" in response.text
    assert "465,97 €" in response.text
    assert "Pendiente de pago" in response.text
    assert "Pago realizado el 01/06/2026" in response.text


def test_factura_imprimir_no_rompe_sin_cobros(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.routers.facturacion import calcular_linea, recalcular_totales_factura

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO clientes (nombre, tipo_cliente, owner_user_id)
            VALUES (?, ?, ?)
            """,
            ("Cliente sin cobros", "particular", user_id),
        )
        cliente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                numero_factura, serie, fecha, estado, cliente_id,
                concepto_general, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "F-2026-0002",
                "F",
                "2026-06-02",
                "emitida",
                cliente_id,
                "Factura sin cobros smoke",
                user_id,
            ),
        )
        factura_id = cur.lastrowid
        subtotal, iva_importe, irpf_importe, total = calcular_linea(
            cantidad=1,
            precio_unitario=100,
            iva_porcentaje=21,
            irpf_porcentaje=0,
        )
        cur.execute(
            """
            INSERT INTO factura_lineas (
                factura_id, concepto, cantidad, precio_unitario,
                iva_porcentaje, irpf_porcentaje, subtotal, iva_importe,
                irpf_importe, total, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                factura_id,
                "Honorarios demo",
                1,
                100,
                21,
                0,
                subtotal,
                iva_importe,
                irpf_importe,
                total,
                1,
            ),
        )
        recalcular_totales_factura(cur, factura_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/facturacion/facturas/{factura_id}/imprimir")

    assert response.status_code == 200
    assert "F-2026-0002" in response.text
    assert "Cliente sin cobros" in response.text
    assert "121,00 €" in response.text
    assert "No constan pagos registrados en esta factura." in response.text
