from pathlib import Path

from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str = "valoracion_workbench"):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente_workbench_con_testigos(cur, user_id: int, suffix: str = ""):
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, tipo_inmueble, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"EXP-VAL-WORKBENCH-SELECT{suffix}",
            "valoracion",
            "particular",
            f"Cliente Workbench Select{suffix}",
            f"Calle Workbench Select{suffix}",
            "Vivienda",
            user_id,
        ),
    )
    expediente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO valoracion_expediente (
            expediente_id, finalidad_valoracion, fecha_valoracion,
            base_valor, superficie_adoptada_calculo,
            metodo_comparacion_aplicado
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (expediente_id, "Compraventa", "2026-06-01", "valor_mercado", "95", 1),
    )
    testigos = []
    for indice, motivo in enumerate(
        ("Motivo primero.", "Motivo segundo seleccionado.", "Motivo excluido."),
        start=1,
    ):
        precio = 200000 + indice * 10000 if indice < 3 else None
        superficie = 95 if indice < 3 else None
        unitario = 2000 + indice * 100 if indice < 3 else None
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, fuente_testigo, fecha_testigo,
                precio_oferta, precio_depurado, superficie_tomada,
                precio_unitario_inicial, fiabilidad_dato,
                similitud_inmueble, superficie_construida, superficie_util,
                planta, banos, ascensor, es_exterior, balcon, terraza, patio,
                estado_conservacion, ano_construccion, ano_reforma,
                aire_acondicionado, tipo_calefaccion, garaje, trastero,
                certificacion_energetica, reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                f"Calle Testigo Workbench {indice}{suffix}",
                "Portal ficticio",
                "2026-06-01",
                precio,
                precio - 10000 if precio else None,
                superficie,
                unitario,
                "alta" if indice == 1 else "media",
                "media" if indice == 3 else "alta",
                120 if indice == 1 else 96 if indice == 2 else None,
                72 if indice == 1 else 82 if indice == 2 else None,
                "4ª" if indice == 1 else "2ª" if indice == 2 else "",
                2 if indice < 3 else None,
                0 if indice == 1 else 1 if indice == 2 else None,
                1 if indice < 3 else None,
                1 if indice == 1 else 0,
                1 if indice == 1 else 0,
                0,
                "Buen estado" if indice == 1 else "Reformado" if indice == 2 else "",
                1975 if indice == 1 else 2008 if indice == 2 else None,
                2021 if indice == 2 else None,
                1 if indice == 2 else 0,
                "Individual gas" if indice == 2 else "",
                0 if indice == 1 else 1 if indice == 2 else None,
                1 if indice == 2 else 0,
                "C" if indice == 2 else "",
                1,
            ),
        )
        testigo_id = cur.lastrowid
        testigos.append(testigo_id)
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido,
                incluido_calculo, peso_porcentaje, motivo_ponderacion,
                representatividad, snapshot_json, valor_unitario_base
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                indice,
                1,
                0 if indice == 3 else 1,
                0 if indice == 3 else 50,
                motivo,
                "alta",
                "{}",
                unitario,
            ),
        )
    return expediente_id, testigos


def _vinculo_testigo(cur, expediente_id: int, testigo_id: int) -> int:
    row = cur.execute(
        """
        SELECT id
        FROM valoracion_expediente_testigos
        WHERE expediente_id = ? AND testigo_id = ?
        """,
        (expediente_id, testigo_id),
    ).fetchone()
    return row["id"]


def _insertar_foto_testigo(cur, testigo_id: int, archivo: str, descripcion: str):
    cur.execute(
        """
        INSERT INTO testigos_valoracion_fotos (
            testigo_id, archivo, descripcion, origen
        )
        VALUES (?, ?, ?, ?)
        """,
        (testigo_id, archivo, descripcion, "manual"),
    )


