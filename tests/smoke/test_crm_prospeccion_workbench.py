from fastapi.testclient import TestClient


def test_plantilla_administrador_fincas_existe_y_renderiza_variables(isolated_import):
    templates = isolated_import("app.services.crm_templates")

    plantilla = templates.obtener_plantilla_comercial("presentacion_administrador_fincas")
    assert plantilla is not None
    assert plantilla.tipo_lead == "administrador_fincas"
    assert plantilla.nombre == "Presentación Administradores de fincas"

    asunto, cuerpo = templates.renderizar_plantilla_comercial(
        plantilla,
        {
            "nombre_contacto": "María",
            "telefono": "600 111 222",
            "email": "contacto@example.test",
        },
    )

    assert asunto == "Servicios de informes periciales para comunidades administradas"
    assert "Buenos días, María:" in cuerpo
    assert "Un cordial saludo," in cuerpo
    assert "600 111 222" not in cuerpo
    assert "contacto@example.test" not in cuerpo
    assert "Arquitecto Técnico · Perito Judicial" not in cuerpo
    assert "{nombre_contacto}" not in cuerpo


def test_plantilla_seguimiento_administrador_fincas_existe_y_renderiza_variables(isolated_import):
    templates = isolated_import("app.services.crm_templates")

    plantilla = templates.obtener_plantilla_comercial("seguimiento_administrador_fincas_10d")
    assert plantilla is not None
    assert plantilla.tipo_lead == "administrador_fincas"
    assert plantilla.nombre == "Seguimiento Administradores de fincas 10 días"

    asunto, cuerpo = templates.renderizar_plantilla_comercial(
        plantilla,
        {
            "telefono": "600 111 222",
            "email": "contacto@example.test",
            "web": "https://example.test",
        },
    )

    assert asunto == "Seguimiento de presentación y disponibilidad técnica"
    assert "Hace unos días os remití" in cuerpo
    assert "Un cordial saludo," in cuerpo
    assert "Tel. 600 111 222" not in cuerpo
    assert "contacto@example.test" not in cuerpo
    assert "https://example.test" not in cuerpo
    assert "Arquitecto Técnico · Perito Judicial" not in cuerpo


def test_plantilla_usa_fallback_si_falta_nombre_contacto(isolated_import):
    templates = isolated_import("app.services.crm_templates")
    plantilla = templates.plantilla_para_tipo("administrador_fincas")
    email = templates.construir_email_comercial(
        "administrador_fincas",
        {"nombre": ""},
        {"nombre": "", "apellido1": ""},
    )

    assert email["plantilla"] == plantilla
    assert "Buenos días, equipo:" in email["cuerpo"]
    assert "623 829 228" not in email["cuerpo"]
    assert "contacto@carlosblancoperito.es" not in email["cuerpo"]


def _crear_usuario(cur, username: str = "crm_prospeccion") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Carlos", "Blanco", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_lead(
    cur,
    user_id: int,
    nombre: str,
    email: str = "",
    estado: str = "nuevo",
    origen: str = "captacion manual",
    servicio: str = "Administrador de fincas",
    notas: str = "Administrador de fincas Madrid",
):
    cur.execute(
        """
        INSERT INTO leads (
            nombre, email, telefono, origen, servicio_solicitado,
            mensaje, estado, prioridad, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nombre,
            email,
            "600000000",
            origen,
            servicio,
            "Comunidad en Madrid",
            estado,
            "alta",
            notas,
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_email_programado(
    cur,
    user_id: int,
    lead_id: int,
    destinatario: str = "admin@example.test",
    tipo: str = "presentacion_programada",
    asunto: str = "Asunto programado",
    cuerpo: str = "Cuerpo programado.",
    fecha_programada: str = "2026-06-20T09:30",
    plantilla: str = "presentacion_administrador_fincas",
):
    cur.execute(
        """
        INSERT INTO emails_enviados (
            tipo, destinatario, asunto, cuerpo_texto, estado, error_mensaje,
            referencia_entidad_tipo, referencia_entidad_id, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tipo,
            destinatario,
            asunto,
            cuerpo,
            "programado",
            f"programado_para={fecha_programada}; plantilla={plantilla}",
            "lead",
            lead_id,
            user_id,
        ),
    )
    return cur.lastrowid


