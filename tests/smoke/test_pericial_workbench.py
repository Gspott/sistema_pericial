from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient


def _crear_usuario(cur, username: str = "pericial_workbench") -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Pericial", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente_patologias(cur, user_id: int) -> int:
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario, cliente,
            direccion, ciudad, provincia, tipo_inmueble,
            descripcion_dano, causa_probable, pruebas_indicios,
            evolucion_preexistencia, propuesta_reparacion, urgencia_gravedad,
            owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "EXP-PER-WB-1",
            "patologias",
            "particular",
            "Cliente Workbench Pericial",
            "Calle Pericial 1",
            "Madrid",
            "Madrid",
            "Vivienda",
            "Daños por agua en falsos techos y paramentos.",
            "Entrada de agua durante reparación de cubierta.",
            "Manchas, moho y escorrentías visibles.",
            "Es necesario revisar la madera por posible afección oculta.",
            "Sustitución de falso techo y revisar elementos ocultos.",
            "Se desaconseja el uso hasta eliminar moho.",
            user_id,
        ),
    )
    expediente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO visitas (
            expediente_id, fecha, tecnico, observaciones_visita, ambito_visita
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            "2026-06-06",
            "Tecnico Pericial",
            "Visita con elementos ocultos y sin realizar catas.",
            "edificio_completo",
        ),
    )
    visita_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO climatologia_visitas (visita_id, resumen)
        VALUES (?, ?)
        """,
        (visita_id, "Semana con lluvia registrada."),
    )
    cur.execute(
        """
        INSERT INTO estancias (
            visita_id, nombre, tipo_estancia, planta,
            ventilacion, acabado_pavimento, acabado_paramento,
            acabado_techo, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "Dormitorio",
            "Dormitorio",
            "1",
            "Natural",
            "Tarima",
            "Pintura",
            "Yeso",
            "No se puede comprobar el estado de la estructura sin catas.",
        ),
    )
    estancia_id = cur.lastrowid
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
            "revestimiento_interior",
            "Deterioro por humedad",
            "Se recomienda revisar soporte antes de cerrar el falso techo.",
            "",
            "techo",
            "Zona junto a fachada",
            "efecto",
        ),
    )
    patologia_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO registro_patologia_fotos (registro_id, archivo)
        VALUES (?, ?)
        """,
        (patologia_id, "demo/pericial.jpg"),
    )
    cur.execute(
        """
        INSERT INTO costes_bases (
            nombre, descripcion, origen, version
        )
        VALUES (?, ?, ?, ?)
        """,
        ("Base pericial", "Base demo.", "manual", "wb-1"),
    )
    base_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_conceptos (
            base_id, codigo, tipo, unidad, resumen, descripcion,
            precio, moneda, estado, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            base_id,
            "PER.001",
            "partida",
            "m2",
            "Falso techo de yeso",
            "Reposición de falso techo afectado.",
            36.57,
            "EUR",
            "validado",
        ),
    )
    concepto_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO actuaciones_reparacion (
            expediente_id, titulo, descripcion, observaciones, orden, updated_at
        )
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            expediente_id,
            "Reposición de falso techo",
            "Actuación económica por estancia afectada.",
            "Medición agrupada.",
            1,
        ),
    )
    actuacion_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO actuacion_partidas (
            actuacion_id, concepto_id, descripcion_snapshot,
            unidad_snapshot, precio_unitario_snapshot, cantidad, importe,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            actuacion_id,
            concepto_id,
            "Falso techo snapshot",
            "m2",
            36.57,
            10,
            365.7,
        ),
    )
    return expediente_id


def test_pericial_workbench_renderiza_diagnostico_y_datos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/pericial-workbench")

    assert response.status_code == 200
    assert "Workbench pericial" in response.text
    assert "Diagnóstico" in response.text
    assert "Borrador de informe" in response.text
    assert "Texto generado autom" in response.text
    assert "Requiere revisi" in response.text
    assert "El expediente EXP-PER-WB-1 documenta Daños por agua" in response.text
    assert "Entrada de agua durante reparación de cubierta" in response.text
    assert "Constan 1 visita" in response.text
    assert "elementos ocultos" in response.text
    assert "Las recomendaciones candidatas" in response.text
    assert "Inventario resumido de daños" in response.text
    assert "Metodología básica" in response.text
    assert "Semana con lluvia registrada." in response.text
    assert "Limitaciones candidatas" in response.text
    assert "No se puede comprobar" in response.text
    assert "Recomendaciones candidatas" in response.text
    assert "ANEXO A. Documentación aportada" in response.text
    assert "No hay documentos PDF aportados gestionados para el Anexo A." in response.text
    assert "Reposición de falso techo" in response.text
    assert "365,70" in response.text
    assert "/informe-v2-editor" in response.text
    assert "Editar informe" in response.text


def test_workbench_gestiona_documentos_anexo_a_y_respeta_ownership(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_docs_a")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        otro_user_id = _crear_usuario(cur, "pericial_docs_a_otro")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    upload_response = client.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos",
        data={
            "nombre_visible": "Presupuesto de reparación de cubierta",
            "descripcion": "Presupuesto aportado por la propiedad.",
            "tipo_documento": "Presupuesto",
            "orden": "20",
        },
        files={
            "archivo": (
                "presupuesto-interno-019-26.pdf",
                b"%PDF-1.4\n% documento de prueba\n",
                "application/pdf",
            )
        },
        follow_redirects=False,
    )

    assert upload_response.status_code == 303
    conn = get_connection()
    try:
        cur = conn.cursor()
        documento = cur.execute(
            """
            SELECT *
            FROM expediente_documentos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()
        assert documento is not None
        assert documento["nombre_visible"] == "Presupuesto de reparación de cubierta"
        assert documento["tipo_documento"] == "Presupuesto"
        assert documento["orden"] == 20
        assert documento["archivo_nombre_original"] == "presupuesto-interno-019-26.pdf"
        assert documento["archivo_ruta"].startswith(
            f"expediente_documentos/{expediente_id}/"
        )
        assert documento["archivo_ruta"].endswith(".pdf")
        documento_id = documento["id"]
        ruta_documento = documento["archivo_ruta"]
        archivo_documento = main_module.resolver_ruta_upload_relativa_segura(ruta_documento)
        assert archivo_documento is not None
        assert archivo_documento.exists()
    finally:
        conn.close()

    listado = client.get(f"/expedientes/{expediente_id}/pericial-workbench")
    assert listado.status_code == 200
    assert "Presupuesto de reparación de cubierta" in listado.text
    assert "Presupuesto aportado por la propiedad." in listado.text
    assert "Eliminar" in listado.text
    assert "¿Seguro que quieres eliminar este documento del Anexo A?" in listado.text
    assert (
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}/eliminar"
        in listado.text
    )
    assert "presupuesto-interno-019-26.pdf" not in listado.text
    assert "expediente_documentos/" not in listado.text

    update_response = client.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}",
        data={
            "nombre_visible": "Presupuesto pericial revisado",
            "descripcion": "Documento base para Anexo A.",
            "tipo_documento": "Informe técnico",
            "orden": "5",
        },
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        actualizado = cur.execute(
            "SELECT * FROM expediente_documentos WHERE id = ?",
            (documento_id,),
        ).fetchone()
        assert actualizado["nombre_visible"] == "Presupuesto pericial revisado"
        assert actualizado["descripcion"] == "Documento base para Anexo A."
        assert actualizado["tipo_documento"] == "Informe técnico"
        assert actualizado["orden"] == 5
    finally:
        conn.close()

    otro_cliente = _autenticar_cliente(main_module, otro_user_id)
    forbidden = otro_cliente.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}",
        data={
            "nombre_visible": "Intento ajeno",
            "descripcion": "",
            "tipo_documento": "Otro",
            "orden": "1",
        },
    )
    assert forbidden.status_code == 404

    forbidden_delete = otro_cliente.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}/eliminar",
        follow_redirects=False,
    )
    assert forbidden_delete.status_code == 404
    assert archivo_documento is not None
    assert archivo_documento.exists()

    delete_response = client.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_id}/eliminar",
        follow_redirects=False,
    )
    assert delete_response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        eliminado = cur.execute(
            "SELECT * FROM expediente_documentos WHERE id = ?",
            (documento_id,),
        ).fetchone()
        assert eliminado is None
    finally:
        conn.close()
    assert not archivo_documento.exists()

    listado_sin_documento = client.get(f"/expedientes/{expediente_id}/pericial-workbench")
    assert listado_sin_documento.status_code == 200
    assert "Presupuesto pericial revisado" not in listado_sin_documento.text
    assert "No hay documentos PDF aportados gestionados para el Anexo A." in listado_sin_documento.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'application/pdf', ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "Documento sin archivo físico",
                "Debe poder eliminarse aunque el PDF ya no exista.",
                "Otro",
                f"expediente_documentos/{expediente_id}/no-existe.pdf",
                "no-existe.pdf",
                30,
            ),
        )
        documento_sin_archivo_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    missing_delete = client.post(
        f"/expedientes/{expediente_id}/pericial-workbench/documentos/{documento_sin_archivo_id}/eliminar",
        follow_redirects=False,
    )
    assert missing_delete.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        eliminado = cur.execute(
            "SELECT * FROM expediente_documentos WHERE id = ?",
            (documento_sin_archivo_id,),
        ).fetchone()
        assert eliminado is None
    finally:
        conn.close()


