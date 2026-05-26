import io
import zipfile


def test_build_informe_context_returns_minimum_structure(isolated_import):
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
                cliente, direccion, objeto_pericia, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-SMOKE-001",
                "patologias",
                "particular",
                "Cliente Demo",
                "Calle Demo 1",
                "Informe pericial demo",
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
            (expediente_id, "2026-01-12", "Tecnico Demo", "Visita demo"),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")

    assert contexto["expediente"]["numero_expediente"] == "EXP-SMOKE-001"
    assert contexto["expediente"]["tipo_informe"] == "patologias"
    assert contexto["tipo_informe"] == "patologias"
    assert contexto["es_valoracion"] is False
    assert contexto["valoracion"] == []
    assert contexto["comparables_valoracion"] == []
    assert contexto["completitud_valoracion"] == {
        "advertencias": [],
        "completo": True,
        "total_advertencias": 0,
    }
    assert "visitas" in contexto
    assert "estancias" in contexto
    assert "patologias_exteriores" in contexto
    assert "toc_items" in contexto


def _grupo_por_clave(valoracion_visita: dict, clave: str) -> dict:
    for grupo in valoracion_visita["grupos"]:
        if grupo["clave"] == clave:
            return grupo
    raise AssertionError(f"Grupo de valoración no encontrado: {clave}")


def _campo_valor(campos, etiqueta: str) -> str:
    for campo in campos:
        if campo["label"] == etiqueta:
            return campo["value"]
    raise AssertionError(f"Campo no encontrado: {etiqueta}")


def test_build_informe_context_degrades_for_valoracion_without_patologias(isolated_import):
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
                cliente, direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-SMOKE-VAL-001",
                "valoracion",
                "particular",
                "Cliente Valoracion Smoke",
                "Calle Valoracion Demo 1",
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
                "Visita de valoracion sin patologias.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, identificacion_bien,
                superficie_valoracion, situacion_ocupacion,
                criterios_metodo_valoracion, valor_tasacion_final
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Compraventa",
                "Vivienda demo de smoke",
                "90 m2",
                "Libre",
                "Metodo de comparacion",
                "180000 EUR",
            ),
        )
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, precio_oferta,
                valor_unitario, superficie_construida, tipologia,
                estado_conservacion, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Testigo Demo 2",
                "Portal inmobiliario demo",
                "185000 EUR",
                "2055 EUR/m2",
                "90 m2",
                "Piso",
                "Buen estado",
                "Comparable demo no visitado.",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")

    assert contexto["expediente"]["tipo_informe"] == "valoracion"
    assert contexto["tipo_informe"] == "valoracion"
    assert contexto["es_valoracion"] is True
    assert contexto["portada"]["tipo_trabajo"] == "Informe de valoración"
    assert len(contexto["visitas"]) == 1
    assert contexto["visitas"][0]["id"] == visita_id
    assert len(contexto["valoracion"]) == 1

    valoracion = contexto["valoracion"][0]
    assert valoracion["visita"]["id"] == visita_id
    assert valoracion["hay_datos"] is True
    assert {grupo["clave"] for grupo in valoracion["grupos"]} >= {
        "encargo",
        "documentacion",
        "identificacion",
        "situacion_legal",
        "entorno",
        "edificio_inmueble",
        "constructivo",
        "estado",
        "metodo",
        "resultado",
        "limitaciones",
    }
    assert _grupo_por_clave(valoracion, "encargo")["hay_datos"] is True
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "encargo")["campos"],
            "Finalidad de la valoración",
        )
        == "Compraventa"
    )
    assert (
        _campo_valor(
            _grupo_por_clave(valoracion, "resultado")["campos"],
            "Valor de tasación final",
        )
        == "180000 EUR"
    )

    assert len(contexto["comparables_valoracion"]) == 1
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["visita_id"] == visita_id
    assert _campo_valor(comparable["campos"], "Dirección") == "Calle Testigo Demo 2"
    assert _campo_valor(comparable["campos"], "Valor unitario") == "2.055 €/m²"
    assert contexto["estancias"] == []
    assert contexto["patologias_exteriores"] == []
    assert contexto["mapas"] == []
    assert contexto["total_figuras"] == 0
    assert isinstance(contexto["toc_items"], list)


def test_build_informe_context_valoracion_without_visits_or_comparables(isolated_import):
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
                "EXP-SMOKE-VAL-EMPTY",
                "valoracion",
                "particular",
                "Cliente Valoracion Sin Visitas",
                "Calle Valoracion Vacia 1",
                1,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")

    assert contexto["tipo_informe"] == "valoracion"
    assert contexto["es_valoracion"] is True
    assert contexto["visitas"] == []
    assert contexto["valoracion"] == []
    assert contexto["comparables_valoracion"] == []
    assert contexto["completitud_valoracion"]["completo"] is False
    assert contexto["completitud_valoracion"]["total_advertencias"] >= 9


def _render_informe_html(main_module, contexto: dict) -> str:
    template = main_module.templates.env.get_template("informes/imprimir.html")
    return template.render({**contexto, "modo_pdf": False})


