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
        ("Tecnico", "Smoke", "", "valoracion_comparacion_2a", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente_valoracion(cur, user_id: int):
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, tipo_inmueble, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EXP-VAL-COMP-2A",
            "valoracion",
            "particular",
            "Cliente Comparacion 2A",
            "Calle Comparacion 2A 1",
            "Vivienda",
            user_id,
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
            "2026-05-26",
            "Tecnico Comparacion",
            "Visita demo comparacion 2A.",
        ),
    )
    return expediente_id, cur.lastrowid


def _docx_text(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_valoracion_comparacion_calculo_puro():
    from app.services.valoracion_comparacion import (
        calcular_precio_unitario,
        preparar_testigo_comparacion,
    )

    assert calcular_precio_unitario("180000", "90") == 2000
    preparado = preparar_testigo_comparacion(
        {
            "precio_oferta": "200000",
            "precio_depurado": "190000",
            "superficie_tomada": "95",
            "fuente_testigo": "Portal ficticio",
            "fecha_testigo": "2026-05-26",
            "fiabilidad_dato": "media",
        }
    )
    assert round(preparado["precio_unitario_inicial"], 2) == 2000

    fallback = preparar_testigo_comparacion(
        {
            "precio_oferta": "210000",
            "superficie_tomada": "100",
            "fuente_testigo": "Portal ficticio",
            "fecha_testigo": "2026-05-26",
            "fiabilidad_dato": "media",
        }
    )
    assert fallback["precio_unitario_inicial"] == 2100

    incompleto = preparar_testigo_comparacion({"precio_oferta": "210000"})
    assert incompleto["precio_unitario_inicial"] is None
    assert "Testigo sin superficie tomada." in incompleto["advertencias_calculo"]


def test_valoracion_comparacion_2a_contexto_html_docx_y_fallback(isolated_import):
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
        expediente_id, visita_id = _crear_expediente_valoracion(cur, user_id)
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, fecha_valoracion,
                superficie_adoptada_calculo, metodo_comparacion_aplicado
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Compraventa",
                "2026-05-26",
                "95",
                1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        "/valoracion/testigos/nuevo",
        data={
            "direccion_testigo": "Calle Testigo Comparacion 2A",
            "referencia_testigo": "COMP-2A-001",
            "precio_oferta": "210000",
            "precio_depurado": "199500",
            "superficie_tomada": "95",
            "tipo_superficie_tomada": "construida",
            "fuente_tipo": "portal_inmobiliario",
            "fuente_testigo": "Portal ficticio",
            "fuente_detalle": "Anuncio ficticio capturado manualmente",
            "url_fuente": "https://example.invalid/testigo-2a",
            "fecha_testigo": "2026-05-26",
            "fecha_captura": "2026-05-26",
            "dato_verificado": "1",
            "testigo_visitado": "1",
            "fiabilidad_dato": "media",
            "similitud_inmueble": "alta",
            "estado_mercado": "oferta activa",
            "observaciones_economicas": "Precio depurado con margen prudente.",
            "tipologia": "Vivienda",
            "validacion_estado": "validado",
            "reutilizable": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        testigo = cur.execute(
            "SELECT * FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()
        testigo_id = testigo["id"]
        assert round(testigo["precio_unitario_inicial"], 2) == 2100
        assert testigo["precio_oferta"] == 210000
        assert testigo["precio_depurado"] == 199500
    finally:
        conn.close()

    response = client.get("/valoracion/testigos")
    assert response.status_code == 200
    assert "199.500 €" in response.text
    assert "95,00 m²" in response.text
    assert "2.100 €/m²" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/anadir",
        data={"testigo_id": str(testigo_id), "notas_seleccion": "Testigo 2A."},
        follow_redirects=False,
    )
    assert response.status_code == 303

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["precio_depurado"] == 199500
    assert comparable["superficie_tomada"] == 95
    assert round(comparable["precio_unitario_inicial"], 2) == 2100
    assert comparable["fuente_tipo"] == "portal_inmobiliario"
    assert comparable["dato_verificado"] == 1
    assert comparable["testigo_visitado"] == 1
    assert comparable["fiabilidad_dato"] == "media"
    assert comparable["similitud_inmueble"] == "alta"
    assert comparable["advertencias_calculo"] == []

    response = client.get(f"/informes/{expediente_id}/imprimir")
    assert response.status_code == 200
    assert "Nota de cálculo inicial" in response.text
    assert "199.500 €" in response.text
    assert "2.100 €/m²" in response.text
    assert "homogeneización ni ponderación técnica" in response.text

    docx_bytes = generar_informe_docx_editable_bytes(expediente_id)
    assert docx_bytes.startswith(b"PK")
    assert "Nota de cálculo inicial" in _docx_text(docx_bytes)

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
            (
                "EXP-VAL-COMP-2A-LEGACY",
                "valoracion",
                "particular",
                "Cliente Legacy",
                "Calle Legacy 2A",
                "Vivienda",
                user_id,
            ),
        )
        expediente_legacy_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_legacy_id,
                "2026-05-26",
                "Tecnico Comparacion",
                "Visita legacy.",
            ),
        )
        visita_legacy_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo,
                precio_oferta, superficie_construida, valor_unitario
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                visita_legacy_id,
                "Calle Legacy Comparable",
                "Portal legacy",
                "180000",
                "90",
                "2000",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto_legacy = build_informe_context(
        expediente_legacy_id,
        base_url="http://testserver",
    )
    assert contexto_legacy["comparables_valoracion"][0]["origen"] == "legacy"
    assert contexto_legacy["comparables_valoracion"][0]["precio_oferta"] == "180000"


def test_valoracion_comparacion_2a_testigo_incompleto_advierte(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id, _ = _crear_expediente_valoracion(cur, user_id)
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, precio_oferta, reutilizable
            )
            VALUES (?, ?, ?, ?)
            """,
            (user_id, "Calle Testigo Incompleto", 180000, 1),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (expediente_id, testigo_id, 1, 1, "{}"),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["precio_unitario_inicial"] is None
    assert "Testigo sin superficie tomada." in comparable["advertencias_calculo"]
    assert "Testigo sin fuente." in comparable["advertencias_calculo"]
    assert "Testigo sin fecha." in comparable["advertencias_calculo"]
