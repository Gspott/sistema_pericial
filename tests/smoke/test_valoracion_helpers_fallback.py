import json


def _campo_valor(campos, etiqueta: str) -> str:
    for campo in campos:
        if campo["label"] == etiqueta:
            return campo["value"]
    raise AssertionError(f"Campo no encontrado: {etiqueta}")


def _grupo_por_clave(valoracion: dict, clave: str) -> dict:
    for grupo in valoracion["grupos"]:
        if grupo["clave"] == clave:
            return grupo
    raise AssertionError(f"Grupo no encontrado: {clave}")


def _crear_expediente_valoracion(cur, numero: str):
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, tipo_inmueble, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            "valoracion",
            "particular",
            f"Cliente {numero}",
            f"Calle {numero}",
            "Vivienda",
            1,
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
            "Tecnico Valoracion",
            "Visita demo de valoracion.",
        ),
    )
    return expediente_id, cur.lastrowid


def test_valoracion_helpers_usan_fallback_legacy(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id, visita_id = _crear_expediente_valoracion(
            cur,
            "EXP-VAL-FALLBACK-LEGACY",
        )
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, identificacion_bien,
                superficie_valoracion, criterios_metodo_valoracion,
                valor_tasacion_final
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Herencia legacy",
                "Vivienda legacy",
                "82 m2",
                "Comparacion legacy",
                "164000 EUR",
            ),
        )
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo,
                precio_oferta, valor_unitario
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Legacy Testigo",
                "Portal legacy",
                "166000 EUR",
                "2024 EUR/m2",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id)

    assert contexto["es_valoracion"] is True
    assert len(contexto["valoracion"]) == 1
    valoracion = contexto["valoracion"][0]
    assert valoracion["visita"]["id"] == visita_id
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "encargo")["campos"],
            "Finalidad de la valoración",
        )
        == "Herencia legacy"
    )
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "resultado")["campos"],
            "Valor de tasación final",
        )
        == "164000 EUR"
    )
    assert len(contexto["comparables_valoracion"]) == 1
    assert contexto["comparables_valoracion"][0]["origen"] == "legacy"
    assert (
        _campo_valor(contexto["comparables_valoracion"][0]["campos"], "Dirección")
        == "Calle Legacy Testigo"
    )


def test_valoracion_helpers_usan_modelo_nuevo_sin_legacy(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id, visita_id = _crear_expediente_valoracion(
            cur,
            "EXP-VAL-MODELO-NUEVO",
        )
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, documentacion_utilizada,
                identificacion_bien, superficie_valoracion,
                criterios_metodo_valoracion
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Compraventa nueva",
                "Catastro y nota simple",
                "Vivienda modelo nuevo",
                "95 m2",
                "Comparacion con testigos reutilizables",
            ),
        )
        cur.execute(
            """
            INSERT INTO valoracion_visita_observaciones (
                visita_id, expediente_id, estado_observado,
                reforma_observada, ocupacion_observada
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                expediente_id,
                "Buen estado observado",
                "Reforma parcial",
                "Libre observado",
            ),
        )
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                direccion_testigo, fuente_testigo, precio_oferta,
                superficie_construida, valor_unitario, validacion_estado,
                reutilizable
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Calle Nuevo Testigo",
                "Portal nuevo",
                205000,
                92,
                2228,
                "validado",
                1,
            ),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json,
                valor_unitario_base, valor_unitario_ajustado, valor_resultante
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                testigo_id,
                1,
                1,
                json.dumps({"direccion_testigo": "Snapshot no preferente"}),
                2228,
                2300,
                218500,
            ),
        )
        expediente_testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_testigo_ajustes (
                expediente_testigo_id, ajuste_superficie_construida,
                ajuste_ubicacion, coeficiente_total, justificacion
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                expediente_testigo_id,
                0.02,
                0.01,
                0.03,
                "Ajuste demo",
            ),
        )
        cur.execute(
            """
            INSERT INTO valoracion_resultados (
                expediente_id, metodo, version, valor_unitario,
                valor_resultante, valor_tasacion_final, resumen_calculo,
                activo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "comparacion",
                1,
                2300,
                218500,
                210000,
                "Resultado demo desde modelo nuevo",
                1,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id)

    assert len(contexto["valoracion"]) == 1
    valoracion = contexto["valoracion"][0]
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "encargo")["campos"],
            "Finalidad de la valoración",
        )
        == "Compraventa nueva"
    )
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "estado")["campos"],
            "Estado actual del inmueble",
        )
        == "Buen estado observado"
    )
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "estado")["campos"],
            "Régimen de ocupación",
        )
        == "Libre observado"
    )
    assert len(contexto["comparables_valoracion"]) == 1
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["origen"] == "modelo_nuevo"
    assert comparable["testigo_id"] == testigo_id
    assert comparable["ajustes"]["coeficiente_total"] == 0.03
    assert _campo_valor(comparable["campos"], "Dirección") == "Calle Nuevo Testigo"
    assert _campo_valor(comparable["campos"], "Valor unitario") == "2.300 €/m²"


def test_valoracion_helpers_priorizan_modelo_nuevo_sobre_legacy(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id, visita_id = _crear_expediente_valoracion(
            cur,
            "EXP-VAL-PRECEDENCIA",
        )
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, identificacion_bien,
                valor_tasacion_final
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Finalidad legacy",
                "Identificacion legacy",
                "100000 EUR",
            ),
        )
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, valor_unitario
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Testigo Legacy",
                "Portal legacy",
                "1800 EUR/m2",
            ),
        )
        cur.execute(
            """
            INSERT INTO valoracion_expediente (
                expediente_id, finalidad_valoracion, identificacion_bien,
                observaciones_valoracion
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Finalidad modelo nuevo",
                "Identificacion modelo nuevo",
                "Observacion modelo nuevo",
            ),
        )
        cur.execute(
            """
            INSERT INTO valoracion_resultados (
                expediente_id, metodo, version, valor_tasacion_final, activo
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "comparacion",
                1,
                240000,
                1,
            ),
        )
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                direccion_testigo, fuente_testigo, valor_unitario, reutilizable
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "Calle Testigo Nuevo",
                "Portal nuevo",
                2500,
                1,
            ),
        )
        testigo_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido,
                valor_unitario_base
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (expediente_id, testigo_id, 1, 1, 2500),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id)
    valoracion = contexto["valoracion"][0]

    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "encargo")["campos"],
            "Finalidad de la valoración",
        )
        == "Finalidad modelo nuevo"
    )
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "resultado")["campos"],
            "Valor de tasación final",
        )
        == "240000.0"
    )
    assert len(contexto["comparables_valoracion"]) == 1
    assert contexto["comparables_valoracion"][0]["origen"] == "modelo_nuevo"
    assert (
        _campo_valor(contexto["comparables_valoracion"][0]["campos"], "Dirección")
        == "Calle Testigo Nuevo"
    )


def test_valoracion_helpers_no_afectan_no_valoracion(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PAT-HELPERS-FALLBACK",
                "patologias",
                "particular",
                "Cliente Patologias",
                "Calle Patologias",
                1,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id)

    assert contexto["es_valoracion"] is False
    assert contexto["valoracion"] == []
    assert contexto["comparables_valoracion"] == []
    assert contexto["completitud_valoracion"] == {
        "advertencias": [],
        "completo": True,
        "total_advertencias": 0,
    }