def test_detalle_expediente_muestra_workbench_solo_en_patologias(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_workbench_link")
        expediente_patologias_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario, cliente,
                direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PER-WB-VAL",
                "valoracion",
                "particular",
                "Cliente Valoracion",
                "Calle Valoracion 1",
                "Vivienda",
                user_id,
            ),
        )
        expediente_valoracion_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    patologias_response = client.get(f"/detalle-expediente/{expediente_patologias_id}")
    valoracion_response = client.get(f"/detalle-expediente/{expediente_valoracion_id}")

    assert patologias_response.status_code == 200
    assert "/pericial-workbench" in patologias_response.text
    assert "Workbench pericial" in patologias_response.text
    assert valoracion_response.status_code == 200
    assert "/pericial-workbench" not in valoracion_response.text


def test_informe_v2_editor_precarga_guarda_y_no_sobrescribe(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Informe pericial" in response.text
    assert "Resumen ejecutivo" in response.text
    assert "contenido_resumen_ejecutivo" in response.text
    assert response.text.count('data-chapter-help-toggle="') == len(
        main_module.INFORME_V2_CAPITULOS
    )
    assert response.text.count('data-review-state="') == len(
        main_module.INFORME_V2_CAPITULOS
    )
    assert "Estado de capítulos" in response.text
    assert "Terminados:" in response.text
    assert "Bloqueados:" in response.text
    assert "Estado: En revisión" not in response.text
    assert "Guía editorial. No se imprime en el PDF." in response.text
    assert "Función:</strong> Ofrecer una visión sintética del informe." in response.text
    assert "Relación:</strong> Resume el contenido del resto del informe." in response.text
    assert "Diagnóstico del informe" in response.text
    assert "Control determinista de completitud. No se imprime en el PDF." in response.text
    assert "Completitud:" in response.text
    assert "Advertencias editoriales:" in response.text
    assert "Advertencias editoriales (" in response.text
    assert "Capítulos obligatorios" in response.text
    assert "Anexos derivados" in response.text
    assert "Anexo B · Reportaje fotográfico" in response.text
    assert "Fotografías detectadas: <strong>1</strong>" in response.text
    assert "Patologías con fotografías: <strong>1</strong>" in response.text
    assert "✓ Disponible" in response.text
    assert "El reportaje fotográfico se generará automáticamente agrupado por patología. No es necesario describir individualmente cada fotografía." in response.text
    assert "Anexo C · Fichas de daños" in response.text
    assert "Estancias con daños: <strong>1</strong>" in response.text
    assert "Patologías interiores: <strong>1</strong>" in response.text
    assert "Las fichas de daños se generarán automáticamente agrupadas por estancia. No es necesario reproducir aquí el inventario completo de daños estancia por estancia." in response.text
    assert "PDF de mediciones para Anexo F" in response.text
    assert "Adjunta aquí la hoja de cálculo de mediciones exportada a PDF. Se incorporará al informe final después del Anexo F." in response.text
    assert f"/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf" in response.text
    assert "Contexto del expediente" in response.text
    assert "Información de apoyo. No se imprime en el PDF." in response.text
    assert "Zona blanca/editor: contenido del informe." in response.text
    assert "Estructura: nivel → unidad → estancia" in response.text
    assert "Dormitorio" in response.text
    assert "Natural" in response.text
    assert "Deterioro por humedad" in response.text
    assert "demo/pericial.jpg" in response.text
    assert "Observaciones técnicas relevantes" in response.text
    assert "Actuaciones y costes" in response.text
    assert f"/informes-v2/{expediente_id}/autosave" in response.text
    assert 'data-autosave-campo="resumen_ejecutivo"' in response.text
    assert 'data-autosave-titulo="Resumen ejecutivo"' in response.text
    assert 'data-autosave-updated-at="resumen_ejecutivo"' in response.text
    assert 'data-chapter-status="resumen_ejecutivo"' in response.text
    assert 'data-local-recovery="resumen_ejecutivo"' in response.text
    assert "Historial" in response.text
    assert f"/informes-v2/{expediente_id}/respaldo.json" in response.text
    assert "window.localStorage.setItem" in response.text
    assert "window.localStorage.removeItem" in response.text
    assert 'body.append("updated_at", getKnownUpdatedAt(campo));' in response.text
    assert "function parseUtcTimestamp(timestamp)" in response.text
    assert 'return new Date(raw.replace(/\\s+/, "T") + "Z");' in response.text
    assert 'toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })' in response.text
    assert 'class="autosave-status ready"' in response.text
    assert ">Listo para editar</strong>" in response.text
    assert ">Guardado</strong>" not in response.text
    assert 'setStatus("Guardado " + titulo' in response.text
    assert "Error al guardar. Usa Guardar datos o revisa la conexión." in response.text
    assert "Hay cambios pendientes de guardar." in response.text
    assert "autosave-status" in response.text
    assert "ANEXO E. Análisis de ejecución de la partida nº 4" in response.text
    assert "contenido_anexo_e_partida_4" in response.text
    assert "ANEXO F. Justificación de mediciones" in response.text
    assert "contenido_anexo_f_mediciones" in response.text
    assert 'data-autosave-campo="conclusiones_periciales"' in response.text
    assert "contenido_conclusiones_periciales" in response.text
    assert "contenido_conclusiones_tecnicas" not in response.text
    assert "Conclusiones técnicas</h2>" not in response.text
    assert "Conclusiones periciales</h2>" not in response.text
    assert "[Completar conclusión técnica sobre la partida analizada.]" in response.text
    assert "[Completar desglose de mediciones por estancia, zona o actuación.]" in response.text
    assert "El expediente EXP-PER-WB-1 documenta Daños por agua" in response.text
    assert "Precargado desde pericial-wb-2" in response.text

    form_data = {
        f"contenido_{capitulo['clave']}": f"Contenido manual {capitulo['clave']}"
        for capitulo in main_module.INFORME_V2_CAPITULOS
    }
    form_data["contenido_resumen_ejecutivo"] = "Resumen manual definitivo"
    form_data["contenido_anexo_e_partida_4"] = "Anexo E manual definitivo"
    form_data["contenido_anexo_f_mediciones"] = "Anexo F manual definitivo"
    post_response = client.post(
        f"/expedientes/{expediente_id}/informe-v2-editor",
        data=form_data,
        follow_redirects=False,
    )

    assert post_response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        filas = cur.execute(
            """
            SELECT clave, contenido, editado_manual, generado_desde
            FROM informe_v2_capitulos
            WHERE expediente_id = ?
            ORDER BY orden ASC
            """,
            (expediente_id,),
        ).fetchall()
    finally:
        conn.close()

    assert len(filas) == len(main_module.INFORME_V2_CAPITULOS)
    resumen = {fila["clave"]: fila for fila in filas}["resumen_ejecutivo"]
    assert resumen["contenido"] == "Resumen manual definitivo"
    assert resumen["editado_manual"] == 1
    assert resumen["generado_desde"] == "pericial-wb-2"
    anexo_e = {fila["clave"]: fila for fila in filas}["anexo_e_partida_4"]
    assert anexo_e["contenido"] == "Anexo E manual definitivo"
    assert anexo_e["editado_manual"] == 1
    anexo_f = {fila["clave"]: fila for fila in filas}["anexo_f_mediciones"]
    assert anexo_f["contenido"] == "Anexo F manual definitivo"
    assert anexo_f["editado_manual"] == 1

    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Resumen manual definitivo" in response.text
    assert "Anexo E manual definitivo" in response.text
    assert "Anexo F manual definitivo" in response.text
    assert "Editado manualmente" in response.text
    assert "El expediente EXP-PER-WB-1 documenta Daños por agua" not in response.text


def test_informe_v2_anexos_derivados_sin_fotos_ni_danos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor_sin_anexos")
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario, cliente,
                direccion, ciudad, provincia, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-SIN-ANEXOS",
                "patologias",
                "particular",
                "Cliente sin anexos",
                "Calle sin anexos 1",
                "Madrid",
                "Madrid",
                "Vivienda",
                user_id,
            ),
        )
        expediente_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Anexos derivados" in response.text
    assert "Fotografías detectadas: <strong>0</strong>" in response.text
    assert "Patologías con fotografías: <strong>0</strong>" in response.text
    assert "Estancias con daños: <strong>0</strong>" in response.text
    assert "Patologías interiores: <strong>0</strong>" in response.text
    assert response.text.count("No disponible") >= 2


