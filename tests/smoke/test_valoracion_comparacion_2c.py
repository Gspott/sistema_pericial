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
        ("Tecnico", "Smoke", "", "valoracion_comparacion_2c", "hash-demo"),
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


def test_valoracion_comparacion_2c_calculo_puro():
    from app.services.valoracion_comparacion import (
        calcular_media_ponderada,
        calcular_media_simple,
        calcular_mediana,
        calcular_minimo_maximo,
        preparar_resumen_comparacion,
    )

    assert calcular_media_simple([1800, 2000, 2200]) == 2000
    assert calcular_mediana([2200, 1800, 2000]) == 2000
    assert calcular_minimo_maximo([2200, 1800, 2000]) == (1800, 2200)
    assert calcular_media_ponderada(
        [
            {"unitario_homogeneizado": 1800, "peso_porcentaje": 25},
            {"unitario_homogeneizado": 2000, "peso_porcentaje": 50},
            {"unitario_homogeneizado": 2200, "peso_porcentaje": 25},
        ]
    ) == 2000

    resumen_ponderado = preparar_resumen_comparacion(
        [
            {
                "unitario_homogeneizado": 1800,
                "peso_porcentaje": 25,
                "motivo_ponderacion": "Menor similitud.",
            },
            {
                "unitario_homogeneizado": 2000,
                "peso_porcentaje": 50,
                "motivo_ponderacion": "Más representativo.",
            },
            {
                "unitario_homogeneizado": 2200,
                "peso_porcentaje": 25,
                "motivo_ponderacion": "Mercado superior.",
            },
        ]
    )
    assert resumen_ponderado["pesos_validos"] is True
    assert resumen_ponderado["propuesta_unitaria_orientativa"] == 2000

    resumen_sin_pesos = preparar_resumen_comparacion(
        [
            {"unitario_homogeneizado": 1800},
            {"unitario_homogeneizado": 2000},
            {"unitario_homogeneizado": 2400},
        ]
    )
    assert resumen_sin_pesos["unitario_ponderado"] is None
    assert resumen_sin_pesos["propuesta_unitaria_orientativa"] == 2000

    resumen_invalido = preparar_resumen_comparacion(
        [
            {"unitario_homogeneizado": 1800, "peso_porcentaje": 40},
            {"precio_unitario_inicial": 2100, "peso_porcentaje": 40},
            {"unitario_homogeneizado": 2200, "incluido_calculo": 0},
        ]
    )
    assert resumen_invalido["testigos_incluidos"] == 2
    assert resumen_invalido["testigos_excluidos"] == 1
    assert "Los pesos informados no suman 100%." in resumen_invalido["advertencias"]
    assert any("se usa €/m² inicial" in item for item in resumen_invalido["advertencias"])
    assert any("excluido sin motivo" in item for item in resumen_invalido["advertencias"])


def test_valoracion_comparacion_2c_contexto_html_docx_y_legacy(isolated_import):
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
            (
                "EXP-VAL-COMP-2C",
                "valoracion",
                "particular",
                "Cliente 2C",
                "Calle 2C",
                "Vivienda",
                user_id,
            ),
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
        testigo_ids = []
        for indice, precio in enumerate((180000, 200000, 220000), start=1):
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
                    f"Calle Testigo 2C {indice}",
                    "Portal ficticio",
                    "2026-05-27",
                    precio,
                    precio,
                    100,
                    precio / 100,
                    "media",
                    1,
                ),
            )
            testigo_ids.append(cur.lastrowid)
        vinculos = []
        pesos = [25, 50, 25]
        for indice, testigo_id in enumerate(testigo_ids, start=1):
            cur.execute(
                """
                INSERT INTO valoracion_expediente_testigos (
                    expediente_id, testigo_id, orden, incluido, incluido_calculo,
                    peso_porcentaje, motivo_ponderacion, representatividad,
                    snapshot_json, valor_unitario_base
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    expediente_id,
                    testigo_id,
                    indice,
                    1,
                    1,
                    pesos[indice - 1],
                    "Ponderación técnica manual.",
                    "media",
                    "{}",
                    2000,
                ),
            )
            vinculos.append(cur.lastrowid)
            cur.execute(
                """
                INSERT INTO valoracion_testigo_ajustes (
                    expediente_testigo_id, expediente_id, testigo_id, variable,
                    tipo_ajuste, ajuste_importe_m2, signo, justificacion, orden, activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vinculos[-1],
                    expediente_id,
                    testigo_id,
                    "ubicacion",
                    "importe_m2",
                    0,
                    "+",
                    "Sin ajuste cuantitativo adicional.",
                    1,
                    1,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/valoracion/testigos")
    assert response.status_code == 200
    assert "Resumen comparativo" in response.text
    assert "Ponderado" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculos[0]}/actualizar",
        data={
            "orden": "1",
            "incluido": "1",
            "incluido_calculo": "1",
            "peso_porcentaje": "30",
            "representatividad": "alta",
            "notas_seleccion": "Actualizado 2C.",
            "motivo_ponderacion": "Más representativo por localización.",
            "motivo_exclusion": "",
            "observaciones_ponderacion": "Revisión manual.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    resumen = contexto["valoracion"]["resumen_comparacion"]
    assert resumen["testigos_incluidos"] == 3
    assert resumen["unitario_ponderado"] is not None
    assert "resumen_comparacion" in contexto["valoracion_eco"]
    assert contexto["comparables_valoracion"][0]["representatividad"] == "alta"
    assert contexto["comparables_valoracion"][0]["unitario_para_resumen"] is not None

    response = client.get(f"/informes/{expediente_id}/imprimir")
    assert response.status_code == 200
    assert "Resumen comparativo y ponderación" in response.text
    assert "carácter preparatorio" in response.text

    docx_bytes = generar_informe_docx_editable_bytes(expediente_id)
    assert docx_bytes.startswith(b"PK")
    assert "Resumen comparativo y ponderación" in _docx_text(docx_bytes)

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
                "EXP-VAL-COMP-2C-LEGACY",
                "valoracion",
                "particular",
                "Cliente Legacy",
                "Calle Legacy",
                "Vivienda",
                user_id,
            ),
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
    assert contexto_legacy["valoracion"]["resumen_comparacion"]["testigos_incluidos"] == 1
