from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Desktop", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int) -> TestClient:
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente(
    cur,
    user_id: int,
    numero: str,
    tipo_informe: str = "patologias",
) -> int:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario, cliente,
            direccion, tipo_inmueble, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            tipo_informe,
            "particular",
            f"Cliente {numero}",
            f"Calle {numero}",
            "Vivienda",
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_visita(cur, expediente_id: int) -> int:
    cur.execute(
        """
        INSERT INTO visitas (
            expediente_id, fecha, tecnico, observaciones_visita
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            expediente_id,
            "2026-06-20",
            "Tecnico Desktop",
            "Visita para smoke desktop.",
        ),
    )
    return cur.lastrowid


def _crear_estancia(
    cur,
    visita_id: int,
    nombre: str,
    tipo_estancia: str = "Estancia",
    planta: str = "",
) -> int:
    cur.execute(
        """
        INSERT INTO estancias (
            visita_id, nombre, tipo_estancia, planta, ventilacion,
            acabado_pavimento, acabado_paramento, acabado_techo, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            nombre,
            tipo_estancia,
            planta,
            "",
            "",
            "",
            "",
            "",
        ),
    )
    return cur.lastrowid


def test_detalle_expediente_renderiza_capa_desktop_workbench(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "desktop_expediente_detalle")
        expediente_id = _crear_expediente(
            cur,
            user_id,
            "EXP-DESKTOP-001",
            tipo_informe="patologias",
        )
        visita_id = _crear_visita(cur, expediente_id)
        estancia_id = _crear_estancia(cur, visita_id, "Salón", "Salón", "Planta baja")
        cur.execute(
            """
            INSERT INTO registros_patologias (
                visita_id, estancia_id, elemento, patologia, observaciones, foto
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (visita_id, estancia_id, "Pared", "Fisura", "", ""),
        )
        cur.execute(
            "INSERT INTO estancia_fotos (estancia_id, archivo) VALUES (?, ?)",
            (estancia_id, "salon.jpg"),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/detalle-expediente/{expediente_id}")

    assert response.status_code == 200
    assert "desktop-shell" in response.text
    assert "desktop-toolbar" in response.text
    assert "desktop-sidebar" in response.text
    assert "desktop-main" in response.text
    assert "desktop-inspector" in response.text
    assert "Estructura del inmueble" in response.text
    assert "Planta baja" in response.text
    assert "Salón" in response.text
    assert f"/editar-estancia/{estancia_id}" in response.text
    assert f"/registrar-patologias/{visita_id}?estancia_id={estancia_id}#formulario_patologia_interior" in response.text
    assert "1 patología" in response.text
    assert "1 foto" in response.text
    assert "@media (min-width: 1280px)" in response.text
    assert "@media (min-width: 1920px)" in response.text
    assert "@media (min-width: 2560px)" in response.text
    assert "minmax(1200px, 1.8fr)" in response.text
    assert "max-height: calc(100vh - 106px)" in response.text
    assert "overflow-y: auto" in response.text

    assert f"/nueva-visita/{expediente_id}" in response.text
    assert f"/definir-estancias/{visita_id}" in response.text
    assert f"/expedientes/{expediente_id}/pericial-workbench#documentacion-aportada" in response.text
    assert f"/expedientes/{expediente_id}/informe-v2-editor" in response.text
    assert f"/expedientes/{expediente_id}/actuaciones-reparacion" in response.text
    assert "Actividad reciente" in response.text
    assert "Checklist de cierre" in response.text


def test_detalle_expediente_desktop_incluye_valoracion_si_aplica(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "desktop_expediente_valoracion")
        expediente_id = _crear_expediente(
            cur,
            user_id,
            "EXP-DESKTOP-VAL",
            tipo_informe="valoracion",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/detalle-expediente/{expediente_id}")

    assert response.status_code == 200
    assert f"/expediente/{expediente_id}/valoracion/workbench" in response.text
    assert "desktop-sidebar" in response.text
    assert "desktop-inspector" in response.text


def test_detalle_expediente_sin_datos_opcionales_sigue_renderizando(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "desktop_expediente_vacio")
        expediente_id = _crear_expediente(
            cur,
            user_id,
            "EXP-DESKTOP-VACIO",
            tipo_informe="patologias",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/detalle-expediente/{expediente_id}")

    assert response.status_code == 200
    assert "No hay visitas registradas." in response.text
    assert "No hay visitas creadas todavía para este expediente." in response.text
    assert "Sin movimientos económicos vinculados." in response.text
    assert "desktop-main" in response.text
    assert "Buscar en expediente" in response.text
    assert "<main class=\"desktop-main\"" in response.text
    assert "Estructura del inmueble" in response.text
    assert "No hay estancias registradas." in response.text
    assert "desktop-room-panel" in response.text
