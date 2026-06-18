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

    assert asunto == "Apoyo técnico para administradores de fincas"
    assert "Buenos días, María:" in cuerpo
    assert "Adjunto una breve presentación" in cuerpo
    assert "IEE.CV" in cuerpo
    assert "pueden responder directamente a este correo" in cuerpo
    assert "600 111 222" not in cuerpo
    assert "contacto@example.test" not in cuerpo
    assert "Arquitecto Técnico · Perito Judicial" not in cuerpo
    assert "{nombre_destinatario}" not in cuerpo


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

    assert asunto == "Disponibilidad para incidencias técnicas e IEE.CV"
    assert "Hace unos días tuve la oportunidad" in cuerpo
    assert "Muchas gracias por su tiempo" in cuerpo
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
    estado: str = "programado",
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
            estado,
            f"programado_para={fecha_programada}; plantilla={plantilla}",
            "lead",
            lead_id,
            user_id,
        ),
    )
    return cur.lastrowid


def _crear_email_enviado_crm(
    cur,
    user_id: int,
    lead_id: int,
    destinatario: str = "admin@example.test",
    tipo: str = "presentacion_comercial",
    asunto: str = "Asunto enviado final",
    cuerpo: str = "Cuerpo final guardado CRM.",
    estado: str = "enviado",
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
            estado,
            f"plantilla={plantilla}",
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
    assert "Apoyo técnico para administradores de fincas" in response.text
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
    assert "Apoyo técnico para administradores de fincas" in seleccionado.text
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
    assert "Disponibilidad para incidencias técnicas e IEE.CV" in response.text
    assert "Hace unos días tuve la oportunidad" in response.text
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
    assert "Apoyo técnico para administradores de fincas" in response.text
    assert "Buenos días, Administración Fincas Centro:" in response.text
    assert 'data-recipient-email="admin@example.test"' in response.text
    assert "Carlos Blanco &lt;contacto@carlosblancoperito.es&gt;" in response.text
    assert "Arquitecto Técnico · Perito Judicial" in response.text
    assert "623 829 228" in response.text
    assert "www.carlosblancoperito.es" in response.text
    assert "contacto@carlosblancoperito.es" in response.text
    assert "info@carlosblancoperito.es" not in response.text
    assert 'data-attachment-name="carlos-blanco-presentacion-administradores.png"' in response.text
    assert "📎 carlos-blanco-presentacion-administradores.png" in response.text
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
    mensajes = []

    def fake_enviar_mensaje_email(mensaje, contexto="email"):
        mensajes.append(mensaje)
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
        "Apoyo técnico para administradores de fincas",
        f"presentacion lead {administrador_id} plantilla presentacion_administrador_fincas",
    )
    assert "Buenos días, Administración Fincas Centro:" in enviados[0][3]
    assert "Arquitecto Técnico · Perito Judicial" in enviados[0][3]
    assert enviados[0][3].count("contacto@carlosblancoperito.es") == 1
    assert enviados[0][4].count("contacto@carlosblancoperito.es") == 1
    assert "cid:carlos-blanco-presentacion-administradores@sistema-pericial" in enviados[0][4]
    assert "info@carlosblancoperito.es" not in enviados[0][3]
    assert "info@carlosblancoperito.es" not in enviados[0][4]
    assert "contacto@carlosblancoperito.es" in enviados[0][5]
    filenames = [part.get_filename() for part in mensajes[0].walk()]
    content_ids = [part.get("Content-ID") for part in mensajes[0].walk()]
    assert filenames.count("carlos-blanco-presentacion-administradores.png") >= 1
    assert "<carlos-blanco-presentacion-administradores@sistema-pericial>" in content_ids

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
    assert emails[0]["asunto"] == "Apoyo técnico para administradores de fincas"
    assert emails[0]["nombre_adjunto"] == "carlos-blanco-presentacion-administradores.png"
    assert emails[0]["tiene_adjunto"] == 1
    assert "Buenos días, Administración Fincas Centro:" in emails[0]["cuerpo_texto"]
    assert "Mi nombre es Carlos Blanco" in emails[0]["cuerpo_texto"]
    assert len(emails[0]["cuerpo_texto"]) > 1000
    assert emails[0]["cuerpo_texto"].endswith("estaré encantado de valorar el caso.")
    assert lead["fecha_primer_contacto"]
    assert lead["apertura_email"] == "no_registrada"
    assert lead["respuesta_email"] == "pendiente"
    assert len(tareas) == 1
    assert tareas[0]["estado"] == "pendiente"
    assert tareas[0]["fecha_programada"] >= "2026-01-01"
    assert len(contactos) == 1

    panel = client.get(f"/crm/prospeccion?lead_id={administrador_id}")
    assert panel.status_code == 200
    assert f"/crm/prospeccion/enviados?email_id={emails[0]['id']}" in panel.text
    assert "Ver email" in panel.text


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


