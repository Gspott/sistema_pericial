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
    assert "visitas" in contexto
    assert "estancias" in contexto
    assert "patologias_exteriores" in contexto
    assert "toc_items" in contexto