def _preparar_cliente_con_leads(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        administrador_id = _crear_lead(
            cur,
            user_id,
            "Administración Fincas Centro",
            "admin@example.test",
        )
        abogado_id = _crear_lead(
            cur,
            user_id,
            "Despacho Legal Norte",
            "legal@example.test",
            servicio="Abogado comunidades",
            notas="Despacho profesional",
        )
        sin_email_id = _crear_lead(
            cur,
            user_id,
            "Administración Sin Email",
            "",
        )
        conn.commit()
    finally:
        conn.close()

    return main_module, _autenticar_cliente(main_module, user_id), user_id, administrador_id, abogado_id, sin_email_id


def test_crm_prospeccion_workbench_carga_y_filtra_administradores(isolated_import):
    _main_module, client, _user_id, _administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )

    response = client.get("/crm/prospeccion")
    assert response.status_code == 200
    assert "Prospección CRM" in response.text
    assert "Administración Fincas Centro" in response.text
    assert "Despacho Legal Norte" in response.text

    filtrado = client.get("/crm/prospeccion?tipo=administrador_fincas")
    assert filtrado.status_code == 200
    assert "Administración Fincas Centro" in filtrado.text
    assert "Administración Sin Email" in filtrado.text
    assert "Despacho Legal Norte" not in filtrado.text


def test_alta_rapida_crea_lead_y_deja_formulario_listo(isolated_import):
    _main_module, client, user_id, _administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection

    response = client.post(
        "/crm/prospeccion/leads/rapido",
        data={
            "nombre": "Administración Nueva Semana",
            "persona_contacto": "Laura",
            "tipo_profesion": "administrador_fincas",
            "email": "laura@example.test",
            "telefono": "611222333",
            "localidad": "Valencia",
            "fuente": "listado colegios",
            "notas": "Priorizar esta semana",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Lead guardado. Formulario listo para otro." in response.text
    assert 'id="crm-quick-lead-form"' in response.text
    assert 'id="quick-nombre" name="nombre" type="text"' in response.text
    assert "Panel de trabajo" in response.text
    assert "Administración Nueva Semana" in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute(
            "SELECT * FROM leads WHERE owner_user_id = ? AND nombre = ?",
            (user_id, "Administración Nueva Semana"),
        ).fetchone()
    finally:
        conn.close()

    assert lead is not None
    assert lead["email"] == "laura@example.test"
    assert lead["servicio_solicitado"] == "Administrador de fincas"
    assert "Persona de contacto: Laura" in lead["notas"]
    assert "Localidad: Valencia" in lead["notas"]


def test_panel_derecho_muestra_preview_personalizado_para_lead_seleccionado(isolated_import):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )

    response = client.get(f"/crm/prospeccion?lead_id={administrador_id}")

    assert response.status_code == 200
    assert "Panel de trabajo" in response.text
    assert "Presentación Administradores de fincas" in response.text
    assert "Servicios de informes periciales para comunidades administradas" in response.text
    assert "Buenos días, Administración Fincas Centro:" in response.text
    assert "Cuerpo renderizado y editable" in response.text


def test_click_nombre_empresa_selecciona_lead_mantiene_filtros_y_abrir_lead_independiente(isolated_import):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )

    listado = client.get("/crm/prospeccion?tipo=administrador_fincas&email=con_email")
    assert listado.status_code == 200
    assert 'class="crm-lead-selector"' in listado.text
    assert "Administración Fincas Centro" in listado.text
    assert 'href="/crm/prospeccion?' in listado.text
    assert "tipo=administrador_fincas" in listado.text
    assert "email=con_email" in listado.text
    assert f"lead_id={administrador_id}" in listado.text
    assert "data-preserve-workbench-scroll" in listado.text

    seleccionado = client.get(
        f"/crm/prospeccion?tipo=administrador_fincas&email=con_email&lead_id={administrador_id}"
    )
    assert seleccionado.status_code == 200
    assert '<tr class="is-selected">' in seleccionado.text
    assert "crm-row-indicator" in seleccionado.text
    assert "Panel de trabajo" in seleccionado.text
    assert "Servicios de informes periciales para comunidades administradas" in seleccionado.text
    assert f'href="/leads/{administrador_id}"' in seleccionado.text