def test_programar_email_sin_fecha_muestra_aviso_controlado_y_no_crea_registro(isolated_import, monkeypatch):
    _main_module, client, _user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.routers import crm

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Programar sin fecha no debe llamar al envio real")

    monkeypatch.setattr(crm, "enviar_mensaje_email", fail_if_called)

    response = client.post(
        f"/crm/prospeccion/leads/{administrador_id}/programar-email",
        data={
            "plantilla_slug": "presentacion_administrador_fincas",
            "asunto": "Asunto sin fecha",
            "cuerpo": "Cuerpo revisado sin fecha.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Asunto, cuerpo y fecha son obligatorios para programar." in response.text
    assert "Field required" not in response.text
    assert '"detail"' not in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        programados_count = cur.execute(
            """
            SELECT COUNT(*)
            FROM emails_enviados
            WHERE referencia_entidad_tipo = 'lead'
              AND referencia_entidad_id = ?
              AND estado = 'programado'
            """,
            (administrador_id,),
        ).fetchone()[0]
    finally:
        conn.close()

    assert programados_count == 0


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


def test_servicio_programados_dry_run_lista_vencidos_sin_enviar(isolated_import, monkeypatch):
    _main_module, _client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.services import crm_scheduled

    conn = get_connection()
    try:
        cur = conn.cursor()
        vencido_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Vencido dry-run",
            fecha_programada="2026-06-17T08:00",
        )
        futuro_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Futuro dry-run",
            fecha_programada="2026-06-18T08:00",
        )
        cancelado_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Cancelado dry-run",
            fecha_programada="2026-06-17T08:30",
            estado="cancelado",
        )
        enviado_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Enviado dry-run",
            fecha_programada="2026-06-17T08:45",
            estado="enviado",
        )
        conn.commit()
    finally:
        conn.close()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Dry-run no debe enviar emails")

    monkeypatch.setattr(crm_scheduled, "enviar_mensaje_email", fail_if_called)

    resultado = crm_scheduled.enviar_emails_programados_vencidos(
        dry_run=True,
        limit=10,
        ahora="2026-06-17T12:00",
    )
    assert [email["id"] for email in resultado["candidatos"]] == [vencido_id]
    assert resultado["enviados"] == []
    assert resultado["errores"] == []

    conn = get_connection()
    try:
        cur = conn.cursor()
        estados = {
            row["id"]: row["estado"]
            for row in cur.execute(
                "SELECT id, estado FROM emails_enviados WHERE id IN (?, ?, ?, ?)",
                (vencido_id, futuro_id, cancelado_id, enviado_id),
            ).fetchall()
        }
    finally:
        conn.close()

    assert estados[vencido_id] == "programado"
    assert estados[futuro_id] == "programado"
    assert estados[cancelado_id] == "cancelado"
    assert estados[enviado_id] == "enviado"


def test_servicio_programados_envia_vencido_y_crea_seguimiento_sin_duplicar(isolated_import, monkeypatch):
    _main_module, _client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.services import crm_scheduled

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Presentación vencida",
            cuerpo="Cuerpo final programado.",
            fecha_programada="2026-06-17T09:00",
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
        enviados.append((mensaje["To"], mensaje["Subject"], contexto))

    monkeypatch.setattr(crm_scheduled, "enviar_mensaje_email", fake_enviar_mensaje_email)

    resultado = crm_scheduled.enviar_emails_programados_vencidos(
        dry_run=False,
        limit=10,
        ahora="2026-06-17T12:00",
    )
    assert resultado["errores"] == []
    assert [email["id"] for email in resultado["enviados"]] == [email_id]
    assert enviados == [
        (
            "admin@example.test",
            "Presentación vencida",
            f"scheduled presentacion_comercial email_programado {email_id}",
        )
    ]

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
    assert email["asunto"] == "Presentación vencida"
    assert email["cuerpo_texto"] == "Cuerpo final programado."
    assert email["nombre_adjunto"] == "carlos-blanco-presentacion-administradores.png"
    assert email["tiene_adjunto"] == 1
    assert email["error_mensaje"] is None
    assert lead["estado"] == "pendiente_respuesta"
    assert tareas_count == 1


