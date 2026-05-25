def test_propuesta_lines_recalculate_and_support_draft_invoice(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.routers.facturacion import recalcular_totales_factura
    from app.routers.propuestas import (
        crear_linea_factura_desde_datos,
        recalcular_totales_propuesta,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO propuestas (
                numero_propuesta, fecha, estado, tipo_trabajo, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("P-SMOKE-001", "2026-01-10", "borrador", "Informe pericial", 1),
        )
        propuesta_id = cur.lastrowid

        cur.executemany(
            """
            INSERT INTO propuesta_lineas (
                propuesta_id, categoria_servicio, concepto, cantidad,
                precio_unitario, iva_porcentaje, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (propuesta_id, "informe_pericial", "Informe demo", 1, 100, 21, 1),
                (propuesta_id, "visita_tecnica", "Visita demo", 2, 75, 21, 2),
            ],
        )
        recalcular_totales_propuesta(cur, propuesta_id)

        propuesta = cur.execute(
            "SELECT * FROM propuestas WHERE id = ?",
            (propuesta_id,),
        ).fetchone()
        lineas = cur.execute(
            """
            SELECT *
            FROM propuesta_lineas
            WHERE propuesta_id = ?
            ORDER BY orden
            """,
            (propuesta_id,),
        ).fetchall()

        cur.execute(
            """
            INSERT INTO facturas_emitidas (
                fecha, estado, propuesta_id, concepto_general, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "2026-01-11",
                "borrador",
                propuesta_id,
                "Factura borrador desde propuesta smoke",
                1,
            ),
        )
        factura_id = cur.lastrowid
        crear_linea_factura_desde_datos(
            cur,
            factura_id=factura_id,
            concepto="Honorarios desde propuesta",
            descripcion="Linea demo no emitida",
            cantidad=1,
            precio_unitario=propuesta["base_imponible"],
            iva_porcentaje=21,
            irpf_porcentaje=0,
            orden=1,
        )
        recalcular_totales_factura(cur, factura_id)
        factura = cur.execute(
            "SELECT * FROM facturas_emitidas WHERE id = ?",
            (factura_id,),
        ).fetchone()
    finally:
        conn.close()

    assert len(lineas) == 2
    assert lineas[0]["total"] == 121
    assert lineas[1]["total"] == 181.5
    assert propuesta["base_imponible"] == 250
    assert propuesta["importe_iva"] == 52.5
    assert propuesta["total_propuesta"] == 302.5
    assert factura["estado"] == "borrador"
    assert factura["propuesta_id"] == propuesta_id
    assert factura["total"] == 302.5

