from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Costes", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_partida_costes(cur, codigo: str = "DEL.001") -> int:
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, fecha_base, provincia, origen, version
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"Base {codigo}",
            "Base temporal para borrado seguro.",
            "2026-06-06",
            "Madrid",
            "manual",
            "costes-lib-1",
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
            codigo,
            "partida",
            "m2",
            "Partida eliminable",
            "Partida temporal para smoke.",
            10,
            "EUR",
            "2026-06-06",
            "Madrid",
            "borrador",
        ),
    )
    concepto_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_descompuestos (
            concepto_padre_id, codigo, tipo, unidad, resumen,
            precio_unitario, rendimiento, importe, orden
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            concepto_id,
            "AUX.001",
            "material",
            "ud",
            "Auxiliar eliminable",
            5,
            2,
            10,
            1,
        ),
    )
    return concepto_id


def _crear_expediente_minimo(cur, owner_id: int, numero: str) -> int:
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
            numero,
            "patologias",
            "particular",
            "Cliente costes lib",
            "Calle Costes Lib 1",
            "28000",
            "Madrid",
            "Madrid",
            "Vivienda",
            "Borrado seguro de costes.",
            "Daño demo.",
            "Causa demo.",
            "Indicios demo.",
            "Reparación demo.",
            owner_id,
        ),
    )
    return cur.lastrowid


def _crear_patologia_minima(cur, expediente_id: int) -> int:
    cur.execute(
        """
        INSERT INTO visitas (
            expediente_id, fecha, tecnico, observaciones_visita
        )
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, "2026-06-06", "Tecnico", "Visita smoke."),
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
            "Tarima",
            "Pintura",
            "Yeso",
            "Estancia smoke.",
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
            "Patologia smoke.",
            "",
            "paramento",
            "Zona inferior",
            "",
        ),
    )
    return cur.lastrowid


def test_costes_workbench_flujo_manual_partida_descompuestos_y_validacion(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_workbench_owner")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/costes")
    assert response.status_code == 200
    assert "Costes de reparación" in response.text
    assert "Nueva partida" in response.text

    response = client.post(
        "/costes/nuevo",
        data={
            "base_id": "",
            "base_nombre": "Base smoke costes",
            "base_descripcion": "Base temporal smoke",
            "capitulo_id": "",
            "codigo": "01.01",
            "tipo": "partida",
            "unidad": "m2",
            "resumen": "Picado y reposicion de revestimiento",
            "descripcion": "Partida smoke sin conexion con patologias.",
            "precio": "100",
            "moneda": "EUR",
            "fecha_base": "2026-06-05",
            "provincia": "Madrid",
            "estado": "borrador",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/costes/")

    conn = get_connection()
    try:
        concepto = conn.execute(
            """
            SELECT c.*, b.nombre AS base_nombre
            FROM costes_conceptos c
            JOIN costes_bases b ON b.id = c.base_id
            WHERE c.codigo = ?
            """,
            ("01.01",),
        ).fetchone()
        assert concepto is not None
        assert concepto["base_nombre"] == "Base smoke costes"
        concepto_id = concepto["id"]
    finally:
        conn.close()

    response = client.get(f"/costes/{concepto_id}")
    assert response.status_code == 200
    assert "Validación económica" in response.text
    assert "Fuente y trazabilidad" in response.text
    assert "Origen: manual" in response.text
    assert "Descomposición" in response.text
    assert "costes-descomp-table" in response.text

    response = client.post(
        f"/costes/{concepto_id}/descompuestos",
        data={
            "codigo": "MAT-01",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Mortero de reparacion",
            "precio_unitario": "15",
            "rendimiento": "2",
            "importe": "",
            "orden": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        descompuesto = conn.execute(
            """
            SELECT *
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            """,
            (concepto_id,),
        ).fetchone()
        assert descompuesto is not None
        assert descompuesto["importe"] == 30.0
        descompuesto_id = descompuesto["id"]
    finally:
        conn.close()

    response = client.post(
        f"/costes/descompuestos/{descompuesto_id}/actualizar",
        data={
            "codigo": "MAT-01B",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Mortero de reparacion corregido",
            "precio_unitario": "20",
            "rendimiento": "2",
            "importe": "",
            "orden": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        descompuesto = conn.execute(
            """
            SELECT codigo, resumen, importe
            FROM costes_descompuestos
            WHERE id = ?
            """,
            (descompuesto_id,),
        ).fetchone()
        estado = conn.execute(
            "SELECT estado FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
        assert descompuesto["codigo"] == "MAT-01B"
        assert "corregido" in descompuesto["resumen"]
        assert descompuesto["importe"] == 40.0
        assert estado == "borrador"
    finally:
        conn.close()

    response = client.get(f"/costes/{concepto_id}")
    assert response.status_code == 200
    assert "/costes/descompuestos/" in response.text
    assert "/actualizar" in response.text
    assert "40.00" in response.text

    response = client.post(
        f"/costes/{concepto_id}/validar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    conn = get_connection()
    try:
        estado = conn.execute(
            "SELECT estado FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
        assert estado == "borrador"
    finally:
        conn.close()

    response = client.post(
        f"/costes/{concepto_id}",
        data={
            "base_id": str(concepto["base_id"]),
            "capitulo_id": "",
            "codigo": "01.01",
            "tipo": "partida",
            "unidad": "m2",
            "resumen": "Picado y reposicion de revestimiento",
            "descripcion": "Partida smoke ajustada.",
            "precio": "40",
            "moneda": "EUR",
            "fecha_base": "2026-06-05",
            "provincia": "Madrid",
            "estado": "borrador",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    response = client.post(
        f"/costes/{concepto_id}/validar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    conn = get_connection()
    try:
        estado = conn.execute(
            "SELECT estado FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
        assert estado == "validado"
    finally:
        conn.close()

    response = client.post(
        f"/costes/descompuestos/{descompuesto_id}/borrar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/costes/{concepto_id}")

    conn = get_connection()
    try:
        cantidad = conn.execute(
            """
            SELECT COUNT(*)
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            """,
            (concepto_id,),
        ).fetchone()[0]
        estado = conn.execute(
            "SELECT estado FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
        assert cantidad == 0
        assert estado == "borrador"
    finally:
        conn.close()


def test_coste_detalle_muestra_enlace_captura_origen(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_ui_2_captura_origen")
        concepto_id = _crear_partida_costes(cur, "CAP.ORIG")
        cur.execute(
            """
            INSERT INTO costes_fuentes (
                concepto_id, tipo_fuente, descripcion, archivo_original, observaciones
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                concepto_id,
                "pantallazo",
                "Captura origen smoke",
                "origen.png",
                "Origen asociado a partida.",
            ),
        )
        fuente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO costes_capturas (
                fuente_id, concepto_id, archivo_imagen, estado, updated_at
            )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                fuente_id,
                concepto_id,
                "costes/capturas/origen.png",
                "revisada",
            ),
        )
        captura_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get(f"/costes/{concepto_id}")

    assert response.status_code == 200
    assert "Captura origen smoke" in response.text
    assert f"/costes/capturas/{captura_id}" in response.text
    assert "Ver captura" in response.text