def test_cambio_plantilla_auto_actualiza_y_protege_ediciones_manuales(isolated_import):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )

    response = client.get(
        f"/crm/prospeccion?lead_id={administrador_id}&plantilla=seguimiento_administrador_fincas_10d"
    )
    assert response.status_code == 200
    assert 'id="crm-template-switch-form"' in response.text
    assert 'data-current-template="seguimiento_administrador_fincas_10d"' in response.text
    assert '<button class="boton secundario" type="submit">Previsualizar</button>' not in response.text
    assert "Seguimiento de presentación y disponibilidad técnica" in response.text
    assert "Hace unos días os remití" in response.text
    assert 'templateSelect.addEventListener("change"' in response.text
    assert "templateForm.submit()" in response.text
    assert "Cambiar de plantilla sustituirá el asunto y cuerpo actuales." in response.text
    assert "templateSelect.value = currentTemplate" in response.text
    assert "saveWorkbenchScroll()" in response.text
    assert 'id="crm-open-email-preview"' in response.text
    assert 'id="crm-email-preview-modal"' in response.text


def test_preview_modal_email_existe_renderiza_y_no_modifica_estado(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Abrir/cargar preview no debe enviar email")

    monkeypatch.setattr(crm, "enviar_mensaje_email", fail_if_called)

    response = client.get(f"/crm/prospeccion?lead_id={administrador_id}")
    assert response.status_code == 200
    assert 'id="crm-open-email-preview"' in response.text
    assert 'id="crm-email-preview-modal"' in response.text
    assert "Gmail escritorio" in response.text
    assert "Gmail móvil" in response.text
    assert "Servicios de informes periciales para comunidades administradas" in response.text
    assert "Buenos días, Administración Fincas Centro:" in response.text
    assert 'data-recipient-email="admin@example.test"' in response.text
    assert "Carlos Blanco &lt;contacto@carlosblancoperito.es&gt;" in response.text
    assert "Arquitecto Técnico · Perito Judicial" in response.text
    assert "623 829 228" in response.text
    assert "www.carlosblancoperito.es" in response.text
    assert "contacto@carlosblancoperito.es" in response.text
    assert "info@carlosblancoperito.es" not in response.text
    assert "Adjuntos: Sin adjuntos previstos" in response.text
    assert "Volver a editar" in response.text
    assert "✓ Revisado antes de enviar" in response.text
    assert "modal.showModal()" in response.text
    assert 'event.target === modal' in response.text
    assert 'data-preview-tab="mobile"' in response.text
    assert 'form="crm-email-send-form"' in response.text
    assert 'formaction="/crm/prospeccion/leads/' in response.text
    assert "subjectInput.value.trim()" in response.text
    assert "bodyInput.value.trim()" in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (administrador_id,)).fetchone()
        emails_count = cur.execute(
            "SELECT COUNT(*) FROM emails_enviados WHERE referencia_entidad_id = ?",
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert lead["estado"] == "nuevo"
    assert emails_count == 0


def test_crm_prospeccion_muestra_sin_accion_comercial(isolated_import):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lead_contactos (
                lead_id, fecha, tipo, resumen, resultado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                administrador_id,
                "2026-06-01T10:00",
                "llamada",
                "Contacto previo",
                "Contactado",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.get("/crm/prospeccion?sin_accion=1")
    assert response.status_code == 200
    assert "Administración Sin Email" in response.text
    assert "Administración Fincas Centro" not in response.text


def test_enviar_presentacion_cambia_estado_registra_email_y_crea_seguimiento(
    isolated_import,
    monkeypatch,
):
    main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    crm.email_sender.SMTP_FROM_NAME = "Carlos Blanco"
    crm.email_sender.SMTP_FROM_EMAIL = "contacto@carlosblancoperito.es"
    enviados = []

    def fake_enviar_mensaje_email(mensaje, contexto="email"):
        body_text = mensaje.get_body(preferencelist=("plain",)).get_content()
        body_html = mensaje.get_body(preferencelist=("html",)).get_content()
        enviados.append((mensaje["To"], mensaje["Subject"], contexto, body_text, body_html, mensaje["From"]))

    monkeypatch.setattr(crm, "enviar_mensaje_email", fake_enviar_mensaje_email)

    response = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-presentacion",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert len(enviados) == 1
    assert enviados[0][:3] == (
        "admin@example.test",
        "Servicios de informes periciales para comunidades administradas",
        f"presentacion lead {administrador_id} plantilla presentacion_administrador_fincas",
    )
    assert "Buenos días, Administración Fincas Centro:" in enviados[0][3]
    assert "Arquitecto Técnico · Perito Judicial" in enviados[0][3]
    assert enviados[0][3].count("contacto@carlosblancoperito.es") == 1
    assert enviados[0][4].count("contacto@carlosblancoperito.es") == 1
    assert "info@carlosblancoperito.es" not in enviados[0][3]
    assert "info@carlosblancoperito.es" not in enviados[0][4]
    assert "contacto@carlosblancoperito.es" in enviados[0][5]

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (administrador_id,)).fetchone()
        emails = cur.execute(
            """
            SELECT *
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead' AND referencia_entidad_id = ?
            """,
            (administrador_id,),
        ).fetchall()
        tareas = cur.execute(
            """
            SELECT *
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'
            """,
            (administrador_id,),
        ).fetchall()
        contactos = cur.execute(
            "SELECT * FROM lead_contactos WHERE lead_id = ? AND tipo = 'email'",
            (administrador_id,),
        ).fetchall()
    finally:
        conn.close()

    assert main_module.app is not None
    assert lead["estado"] == "pendiente_respuesta"
    assert len(emails) == 1
    assert emails[0]["estado"] == "enviado"
    assert emails[0]["tipo"] == "presentacion_comercial"
    assert emails[0]["asunto"] == "Servicios de informes periciales para comunidades administradas"
    assert "Buenos días, Administración Fincas Centro:" in emails[0]["cuerpo_texto"]
    assert "Me presento, soy Carlos Blanco" in emails[0]["cuerpo_texto"]
    assert len(tareas) == 1
    assert tareas[0]["estado"] == "pendiente"
    assert tareas[0]["fecha_programada"] >= "2026-01-01"
    assert len(contactos) == 1


def test_enviar_email_editado_guarda_texto_final_y_crea_seguimiento(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    enviados = []

    def fake_enviar_mensaje_email(mensaje, contexto="email"):
        body_text = mensaje.get_body(preferencelist=("plain",)).get_content()
        enviados.append((mensaje["To"], mensaje["Subject"], contexto, body_text))

    monkeypatch.setattr(crm, "enviar_mensaje_email", fake_enviar_mensaje_email)

    response = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-editado",
        data={
            "plantilla_slug": "presentacion_administrador_fincas",
            "asunto": "Asunto revisado para Laura",
            "cuerpo": "Texto final editado para este lead.",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert len(enviados) == 1
    assert enviados[0][1] == "Asunto revisado para Laura"
    assert "Texto final editado para este lead." in enviados[0][3]

    conn = get_connection()
    try:
        cur = conn.cursor()
        email = cur.execute(
            """
            SELECT *
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead'
              AND referencia_entidad_id = ?
              AND tipo = 'presentacion_comercial'
            """,
            (administrador_id,),
        ).fetchone()
        tareas_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'
            """,
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert email["asunto"] == "Asunto revisado para Laura"
    assert email["cuerpo_texto"] == "Texto final editado para este lead."
    assert tareas_count == 1


def test_programar_email_no_envia_y_queda_registrado_como_programado(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Programar no debe llamar al envio real")

    monkeypatch.setattr(crm, "enviar_mensaje_email", fail_if_called)

    response = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/programar-email",
        data={
            "plantilla_slug": "presentacion_administrador_fincas",
            "asunto": "Asunto programado",
            "cuerpo": "Cuerpo programado y revisado.",
            "fecha_programada": "2026-06-20T09:30",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        email = cur.execute(
            """
            SELECT *
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead'
              AND referencia_entidad_id = ?
              AND tipo = 'presentacion_programada'
            """,
            (administrador_id,),
        ).fetchone()
        contactos = cur.execute(
            "SELECT * FROM lead_contactos WHERE lead_id = ? AND resultado = 'Programado'",
            (administrador_id,),
        ).fetchall()
    finally:
        conn.close()

    assert email["estado"] == "programado"
    assert email["asunto"] == "Asunto programado"
    assert email["cuerpo_texto"] == "Cuerpo programado y revisado."
    assert "programado_para=2026-06-20T09:30" in email["error_mensaje"]
    assert len(contactos) == 1


def test_agenda_carga_lista_y_permite_seleccionar_email_programado(isolated_import):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Agenda asunto final",
            cuerpo="Agenda cuerpo final.",
        )
        conn.commit()
    finally:
        conn.close()

    response = client.get("/crm/prospeccion/agenda")
    assert response.status_code == 200
    assert "Agenda de emails programados" in response.text
    assert "Agenda asunto final" in response.text
    assert "Administración Fincas Centro" in response.text
    assert "2026-06-20T09:30" in response.text

    selected = client.get(f"/crm/prospeccion/agenda?email_id={email_id}")
    assert selected.status_code == 200
    assert "Cuerpo final editable" in selected.text
    assert "Agenda cuerpo final." in selected.text
    assert "Confirmar envío" in selected.text


def test_agenda_confirmar_presentacion_envia_texto_editado_y_crea_seguimiento_sin_duplicar(
    isolated_import,
    monkeypatch,
):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_programado(cur, user_id, administrador_id)
        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                administrador_id,
                "Seguimiento presentación comercial",
                "seguimiento_presentacion",
                "2026-06-30",
                "pendiente",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    enviados = []

    def fake_enviar_mensaje_email(mensaje, contexto="email"):
        body_text = mensaje.get_body(preferencelist=("plain",)).get_content()
        enviados.append((mensaje["To"], mensaje["Subject"], contexto, body_text))

    monkeypatch.setattr(crm, "enviar_mensaje_email", fake_enviar_mensaje_email)

    response = client.post(
        f"/crm/prospeccion/agenda/{email_id}/confirmar",
        data={
            "asunto": "Asunto confirmado editado",
            "cuerpo": "Cuerpo confirmado y revisado.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert len(enviados) == 1
    assert enviados[0][1] == "Asunto confirmado editado"
    assert "Cuerpo confirmado y revisado." in enviados[0][3]

    conn = get_connection()
    try:
        cur = conn.cursor()
        email = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (email_id,)).fetchone()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (administrador_id,)).fetchone()
        tareas_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'
            """,
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert email["estado"] == "enviado"
    assert email["tipo"] == "presentacion_comercial"
    assert email["asunto"] == "Asunto confirmado editado"
    assert email["cuerpo_texto"] == "Cuerpo confirmado y revisado."
    assert email["error_mensaje"] is None
    assert lead["estado"] == "pendiente_respuesta"
    assert tareas_count == 1


def test_agenda_confirmar_seguimiento_resuelve_tarea_y_crea_revision_sin_duplicar(
    isolated_import,
    monkeypatch,
):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            tipo="seguimiento_programado",
            asunto="Seguimiento programado",
            cuerpo="Seguimiento cuerpo.",
            plantilla="seguimiento_administrador_fincas_10d",
        )
        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                administrador_id,
                "Seguimiento presentación comercial",
                "seguimiento_presentacion",
                "2026-06-20",
                "pendiente",
                user_id,
            ),
        )
        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                administrador_id,
                "Revisión tras seguimiento comercial",
                "revision_post_seguimiento",
                "2026-07-20",
                "pendiente",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(crm, "enviar_mensaje_email", lambda mensaje, contexto="email": None)

    response = client.post(
        f"/crm/prospeccion/agenda/{email_id}/confirmar",
        data={
            "asunto": "Seguimiento confirmado",
            "cuerpo": "Seguimiento final editado.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        email = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (email_id,)).fetchone()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (administrador_id,)).fetchone()
        seguimiento = cur.execute(
            "SELECT * FROM lead_tareas WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'",
            (administrador_id,),
        ).fetchone()
        revisiones_count = cur.execute(
            "SELECT COUNT(*) FROM lead_tareas WHERE lead_id = ? AND tipo = 'revision_post_seguimiento'",
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert email["estado"] == "enviado"
    assert email["tipo"] == "seguimiento_comercial"
    assert email["asunto"] == "Seguimiento confirmado"
    assert email["cuerpo_texto"] == "Seguimiento final editado."
    assert lead["estado"] == "seguimiento_enviado"
    assert seguimiento["estado"] == "hecha"
    assert revisiones_count == 1


def test_agenda_cancelar_y_reprogramar_email_programado(isolated_import):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_reprogramar_id = _crear_email_programado(cur, user_id, administrador_id)
        email_cancelar_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Cancelar este programado",
            fecha_programada="2026-06-21T10:00",
        )
        conn.commit()
    finally:
        conn.close()

    reprogramar = client.post(
        f"/crm/prospeccion/agenda/{email_reprogramar_id}/reprogramar",
        data={"fecha_programada": "2026-06-25T12:45"},
        follow_redirects=False,
    )
    cancelar = client.post(
        f"/crm/prospeccion/agenda/{email_cancelar_id}/cancelar",
        follow_redirects=False,
    )

    assert reprogramar.status_code == 303
    assert cancelar.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        reprogramado = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (email_reprogramar_id,)).fetchone()
        cancelado = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (email_cancelar_id,)).fetchone()
    finally:
        conn.close()

    assert reprogramado["estado"] == "programado"
    assert "programado_para=2026-06-25T12:45" in reprogramado["error_mensaje"]
    assert cancelado["estado"] == "cancelado"
    assert "cancelado_en=" in cancelado["error_mensaje"]


