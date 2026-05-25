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

