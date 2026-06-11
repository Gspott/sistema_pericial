from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Dashboard", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_dashboard_crm_cockpit_renderiza_readonly_y_respeta_owner(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "dashboard_owner")
        other_id = _crear_usuario(cur, "dashboard_other")
        cur.execute(
            """
            INSERT INTO clientes (nombre, apellidos, email, owner_user_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Cliente", "Cockpit", "cliente@example.test", owner_id),
        )
        cliente_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, telefono, origen, estado, cliente_id, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Lead visible cockpit",
                "lead@example.test",
                "600000001",
                "abogado",
                "contactado",
                cliente_id,
                owner_id,
            ),
        )
        lead_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lead_id, "Llamar hoy", "llamada", "2020-01-01", "pendiente", owner_id),
        )
        tarea_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO lead_contactos (
                lead_id, fecha, tipo, resumen, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (lead_id, "2026-06-01", "email", "Contacto previo", owner_id),
        )
        cur.execute(
            """
            INSERT INTO propuestas (
                numero_propuesta, lead_id, cliente_id, fecha, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("P-CRM-1A", lead_id, cliente_id, "2026-06-01", "enviada", owner_id),
        )
        propuesta_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO emails_enviados (
                tipo, destinatario, asunto, referencia_entidad_tipo,
                referencia_entidad_id, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "propuesta",
                "lead@example.test",
                "Propuesta enviada",
                "propuesta",
                propuesta_id,
                owner_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO leads (nombre, estado, owner_user_id)
            VALUES (?, ?, ?)
            """,
            ("Lead ajeno no visible", "nuevo", other_id),
        )
        cur.execute(
            """
            INSERT INTO leads (
                nombre, email, origen, estado, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "Administrador prospectado",
                "admin@example.test",
                "administrador_fincas",
                "pendiente",
                "Madrid",
                owner_id,
            ),
        )
        admin_lead_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO leads (nombre, origen, estado, owner_user_id)
            VALUES (?, ?, ?, ?)
            """,
            ("Lead respondido", "empresa", "respondio", owner_id),
        )
        cur.execute(
            """
            INSERT INTO lead_contactos (
                lead_id, fecha, tipo, resumen, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (admin_lead_id, "2026-06-02", "reunion", "Reunión inicial", owner_id),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert '<body class="dashboard-cockpit-page">' in response.text
    assert '<div class="page dashboard-page dashboard-cockpit">' in response.text
    assert '<main class="page dashboard-page dashboard-cockpit">' not in response.text
    assert "/static/mobile.css?v=11" in response.text
    assert "Cockpit operativo" in response.text
    assert "Hoy" in response.text
    assert "Seguimientos pendientes hoy" in response.text
    assert "Captación" in response.text
    assert "Comunicación" in response.text
    assert "Pipeline" in response.text
    assert "Lead visible cockpit" in response.text
    assert "Llamar hoy" in response.text
    assert "días de retraso" in response.text
    assert "Nueva tarea" in response.text
    assert "Propuesta enviada" in response.text
    assert "/propuestas/nueva?lead_id=" in response.text
    assert f"/leads/{lead_id}/tareas/{tarea_id}/hecha" in response.text
    assert "Actividad operativa" in response.text
    assert "Campañas / Próximos pasos" in response.text
    assert "Prospección" in response.text
    assert "Administradores" in response.text
    assert "Abogados" in response.text
    assert "Pendientes contacto" in response.text
    assert "Respondidos" in response.text
    assert "Reuniones" in response.text
    assert "/leads?tipo=administrador_fincas" in response.text
    assert "/leads?estado=respondio" in response.text
    assert "dashboard-priority-section" in response.text
    assert "dashboard-operative-section" in response.text
    assert "dashboard-capture-section" in response.text
    assert "dashboard-communication-section" in response.text
    assert "dashboard-campaign-section" in response.text
    assert "dashboard-admin-section" in response.text
    assert "Lead ajeno no visible" not in response.text

    filtrado = client.get("/dashboard?periodo=30&tipo=leads&estado=contactado")
    assert filtrado.status_code == 200
    assert "Lead visible cockpit" in filtrado.text
    assert "selected>30 días" in filtrado.text
    assert "selected>Leads" in filtrado.text
    assert "selected>Contactado" in filtrado.text

    response = client.post(
        f"/leads/{lead_id}/tareas/{tarea_id}/hecha",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        tarea = conn.execute(
            """
            SELECT estado
            FROM lead_tareas
            WHERE id = ? AND lead_id = ? AND owner_user_id = ?
            """,
            (tarea_id, lead_id, owner_id),
        ).fetchone()
    finally:
        conn.close()
    assert tarea["estado"] == "hecha"


def test_dashboard_crm_degrada_sin_log_emails(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "dashboard_degrada")
        cur.execute("DROP TABLE emails_enviados")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Comunicación" in response.text
    assert "No hay emails enviados registrados." in response.text


def test_dashboard_css_declara_override_desktop_especifico():
    css = (REPO_ROOT / "static" / "mobile.css").read_text(encoding="utf-8")

    assert "body.dashboard-cockpit-page .dashboard-cockpit" in css
    assert (
        "body.dashboard-cockpit-page .app-shell > .app-content > .dashboard-cockpit.page"
        in css
    )
    assert "grid-template-columns: repeat(12, minmax(0, 1fr));" in css
    assert "max-width: 1440px !important;" in css
    assert "min-width: 1200px;" in css