def test_informe_v2_pdf_mediciones_anexo_f_subir_reemplazar_eliminar(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor_pdf_mediciones")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    editor_inicial = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert editor_inicial.status_code == 200
    assert "PDF de mediciones para Anexo F" in editor_inicial.text
    assert "Subir PDF" in editor_inicial.text
    assert "Adjunta aquí la hoja de cálculo de mediciones exportada a PDF." in editor_inicial.text

    invalido = client.post(
        f"/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf",
        files={
            "archivo": (
                "mediciones.txt",
                b"no es pdf",
                "text/plain",
            )
        },
        follow_redirects=False,
    )
    assert invalido.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM expediente_documentos
            WHERE expediente_id = ? AND tipo_documento = ?
            """,
            (expediente_id, main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
        ).fetchone()["total"]
    finally:
        conn.close()
    assert total == 0

    subida = client.post(
        f"/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf",
        files={
            "archivo": (
                "mediciones-anexo-f.pdf",
                b"%PDF-1.4\n% mediciones primera version\n",
                "application/pdf",
            )
        },
        follow_redirects=False,
    )
    assert subida.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        documento = cur.execute(
            """
            SELECT *
            FROM expediente_documentos
            WHERE expediente_id = ? AND tipo_documento = ?
            """,
            (expediente_id, main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
        ).fetchone()
        assert documento is not None
        assert documento["nombre_visible"] == "PDF de mediciones para Anexo F"
        assert documento["archivo_nombre_original"] == "mediciones-anexo-f.pdf"
        primera_ruta = documento["archivo_ruta"]
        primera_path = main_module.resolver_ruta_upload_relativa_segura(primera_ruta)
        assert primera_path is not None
        assert primera_path.exists()
    finally:
        conn.close()

    editor_con_pdf = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    assert editor_con_pdf.status_code == 200
    assert "mediciones-anexo-f.pdf" in editor_con_pdf.text
    assert "Ver/descargar" in editor_con_pdf.text
    assert "Reemplazar PDF" in editor_con_pdf.text
    assert "Eliminar" in editor_con_pdf.text

    reemplazo = client.post(
        f"/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf",
        files={
            "archivo": (
                "mediciones-revisadas.pdf",
                b"%PDF-1.4\n% mediciones revisadas\n",
                "application/pdf",
            )
        },
        follow_redirects=False,
    )
    assert reemplazo.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        documentos = cur.execute(
            """
            SELECT *
            FROM expediente_documentos
            WHERE expediente_id = ? AND tipo_documento = ?
            """,
            (expediente_id, main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
        ).fetchall()
        assert len(documentos) == 1
        assert documentos[0]["archivo_nombre_original"] == "mediciones-revisadas.pdf"
        segunda_path = main_module.resolver_ruta_upload_relativa_segura(
            documentos[0]["archivo_ruta"]
        )
        assert segunda_path is not None
        assert segunda_path.exists()
    finally:
        conn.close()
    assert primera_path is not None
    assert not primera_path.exists()

    eliminacion = client.post(
        f"/expedientes/{expediente_id}/informe-v2/anexo-f-mediciones-pdf/eliminar",
        follow_redirects=False,
    )
    assert eliminacion.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM expediente_documentos
            WHERE expediente_id = ? AND tipo_documento = ?
            """,
            (expediente_id, main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES),
        ).fetchone()["total"]
    finally:
        conn.close()
    assert total == 0
    assert segunda_path is not None
    assert not segunda_path.exists()


def _capitulos_informe_v2_para_advertencias(main_module, contenidos):
    return [
        {
            **capitulo,
            "contenido": contenidos.get(capitulo["clave"], ""),
        }
        for capitulo in main_module.INFORME_V2_CAPITULOS
    ]


def test_informe_v2_advertencias_editoriales_detectan_redundancias(isolated_import):
    main_module = isolated_import("app.main")

    capitulos = _capitulos_informe_v2_para_advertencias(
        main_module,
        {
            "resumen_ejecutivo": "foto fotografía imagen figura foto",
            "inventario_resumido_danos": "estancia dormitorio cocina baño salón habitación",
            "conclusiones_periciales": "antecedentes cronología visita",
            "antecedentes_objeto": "se concluye por tanto responsabilidad",
            "valoracion_economica": "origen del daño causa mecanismo lesional",
        },
    )
    anexos = {
        "anexo_b": {"disponible": True},
        "anexo_c": {"disponible": True},
    }

    advertencias = main_module.evaluar_advertencias_editoriales_informe_v2(
        capitulos,
        anexos,
    )
    reglas = {item["regla"] for item in advertencias}

    assert {"A", "B", "C", "D", "E"} <= reglas
    assert any(
        item["clave"] == "resumen_ejecutivo" and "Anexo B" in item["explicacion"]
        for item in advertencias
    )
    assert any(
        item["clave"] == "inventario_resumido_danos"
        and "Anexo C" in item["explicacion"]
        for item in advertencias
    )
    assert any(
        item["clave"] == "conclusiones_periciales"
        and "cronología" in item["explicacion"]
        for item in advertencias
    )
    assert any(
        item["clave"] == "antecedentes_objeto"
        and "conclusiones periciales" in item["explicacion"]
        for item in advertencias
    )
    assert any(
        item["clave"] == "valoracion_economica"
        and "análisis causal" in item["explicacion"]
        for item in advertencias
    )


def test_informe_v2_advertencias_editoriales_expediente_limpio(isolated_import):
    main_module = isolated_import("app.main")

    capitulos = _capitulos_informe_v2_para_advertencias(
        main_module,
        {
            "resumen_ejecutivo": "Síntesis pericial breve sin repeticiones.",
            "antecedentes_objeto": "Se describe el encargo y el alcance solicitado.",
            "conclusiones_periciales": "Dictamen final centrado en causa, reparación y alcance económico.",
        },
    )
    anexos = {
        "anexo_b": {"disponible": False},
        "anexo_c": {"disponible": False},
    }

    advertencias = main_module.evaluar_advertencias_editoriales_informe_v2(
        capitulos,
        anexos,
    )

    assert advertencias == []