def test_coste_eliminar_sin_referencias(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_lib_delete_free")
        concepto_id = _crear_partida_costes(cur, "DEL.FREE")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/costes?q=DEL.FREE")
    assert response.status_code == 200
    assert "Eliminar" in response.text
    assert "¿Seguro que deseas eliminar esta partida?" in response.text

    response = client.post(
        f"/costes/{concepto_id}/eliminar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/costes")

    conn = get_connection()
    try:
        total_conceptos = conn.execute(
            "SELECT COUNT(*) FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
        total_descompuestos = conn.execute(
            """
            SELECT COUNT(*)
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            """,
            (concepto_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert total_conceptos == 0
    assert total_descompuestos == 0


def test_coste_eliminar_con_actuacion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_lib_delete_actuacion")
        concepto_id = _crear_partida_costes(cur, "DEL.ACT")
        expediente_id = _crear_expediente_minimo(cur, owner_id, "EXP-COSTES-LIB-ACT")
        cur.execute(
            """
            INSERT INTO actuaciones_reparacion (
                expediente_id, titulo, descripcion, observaciones, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "Actuacion smoke",
                "Actuacion vinculada a partida.",
                "",
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
                "Snapshot actuacion",
                "m2",
                10,
                1,
                10,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(
        f"/costes/{concepto_id}/eliminar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Esta%20partida%20est%C3%A1%20siendo%20utilizada" in response.headers["location"]

    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert total == 1


def test_coste_eliminar_con_patologia(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_lib_delete_patologia")
        concepto_id = _crear_partida_costes(cur, "DEL.PAT")
        expediente_id = _crear_expediente_minimo(cur, owner_id, "EXP-COSTES-LIB-PAT")
        patologia_id = _crear_patologia_minima(cur, expediente_id)
        cur.execute(
            """
            INSERT INTO patologia_costes (
                patologia_id, concepto_id, descripcion_actuacion,
                cantidad, unidad, precio_unitario, importe, estado, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patologia_id,
                concepto_id,
                "Coste vinculado a patologia",
                1,
                "m2",
                10,
                10,
                "incluido",
                "",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(
        f"/costes/{concepto_id}/eliminar",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Esta%20partida%20est%C3%A1%20siendo%20utilizada" in response.headers["location"]

    conn = get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert total == 1