def test_servicio_programados_respeta_limite_y_registra_error(isolated_import, monkeypatch):
    _main_module, _client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.services import crm_scheduled

    conn = get_connection()
    try:
        cur = conn.cursor()
        primero_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="Falla primero",
            fecha_programada="2026-06-17T08:00",
        )
        segundo_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            asunto="No debe procesarse por limite",
            fecha_programada="2026-06-17T08:01",
        )
        conn.commit()
    finally:
        conn.close()

    def fake_error(*args, **kwargs):
        raise RuntimeError("smtp_test_failure")

    monkeypatch.setattr(crm_scheduled, "enviar_mensaje_email", fake_error)

    resultado = crm_scheduled.enviar_emails_programados_vencidos(
        dry_run=False,
        limit=1,
        ahora="2026-06-17T12:00",
    )
    assert [email["id"] for email in resultado["candidatos"]] == [primero_id]
    assert resultado["enviados"] == []
    assert resultado["errores"] == [{"id": primero_id, "error": "smtp_test_failure"}]

    conn = get_connection()
    try:
        cur = conn.cursor()
        primero = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (primero_id,)).fetchone()
        segundo = cur.execute("SELECT * FROM emails_enviados WHERE id = ?", (segundo_id,)).fetchone()
    finally:
        conn.close()

    assert primero["estado"] == "error"
    assert "smtp_test_failure" in primero["error_mensaje"]
    assert segundo["estado"] == "programado"


def test_servicio_programados_seguimiento_resuelve_y_crea_revision_sin_duplicar(isolated_import, monkeypatch):
    _main_module, _client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection
    from app.services import crm_scheduled

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_programado(
            cur,
            user_id,
            administrador_id,
            tipo="seguimiento_programado",
            asunto="Seguimiento vencido",
            cuerpo="Seguimiento final programado.",
            fecha_programada="2026-06-17T09:00",
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
                "2026-06-17",
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

    monkeypatch.setattr(crm_scheduled, "enviar_mensaje_email", lambda mensaje, contexto="email": None)

    resultado = crm_scheduled.enviar_emails_programados_vencidos(
        dry_run=False,
        limit=10,
        ahora="2026-06-17T12:00",
    )
    assert resultado["errores"] == []
    assert [email["id"] for email in resultado["enviados"]] == [email_id]

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
    assert lead["estado"] == "seguimiento_enviado"
    assert seguimiento["estado"] == "hecha"
    assert seguimiento["completed_at"]
    assert revisiones_count == 1


def test_prospeccion_enviados_lista_y_muestra_detalle_readonly(isolated_import):
    _main_module, client, user_id, administrador_id, _abogado_id, _sin_email_id = _preparar_cliente_con_leads(
        isolated_import
    )
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        email_id = _crear_email_enviado_crm(
            cur,
            user_id,
            administrador_id,
            destinatario="admin@example.test",
            asunto="Asunto enviado editado",
            cuerpo="Cuerpo final guardado CRM sin firma manual.",
        )
        conn.commit()
    finally:
        conn.close()

    listado = client.get("/crm/prospeccion/enviados")
    detalle = client.get(f"/crm/prospeccion/enviados?email_id={email_id}")

    assert listado.status_code == 200
    assert "Emails enviados CRM" in listado.text
    assert "admin@example.test" in listado.text
    assert "Administración Fincas Centro" in listado.text
    assert "Asunto enviado editado" in listado.text

    assert detalle.status_code == 200
    assert "Contenido comercial guardado" in detalle.text
    assert "Vista final con firma corporativa" in detalle.text
    assert "admin@example.test" in detalle.text
    assert "Asunto enviado editado" in detalle.text
    assert "Cuerpo final guardado CRM sin firma manual." in detalle.text
    assert "Carlos Blanco" in detalle.text
    assert "Arquitecto Técnico · Perito Judicial" in detalle.text
    assert "contacto@carlosblancoperito.es" in detalle.text
    assert "info@carlosblancoperito.es" not in detalle.text
    assert "<textarea" not in detalle.text
    assert 'method="post"' not in detalle.text


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
        "Disponibilidad para incidencias técnicas e IEE.CV",
        f"seguimiento lead {administrador_id} plantilla seguimiento_administrador_fincas_10d",
    )
    assert "Hace unos días tuve la oportunidad" in enviados[1][3]
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
    assert lead["fecha_primer_contacto"]
    assert lead["fecha_segundo_contacto"]
    assert email_seguimiento["asunto"] == "Disponibilidad para incidencias técnicas e IEE.CV"
    assert "Hace unos días tuve la oportunidad" in email_seguimiento["cuerpo_texto"]
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
