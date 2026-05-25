def _campo_valor(campos, etiqueta: str) -> str:
    for campo in campos:
        if campo["label"] == etiqueta:
            return campo["value"]
    raise AssertionError(f"Campo no encontrado: {etiqueta}")


def test_expediente_visita_build_informe_context_sin_fotos(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
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
                "EXP-SMOKE-FLOW-001",
                "patologias",
                "particular",
                "Cliente Informe Smoke",
                "Calle Informe Demo 1",
                "28000",
                "Madrid",
                "Madrid",
                "Vivienda",
                "Informe pericial demo sin generar documentos.",
                "Humedad localizada en estancia demo.",
                "Pendiente de confirmacion con inspeccion completa.",
                "Inspeccion visual demo.",
                "Reparacion demo pendiente de definir.",
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
                "Tecnico Smoke",
                "Visita demo sin fotos ni adjuntos.",
            ),
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
                "Salon demo",
                "salon",
                "Ventilacion natural",
                "1",
                "Tarima",
                "Pintura",
                "Yeso",
                "Estancia demo sin fotografia asociada.",
            ),
        )
        estancia_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO biblioteca_patologias (
                nombre, categoria, elemento_afectado, rol_patologia, activo
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Humedad demo", "humedades", "paramento", "efecto", 1),
        )
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
                "Paramento vertical",
                "Humedad demo",
                "Patologia demo sin foto para validar degradacion controlada.",
                "",
                "Pared norte",
                "Zona superior junto a encuentro con techo",
                "",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    contexto = build_informe_context(expediente_id, base_url="http://testserver")

    assert contexto["expediente"]["id"] == expediente_id
    assert contexto["expediente"]["numero_expediente"] == "EXP-SMOKE-FLOW-001"
    assert contexto["expediente"]["tipo_informe"] == "patologias"
    assert contexto["portada"]["tipo_trabajo"] == "Informe de patologías"
    assert contexto["portada"]["tecnico"] == "Tecnico Smoke"

    assert len(contexto["visitas"]) == 1
    visita = contexto["visitas"][0]
    assert visita["id"] == visita_id
    assert visita["fecha"] == "2026-05-25"
    assert visita["tecnico"] == "Tecnico Smoke"
    assert visita["fotos_exteriores"] == []
    assert visita["climatologia"] == "No consta climatología registrada"

    assert len(contexto["estancias"]) == 1
    estancia = contexto["estancias"][0]
    assert estancia["id"] == estancia_id
    assert estancia["visita_id"] == visita_id
    assert estancia["nombre"] == "Salon demo"
    assert estancia["fotos"] == []
    assert isinstance(estancia["incoherencias"], list)
    assert estancia["incoherencias"]
    assert _campo_valor(estancia["campos"], "Ventilación") == "Ventilacion natural"

    assert len(estancia["patologias"]) == 1
    patologia = estancia["patologias"][0]
    assert patologia["titulo"] == "Humedad demo"
    assert patologia["fotos"] == []
    assert _campo_valor(patologia["campos"], "Localización del daño") == "Pared norte"
    assert _campo_valor(patologia["campos"], "Rol técnico") == "efecto"

    assert contexto["patologias_exteriores"] == []
    assert contexto["mapas"] == []
    assert contexto["total_figuras"] == 0
    assert isinstance(contexto["toc_items"], list)
    assert contexto["propuesta_reparacion"] == "Reparacion demo pendiente de definir."
