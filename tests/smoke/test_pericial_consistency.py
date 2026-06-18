from fastapi.testclient import TestClient


def _crear_usuario(cur) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash, activo
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Demo", "", "consistency", "hash", 1),
    )
    return cur.lastrowid


def _crear_expediente_basico(cur, owner_user_id: int = 1) -> int:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, objeto_pericia, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EXP-CONSISTENCY-001",
            "patologias",
            "particular",
            "Cliente Demo",
            "Calle Demo 1",
            "Informe pericial demo",
            owner_user_id,
        ),
    )
    return cur.lastrowid


def _crear_visita(cur, expediente_id: int) -> int:
    cur.execute(
        """
        INSERT INTO visitas (expediente_id, fecha, tecnico, observaciones_visita)
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, "2026-01-12", "Tecnico Demo", "Visita demo"),
    )
    return cur.lastrowid


def _guardar_capitulo(cur, expediente_id: int, clave: str, titulo: str, contenido: str, orden: int = 1):
    cur.execute(
        """
        INSERT INTO informe_v2_capitulos (
            expediente_id, clave, titulo, orden, contenido, editado_manual
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (expediente_id, clave, titulo, orden, contenido, 1),
    )


def test_consistency_service_returns_stable_structure(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert set(resultado) >= {
        "expediente_id",
        "errores",
        "advertencias",
        "advertencias_coherencia",
        "riesgos_periciales",
        "revision_juridica",
        "informacion",
        "score",
        "resumen",
    }
    assert resultado["expediente_id"] == expediente_id
    assert isinstance(resultado["errores"], list)
    assert isinstance(resultado["advertencias"], list)
    assert isinstance(resultado["advertencias_coherencia"], list)
    assert isinstance(resultado["riesgos_periciales"], list)
    assert isinstance(resultado["revision_juridica"], list)
    assert isinstance(resultado["informacion"], list)
    assert {"codigo", "severidad", "categoria", "mensaje", "entidad", "entidad_id"} <= set(
        resultado["informacion"][0]
    )


def test_consistency_detects_empty_chapter(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Resumen ejecutivo",
            "Pendiente de redacción.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(item["codigo"] == "EMPTY_CHAPTER" for item in resultado["errores"])


def test_consistency_detects_photo_not_referenced_and_broken_reference(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        visita_id = _crear_visita(cur, expediente_id)
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, ?, ?, ?)
            """,
            (visita_id, "exterior", "demo/foto1.jpg", "Fachada"),
        )
        _guardar_capitulo(
            cur,
            expediente_id,
            "conclusiones_periciales",
            "Conclusiones",
            "La Figura 2 evidencia la filtración descrita.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(item["codigo"] == "PHOTO_NOT_REFERENCED" for item in resultado["advertencias"])
    assert any(item["codigo"] == "PHOTO_REFERENCE_BROKEN" for item in resultado["errores"])


def test_consistency_detects_annex_not_referenced_and_broken_reference(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, tipo_documento,
                archivo_ruta, archivo_nombre_original, orden
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                expediente_id,
                "Presupuesto aportado",
                "Presupuesto",
                "expediente_documentos/1/presupuesto.pdf",
                "presupuesto.pdf",
                1,
            ),
        )
        _guardar_capitulo(
            cur,
            expediente_id,
            "antecedentes_objeto",
            "Antecedentes y objeto",
            "Se revisa la documentación y se cita el Anexo Z.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(item["codigo"] == "ANNEX_NOT_REFERENCED" for item in resultado["advertencias"])
    assert any(item["codigo"] == "ANNEX_REFERENCE_BROKEN" for item in resultado["errores"])


def test_consistency_detects_structural_collapse_risk_statement(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "conclusiones_periciales",
            "Conclusiones",
            "Se aprecia riesgo de colapso en la zona afectada.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    riesgos = resultado["riesgos_periciales"]
    assert any(item["codigo"] == "RISK_STRUCTURAL_COLLAPSE" for item in riesgos)
    assert any(item["categoria"] == "riesgo_pericial" for item in riesgos)
    assert any("riesgo de colapso" in item.get("fragmento", "") for item in riesgos)


def test_consistency_detects_mechanical_properties_risk_statement(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "analisis_causal",
            "Análisis causal",
            "La exposición continuada produce pérdida de propiedades mecánicas.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(
        item["codigo"] == "RISK_MECHANICAL_PROPERTIES"
        for item in resultado["riesgos_periciales"]
    )


def test_consistency_detects_categorical_causation_risk_statement(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "analisis_causal",
            "Análisis causal",
            "Queda demostrado que la humedad procede de la cubierta.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(
        item["codigo"] == "RISK_CAUSATION_CERTAINTY"
        for item in resultado["riesgos_periciales"]
    )


def test_consistency_detects_legal_excessive_certainty(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "conclusiones_periciales",
            "Conclusiones",
            "Queda demostrado que los daños proceden de la cubierta.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)
    revision = resultado["revision_juridica"]

    assert any(item["codigo"] == "LEGAL_EXCESSIVE_CERTAINTY" for item in revision)
    assert any(item["categoria"] == "revision_juridica" for item in revision)
    assert any("sugerencia" in item for item in revision)


def test_consistency_detects_legal_absolute_causation(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "analisis_causal",
            "Análisis causal",
            "La causa es la falta de mantenimiento de la cubierta.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(
        item["codigo"] == "LEGAL_ABSOLUTE_CAUSATION"
        for item in resultado["revision_juridica"]
    )


def test_consistency_detects_legal_attribution_of_liability(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "conclusiones_periciales",
            "Conclusiones",
            "La constructora es responsable de las deficiencias observadas.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(
        item["codigo"] == "LEGAL_ATTRIBUTION_OF_LIABILITY"
        for item in resultado["revision_juridica"]
    )


def test_consistency_detects_legal_overconclusive_language(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.pericial_consistency import analizar_consistencia_expediente

    conn = get_connection()
    try:
        cur = conn.cursor()
        expediente_id = _crear_expediente_basico(cur)
        _guardar_capitulo(
            cur,
            expediente_id,
            "valoracion_economica",
            "Valoración económica",
            "Sin lugar a dudas, la reparación debe ejecutarse de forma inmediata.",
        )
        conn.commit()
    finally:
        conn.close()

    resultado = analizar_consistencia_expediente(expediente_id)

    assert any(
        item["codigo"] == "LEGAL_OVERCONCLUSIVE_LANGUAGE"
        for item in resultado["revision_juridica"]
    )


def test_consistency_block_is_rendered_in_informe_v2_editor(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id = _crear_expediente_basico(cur, owner_user_id=user_id)
        _crear_visita(cur, expediente_id)
        conn.commit()
    finally:
        conn.close()

    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )

    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Revisión de coherencia" in response.text
    assert "Afirmaciones a revisar" in response.text
    assert "Redacción potencialmente impugnable" in response.text
    assert "Motor V1 informativo" in response.text
