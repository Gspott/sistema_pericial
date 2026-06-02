import io
import zipfile

from fastapi.testclient import TestClient


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", "valoracion_comparacion_2b", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _docx_text(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_valoracion_comparacion_2b_calculo_puro():
    from app.services.valoracion_comparacion import (
        aplicar_ajuste_unitario,
        calcular_unitario_homogeneizado,
    )

    assert aplicar_ajuste_unitario(2000, {"tipo_ajuste": "porcentaje", "signo": "+", "ajuste_porcentaje": "0.05"}) == 2100
    assert aplicar_ajuste_unitario(2000, {"tipo_ajuste": "porcentaje", "signo": "-", "ajuste_porcentaje": "0.05"}) == 1900
    assert aplicar_ajuste_unitario(2000, {"tipo_ajuste": "importe_m2", "signo": "+", "ajuste_importe_m2": "75"}) == 2075
    assert aplicar_ajuste_unitario(2000, {"tipo_ajuste": "cualitativo_no_cuantificado"}) == 2000

    calculo = calcular_unitario_homogeneizado(
        {"precio_unitario_inicial": 2000},
        [
            {"variable": "ubicacion", "tipo_ajuste": "porcentaje", "signo": "+", "ajuste_porcentaje": 0.05, "justificacion": "Mejor ubicación", "orden": 1, "activo": 1},
            {"variable": "estado_conservacion", "tipo_ajuste": "importe_m2", "signo": "-", "ajuste_importe_m2": 50, "justificacion": "Peor estado", "orden": 2, "activo": 1},
            {"variable": "fuente_negociacion", "tipo_ajuste": "cualitativo_no_cuantificado", "justificacion": "Observación cualitativa", "orden": 3, "activo": 1},
        ],
    )
    assert round(calculo["unitario_homogeneizado"], 2) == 2050
    assert len(calculo["pasos"]) == 3

    sin_justificacion = calcular_unitario_homogeneizado(
        {"precio_unitario_inicial": 2000},
        [{"variable": "ubicacion", "tipo_ajuste": "porcentaje", "signo": "+", "ajuste_porcentaje": 0.05, "activo": 1}],
    )
    assert "Ajuste sin justificación." in sin_justificacion["advertencias"]

    sin_unitario = calcular_unitario_homogeneizado({}, [])
    assert "Homogeneización no calculable por falta de €/m² inicial." in sin_unitario["advertencias"]


def test_valoracion_comparacion_2b_ux_contexto_html_docx_y_legacy(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import (
        build_informe_context,
        generar_informe_docx_editable_bytes,
    )

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
            ("EXP-VAL-COMP-2B", "valoracion", "particular", "Cliente 2B", "Calle 2B", "Vivienda", user_id),
        )
        expediente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, fecha_valoracion,
                superficie_adoptada_calculo, metodo_comparacion_aplicado
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (expediente_id, "Compraventa", "2026-05-27", "100", 1),
        )
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, fuente_testigo, fecha_testigo,
                precio_oferta, precio_depurado, superficie_tomada,
                precio_unitario_inicial, fiabilidad_dato, reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                "Calle Testigo 2B",
                "Portal ficticio",
                "2026-05-27",
                210000,
                200000,
                100,
                2000,
                "media",
                1,
            ),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json,
                valor_unitario_base
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (expediente_id, testigo_id, 1, 1, "{}", 2000),
        )
        vinculo_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes"
    )
    assert response.status_code == 200
    assert "Homogeneización" in response.text
    assert "Matriz de homogeneización" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion",
        data={
            "variable": "ubicacion",
            "valor_inmueble": "Mejor zona",
            "valor_testigo": "Zona comparable",
            "tipo_ajuste": "porcentaje",
            "signo": "+",
            "ajuste_porcentaje": "0.05",
            "justificacion": "Ubicación ligeramente superior del inmueble valorado.",
            "orden": "1",
            "activo": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion",
        data={
            "variable": "estado_conservacion",
            "valor_inmueble": "Normal",
            "valor_testigo": "Reformado",
            "tipo_ajuste": "importe_m2",
            "signo": "-",
            "ajuste_importe_m2": "40",
            "justificacion": "",
            "orden": "2",
            "activo": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo_id}/ajustes/homogeneizacion",
        data={
            "variable": "fuente_negociacion",
            "tipo_ajuste": "cualitativo_no_cuantificado",
            "justificacion": "Fuente de oferta, sin cierre acreditado.",
            "orden": "3",
            "activo": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    comparable = contexto["comparables_valoracion"][0]
    assert len(comparable["ajustes_homogeneizacion"]) == 3
    assert round(comparable["unitario_homogeneizado"], 2) == 2060
    assert round(comparable["ajuste_total_importe_m2"], 2) == 60
    assert "Ajuste sin justificación." in comparable["advertencias_homogeneizacion"]
    assert len(comparable["pasos_homogeneizacion"]) == 3

    response = client.get(f"/informes/{expediente_id}/imprimir")
    assert response.status_code == 200
    assert "Matriz de homogeneización" in response.text
    assert "€/m² homogeneizado" in response.text
    assert "La homogeneización recoge ajustes técnicos" in response.text

    docx_bytes = generar_informe_docx_editable_bytes(expediente_id)
    assert docx_bytes.startswith(b"PK")
    assert "Matriz de homogeneización" in _docx_text(docx_bytes)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("EXP-VAL-COMP-2B-LEGACY", "valoracion", "particular", "Cliente Legacy", "Calle Legacy", "Vivienda", user_id),
        )
        expediente_legacy_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO visitas (expediente_id, fecha, tecnico, observaciones_visita)
            VALUES (?, ?, ?, ?)
            """,
            (expediente_legacy_id, "2026-05-27", "Tecnico", "Legacy"),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo,
                precio_oferta, superficie_construida, valor_unitario
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (visita_id, "Calle Legacy", "Portal legacy", "180000", "90", "2000"),
        )
        conn.commit()
    finally:
        conn.close()

    contexto_legacy = build_informe_context(expediente_legacy_id)
    assert contexto_legacy["comparables_valoracion"][0]["origen"] == "legacy"
    assert contexto_legacy["comparables_valoracion"][0]["ajustes_homogeneizacion"] == []
