import json


TABLAS_VALORACION_DEFENSIVA = {
    "valoracion_expediente": {
        "expediente_id",
        "finalidad_valoracion",
        "identificacion_bien",
        "superficie_valoracion",
        "metodo_comparacion_activo",
        "metodo_coste_activo",
    },
    "valoracion_visita_observaciones": {
        "visita_id",
        "expediente_id",
        "estado_observado",
        "reforma_observada",
        "ocupacion_observada",
        "observaciones_portal",
        "observaciones_cuadro_contadores",
    },
    "testigos_valoracion": {
        "owner_user_id",
        "direccion_testigo",
        "fuente_testigo",
        "precio_oferta",
        "precio_depurado",
        "precio_unitario_inicial",
        "superficie_tomada",
        "tipo_superficie_tomada",
        "valor_unitario",
        "fuente_tipo",
        "fuente_detalle",
        "fecha_captura",
        "dato_verificado",
        "testigo_visitado",
        "fiabilidad_dato",
        "similitud_inmueble",
        "observaciones_economicas",
        "validacion_estado",
        "reutilizable",
    },
    "testigos_valoracion_fotos": {
        "testigo_id",
        "archivo",
        "descripcion",
        "origen",
    },
    "valoracion_expediente_testigos": {
        "expediente_id",
        "testigo_id",
        "snapshot_json",
        "valor_unitario_base",
        "valor_unitario_ajustado",
        "valor_resultante",
    },
    "valoracion_testigo_ajustes": {
        "expediente_testigo_id",
        "expediente_id",
        "testigo_id",
        "variable",
        "valor_inmueble",
        "valor_testigo",
        "tipo_ajuste",
        "ajuste_porcentaje",
        "ajuste_importe_m2",
        "signo",
        "ajuste_superficie_construida",
        "ajuste_ubicacion",
        "ajuste_antiguedad",
        "ajuste_calidades",
        "ajuste_caracteristicas_constructivas",
        "coeficiente_total",
        "orden",
        "activo",
    },
    "valoracion_resultados": {
        "expediente_id",
        "metodo",
        "version",
        "valor_unitario",
        "valor_resultante",
        "valor_tasacion_final",
        "datos_calculo_json",
    },
}


def _columnas(cur, tabla):
    return {fila["name"] for fila in cur.execute(f"PRAGMA table_info({tabla})")}


def test_valoracion_db_defensiva_crea_tablas_y_relaciones(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()

        for tabla, columnas in TABLAS_VALORACION_DEFENSIVA.items():
            existe = cur.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (tabla,),
            ).fetchone()
            assert existe is not None
            assert columnas <= _columnas(cur, tabla)

        cur.execute(
            """
            INSERT INTO usuarios (
                nombre, apellido1, apellido2, username, password_hash
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Tecnico", "Smoke", "", "tecnico_valoracion_db", "hash-demo"),
        )
        owner_user_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-DB-001",
                "valoracion",
                "particular",
                "Cliente Demo Valoracion",
                "Calle Demo Valoracion 1",
                "Vivienda",
                owner_user_id,
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
                "Visita demo para modelo defensivo.",
            ),
        )
        visita_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, identificacion_bien,
                superficie_valoracion, superficie_construida,
                metodo_comparacion_activo, metodo_coste_activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "compraventa",
                "Vivienda demo sin datos reales",
                "90",
                90,
                1,
                1,
            ),
        )

        cur.execute(
            """
            INSERT INTO valoracion_visita_observaciones (
                visita_id, expediente_id, estado_observado,
                reforma_observada, ocupacion_observada,
                observaciones_portal, observaciones_cuadro_contadores
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                expediente_id,
                "normal",
                "no observada",
                "desconocida",
                "Portal demo sin incidencias",
                "Cuadro de contadores accesible",
            ),
        )

        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, referencia_testigo,
                fuente_testigo, precio_oferta, superficie_construida,
                valor_unitario, validacion_estado, reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                owner_user_id,
                "Calle Testigo Demo 2",
                "TEST-001",
                "portal demo",
                190000,
                95,
                2000,
                "validado",
                1,
            ),
        )
        testigo_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO testigos_valoracion_fotos (
                testigo_id, archivo, descripcion, origen
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                testigo_id,
                "testigo-demo.jpg",
                "Referencia tecnica demo sin archivo real",
                "smoke",
            ),
        )

        snapshot = json.dumps(
            {
                "direccion_testigo": "Calle Testigo Demo 2",
                "valor_unitario": 2000,
                "superficie_construida": 95,
            },
            sort_keys=True,
        )
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json,
                notas_seleccion, valor_unitario_base,
                valor_unitario_ajustado, valor_resultante
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                1,
                1,
                snapshot,
                "Seleccion demo para smoke",
                2000,
                2060,
                185400,
            ),
        )
        expediente_testigo_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO valoracion_testigo_ajustes (
                expediente_testigo_id, ajuste_superficie_construida,
                ajuste_ubicacion, ajuste_antiguedad, ajuste_calidades,
                ajuste_caracteristicas_constructivas, coeficiente_total,
                justificacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_testigo_id,
                0.02,
                0.03,
                -0.01,
                0.0,
                -0.01,
                0.03,
                "Coeficientes demo sin calculo productivo",
            ),
        )

        cur.execute(
            """
            INSERT INTO valoracion_resultados (
                expediente_id, metodo, version, valor_unitario,
                valor_resultante, valor_tasacion_final,
                resumen_calculo, datos_calculo_json, activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "comparacion",
                1,
                2060,
                185400,
                185400,
                "Resultado demo sin calculo implementado",
                json.dumps({"fuente": "smoke"}, sort_keys=True),
                1,
            ),
        )

        conn.commit()

        assert cur.execute(
            """
            SELECT COUNT(*)
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigo_id),
        ).fetchone()[0] == 1
        assert cur.execute(
            """
            SELECT coeficiente_total
            FROM valoracion_testigo_ajustes
            WHERE expediente_testigo_id = ?
            """,
            (expediente_testigo_id,),
        ).fetchone()[0] == 0.03
        assert cur.execute(
            """
            SELECT metodo
            FROM valoracion_resultados
            WHERE expediente_id = ? AND activo = 1
            """,
            (expediente_id,),
        ).fetchone()[0] == "comparacion"
    finally:
        conn.close()
