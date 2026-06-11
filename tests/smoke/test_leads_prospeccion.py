from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Prospeccion", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_leads_prospeccion_filtra_tipifica_y_prepara_seleccion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "leads_prospeccion_owner")
        other_id = _crear_usuario(cur, "leads_prospeccion_other")
        cur.execute(
            """
            INSERT INTO clientes (
                nombre, apellidos, email, ciudad, provincia, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Comunidad", "Centro", "comunidad@example.test", "Madrid", "Madrid", owner_id),
        )
        cliente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, telefono, origen, estado, servicio_solicitado,
                notas, cliente_id, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Administrador Madrid",
                "admin-madrid@example.test",
                "600000111",
                "administrador_fincas",
                "pendiente",
                "ITE comunidad",
                "Zona Madrid centro",
                cliente_id,
                owner_id,
            ),
        )
        lead_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, origen, estado, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Abogado no filtrado",
                "abogado@example.test",
                "abogado",
                "respondio",
                "Barcelona",
                owner_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO leads (nombre, origen, estado, owner_user_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Lead ajeno", "administrador_fincas", "pendiente", other_id),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get(
        "/leads?tipo=administrador_fincas&estado=pendiente&localidad=Madrid&fecha=30"
    )

    assert response.status_code == 200
    assert "Repositorio de prospección comercial" in response.text
    assert "Administrador de fincas" in response.text
    assert "Pendiente" in response.text
    assert "Administrador Madrid" in response.text
    assert "Abogado no filtrado" not in response.text
    assert "Lead ajeno" not in response.text
    assert f'name="lead_ids" value="{lead_id}"' in response.text
    assert "Acciones masivas" in response.text
    assert "disabled" in response.text
    assert 'name="tipo"' in response.text
    assert 'name="localidad"' in response.text
    assert 'name="fecha"' in response.text


def test_lead_form_usa_origen_como_tipo_sin_nuevo_esquema(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "leads_prospeccion_form")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/leads/nuevo")

    assert response.status_code == 200
    assert "Tipo / categoría" in response.text
    assert 'name="origen"' in response.text
    assert 'value="administrador_fincas"' in response.text
    assert 'value="abogado"' in response.text
    assert 'value="respondio"' in response.text
    assert 'value="reunion"' in response.text


def test_workbench_prospeccion_crea_detecta_duplicados_y_marca_revisado(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "workbench_prospeccion_owner")
        other_id = _crear_usuario(cur, "workbench_prospeccion_other")
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, telefono, origen, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Administrador existente",
                "duplicado@example.test",
                "600 111 222",
                "administrador_fincas",
                "pendiente",
                owner_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, origen, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Administrador ajeno",
                "ajeno@example.test",
                "administrador_fincas",
                "pendiente",
                other_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/leads/prospeccion")

    assert response.status_code == 200
    assert "Workbench de prospección" in response.text
    assert "Alta rápida" in response.text
    assert "Crear lead y seguir" in response.text
    assert "Administrador existente" in response.text
    assert "Administrador ajeno" not in response.text

    response = client.post(
        "/leads/prospeccion",
        data={
            "empresa": "Administrador nuevo",
            "contacto": "Ana Admin",
            "email": "nuevo@example.test",
            "telefono": "600222333",
            "localidad": "Madrid",
            "tipo": "administrador_fincas",
            "web": "adminnuevo.test",
            "observaciones": "Contacto encontrado manualmente",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/leads/prospeccion?" in response.headers["location"]

    conn = get_connection()
    try:
        lead = conn.execute(
            """
            SELECT *
            FROM leads
            WHERE owner_user_id = ? AND email = ?
            """,
            (owner_id, "nuevo@example.test"),
        ).fetchone()
    finally:
        conn.close()
    assert lead is not None
    assert lead["nombre"] == "Administrador nuevo"
    assert lead["origen"] == "administrador_fincas"
    assert lead["estado"] == "pendiente"
    assert "Localidad: Madrid" in lead["mensaje"]
    assert "Web: https://adminnuevo.test" in lead["notas"]

    response = client.post(
        "/leads/prospeccion",
        data={
            "empresa": "Administrador duplicado",
            "email": "duplicado@example.test",
            "telefono": "600111222",
            "localidad": "Madrid",
            "tipo": "administrador_fincas",
        },
    )
    assert response.status_code == 200
    assert "Posibles duplicados encontrados" in response.text
    assert "Administrador existente" in response.text
    assert "Crear de todos modos" in response.text

    response = client.post(
        f"/leads/prospeccion/{lead['id']}/revisado",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        revisado = conn.execute(
            """
            SELECT estado
            FROM leads
            WHERE id = ? AND owner_user_id = ?
            """,
            (lead["id"], owner_id),
        ).fetchone()
    finally:
        conn.close()
    assert revisado["estado"] == "contactado"