def test_valoracion_workbench_ssr_renderiza_contexto_moderno(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-WORKBENCH",
                "valoracion",
                "particular",
                "Cliente Workbench",
                "Calle Workbench 12",
                "Vivienda",
                user_id,
            ),
        )
        expediente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, fecha_valoracion,
                base_valor, superficie_adoptada_calculo,
                metodo_comparacion_aplicado
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Compraventa",
                "2026-06-01",
                "valor_mercado",
                "95",
                1,
            ),
        )
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, fuente_testigo, fecha_testigo,
                precio_oferta, precio_depurado, superficie_tomada,
                precio_unitario_inicial, fiabilidad_dato,
                similitud_inmueble, superficie_construida, superficie_util,
                planta, banos, ascensor, es_exterior, balcon, terraza, patio,
                estado_conservacion, ano_construccion, ano_reforma,
                aire_acondicionado, tipo_calefaccion, garaje, trastero,
                certificacion_energetica, reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "Calle Testigo Workbench",
                "Portal ficticio",
                "2026-06-01",
                210000,
                199500,
                95,
                2100,
                "media",
                "alta",
                118,
                88,
                "3ª",
                2,
                1,
                1,
                1,
                0,
                0,
                "Buen estado",
                1998,
                2020,
                1,
                "Individual gas",
                1,
                1,
                "D",
                1,
            ),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido,
                incluido_calculo, peso_porcentaje, motivo_ponderacion,
                representatividad, snapshot_json, valor_unitario_base
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                1,
                1,
                1,
                100,
                "Testigo principal por similitud y fuente trazable.",
                "alta",
                "{}",
                2100,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench")

    assert response.status_code == 200
    assert "Workbench de valoración" in response.text
    assert "workbench-wide-desktop" in response.text
    assert "Vista de análisis de escritorio" in response.text
    assert "Resumen de valoración" in response.text
    assert "Testigos comparables" in response.text
    assert "Panel contextual" in response.text
    assert "€/m² inicial" in response.text
    assert "2.100 €/m²" in response.text
    assert "Incluido" in response.text
    assert "Características técnicas del testigo" in response.text
    assert "Sup. constr./útil" in response.text
    assert "118,00 m²" in response.text
    assert "2 baños" in response.text
    assert "Ascensor" in response.text
    assert "Certificación energética" in response.text


def test_valoracion_workbench_muestra_fotos_de_testigo(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_fotos")
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        _insertar_foto_testigo(
            cur,
            testigos[0],
            "testigo_valoracion/1/captura-salon.jpg",
            "Captura manual del salón",
        )
        _insertar_foto_testigo(
            cur,
            testigos[0],
            "testigo_valoracion/1/fachada.jpg",
            "Fachada del testigo",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Evidencia visual" in response.text
    assert "2 fotos" in response.text
    assert "Captura manual del salón" in response.text
    assert "/uploads/testigo_valoracion/1/captura-salon.jpg" in response.text
    assert "Evidencias auxiliares manuales" in response.text
    assert "Ver foto" in response.text


def test_valoracion_workbench_degrada_sin_fotos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_sin_fotos")
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[1]}"
    )

    assert response.status_code == 200
    assert "Evidencia visual" in response.text
    assert "Sin fotos" in response.text
    assert "Este testigo no tiene fotos o capturas manuales asociadas." in response.text


def test_valoracion_workbench_no_muestra_fotos_de_testigo_ajeno(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_foto_owner")
        otro_user_id = _crear_usuario(cur, "valoracion_workbench_foto_otro")
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        cur.execute(
            "UPDATE testigos_valoracion SET owner_user_id = ? WHERE id = ?",
            (otro_user_id, testigos[0]),
        )
        _insertar_foto_testigo(
            cur,
            testigos[0],
            "testigo_valoracion/ajeno/captura.jpg",
            "Foto ajena no visible",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Evidencia visual" in response.text
    assert "Foto ajena no visible" not in response.text
    assert "Este testigo no tiene fotos o capturas manuales asociadas." in response.text


def test_valoracion_workbench_comparativa_tecnica_y_qa(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_tecnica")
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Características técnicas del testigo" in response.text
    assert "Constr.: 120,00 m²" in response.text
    assert "Útil: 72,00 m²" in response.text
    assert "4ª" in response.text
    assert "Sin ascensor" in response.text
    assert "Exterior" in response.text
    assert "Balcón" in response.text
    assert "Terraza" in response.text
    assert "Buen estado" in response.text
    assert "4ª planta o superior sin ascensor." in response.text
    assert "Superficie útil/construida muy divergente." in response.text

    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?filtro=advertencias"
    )
    assert response.status_code == 200
    assert "Calle Testigo Workbench 1" in response.text
    assert "4ª planta o superior sin ascensor." in response.text


def test_valoracion_workbench_comparativa_tecnica_degrada_sin_campos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_tecnica_vacia")
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[2]}"
    )

    assert response.status_code == 200
    assert "Datos técnicos pendientes" in response.text
    assert "Falta superficie útil y construida." in response.text
    assert "Estado de conservación desconocido." in response.text
    assert "Año de construcción ausente." in response.text