def test_informe_v2_advertencias_editoriales_renderizan_panel_y_badge(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor_advertencias")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "foto fotografía imagen figura foto",
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Advertencias editoriales:" in response.text
    assert "Advertencias editoriales (" in response.text
    assert "⚠ Posible redundancia detectada" in response.text
    assert "El capítulo contiene numerosas referencias a fotografías." in response.text
    assert "No se imprime en el PDF." in response.text


def test_informe_v2_diagnostico_detecta_errores_y_advertencias(isolated_import):
    main_module = isolated_import("app.main")

    capitulos = [
        {
            **capitulo,
            "contenido": (
                "x" * 320
                if capitulo["clave"]
                in {
                    "resumen_ejecutivo",
                    "metodologia",
                    "analisis_causal",
                    "inventario_resumido_danos",
                    "actuaciones_verificadas",
                    "propuesta_reparacion",
                }
                else ""
            ),
        }
        for capitulo in main_module.INFORME_V2_CAPITULOS
    ]
    workbench = {
        "metricas": {
            "visitas": 1,
            "patologias_interiores": 2,
            "patologias_exteriores": 0,
            "fotografias": 12,
        },
        "actuaciones": {"actuaciones": [{"partidas": [{"importe": 100}]}]},
    }

    diagnostico = main_module.evaluar_diagnostico_informe_v2(capitulos, workbench)

    assert diagnostico["estado"]["clave"] == "incompleto"
    assert diagnostico["porcentaje"] == 75
    assert any(item["clave"] == "valoracion_economica" for item in diagnostico["errores"])
    assert any(item["clave"] == "conclusiones_periciales" for item in diagnostico["errores"])
    assert any(
        item["clave"] == "recomendaciones_tecnicas"
        for item in diagnostico["advertencias"]
    )
    assert any(
        item["clave"] == "inventario_resumido_danos"
        for item in diagnostico["advertencias"]
    )


def test_informe_v2_estado_revision_guarda_y_persiste_sin_tocar_contenido(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_estado_revision")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        columnas = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(informe_v2_capitulos)").fetchall()
        }
        assert "estado_revision" in columnas
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen existente.",
                "pericial-editor-1",
            ),
        )
        fila = cur.execute(
            """
            SELECT estado_revision
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = ?
            """,
            (expediente_id, "resumen_ejecutivo"),
        ).fetchone()
        assert fila["estado_revision"] == "Pendiente"
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/informes-v2/{expediente_id}/capitulos/inventario_resumido_danos/estado",
        data={"estado_revision": "En revisión"},
    )
    assert response.status_code == 200
    assert response.json()["estado_revision"] == "En revisión"

    conn = get_connection()
    try:
        cur = conn.cursor()
        estado = cur.execute(
            """
            SELECT contenido, editado_manual, estado_revision, updated_at
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = ?
            """,
            (expediente_id, "inventario_resumido_danos"),
        ).fetchone()
        assert estado["contenido"] is None
        assert estado["editado_manual"] == 0
        assert estado["estado_revision"] == "En revisión"
        assert estado["updated_at"] is None
    finally:
        conn.close()

    editor_response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    assert editor_response.status_code == 200
    assert 'data-review-state="inventario_resumido_danos"' in editor_response.text
    assert '<option value="En revisión" selected>En revisión</option>' in editor_response.text
    assert "No hay inventario resumido de daños disponible." not in editor_response.text


