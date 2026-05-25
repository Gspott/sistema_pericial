import pytest


OWNER_USER_ID = 1


def _crear_factura_borrador_desde_propuesta(cur, propuesta_id: int):
    from app.routers.facturacion import recalcular_totales_factura
    from app.routers.propuestas import (
        crear_linea_factura_desde_datos,
        descripcion_factura_desde_propuesta,
        obtener_factura_borrador_vinculada,
        obtener_facturas_vinculadas_propuesta,
        obtener_lineas_propuesta,
    )

    facturas_vinculadas = obtener_facturas_vinculadas_propuesta(
        cur, propuesta_id, OWNER_USER_ID
    )
    factura_borrador = obtener_factura_borrador_vinculada(facturas_vinculadas)
    if factura_borrador:
        return factura_borrador["id"]

    propuesta = cur.execute(
        "SELECT * FROM propuestas WHERE id = ? AND owner_user_id = ?",
        (propuesta_id, OWNER_USER_ID),
    ).fetchone()
    lineas_propuesta = obtener_lineas_propuesta(cur, propuesta_id)

    cur.execute(
        """
        INSERT INTO facturas_emitidas (
            serie, fecha, estado, cliente_id, propuesta_id, expediente_id,
            concepto_general, irpf_porcentaje_defecto, notas, tipo_factura,
            owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "F",
            "2026-05-25",
            "borrador",
            propuesta["cliente_id"],
            propuesta_id,
            propuesta["expediente_id"],
            propuesta["tipo_trabajo"],
            0,
            "Smoke test: factura borrador no emitida.",
            "ordinaria",
            OWNER_USER_ID,
        ),
    )
    factura_id = cur.lastrowid

    for indice, linea in enumerate(lineas_propuesta, start=1):
        crear_linea_factura_desde_datos(
            cur,
            factura_id=factura_id,
            concepto=linea["concepto"],
            descripcion=descripcion_factura_desde_propuesta(linea),
            cantidad=float(linea["cantidad"] or 0),
            precio_unitario=float(linea["precio_unitario"] or 0),
            iva_porcentaje=float(linea["iva_porcentaje"] or 0),
            irpf_porcentaje=0,
            orden=int(linea["orden"] or indice),
        )

    recalcular_totales_factura(cur, factura_id)
    return factura_id


def test_propuesta_aceptada_crea_factura_borrador_sin_emitir(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.routers.propuestas import (
        obtener_factura_borrador_vinculada,
        obtener_facturas_vinculadas_propuesta,
        obtener_lineas_propuesta,
        recalcular_totales_propuesta,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clientes (nombre, email, tipo_cliente, owner_user_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Cliente Smoke", "cliente.smoke@example.test", "particular", OWNER_USER_ID),
        )
        cliente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO propuestas (
                numero_propuesta, cliente_id, fecha, estado, tipo_trabajo,
                direccion_inmueble, alcance, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "P-SMOKE-FLOW-001",
                cliente_id,
                "2026-05-24",
                "borrador",
                "Informe pericial demo",
                "Calle Demo 1",
                "Alcance demo para smoke test.",
                OWNER_USER_ID,
            ),
        )
        propuesta_id = cur.lastrowid
        cur.executemany(
            """
            INSERT INTO propuesta_lineas (
                propuesta_id, categoria_servicio, concepto, descripcion,
                cantidad, precio_unitario, iva_porcentaje, orden
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    propuesta_id,
                    "informe_pericial",
                    "Informe demo",
                    "Redaccion de informe pericial demo.",
                    1,
                    100,
                    21,
                    1,
                ),
                (
                    propuesta_id,
                    "visita_tecnica",
                    "Visita demo",
                    "Visita tecnica demo.",
                    2,
                    75,
                    21,
                    2,
                ),
            ],
        )
        recalcular_totales_propuesta(cur, propuesta_id)

        cur.execute(
            """
            UPDATE propuestas
            SET estado = ?, fecha_aceptacion = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            ("aceptada", "2026-05-25", propuesta_id),
        )

        factura_id = _crear_factura_borrador_desde_propuesta(cur, propuesta_id)
        factura_id_repetida = _crear_factura_borrador_desde_propuesta(cur, propuesta_id)
        conn.commit()

        propuesta = cur.execute(
            "SELECT * FROM propuestas WHERE id = ?",
            (propuesta_id,),
        ).fetchone()
        lineas_propuesta = obtener_lineas_propuesta(cur, propuesta_id)
        factura = cur.execute(
            "SELECT * FROM facturas_emitidas WHERE id = ?",
            (factura_id,),
        ).fetchone()
        lineas_factura = cur.execute(
            """
            SELECT *
            FROM factura_lineas
            WHERE factura_id = ?
            ORDER BY orden ASC, id ASC
            """,
            (factura_id,),
        ).fetchall()
        factura_lineas_columnas = {
            row["name"] for row in cur.execute("PRAGMA table_info(factura_lineas)")
        }
        facturas_vinculadas = obtener_facturas_vinculadas_propuesta(
            cur, propuesta_id, OWNER_USER_ID
        )
    finally:
        conn.close()

    factura_borrador = obtener_factura_borrador_vinculada(facturas_vinculadas)

    assert propuesta["estado"] == "aceptada"
    assert propuesta["fecha_aceptacion"] == "2026-05-25"
    assert propuesta["base_imponible"] == pytest.approx(250)
    assert propuesta["importe_iva"] == pytest.approx(52.5)
    assert propuesta["total_propuesta"] == pytest.approx(302.5)

    assert factura_id_repetida == factura_id
    assert len(facturas_vinculadas) == 1
    assert factura_borrador["id"] == factura_id
    assert factura["estado"] == "borrador"
    assert factura["numero_factura"] is None
    assert factura["fecha_emision"] is None
    assert factura["hash_factura"] is None
    assert factura["verifactu_fecha_generacion"] is None
    assert factura["propuesta_id"] == propuesta_id
    assert factura["cliente_id"] == cliente_id
    assert factura["tipo_factura"] == "ordinaria"
    assert factura["base_imponible"] == pytest.approx(propuesta["base_imponible"])
    assert factura["iva"] == pytest.approx(propuesta["importe_iva"])
    assert factura["irpf"] == pytest.approx(0)
    assert factura["total"] == pytest.approx(propuesta["total_propuesta"])

    assert len(lineas_factura) == len(lineas_propuesta) == 2
    assert "propuesta_id" not in factura_lineas_columnas
    for linea_propuesta, linea_factura in zip(lineas_propuesta, lineas_factura):
        assert linea_factura["factura_id"] == factura_id
        assert linea_factura["concepto"] == linea_propuesta["concepto"]
        assert linea_factura["cantidad"] == pytest.approx(linea_propuesta["cantidad"])
        assert linea_factura["precio_unitario"] == pytest.approx(
            linea_propuesta["precio_unitario"]
        )
        assert linea_factura["iva_porcentaje"] == pytest.approx(
            linea_propuesta["iva_porcentaje"]
        )
        assert linea_factura["subtotal"] == pytest.approx(
            linea_propuesta["cantidad"] * linea_propuesta["precio_unitario"]
        )
        assert linea_factura["total"] == pytest.approx(linea_propuesta["total"])