def test_workbench_muestra_accion_seguimiento_tras_presentacion(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.routers import crm

    monkeypatch.setattr(crm, "enviar_mensaje_email", lambda mensaje, contexto="email": None)

    inicial = client.get("/crm/prospeccion")
    assert "Enviar seguimiento" not in inicial.text

    response = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-presentacion",
        follow_redirects=False,
    )
    assert response.status_code == 303

    workbench = client.get("/crm/prospeccion")
    assert workbench.status_code == 200
    assert "Enviar seguimiento" in workbench.text
    assert "Seguimiento Administradores de fincas 10 días" in workbench.text


def test_enviar_seguimiento_registra_email_resuelve_tarea_y_crea_revision(
    isolated_import,
    monkeypatch,
):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    enviados = []

    def fake_enviar_mensaje_email(mensaje, contexto="email"):
        body_text = mensaje.get_body(preferencelist=("plain",)).get_content()
        enviados.append((mensaje["To"], mensaje["Subject"], contexto, body_text))

    monkeypatch.setattr(crm, "enviar_mensaje_email", fake_enviar_mensaje_email)

    presentacion = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-presentacion",
        follow_redirects=False,
    )
    assert presentacion.status_code == 303

    seguimiento = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-seguimiento",
        follow_redirects=False,
    )
    assert seguimiento.status_code == 303
    assert len(enviados) == 2
    assert enviados[1][:3] == (
        "admin@example.test",
        "Seguimiento de presentación y disponibilidad técnica",
        f"seguimiento lead {administrador_id} plantilla seguimiento_administrador_fincas_10d",
    )
    assert "Hace unos días os remití" in enviados[1][3]
    assert "623 829 228" in enviados[1][3]
    assert "contacto@carlosblancoperito.es" in enviados[1][3]

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (administrador_id,)).fetchone()
        email_seguimiento = cur.execute(
            """
            SELECT *
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead'
              AND referencia_entidad_id = ?
              AND tipo = 'seguimiento_comercial'
            """,
            (administrador_id,),
        ).fetchone()
        tarea_seguimiento = cur.execute(
            """
            SELECT *
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'
            """,
            (administrador_id,),
        ).fetchone()
        revisiones = cur.execute(
            """
            SELECT *
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'revision_post_seguimiento'
            """,
            (administrador_id,),
        ).fetchall()
    finally:
        conn.close()

    assert lead["estado"] == "seguimiento_enviado"
    assert email_seguimiento["asunto"] == "Seguimiento de presentación y disponibilidad técnica"
    assert "Hace unos días os remití" in email_seguimiento["cuerpo_texto"]
    assert tarea_seguimiento["estado"] == "hecha"
    assert tarea_seguimiento["completed_at"]
    assert len(revisiones) == 1
    assert revisiones[0]["estado"] == "pendiente"

    segundo = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/enviar-seguimiento",
        follow_redirects=False,
    )
    assert segundo.status_code == 303
    conn = get_connection()
    try:
        cur = conn.cursor()
        revisiones_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'revision_post_seguimiento'
            """,
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert revisiones_count == 1


def test_enviar_presentacion_no_duplica_tarea_de_seguimiento(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    monkeypatch.setattr(crm, "enviar_mensaje_email", lambda mensaje, contexto="email": None)

    for _ in range(2):
        response = client.post(
            f"/crm/prospeccion/leads/{administrador_id}/enviar-presentacion",
            follow_redirects=False,
        )
        assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        tareas_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM lead_tareas
            WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'
            """,
            (administrador_id,),
        ).fetchone()[0]
        emails_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead' AND referencia_entidad_id = ?
            """,
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert tareas_count == 1
    assert emails_count == 2


def test_enviar_presentacion_sin_email_no_envia_ni_modifica(isolated_import, monkeypatch):
    _main_module, client, _user_id, _administrador_id, _abogado_id, sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    def fail_if_called(*args, **kwargs):
        raise AssertionError("No se debe intentar enviar si el lead no tiene email")

    monkeypatch.setattr(crm, "enviar_mensaje_email", fail_if_called)

    response = client.post(
        f"/crm/prospeccion/leads/{sin_email_id}/enviar-presentacion",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (sin_email_id,)).fetchone()
        emails_count = cur.execute(
            "SELECT COUNT(*) FROM emails_enviados WHERE referencia_entidad_id = ?",
            (sin_email_id,),
        ).fetchone()[0]
        tareas_count = cur.execute(
            "SELECT COUNT(*) FROM lead_tareas WHERE lead_id = ?",
            (sin_email_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert lead["estado"] == "nuevo"
    assert emails_count == 0
    assert tareas_count == 0


def test_enviar_seguimiento_sin_email_no_envia_ni_modifica(isolated_import, monkeypatch):
    _main_module, client, user_id, _administrador_id, _abogado_id, sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lead_tareas (
                lead_id, titulo, tipo, fecha_programada, estado, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sin_email_id,
                "Seguimiento presentación comercial",
                "seguimiento_presentacion",
                "2026-06-20",
                "pendiente",
                user_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("No se debe intentar enviar seguimiento si el lead no tiene email")

    monkeypatch.setattr(crm, "enviar_mensaje_email", fail_if_called)

    response = client.post(
        f"/crm/prospeccion/leads/{sin_email_id}/enviar-seguimiento",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        lead = cur.execute("SELECT * FROM leads WHERE id = ?", (sin_email_id,)).fetchone()
        emails_count = cur.execute(
            "SELECT COUNT(*) FROM emails_enviados WHERE referencia_entidad_id = ?",
            (sin_email_id,),
        ).fetchone()[0]
        tarea = cur.execute(
            "SELECT * FROM lead_tareas WHERE lead_id = ? AND tipo = 'seguimiento_presentacion'",
            (sin_email_id,),
        ).fetchone()
    finally:
        conn.close()

    assert lead["estado"] == "nuevo"
    assert emails_count == 0
    assert tarea["estado"] == "pendiente"


def test_dashboard_y_listado_leads_siguen_cargando(isolated_import):
    _main_module, client, _user_id, _administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )

    dashboard = client.get("/dashboard")
    leads = client.get("/leads")

    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text
    assert leads.status_code == 200
    assert "Leads" in leads.text
