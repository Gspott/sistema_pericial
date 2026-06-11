import json


TABLAS_COSTES = {
    "costes_bases": {
        "nombre",
        "descripcion",
        "fecha_base",
        "provincia",
        "origen",
        "version",
        "created_at",
    },
    "costes_capitulos": {
        "base_id",
        "codigo",
        "nombre",
        "descripcion",
        "parent_id",
        "orden",
        "created_at",
    },
    "costes_conceptos": {
        "base_id",
        "capitulo_id",
        "codigo",
        "tipo",
        "unidad",
        "resumen",
        "descripcion",
        "precio",
        "moneda",
        "fecha_base",
        "provincia",
        "estado",
        "created_at",
        "updated_at",
    },
    "costes_descompuestos": {
        "concepto_padre_id",
        "concepto_hijo_id",
        "codigo",
        "tipo",
        "unidad",
        "resumen",
        "precio_unitario",
        "rendimiento",
        "importe",
        "orden",
        "created_at",
    },
    "costes_fuentes": {
        "base_id",
        "concepto_id",
        "tipo_fuente",
        "descripcion",
        "archivo_original",
        "url_origen",
        "observaciones",
        "created_at",
    },
    "costes_capturas": {
        "fuente_id",
        "concepto_id",
        "archivo_imagen",
        "estado",
        "datos_extraidos_json",
        "created_at",
        "updated_at",
    },
}

INDICES_COSTES = {
    "idx_costes_capitulos_base_id",
    "idx_costes_capitulos_codigo",
    "idx_costes_conceptos_base_id",
    "idx_costes_conceptos_codigo",
    "idx_costes_conceptos_resumen",
    "idx_costes_conceptos_estado",
    "idx_costes_descompuestos_concepto_padre_id",
    "idx_costes_descompuestos_codigo",
    "idx_costes_fuentes_base_id",
    "idx_costes_fuentes_concepto_id",
    "idx_costes_capturas_concepto_id",
    "idx_costes_capturas_estado",
}


def _columnas(cur, tabla):
    return {fila["name"] for fila in cur.execute(f"PRAGMA table_info({tabla})")}


def _tablas_costes(cur):
    return {
        fila["name"]
        for fila in cur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name LIKE 'costes_%'
            """
        )
    }


def test_costes_db_crea_tablas_indices_e_idempotencia(isolated_import):
    db = isolated_import("app.database")

    from app.config import ensure_directories

    ensure_directories()
    db.init_db()
    db.init_db()

    conn = db.get_connection()
    try:
        cur = conn.cursor()
        assert set(TABLAS_COSTES) <= _tablas_costes(cur)

        for tabla, columnas in TABLAS_COSTES.items():
            assert columnas <= _columnas(cur, tabla)

        indices = {
            fila["name"]
            for fila in cur.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index' AND name LIKE 'idx_costes_%'
                """
            )
        }
        assert INDICES_COSTES <= indices
    finally:
        conn.close()


def test_costes_db_inserta_partida_con_descomposicion_y_trazabilidad(
    isolated_import,
):
    db = isolated_import("app.database")

    from app.config import ensure_directories

    ensure_directories()
    db.init_db()

    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO costes_bases (
                nombre, descripcion, fecha_base, provincia, origen, version
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Base costes demo",
                "Base sandbox sin datos reales",
                "2026-06-05",
                "Madrid",
                "captura manual demo",
                "costes-1",
            ),
        )
        base_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO costes_capitulos (
                base_id, codigo, nombre, descripcion, orden
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                base_id,
                "01",
                "Reparaciones",
                "Capitulo demo para reparaciones de patologias",
                1,
            ),
        )
        capitulo_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO costes_conceptos (
                base_id, capitulo_id, codigo, tipo, unidad, resumen,
                descripcion, precio, moneda, fecha_base, provincia, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                base_id,
                capitulo_id,
                "01.01",
                "partida",
                "m2",
                "Picado y reposicion de revestimiento",
                "Partida demo no conectada con patologias.",
                30.0,
                "EUR",
                "2026-06-05",
                "Madrid",
                "borrador",
            ),
        )
        partida_id = cur.lastrowid

        lineas = [
            ("MAT-MORTERO", "material", "kg", "Mortero reparacion", 2.5, 4.0, 1),
            ("MO-OFICIAL", "mano_obra", "h", "Oficial primera", 25.0, 0.8, 2),
        ]
        importe_total = 0
        for codigo, tipo, unidad, resumen, precio_unitario, rendimiento, orden in lineas:
            importe = round(precio_unitario * rendimiento, 2)
            importe_total += importe
            cur.execute(
                """
                INSERT INTO costes_descompuestos (
                    concepto_padre_id, codigo, tipo, unidad, resumen,
                    precio_unitario, rendimiento, importe, orden
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    partida_id,
                    codigo,
                    tipo,
                    unidad,
                    resumen,
                    precio_unitario,
                    rendimiento,
                    importe,
                    orden,
                ),
            )

        cur.execute(
            """
            INSERT INTO costes_fuentes (
                base_id, concepto_id, tipo_fuente, descripcion,
                archivo_original, url_origen, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                base_id,
                partida_id,
                "manual",
                "Fuente demo para smoke de costes.",
                "base-demo.pdf",
                None,
                "Sin OCR ni importador BC3.",
            ),
        )
        fuente_id = cur.lastrowid

        cur.execute(
            """
            INSERT INTO costes_capturas (
                fuente_id, concepto_id, archivo_imagen, estado,
                datos_extraidos_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                fuente_id,
                partida_id,
                "captura-demo.png",
                "pendiente",
                json.dumps({"codigo": "01.01", "ocr": False}, sort_keys=True),
            ),
        )

        cur.execute(
            """
            UPDATE costes_conceptos
            SET precio = ?
            WHERE id = ?
            """,
            (round(importe_total, 2), partida_id),
        )
        conn.commit()

        total_descompuesto = cur.execute(
            """
            SELECT ROUND(SUM(importe), 2)
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            """,
            (partida_id,),
        ).fetchone()[0]
        precio_partida = cur.execute(
            """
            SELECT precio
            FROM costes_conceptos
            WHERE id = ?
            """,
            (partida_id,),
        ).fetchone()[0]

        assert total_descompuesto == 30.0
        assert precio_partida == total_descompuesto
        assert cur.execute(
            """
            SELECT COUNT(*)
            FROM costes_capturas
            WHERE fuente_id = ? AND concepto_id = ? AND estado = 'pendiente'
            """,
            (fuente_id, partida_id),
        ).fetchone()[0] == 1
    finally:
        conn.close()