def test_informe_v2_guardado_manual_detecta_conflicto_updated_at(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor_conflict")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen autosalvado reciente",
                "pericial-editor-1",
                "2026-06-10 12:00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    form_data = {
        f"contenido_{capitulo['clave']}": f"Contenido manual {capitulo['clave']}"
        for capitulo in main_module.INFORME_V2_CAPITULOS
    }
    form_data.update(
        {
            f"updated_at_{capitulo['clave']}": ""
            for capitulo in main_module.INFORME_V2_CAPITULOS
        }
    )
    form_data["contenido_resumen_ejecutivo"] = "Resumen manual desactualizado"
    form_data["updated_at_resumen_ejecutivo"] = "2026-06-10 11:59:00"

    response = client.post(
        f"/expedientes/{expediente_id}/informe-v2-editor",
        data=form_data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "Hay+cambios+m%C3%A1s+recientes" in response.headers["location"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["contenido"] == "Resumen autosalvado reciente"


def test_informe_v2_guardado_manual_permite_updated_at_vigente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_editor_no_conflict")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen vigente",
                "pericial-editor-1",
                "2026-06-10 12:00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    form_data = {
        f"contenido_{capitulo['clave']}": f"Contenido manual {capitulo['clave']}"
        for capitulo in main_module.INFORME_V2_CAPITULOS
    }
    form_data.update(
        {
            f"updated_at_{capitulo['clave']}": ""
            for capitulo in main_module.INFORME_V2_CAPITULOS
        }
    )
    form_data["contenido_resumen_ejecutivo"] = "Resumen manual sin conflicto"
    form_data["updated_at_resumen_ejecutivo"] = "2026-06-10 12:00:00"

    response = client.post(
        f"/expedientes/{expediente_id}/informe-v2-editor",
        data=form_data,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "mensaje=Informe%20guardado" in response.headers["location"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["contenido"] == "Resumen manual sin conflicto"


def test_informe_v2_autosave_valida_campo_y_no_pisa_otros_capitulos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_autosave")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "metodologia",
                "Metodología",
                3,
                "Metodología manual previa",
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    rechazo = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={"campo": "campo_no_permitido", "valor": "No debe guardarse"},
    )
    assert rechazo.status_code == 400
    assert rechazo.json()["ok"] is False

    response = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={
            "campo": "resumen_ejecutivo",
            "valor": "Resumen autosalvado por campo",
            "timestamp": "2026-06-10T12:00:00",
        },
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["campo"] == "resumen_ejecutivo"
    assert ":" in response.json()["updated_at"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        filas = cur.execute(
            """
            SELECT clave, contenido, editado_manual
            FROM informe_v2_capitulos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchall()
    finally:
        conn.close()

    por_clave = {fila["clave"]: fila for fila in filas}
    assert por_clave["resumen_ejecutivo"]["contenido"] == "Resumen autosalvado por campo"
    assert por_clave["resumen_ejecutivo"]["editado_manual"] == 1
    assert por_clave["metodologia"]["contenido"] == "Metodología manual previa"

    editor = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    assert editor.status_code == 200
    assert "Resumen autosalvado por campo" in editor.text
    assert "Metodología manual previa" in editor.text


def test_informe_v2_autosave_con_updated_at_vigente_guarda(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_autosave_vigente")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen vigente antes",
                "pericial-editor-1",
                "2026-06-10 12:00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={
            "campo": "resumen_ejecutivo",
            "valor": "Resumen autosalvado vigente",
            "updated_at": "2026-06-10 12:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["updated_at"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["contenido"] == "Resumen autosalvado vigente"


def test_informe_v2_autosave_con_updated_at_obsoleto_no_sobrescribe(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_autosave_conflict")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen reciente de otra pestaña",
                "pericial-editor-1",
                "2026-06-10 12:05:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={
            "campo": "resumen_ejecutivo",
            "valor": "Resumen obsoleto que no debe pisar",
            "updated_at": "2026-06-10 12:00:00",
        },
    )

    assert response.status_code == 409
    assert response.json()["ok"] is False
    assert response.json()["code"] == "conflict"

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["contenido"] == "Resumen reciente de otra pestaña"


def test_informe_v2_autosave_vacio_no_pisa_contenido_existente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_autosave_empty")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen que no debe vaciarse",
                "pericial-editor-1",
                "2026-06-10 12:00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={
            "campo": "resumen_ejecutivo",
            "valor": "   ",
            "updated_at": "2026-06-10 12:00:00",
        },
    )

    assert response.status_code == 422
    assert response.json()["ok"] is False
    assert response.json()["code"] == "empty_autosave"

    conn = get_connection()
    try:
        cur = conn.cursor()
        row = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["contenido"] == "Resumen que no debe vaciarse"


def test_informe_v2_crea_snapshot_al_modificar_capitulo(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_snapshot")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Contenido inicial",
            origen_version="manual",
        )
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Contenido modificado",
            origen_version="autosave",
        )
        conn.commit()
        version = cur.execute(
            """
            SELECT contenido, origen
            FROM informe_v2_capitulo_versiones
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert version["contenido"] == "Contenido inicial"
    assert version["origen"] == "autosave"


def test_informe_v2_no_crea_snapshot_si_contenido_no_cambia(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_snapshot_same")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Mismo contenido",
            origen_version="manual",
        )
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Mismo contenido",
            origen_version="autosave",
        )
        conn.commit()
        total = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM informe_v2_capitulo_versiones
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()["total"]
    finally:
        conn.close()

    assert total == 0


def test_informe_v2_retiene_maximo_50_versiones_por_capitulo(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_snapshot_retention")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Contenido 0",
            origen_version="manual",
        )
        for indice in range(1, 56):
            main_module.guardar_capitulo_informe_v2(
                cur,
                expediente_id,
                "resumen_ejecutivo",
                f"Contenido {indice}",
                origen_version="autosave",
            )
        conn.commit()
        total = cur.execute(
            """
            SELECT COUNT(*) AS total
            FROM informe_v2_capitulo_versiones
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()["total"]
    finally:
        conn.close()

    assert total == 50


def test_informe_v2_restauracion_guarda_snapshot_y_reemplaza_contenido(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_restore")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Contenido actual",
            origen_version="manual",
        )
        cur.execute(
            """
            INSERT INTO informe_v2_capitulo_versiones (
                expediente_id, clave, contenido, updated_at_original, origen
            )
            VALUES (?, 'resumen_ejecutivo', 'Contenido anterior restaurable', ?, 'manual')
            """,
            (expediente_id, "2026-06-10 12:00:00"),
        )
        version_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/informes-v2/{expediente_id}/capitulos/resumen_ejecutivo/restaurar/{version_id}",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "Versi%C3%B3n+restaurada" in response.headers["location"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        actual = cur.execute(
            """
            SELECT contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            """,
            (expediente_id,),
        ).fetchone()
        snapshot = cur.execute(
            """
            SELECT contenido, origen
            FROM informe_v2_capitulo_versiones
            WHERE expediente_id = ? AND clave = 'resumen_ejecutivo'
            ORDER BY id DESC
            LIMIT 1
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()

    assert actual["contenido"] == "Contenido anterior restaurable"
    assert snapshot["contenido"] == "Contenido actual"
    assert snapshot["origen"] == "restauracion"


def test_informe_v2_exporta_respaldo_json(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_backup_json")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        main_module.guardar_capitulo_informe_v2(
            cur,
            expediente_id,
            "resumen_ejecutivo",
            "Contenido para respaldo",
            origen_version="manual",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/informes-v2/{expediente_id}/respaldo.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["expediente"]["id"] == expediente_id
    assert data["fecha_exportacion"]
    por_clave = {capitulo["clave"]: capitulo for capitulo in data["capitulos"]}
    assert por_clave["resumen_ejecutivo"]["contenido"] == "Contenido para respaldo"


def test_pdf_v2_usa_capitulos_guardados_y_convive_con_informe_clasico(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Resumen redactado por el técnico",
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        return b"%PDF-1.4\n%PDF test\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)

    workbench_response = client.get(f"/expedientes/{expediente_id}/pericial-workbench")
    editor_response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    classic_response = client.get(f"/informes/{expediente_id}/imprimir")
    pdf_response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert workbench_response.status_code == 200
    assert "Generar PDF" in workbench_response.text
    assert editor_response.status_code == 200
    assert "Generar PDF" in editor_response.text
    assert classic_response.status_code == 200
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "Informe-EXP-PER-WB-1.pdf" in pdf_response.headers["content-disposition"]

    contexto = capturado["contexto"]
    resumen = [
        capitulo
        for capitulo in contexto["capitulos"]
        if capitulo["clave"] == "resumen_ejecutivo"
    ][0]
    assert resumen["contenido"] == "Resumen redactado por el técnico"
    assert contexto["capitulos_guardados"] == 1
    assert contexto["indice"][0]["titulo"] == "Portada"
    assert contexto["indice"][-1]["titulo"] == "Justificación de mediciones"
    assert contexto["conclusiones"]["titulo"] == "Conclusiones"
    assert all(
        capitulo["clave"] not in {
            "conclusiones_tecnicas",
            "conclusiones_periciales",
            "anexo_e_partida_4",
            "anexo_f_mediciones",
        }
        for capitulo in contexto["capitulos"]
    )


def test_pdf_v2_expediente_sin_capitulos_no_regenera_borradores(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_empty")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        return b"%PDF-1.4\n%PDF empty test\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert response.status_code == 200
    contexto = capturado["contexto"]
    assert contexto["capitulos_guardados"] == 0
    assert len(contexto["capitulos_editor"]) == len(main_module.INFORME_V2_CAPITULOS)
    assert len(contexto["capitulos"]) == len(main_module.INFORME_V2_CAPITULOS) - 3
    assert all(capitulo["contenido"] == "" for capitulo in contexto["capitulos_editor"])
    assert contexto["anexos"]["analisis_partida_4"]["contenido_pdf"].startswith("E.1 Objeto")
    assert contexto["anexos"]["analisis_partida_4"]["guardado"] is False
    assert contexto["anexos"]["justificacion_mediciones"]["contenido_pdf"].startswith("F.1 Criterios de medición")
    assert contexto["anexos"]["justificacion_mediciones"]["guardado"] is False
    assert contexto["pdf_mediciones_anexo_f"] is None


def test_pdf_v2_anexa_pdf_mediciones_tras_anexo_f(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_mediciones")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'application/pdf', ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "PDF de mediciones para Anexo F",
                "Desarrollo completo de mediciones incorporado al informe.",
                main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES,
                f"expediente_documentos/{expediente_id}/mediciones.pdf",
                "mediciones-completas.pdf",
                900,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF con separador F4\n"

    def fake_fusion(pdf_informe, documentos_anexo_a, pdf_mediciones):
        capturado["fusion_pdf_informe"] = pdf_informe
        capturado["fusion_documentos_anexo_a"] = documentos_anexo_a
        capturado["fusion_pdf_mediciones"] = pdf_mediciones
        return pdf_informe + b"%PDF_MEDICIONES_ANEXO_F\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    monkeypatch.setattr(main_module, "fusionar_pdf_informe_v2_con_anexos_integrados", fake_fusion)
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert response.status_code == 200
    assert response.content.endswith(b"%PDF_MEDICIONES_ANEXO_F\n")
    contexto = capturado["contexto"]
    html = capturado["html"]
    assert contexto["pdf_mediciones_anexo_f"]["archivo_nombre_original"] == "mediciones-completas.pdf"
    assert capturado["fusion_documentos_anexo_a"] == []
    assert capturado["fusion_pdf_mediciones"]["archivo_nombre_original"] == "mediciones-completas.pdf"
    assert "F.4 Desarrollo completo de mediciones" in html
    assert "Se incorpora a continuación la hoja de cálculo de mediciones elaborada por el perito." in html
    assert "Documento incorporado: Desarrollo completo de mediciones." in html
    assert "mediciones-completas.pdf" not in html


def test_pdf_v2_footer_no_muestra_total_paginas(isolated_import):
    isolated_import("app.main")

    fuente = Path("app/services/informe.py").read_text()
    bloque_v2 = fuente.split("def generar_informe_v2_pdf_bytes", 1)[1].split(
        "def normalizar_texto_indice_pdf_v2",
        1,
    )[0]

    assert "Informe Pericial · Expediente" in bloque_v2
    assert "totalPages" not in bloque_v2
    assert "Página <span class='pageNumber'></span>" not in bloque_v2


def test_pdf_v2_anexo_a_respeta_inclusion_y_excluye_adjuntos_internos(isolated_import):
    main_module = isolated_import("app.main")

    documentos = main_module.recopilar_documentacion_anexo_v2(
        {},
        {},
        [
            {
                "orden": 10,
                "nombre_visible": "Documento incluido",
                "tipo_documento": "Presupuesto",
                "archivo_nombre_original": "incluido.pdf",
                "archivo_ruta": "expediente_documentos/1/incluido_hash.pdf",
                "descripcion": "Documento que debe imprimirse.",
                "created_at": "2026-06-15 10:00:00",
                "incluir_en_pdf": 1,
            },
            {
                "orden": 20,
                "nombre_visible": "Documento no incluido",
                "tipo_documento": "Factura",
                "archivo_nombre_original": "no-incluido.pdf",
                "archivo_ruta": "expediente_documentos/1/no_incluido_hash.pdf",
                "descripcion": "Documento que no debe imprimirse.",
                "created_at": "2026-06-15 10:00:00",
                "incluir_en_pdf": 0,
            },
            {
                "orden": 30,
                "nombre_visible": "PDF interno de mediciones",
                "tipo_documento": main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES,
                "archivo_nombre_original": "mediciones.pdf",
                "archivo_ruta": "expediente_documentos/1/mediciones.pdf",
                "descripcion": "Pertenece al Anexo F, no al Anexo A.",
                "created_at": "2026-06-15 10:00:00",
            },
        ],
    )

    assert documentos == [
        {
            "orden": 10,
            "nombre": "Documento incluido",
            "numero_anexo": "A.2",
            "tipo": "Presupuesto",
            "fecha": "2026-06-15",
            "descripcion": "Documento que debe imprimirse.",
            "archivo_ruta": "expediente_documentos/1/incluido_hash.pdf",
            "archivo": "incluido.pdf",
            "mime_type": "",
            "es_pdf": True,
        }
    ]


def test_pdf_v2_fusiona_pdfs_aportados_anexo_a_y_omite_no_validos(isolated_import):
    main_module = isolated_import("app.main")

    from pypdf import PdfReader, PdfWriter

    informe = PdfWriter()
    informe.add_blank_page(width=595, height=842)
    informe_buffer = BytesIO()
    informe.write(informe_buffer)

    anexo_a = PdfWriter()
    anexo_a.add_blank_page(width=595, height=842)
    anexo_a.add_blank_page(width=595, height=842)
    ruta_relativa = "expediente_documentos/1/anexo-a.pdf"
    ruta_anexo = main_module.UPLOAD_PATH / ruta_relativa
    ruta_anexo.parent.mkdir(parents=True, exist_ok=True)
    with ruta_anexo.open("wb") as buffer:
        anexo_a.write(buffer)

    corrupto_relativo = "expediente_documentos/1/corrupto.pdf"
    ruta_corrupta = main_module.UPLOAD_PATH / corrupto_relativo
    ruta_corrupta.write_bytes(b"no es un pdf valido")

    fusionado = main_module.fusionar_pdf_informe_v2_con_anexo_a(
        informe_buffer.getvalue(),
        [
            {
                "nombre": "Documento no PDF",
                "archivo": "imagen.jpg",
                "archivo_ruta": "expediente_documentos/1/imagen.jpg",
                "mime_type": "image/jpeg",
            },
            {
                "nombre": "Documento Anexo A",
                "archivo": "anexo-a.pdf",
                "archivo_ruta": ruta_relativa,
                "mime_type": "application/pdf",
            },
            {
                "nombre": "Documento corrupto",
                "archivo": "corrupto.pdf",
                "archivo_ruta": corrupto_relativo,
                "mime_type": "application/pdf",
            },
            {
                "nombre": "Documento ausente",
                "archivo": "ausente.pdf",
                "archivo_ruta": "expediente_documentos/1/ausente.pdf",
                "mime_type": "application/pdf",
            },
        ],
    )

    assert len(PdfReader(BytesIO(fusionado)).pages) == 3


def test_pdf_v2_integra_anexo_a_como_portadilla_mas_documento(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from pypdf import PdfReader, PdfWriter

    def pdf_con_paginas(anchos):
        writer = PdfWriter()
        for ancho in anchos:
            writer.add_blank_page(width=ancho, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    informe = pdf_con_paginas([500])
    ruta_relativa = "expediente_documentos/1/anexo-a-integrado.pdf"
    ruta_anexo = main_module.UPLOAD_PATH / ruta_relativa
    ruta_anexo.parent.mkdir(parents=True, exist_ok=True)
    ruta_anexo.write_bytes(pdf_con_paginas([520, 530]))

    corrupto_relativo = "expediente_documentos/1/anexo-a-corrupto.pdf"
    ruta_corrupta = main_module.UPLOAD_PATH / corrupto_relativo
    ruta_corrupta.write_bytes(b"no es un pdf valido")

    def fake_portadilla(documento, pdf_integrado):
        writer = PdfWriter()
        writer.add_blank_page(width=510 if pdf_integrado else 515, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        return [pagina for pagina in PdfReader(BytesIO(buffer.getvalue())).pages]

    monkeypatch.setattr(
        main_module,
        "generar_paginas_portadilla_anexo_a_v2",
        fake_portadilla,
    )

    fusionado = main_module.fusionar_pdf_informe_v2_con_anexos_integrados(
        informe,
        [
            {
                "nombre": "Documento integrado",
                "numero_anexo": "A.2",
                "archivo": "anexo-a-integrado.pdf",
                "archivo_ruta": ruta_relativa,
                "mime_type": "application/pdf",
            },
            {
                "nombre": "Documento corrupto",
                "numero_anexo": "A.3",
                "archivo": "anexo-a-corrupto.pdf",
                "archivo_ruta": corrupto_relativo,
                "mime_type": "application/pdf",
            },
            {
                "nombre": "Documento ausente",
                "numero_anexo": "A.4",
                "archivo": "ausente.pdf",
                "archivo_ruta": "expediente_documentos/1/ausente.pdf",
                "mime_type": "application/pdf",
            },
        ],
        None,
    )

    anchos = [
        int(float(pagina.mediabox.width))
        for pagina in PdfReader(BytesIO(fusionado)).pages
    ]
    assert anchos == [500, 510, 520, 530, 515, 515]


def test_pdf_v2_endpoint_integra_anexo_a_y_mediciones_en_merge_unico(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_merge_anexo_a")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'application/pdf', ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "Documento Anexo A",
                "Documento externo aportado.",
                "Presupuesto",
                f"expediente_documentos/{expediente_id}/anexo-a.pdf",
                "anexo-a.pdf",
                10,
            ),
        )
        cur.execute(
            """
            INSERT INTO expediente_documentos (
                expediente_id, nombre_visible, descripcion, tipo_documento,
                archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'application/pdf', ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "PDF interno de mediciones",
                "Debe quedar fuera de Anexo A.",
                main_module.TIPO_DOCUMENTO_INFORME_V2_ANEXO_F_MEDICIONES,
                f"expediente_documentos/{expediente_id}/mediciones.pdf",
                "mediciones.pdf",
                900,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    llamadas = []

    def fake_pdf_bytes(request, contexto):
        return b"%PDF-1.4\n%PDF base\n"

    def fake_merge(pdf_informe, documentos, pdf_mediciones):
        llamadas.append(("integrado", pdf_informe, documentos, pdf_mediciones))
        assert [documento["archivo"] for documento in documentos] == ["anexo-a.pdf"]
        assert pdf_mediciones["archivo_nombre_original"] == "mediciones.pdf"
        return pdf_informe + b"ANEXOS_INTEGRADOS\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    monkeypatch.setattr(main_module, "fusionar_pdf_informe_v2_con_anexos_integrados", fake_merge)

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert response.status_code == 200
    assert response.content.endswith(b"ANEXOS_INTEGRADOS\n")
    assert [llamada[0] for llamada in llamadas] == ["integrado"]


def test_informe_v2_fusion_pdf_mediciones_agrega_paginas(isolated_import):
    main_module = isolated_import("app.main")

    from pypdf import PdfReader, PdfWriter

    informe = PdfWriter()
    informe.add_blank_page(width=595, height=842)
    informe_buffer = BytesIO()
    informe.write(informe_buffer)

    mediciones = PdfWriter()
    mediciones.add_blank_page(width=595, height=842)
    mediciones.add_blank_page(width=595, height=842)
    ruta_relativa = "expediente_documentos/1/mediciones.pdf"
    ruta_mediciones = main_module.UPLOAD_PATH / ruta_relativa
    ruta_mediciones.parent.mkdir(parents=True, exist_ok=True)
    with ruta_mediciones.open("wb") as buffer:
        mediciones.write(buffer)

    fusionado = main_module.fusionar_pdf_informe_v2_con_mediciones(
        informe_buffer.getvalue(),
        {"archivo_ruta": ruta_relativa},
    )

    assert len(PdfReader(BytesIO(fusionado)).pages) == 3


def test_pdf_v2_limpia_vocabulario_interno_sin_modificar_contenido_guardado(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    contenido_guardado = (
        "- Dormitorio 2: Deterioro de revestimientos interiores en techo "
        "(rol pendiente, 11 foto(s)).\n"
        "Contenido guardado. Última actualización. Texto generado automáticamente. "
        "Pendiente de revisión."
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_cleanup")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "inventario_resumido_danos",
                "Inventario resumido de daños",
                6,
                contenido_guardado,
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF cleanup test\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert response.status_code == 200
    html = capturado["html"]
    for texto_interno in [
        "Contenido guardado",
        "Última actualización",
        "Texto generado automáticamente",
        "Pendiente de revisión",
        "rol pendiente",
        "11 foto(s)",
        "informe_v2_capitulos",
        "PDF-V2-2",
    ]:
        assert texto_interno not in html

    assert "Dormitorio 2:" in html
    assert "Se observan deterioro de revestimientos interiores en techo" in html
    assert "documentados mediante reportaje fotográfico" in html

    capitulo = [
        item
        for item in capturado["contexto"]["capitulos"]
        if item["clave"] == "inventario_resumido_danos"
    ][0]
    assert capitulo["contenido"] == contenido_guardado
    assert capitulo["contenido_pdf"] != contenido_guardado


def test_informe_v2_conclusiones_periciales_prioridad_y_fallback_legacy(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_conclusiones_legacy")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "conclusiones_tecnicas",
                "Conclusiones técnicas",
                11,
                "Conclusión técnica histórica heredada.",
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF conclusiones fallback test\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)

    editor_response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    assert editor_response.status_code == 200
    assert "Conclusión técnica histórica heredada." in editor_response.text
    assert "contenido_conclusiones_periciales" in editor_response.text
    assert "contenido_conclusiones_tecnicas" not in editor_response.text

    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")
    assert response.status_code == 200
    html = capturado["html"]
    contexto = capturado["contexto"]
    assert html.count("13. Conclusiones") == 1
    assert "Conclusión técnica histórica heredada." in html
    assert "Conclusiones técnicas" not in html
    assert "Conclusiones periciales" not in html
    assert len(contexto["conclusiones"]["bloques"]) == 1
    assert contexto["conclusiones"]["bloques"][0]["clave"] == "conclusiones_periciales"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO informe_v2_capitulos (
                expediente_id, clave, titulo, orden, contenido,
                generado_desde, editado_manual, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "conclusiones_periciales",
                "Conclusiones",
                11,
                "Conclusión pericial prioritaria.",
                "pericial-editor-1",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")
    assert response.status_code == 200
    html = capturado["html"]
    assert html.count("13. Conclusiones") == 1
    assert "Conclusión pericial prioritaria." in html
    assert "Conclusión técnica histórica heredada." not in html


def test_pdf_v2_fusiona_conclusiones_y_renderiza_anexos_derivados(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_annexes")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        actuacion = cur.execute(
            """
            SELECT id
            FROM actuaciones_reparacion
            WHERE expediente_id = ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (expediente_id,),
        ).fetchone()
        concepto = cur.execute(
            """
            SELECT id
            FROM costes_conceptos
            ORDER BY id ASC
            LIMIT 1
            """
        ).fetchone()
        cur.execute(
            """
            INSERT INTO actuacion_partidas (
                actuacion_id, concepto_id, descripcion_snapshot,
                unidad_snapshot, precio_unitario_snapshot, cantidad, importe,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                actuacion["id"],
                concepto["id"],
                "Reparación de cubierta snapshot",
                "m2",
                46.572973,
                185,
                8616.0,
            ),
        )
        for nombre_visible, tipo_documento, descripcion, archivo_ruta, original, orden in [
            (
                "Factura de reparación de cubierta",
                "Factura",
                "Factura aportada por la propiedad.",
                "expediente_documentos/interno/factura_hash.pdf",
                "factura-original-privada.pdf",
                20,
            ),
            (
                "Presupuesto pericial de reparación",
                "Presupuesto",
                "Presupuesto base de valoración.",
                "expediente_documentos/interno/presupuesto_hash.pdf",
                "presupuesto-original-privado.pdf",
                10,
            ),
        ]:
            cur.execute(
                """
                INSERT INTO expediente_documentos (
                    expediente_id, nombre_visible, descripcion, tipo_documento,
                    archivo_ruta, archivo_nombre_original, mime_type, orden, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'application/pdf', ?, CURRENT_TIMESTAMP)
                """,
                (
                    expediente_id,
                    nombre_visible,
                    descripcion,
                    tipo_documento,
                    archivo_ruta,
                    original,
                    orden,
                ),
            )
        visita = cur.execute(
            "SELECT id FROM visitas WHERE expediente_id = ?",
            (expediente_id,),
        ).fetchone()
        estancia = cur.execute(
            """
            SELECT e.id
            FROM estancias e
            JOIN visitas v ON v.id = e.visita_id
            WHERE v.expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, 'exterior', ?, ?)
            """,
            (visita["id"], "demo/exterior.jpg", "Vista exterior de cubierta"),
        )
        cur.execute(
            """
            INSERT INTO estancia_fotos (estancia_id, archivo)
            VALUES (?, ?)
            """,
            (estancia["id"], "demo/estancia.jpg"),
        )
        registro = cur.execute(
            """
            SELECT rp.id
            FROM registros_patologias rp
            WHERE rp.estancia_id = ?
            ORDER BY rp.id ASC
            LIMIT 1
            """,
            (estancia["id"],),
        ).fetchone()
        for indice in range(2, 8):
            cur.execute(
                """
                INSERT INTO registro_patologia_fotos (registro_id, archivo)
                VALUES (?, ?)
                """,
                (registro["id"], f"demo/humedad-{indice}.jpg"),
            )
        for patologia, elemento, archivo in [
            (
                "Deterioro de revestimientos interiores por humedad",
                "revestimiento_interior",
                "demo/revestimiento.jpg",
            ),
            (
                "Aparición de moho en superficies interiores",
                "paramento_vertical",
                "demo/moho.jpg",
            ),
            (
                "Deterioro de carpinterías por humedad",
                "carpinteria",
                "demo/carpinteria.jpg",
            ),
        ]:
            cur.execute(
                """
                INSERT INTO registros_patologias (
                    visita_id, estancia_id, elemento, patologia, observaciones,
                    foto, localizacion_dano, detalle_localizacion,
                    rol_patologia_observado
                )
                VALUES (?, ?, ?, ?, ?, '', 'paramento', '', 'efecto')
                """,
                (
                    visita["id"],
                    estancia["id"],
                    elemento,
                    patologia,
                    "Observación probatoria.",
                ),
            )
            cur.execute(
                """
                INSERT INTO registro_patologia_fotos (registro_id, archivo)
                VALUES (?, ?)
                """,
                (cur.lastrowid, archivo),
            )
        for clave, titulo, orden, contenido in [
            (
                "conclusiones_tecnicas",
                "Conclusiones técnicas",
                11,
                "Conclusión técnica redactada por el técnico.",
            ),
            (
                "conclusiones_periciales",
                "Conclusiones periciales",
                12,
                "Conclusión pericial redactada por el técnico.",
            ),
            (
                "anexo_e_partida_4",
                "ANEXO E. Análisis de ejecución de la partida nº 4",
                13,
                "E.1 Objeto\n\nContenido manual guardado del Anexo E.\n\nE.6 Conclusión\n\nConclusión manual del Anexo E.",
            ),
            (
                "anexo_f_mediciones",
                "ANEXO F. Justificación de mediciones",
                14,
                "F.1 Criterios de medición\n\nContenido manual guardado del Anexo F.\n\nF.3 Observaciones\n\nObservación manual del Anexo F.",
            ),
        ]:
            cur.execute(
                """
                INSERT INTO informe_v2_capitulos (
                    expediente_id, clave, titulo, orden, contenido,
                    generado_desde, editado_manual, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """,
                (
                    expediente_id,
                    clave,
                    titulo,
                    orden,
                    contenido,
                    "pericial-editor-1",
                ),
            )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF annexes test\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}")

    assert response.status_code == 200
    contexto = capturado["contexto"]
    html = capturado["html"]

    assert "13. Conclusiones" in html
    assert "Sistema Pericial" not in html
    assert "Diagnóstico del informe" not in html
    assert "Control determinista de completitud. No se imprime en el PDF." not in html
    assert "Estado de capítulos" not in html
    assert "Terminados:" not in html
    assert "Bloqueados:" not in html
    assert "Anexos derivados" not in html
    assert "El reportaje fotográfico se generará automáticamente agrupado por patología" not in html
    assert "Las fichas de daños se generarán automáticamente agrupadas por estancia" not in html
    assert "Advertencias editoriales" not in html
    assert "Posible redundancia detectada" not in html
    assert "Guía editorial. No se imprime en el PDF." not in html
    assert "F.4 Desarrollo completo de mediciones" not in html
    assert html.count("13. Conclusiones") == 1
    assert len(contexto["conclusiones"]["bloques"]) == 1
    assert "Conclusión técnica redactada por el técnico." not in html
    assert "Conclusión pericial redactada por el técnico." in html
    assert "Conclusiones técnicas" not in html
    assert "Conclusiones periciales" not in html
    assert "14. Conclusiones periciales" not in html
    assert "ANEXO A. DOCUMENTACIÓN APORTADA" in html
    assert "A.1 Relación de documentación aportada" in html
    assert "A.2" in html
    assert "A.3" in html
    assert "Presupuesto pericial de reparación" in html
    assert "Factura de reparación de cubierta" in html
    assert "Presupuesto base de valoración." in html
    assert "El documento queda referenciado, pero el PDF aportado no se pudo incorporar físicamente." not in html
    assert "Documento aportado por la propiedad." not in html
    assert "factura-original-privada.pdf" not in html
    assert "presupuesto-original-privado.pdf" not in html
    assert "presupuesto_hash.pdf" not in html
    assert "expediente_documentos/" not in html
    assert "ANEXO B. REPORTAJE FOTOGRÁFICO DE PATOLOGÍAS" in html
    assert "B.1 FILTRACIONES Y HUMEDADES" in html
    assert "B.2 DETERIORO DE REVESTIMIENTOS Y ACABADOS" in html
    assert "B.3 MOHOS Y COLONIZACIÓN BIOLÓGICA" in html
    assert "B.4 DAÑOS EN CARPINTERÍAS Y ELEMENTOS AUXILIARES" in html
    assert "B.5 DAÑOS EXTERIORES Y FACHADA" in html
    assert "B.6 OTRAS EVIDENCIAS FOTOGRÁFICAS" in html
    assert "Figura B-1" in html
    assert "Estancia asociada:" not in html
    assert "Patología de referencia:" not in html
    assert "Se muestran 6 fotografías representativas de 7 clasificadas en este grupo." in html
    assert "ANEXO C. FICHAS DE DAÑOS POR ESTANCIA" in html
    assert "ANEXO D. VALORACIÓN ECONÓMICA DETALLADA" in html
    assert "annex-section annex-d-landscape" in html
    assert "@page anexo-d-landscape" in html
    assert "margin: 15mm 10mm 18mm;" in html
    assert "PRESUPUESTO DE EJECUCIÓN MATERIAL" in html
    assert "365,70 €" in html
    assert "8.616,00 €" in html
    assert "8.981,70 €" in html
    assert "10,00 m²" in html
    assert "185,00 m²" in html
    assert "10,0000 m2" not in html
    assert "8616.00 EUR" not in html
    assert '<td class="money amount">8.616,00 €</td>' in html
    assert "ANEXO E. ANÁLISIS DE EJECUCIÓN DE LA PARTIDA Nº 4" in html
    assert "E.1 Objeto" in html
    assert "Contenido manual guardado del Anexo E." in html
    assert "Conclusión manual del Anexo E." in html
    assert "[Completar conclusión técnica sobre la partida analizada.]" not in html
    assert "E.6 Conclusión" in html
    assert "ANEXO F. JUSTIFICACIÓN DE MEDICIONES" in html
    assert "Contenido manual guardado del Anexo F." in html
    assert "Observación manual del Anexo F." in html
    assert "[Completar desglose de mediciones por estancia, zona o actuación.]" not in html
    assert "Dormitorio" in html
    assert "Deterioro por humedad" in html
    assert "Elementos afectados" not in html
    assert "revestimiento_interior" not in html
    assert "demo/pericial.jpg" in html
    assert "demo/estancia.jpg" in html
    assert "Falso techo snapshot" in html
    assert "365.70 EUR" not in html
    assert contexto["anexos"]["valoracion"]["total_pem"] == 8981.7
    assert [
        documento["nombre"]
        for documento in contexto["anexos"]["documentacion"]
    ] == [
        "Presupuesto pericial de reparación",
        "Factura de reparación de cubierta",
    ]
    assert [
        documento["archivo"]
        for documento in contexto["anexos"]["documentacion"]
    ] == [
        "presupuesto-original-privado.pdf",
        "factura-original-privada.pdf",
    ]
    assert len(contexto["anexos"]["fotografias"]) == 12
    grupos = {
        grupo["clave"]: grupo
        for grupo in contexto["anexos"]["fotografias_grupos"]
    }
    assert grupos["filtraciones_humedades"]["total_clasificadas"] == 7
    assert len(grupos["filtraciones_humedades"]["fotos"]) == 6
    assert grupos["filtraciones_humedades"]["omitidas"] == 1
    assert grupos["revestimientos_acabados"]["total_clasificadas"] == 1
    assert grupos["mohos_colonizacion"]["total_clasificadas"] == 1
    assert grupos["carpinterias_auxiliares"]["total_clasificadas"] == 1
    assert grupos["exteriores_fachada"]["total_clasificadas"] == 1
    assert grupos["otras_evidencias"]["total_clasificadas"] == 1
    assert contexto["anexos"]["analisis_partida_4"]["partida"] is None
    assert contexto["anexos"]["analisis_partida_4"]["guardado"] is True
    assert contexto["anexos"]["analisis_partida_4"]["editado_manual"] is True
    assert contexto["anexos"]["analisis_partida_4"]["total_partidas_estructuradas"] == 2
    assert contexto["anexos"]["justificacion_mediciones"]["guardado"] is True
    assert contexto["anexos"]["justificacion_mediciones"]["editado_manual"] is True