def test_informe_html_valoracion_renderiza_secciones_propias(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

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
                "EXP-SMOKE-VAL-HTML",
                "valoracion",
                "particular",
                "Cliente Valoracion HTML",
                "Calle Valoracion HTML 1",
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
                "Visita de valoracion para HTML.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, documentacion_utilizada,
                identificacion_bien, superficie_valoracion,
                situacion_ocupacion, descripcion_entorno, tipo_edificio,
                estructura, estado_inmueble, criterios_metodo_valoracion,
                valor_tasacion_final, condicionantes_limitaciones_valoracion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Compraventa",
                "Catastro y visita",
                "Vivienda demo HTML",
                "90 m2",
                "Libre",
                "Entorno residencial consolidado",
                "Edificio plurifamiliar",
                "Estructura convencional",
                "Buen estado",
                "Metodo de comparacion",
                "180000 EUR",
                "Superficies no comprobadas registralmente",
            ),
        )
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, precio_oferta,
                valor_unitario, superficie_construida, tipologia,
                estado_conservacion, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Testigo HTML 2",
                "Portal inmobiliario demo",
                "185000 EUR",
                "2055 EUR/m2",
                "90 m2",
                "Piso",
                "Buen estado",
                "Comparable demo no visitado.",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    html = _render_informe_html(main_module, contexto)

    assert contexto["completitud_valoracion"]["advertencias"] == []
    assert "INFORME DE VALORACIÓN INMOBILIARIA" in html
    for titulo in (
        "Encargo",
        "Documentación utilizada",
        "Identificación del bien",
        "Situación legal",
        "Entorno",
        "Edificio/inmueble",
        "Características constructivas",
        "Estado",
        "Método de valoración",
        "Comparables",
        "Resultado",
        "Limitaciones",
    ):
        assert titulo in html
    assert "Calle Testigo HTML 2" in html
    assert "180000 EUR" in html
    assert "Datos específicos del informe de patologías" not in html
    assert "Patologías interiores" not in html
    assert "Patologías exteriores" not in html
    assert "Propuesta de reparación" not in html
    assert "Conclusiones técnicas" not in html


def test_informe_html_valoracion_incompleta_muestra_advertencias(isolated_import):
    main_module = isolated_import("app.main")

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
                "EXP-SMOKE-VAL-WARN",
                "valoracion",
                "particular",
                "Cliente Valoracion Incompleta",
                "Calle Valoracion Incompleta 1",
                1,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    html = _render_informe_html(main_module, contexto)

    assert contexto["completitud_valoracion"]["completo"] is False
    assert "Falta documentacion utilizada." in html
    assert "Faltan comparables de mercado." in html
    assert "Estas advertencias no bloquean la generación manual del informe." in html


def test_informe_html_patologias_conserva_secciones_existentes(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, objeto_pericia, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-SMOKE-PAT-HTML",
                "patologias",
                "particular",
                "Cliente Patologias HTML",
                "Calle Patologias HTML 1",
                "Informe pericial de patologias demo",
                1,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")
    html = _render_informe_html(main_module, contexto)

    assert "Datos específicos del informe de patologías" in html
    assert "Patologías interiores" in html
    assert "Patologías exteriores" in html
    assert "Propuesta de reparación" in html
    assert "INFORME DE VALORACIÓN INMOBILIARIA" not in html


def _docx_text(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_docx_editable_valoracion_usa_contexto_moderno(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import generar_informe_docx_editable_bytes

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
                "EXP-SMOKE-VAL-DOCX",
                "valoracion",
                "particular",
                "Cliente Valoracion DOCX",
                "Calle Valoracion DOCX 1",
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
                "Visita de valoracion para DOCX.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO valoracion_visita (
                visita_id, finalidad_valoracion, documentacion_utilizada,
                identificacion_bien, superficie_valoracion,
                situacion_ocupacion, descripcion_entorno, tipo_edificio,
                estructura, estado_inmueble, criterios_metodo_valoracion,
                valor_tasacion_final, condicionantes_limitaciones_valoracion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Compraventa",
                "Catastro y visita",
                "Vivienda demo DOCX",
                "90 m2",
                "Libre",
                "Entorno residencial consolidado",
                "Edificio plurifamiliar",
                "Estructura convencional",
                "Buen estado",
                "Metodo de comparacion",
                "180000 EUR",
                "Superficies no comprobadas registralmente",
            ),
        )
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, precio_oferta,
                valor_unitario, superficie_construida, tipologia,
                estado_conservacion, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Testigo DOCX 2",
                "Portal inmobiliario demo",
                "185000 EUR",
                "2055 EUR/m2",
                "90 m2",
                "Piso",
                "Buen estado",
                "Comparable demo no visitado.",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    docx_bytes = generar_informe_docx_editable_bytes(expediente_id)
    texto = _docx_text(docx_bytes)

    assert docx_bytes.startswith(b"PK")
    for titulo in (
        "INFORME DE VALORACIÓN INMOBILIARIA",
        "Encargo",
        "Documentación utilizada",
        "Identificación del bien",
        "Situación legal",
        "Entorno",
        "Edificio/inmueble",
        "Características constructivas",
        "Estado",
        "Método de valoración",
        "Comparables",
        "Resultado",
        "Limitaciones",
    ):
        assert titulo in texto
    assert "Calle Testigo DOCX 2" in texto
    assert "180000 EUR" in texto
    assert "Datos específicos del informe de patologías" not in texto
    assert "Patologías interiores" not in texto
    assert "Patologías exteriores" not in texto
    assert "Conclusiones técnicas" not in texto
