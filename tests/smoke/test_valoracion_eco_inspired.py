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
        ("Tecnico", "Smoke", "", "valoracion_eco", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _render_informe_html(main_module, contexto: dict) -> str:
    template = main_module.templates.env.get_template("informes/imprimir.html")
    return template.render({**contexto, "modo_pdf": False})


def _docx_text(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_valoracion_eco_inspired_contexto_form_html_y_docx(isolated_import):
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
                cliente, direccion, tipo_inmueble, referencia_catastral,
                owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-ECO-001",
                "valoracion",
                "particular",
                "Cliente Eco",
                "Calle Eco 1",
                "Vivienda",
                "1234567VK4713S0001AB",
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
                "Tecnico Eco",
                "Visita de valoración ECO-inspired.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, identificacion_bien,
                superficie_valoracion
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Legacy previo",
                "Identificación legacy",
                "82 m2",
            ),
        )
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, finalidad_otro,
                alcance_valoracion, fecha_valoracion, base_valor,
                definicion_base_valor, documentacion_utilizada,
                datos_registrales, identificacion_bien, superficie_util,
                superficie_construida, superficie_registral,
                superficie_catastral, superficie_comprobada,
                superficie_computable, superficie_adoptada_calculo,
                criterio_superficie_adoptada, metodo_comparacion_activo,
                metodo_coste_activo, metodo_comparacion_aplicado,
                metodo_coste_descartado, metodo_coste_justificacion,
                metodo_actualizacion_rentas_descartado,
                metodo_actualizacion_rentas_justificacion,
                metodo_residual_descartado, metodo_residual_justificacion,
                incidencias_advertencias_manuales
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Compraventa",
                "",
                "Valoración pericial con estructura inspirada en estándares ECO/805/2003",
                "2026-05-26",
                "valor_mercado",
                "Importe estimado en condiciones normales de mercado.",
                "Catastro, nota simple y visita",
                "Finca registral demo sin datos reales",
                "Vivienda ficticia objeto de valoración",
                "80",
                "95",
                "94",
                "96",
                "Sí",
                "95",
                "95",
                "Se adopta superficie construida contrastada por prudencia.",
                1,
                1,
                1,
                1,
                "No se desarrolla coste en esta fase.",
                1,
                "No consta explotación en renta suficiente.",
                1,
                "No procede por tipología residencial consolidada.",
                "Comparables pendientes de verificación presencial individual.",
            ),
        )
        for indice in range(3):
            cur.execute(
                """
                INSERT INTO testigos_valoracion (
                    owner_user_id, direccion_testigo, fuente_testigo,
                    precio_oferta, superficie_construida, valor_unitario,
                    tipologia, reutilizable
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    f"Calle Testigo Eco {indice + 1}",
                    "Portal inmobiliario ficticio" if indice < 2 else "",
                    str(180000 + indice * 5000),
                    "95",
                    str(1895 + indice * 30),
                    "Piso",
                    1,
                ),
            )
            testigo_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO valoracion_expediente_testigos (
                    expediente_id, testigo_id, orden, incluido,
                    snapshot_json, valor_unitario_base
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    expediente_id,
                    testigo_id,
                    indice + 1,
                    1,
                    "{}",
                    str(1895 + indice * 30),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/valoracion")
    assert response.status_code == 200
    assert "Base de valor" in response.text
    assert "Superficie adoptada para cálculo" in response.text

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    assert contexto["tipo_informe"] == "valoracion"
    assert contexto["valoracion"]["finalidad"]["hay_datos"] is True
    assert contexto["valoracion"]["base_valor"]["hay_datos"] is True
    assert contexto["valoracion"]["superficies"]["hay_datos"] is True
    assert contexto["valoracion"]["metodos"]["hay_datos"] is True
    assert any(
        incidencia["descripcion"] == "Existen testigos sin fuente informada."
        for incidencia in contexto["valoracion"]["incidencias"]["items"]
    )
    assert len(contexto["comparables_valoracion"]) == 3

    html = _render_informe_html(main_module, contexto)
    assert "Finalidad y alcance" in html
    assert "Base de valor" in html
    assert "Superficies consideradas y superficie adoptada" in html
    assert "Métodos aplicados y descartados" in html
    assert "Condicionantes, advertencias y limitaciones" in html
    assert "estructura inspirada en estándares ECO/805/2003" in html
    assert "Datos específicos del informe de patologías" not in html

    docx_bytes = generar_informe_docx_editable_bytes(expediente_id)
    texto_docx = _docx_text(docx_bytes)
    assert docx_bytes.startswith(b"PK")
    assert "Finalidad y alcance" in texto_docx
    assert "Base de valor" in texto_docx
    assert "Métodos aplicados y descartados" in texto_docx


def test_valoracion_eco_inspired_degrada_con_datos_incompletos_y_fallback(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

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
                "EXP-VAL-ECO-INCOMPLETA",
                "valoracion",
                "particular",
                "Cliente Eco Incompleta",
                "Calle Eco Incompleta 1",
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
                "Tecnico Eco",
                "Visita con fallback legacy.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, criterios_metodo_valoracion
            )
            VALUES (?, ?, ?)
            """,
            (visita_id, "Herencia legacy", "Comparación legacy"),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")

    assert contexto["es_valoracion"] is True
    assert contexto["valoracion"][0]["hay_datos"] is True
    assert contexto["valoracion"]["finalidad"]["hay_datos"] is True
    assert contexto["valoracion"]["base_valor"]["hay_datos"] is False
    assert contexto["comparables_valoracion"] == []
    assert any(
        "No consta superficie adoptada" in incidencia["descripcion"]
        for incidencia in contexto["valoracion"]["incidencias"]["items"]
    )