def test_valoracion_workbench_selecciona_testigo_valido(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[1]}"
    )

    assert response.status_code == 200
    assert "Motivo segundo seleccionado." in response.text
    assert "row-selected" in response.text
    assert "Editar testigo" in response.text
    assert "Editar ajustes" in response.text


def test_valoracion_workbench_trazabilidad_con_ajustes(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        vinculo_id = _vinculo_testigo(cur, expediente_id, testigos[0])
        cur.executemany(
            """
            INSERT INTO valoracion_testigo_ajustes (
                expediente_testigo_id, expediente_id, testigo_id, variable,
                valor_inmueble, valor_testigo, tipo_ajuste, ajuste_porcentaje,
                ajuste_importe_m2, signo, justificacion, orden, activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    vinculo_id,
                    expediente_id,
                    testigos[0],
                    "ubicacion",
                    "Calle principal",
                    "Calle secundaria",
                    "porcentaje",
                    0.05,
                    None,
                    "+",
                    "Mejor ubicación relativa del inmueble valorado.",
                    1,
                    1,
                ),
                (
                    vinculo_id,
                    expediente_id,
                    testigos[0],
                    "estado_conservacion",
                    "Buen estado",
                    "Requiere actualización",
                    "importe_m2",
                    None,
                    40,
                    "-",
                    "Corrección por estado inferior del testigo.",
                    2,
                    1,
                ),
                (
                    vinculo_id,
                    expediente_id,
                    testigos[0],
                    "fuente_negociacion",
                    "",
                    "",
                    "cualitativo_no_cuantificado",
                    None,
                    None,
                    "",
                    "Observación cualitativa sobre margen de negociación.",
                    3,
                    1,
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Trazabilidad de homogeneización" in response.text
    assert "Ubicacion" in response.text
    assert "5,00%" in response.text
    assert "40 €/m²" in response.text
    assert "Cualitativo no cuantificado" in response.text
    assert "Ajuste cualitativo sin efecto numérico" in response.text
    assert "Editar ajustes" in response.text


def test_valoracion_workbench_trazabilidad_sin_ajustes(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Trazabilidad de homogeneización" in response.text
    assert "Sin ajustes aplicados." in response.text
    assert "Trazabilidad incompleta." in response.text
    assert "No hay ajustes activos trazables" in response.text


def test_valoracion_workbench_trazabilidad_avisa_importe_incompleto(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        vinculo_id = _vinculo_testigo(cur, expediente_id, testigos[0])
        cur.execute(
            """
            INSERT INTO valoracion_testigo_ajustes (
                expediente_testigo_id, expediente_id, testigo_id, variable,
                tipo_ajuste, ajuste_importe_m2, signo, justificacion, orden, activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vinculo_id,
                expediente_id,
                testigos[0],
                "calidad_constructiva",
                "importe_m2",
                None,
                "+",
                "Pendiente cuantificar tras revisar calidades.",
                1,
                1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "Trazabilidad incompleta." in response.text
    assert "Ajuste por importe €/m² sin importe en Calidad constructiva." in response.text
    assert "Pendiente cuantificar tras revisar calidades." in response.text


def test_valoracion_workbench_filtros_y_degradacion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?filtro=todos")
    assert response.status_code == 200
    assert "Total testigos" in response.text
    assert "Calle Testigo Workbench 1" in response.text
    assert "Calle Testigo Workbench 3" in response.text

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?filtro=incluidos")
    assert response.status_code == 200
    assert "Calle Testigo Workbench 1" in response.text
    assert "Calle Testigo Workbench 3" not in response.text

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?filtro=excluidos")
    assert response.status_code == 200
    assert "Calle Testigo Workbench 3" in response.text
    assert "Calle Testigo Workbench 1" not in response.text

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?filtro=nope")
    assert response.status_code == 200
    assert "El filtro solicitado no existe" in response.text
    assert "Calle Testigo Workbench 1" in response.text
    assert "Calle Testigo Workbench 3" in response.text

    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench"
        f"?filtro=incluidos&testigo_id={testigos[2]}"
    )
    assert response.status_code == 200
    assert "queda fuera del filtro actual" in response.text
    assert "Motivo segundo seleccionado." in response.text


def test_valoracion_workbench_ordenacion_y_estado_vacio(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, _ = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?ordenar=homogeneizado&dir=desc"
    )
    assert response.status_code == 200
    assert "Orden" in response.text
    assert "Calle Testigo Workbench 2" in response.text

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?ordenar=raro")
    assert response.status_code == 200
    assert "La ordenación solicitada no existe" in response.text

    response = client.get(f"/expediente/{expediente_id}/valoracion/workbench?filtro=incompletos")
    assert response.status_code == 200
    assert "Calle Testigo Workbench 3" in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_workbench_empty")
        expediente_vacio_id, _ = _crear_expediente_workbench_con_testigos(cur, user_id)
        cur.execute(
            "UPDATE valoracion_expediente_testigos SET incluido_calculo = 1 WHERE expediente_id = ?",
            (expediente_vacio_id,),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_vacio_id}/valoracion/workbench?filtro=excluidos"
    )
    assert response.status_code == 200
    assert "No hay testigos visibles con el filtro actual" in response.text


def test_valoracion_workbench_microedicion_valida_y_redirect(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{testigos[0]}",
        data={
            "filtro": "incluidos",
            "ordenar": "peso",
            "dir": "asc",
            "incluido_calculo": "1",
            "peso_porcentaje": "35.5",
            "representatividad": "media_alta",
            "motivo_ponderacion": "Peso ajustado desde workbench.",
            "motivo_exclusion": "",
            "observaciones_ponderacion": "Observación técnica breve.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    location = response.headers["location"]
    assert "filtro=incluidos" in location
    assert "ordenar=peso" in location
    assert "dir=asc" in location
    assert f"testigo_id={testigos[0]}" in location

    conn = get_connection()
    try:
        cur = conn.cursor()
        vinculo = cur.execute(
            """
            SELECT incluido_calculo, peso_porcentaje, representatividad,
                   motivo_ponderacion, observaciones_ponderacion
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigos[0]),
        ).fetchone()
    finally:
        conn.close()

    assert vinculo["incluido_calculo"] == 1
    assert vinculo["peso_porcentaje"] == 35.5
    assert vinculo["representatividad"] == "media_alta"
    assert vinculo["motivo_ponderacion"] == "Peso ajustado desde workbench."
    assert vinculo["observaciones_ponderacion"] == "Observación técnica breve."


def test_valoracion_workbench_autosave_renderiza_contrato_comun(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )

    assert response.status_code == 200
    assert "/static/js/autosave.js" in response.text
    assert "data-autosave-form" in response.text
    assert "data-autosave-url=" in response.text
    assert "data-autosave-debounce=\"1200\"" in response.text
    assert "Listo para editar" in response.text
    assert "name=\"updated_at\"" in response.text


def test_valoracion_workbench_autosave_guarda_y_persiste(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        vinculo = cur.execute(
            """
            SELECT updated_at
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigos[0]),
        ).fetchone()
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{testigos[0]}/autosave",
        data={
            "updated_at": vinculo["updated_at"] or "",
            "incluido_calculo": "1",
            "peso_porcentaje": "42",
            "representatividad": "alta",
            "motivo_ponderacion": "Autosave prueba persistente.",
            "motivo_exclusion": "",
            "observaciones_ponderacion": "Guardado AJAX desde smoke.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["updated_at"]
    assert payload["saved_at"]
    assert payload["message"] == "Guardado correctamente"

    conn = get_connection()
    try:
        cur = conn.cursor()
        guardado = cur.execute(
            """
            SELECT peso_porcentaje, motivo_ponderacion, observaciones_ponderacion
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigos[0]),
        ).fetchone()
    finally:
        conn.close()

    assert guardado["peso_porcentaje"] == 42
    assert guardado["motivo_ponderacion"] == "Autosave prueba persistente."
    assert guardado["observaciones_ponderacion"] == "Guardado AJAX desde smoke."

    reload_response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id={testigos[0]}"
    )
    assert reload_response.status_code == 200
    assert "Autosave prueba persistente." in reload_response.text


def test_valoracion_workbench_autosave_detecta_conflicto_updated_at(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        cur.execute(
            """
            UPDATE valoracion_expediente_testigos
            SET updated_at = ?
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            ("2026-06-19 10:00:00", expediente_id, testigos[0]),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{testigos[0]}/autosave",
        data={
            "updated_at": "2026-06-19 09:00:00",
            "incluido_calculo": "1",
            "peso_porcentaje": "55",
            "representatividad": "alta",
            "motivo_ponderacion": "No debe sobrescribir.",
            "motivo_exclusion": "",
            "observaciones_ponderacion": "",
        },
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["ok"] is False
    assert payload["conflict"] is True
    assert payload["message"] == "Otro proceso ha modificado el registro."
    assert payload["updated_at"] == "2026-06-19 10:00:00"

    conn = get_connection()
    try:
        cur = conn.cursor()
        guardado = cur.execute(
            """
            SELECT motivo_ponderacion
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigos[0]),
        ).fetchone()
    finally:
        conn.close()

    assert guardado["motivo_ponderacion"] != "No debe sobrescribir."


def test_autosave_js_estados_reintento_y_fallback_manual():
    fuente = Path("static/js/autosave.js").read_text(encoding="utf-8")

    assert "Cambios pendientes" in fuente
    assert "Guardando..." in fuente
    assert "Guardado" in fuente
    assert "Error al guardar" in fuente
    assert "Otro proceso ha modificado el registro." in fuente
    assert "Reintentando" in fuente
    assert "beforeunload" in fuente
    assert "submit" in fuente


def test_valoracion_workbench_microedicion_rechaza_ajeno_e_invalido(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        otro_expediente_id, otros_testigos = _crear_expediente_workbench_con_testigos(
            cur,
            user_id,
            "-OTRO",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{otros_testigos[0]}",
        data={"incluido_calculo": "1", "peso_porcentaje": "20"},
        follow_redirects=False,
    )
    assert response.status_code == 404

    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{testigos[0]}",
        data={
            "filtro": "todos",
            "ordenar": "homogeneizado",
            "dir": "desc",
            "incluido_calculo": "1",
            "peso_porcentaje": "150",
            "representatividad": "alta",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=El+peso+debe+estar+entre+0+y+100." in response.headers["location"]


def test_valoracion_workbench_microedicion_exclusion_sin_motivo_advierte(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, testigos = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expediente/{expediente_id}/valoracion/workbench/testigo/{testigos[0]}",
        data={
            "filtro": "todos",
            "ordenar": "homogeneizado",
            "dir": "desc",
            "peso_porcentaje": "0",
            "representatividad": "baja",
            "motivo_ponderacion": "",
            "motivo_exclusion": "",
            "observaciones_ponderacion": "Exclusión revisable.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Recomendación: documenta el motivo de exclusión." in response.text
    assert "Testigo excluido sin motivo técnico breve." in response.text


def test_valoracion_workbench_degrada_testigo_inexistente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, _ = _crear_expediente_workbench_con_testigos(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench?testigo_id=999999"
    )

    assert response.status_code == 200
    assert "no pertenece al contexto de este expediente" in response.text
    assert "Motivo segundo seleccionado." in response.text


def test_valoracion_workbench_rechaza_no_valoracion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PAT-WORKBENCH",
                "patologias",
                "particular",
                "Cliente Patologias",
                "Calle Patologias 4",
                "Vivienda",
                user_id,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expediente/{expediente_id}/valoracion/workbench",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/detalle-expediente/{expediente_id}")
