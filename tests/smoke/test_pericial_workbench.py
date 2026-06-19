import json
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


def _pdf_simple_bytes(total_paginas: int = 1, width: int = 595, height: int = 842) -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    for _ in range(total_paginas):
        writer.add_blank_page(width=width, height=height)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _pdf_texto_paginas(paginas: list[str]) -> bytes:
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    for texto in paginas:
        y = 780
        for linea in texto.splitlines():
            pdf.drawString(48, y, linea)
            y -= 18
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _outline_titles(outline) -> list[str]:
    titulos = []
    for item in outline:
        if isinstance(item, list):
            titulos.extend(_outline_titles(item))
            continue
        titulo = getattr(item, "title", None)
        if titulo:
            titulos.append(titulo)
    return titulos


def _outline_top_titles(outline) -> list[str]:
    return [
        item.title
        for item in outline
        if not isinstance(item, list) and getattr(item, "title", None)
    ]


def _crear_documento_pdf_expediente(
    main_module,
    cur,
    expediente_id: int,
    nombre_archivo: str = "anexo-smoke.pdf",
    total_paginas: int = 1,
    padding_bytes: int = 0,
):
    ruta_relativa = f"expediente_documentos/{expediente_id}/{nombre_archivo}"
    ruta_pdf = main_module.UPLOAD_PATH / ruta_relativa
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    ruta_pdf.write_bytes(_pdf_simple_bytes(total_paginas))
    if padding_bytes:
        with ruta_pdf.open("ab") as buffer:
            buffer.write(b"0" * padding_bytes)
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
            "Anexo documental smoke",
            "PDF externo aportado para smoke test.",
            "Documentación aportada",
            ruta_relativa,
            nombre_archivo,
            10,
        ),
    )
    return ruta_pdf


def _crear_foto_visita_para_lamina(main_module, cur, expediente_id: int, nombre: str, descripcion: str):
    from PIL import Image

    visita_id = cur.execute(
        "SELECT id FROM visitas WHERE expediente_id=? LIMIT 1",
        (expediente_id,),
    ).fetchone()["id"]
    ruta_foto = main_module.UPLOAD_PATH / nombre
    Image.new("RGB", (800, 520), (90, 120, 150)).save(ruta_foto, quality=90)
    cur.execute(
        """
        INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
        VALUES (?, 'exterior', ?, ?)
        """,
        (visita_id, nombre, descripcion),
    )
    return cur.lastrowid, ruta_foto


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
    assert "Presentación del informe" in response.text
    assert "Título principal de portada" in response.text
    assert "Subtítulo de portada" in response.text
    assert "Título que aparece en la portada del informe." in response.text
    assert "DICTAMEN TÉCNICO PERICIAL" in response.text
    assert "DAÑOS POR ENTRADA DE AGUA DE LLUVIA Y" in response.text
    assert "Análisis técnico de los daños observados" in response.text
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
    assert "Anexo A · Reportaje fotográfico" in response.text
    assert "Anexo B · Reportaje fotográfico" not in response.text
    assert "Fotografías detectadas: <strong>1</strong>" in response.text
    assert "Patologías con fotografías: <strong>1</strong>" in response.text
    assert "✓ Disponible" in response.text
    assert "El reportaje fotográfico se generará automáticamente agrupado por patología. No es necesario describir individualmente cada fotografía." in response.text
    assert "Anexo B · Fichas de daños" in response.text
    assert "Anexo C · Fichas de daños" not in response.text
    assert "Estancias con daños: <strong>1</strong>" in response.text
    assert "Patologías interiores: <strong>1</strong>" in response.text
    assert "Las fichas de daños se generarán automáticamente agrupadas por estancia. No es necesario reproducir aquí el inventario completo de daños estancia por estancia." in response.text
    assert "PDF de mediciones para Anexo E" in response.text
    assert "PDF de mediciones para Anexo F" not in response.text
    assert "Adjunta aquí la hoja de cálculo de mediciones exportada a PDF. Se incorporará al informe final dentro del Anexo E." in response.text
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
    assert "ANEXO D. Análisis de ejecución de la partida nº 4" in response.text
    assert "contenido_anexo_e_partida_4" in response.text
    assert "ANEXO E. Justificación de mediciones" in response.text
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

    autosave_presentacion = client.post(
        f"/informes-v2/{expediente_id}/autosave",
        data={
            "campo": "titulo_portada",
            "valor": "Título autosalvado de portada",
            "updated_at": "",
        },
    )
    assert autosave_presentacion.status_code == 200
    assert autosave_presentacion.json()["tipo"] == "metadatos"

    conn = get_connection()
    try:
        cur = conn.cursor()
        metadatos_autosave = cur.execute(
            """
            SELECT titulo_portada, updated_at
            FROM informe_v2_metadatos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()
    assert metadatos_autosave["titulo_portada"] == "Título autosalvado de portada"
    assert metadatos_autosave["updated_at"]

    form_data = {
        f"contenido_{capitulo['clave']}": f"Contenido manual {capitulo['clave']}"
        for capitulo in main_module.INFORME_V2_CAPITULOS
    }
    form_data["contenido_resumen_ejecutivo"] = "Resumen manual definitivo"
    form_data["contenido_anexo_e_partida_4"] = "Anexo E manual definitivo"
    form_data["contenido_anexo_f_mediciones"] = "Anexo F manual definitivo"
    form_data["titulo_portada"] = "Título personalizado de portada"
    form_data["subtitulo_portada"] = "Subtítulo personalizado de portada"
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
        metadatos = cur.execute(
            """
            SELECT titulo_portada, subtitulo_portada, updated_at
            FROM informe_v2_metadatos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()
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
    assert metadatos["titulo_portada"] == "Título personalizado de portada"
    assert metadatos["subtitulo_portada"] == "Subtítulo personalizado de portada"
    assert metadatos["updated_at"]

    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Título personalizado de portada" in response.text
    assert "Subtítulo personalizado de portada" in response.text
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
    assert "PDF de mediciones para Anexo E" in editor_inicial.text
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
        assert documento["nombre_visible"] == "PDF de mediciones para Anexo E"
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
        item["clave"] == "resumen_ejecutivo" and "Anexo A" in item["explicacion"]
        for item in advertencias
    )
    assert any(
        item["clave"] == "inventario_resumido_danos"
        and "Anexo B" in item["explicacion"]
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


def test_informe_v2_buscar_reemplazar_respeta_alcance_y_updated_at(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_find_replace")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        for clave, titulo, orden, contenido, updated_at in [
            (
                "resumen_ejecutivo",
                "Resumen ejecutivo",
                1,
                "Referencia al Anexo B y otra referencia al Anexo B.",
                "2026-06-10 12:00:00",
            ),
            (
                "metodologia",
                "Metodología",
                3,
                "Texto con Anexo B pendiente.",
                "2026-06-10 12:01:00",
            ),
        ]:
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
                    clave,
                    titulo,
                    orden,
                    contenido,
                    "pericial-editor-1",
                    updated_at,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    editor = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    assert editor.status_code == 200
    assert "Buscar y reemplazar" in editor.text
    assert "/buscar-reemplazar/contar" in editor.text
    assert "/buscar-reemplazar/reemplazar" in editor.text
    assert "find-replace-list" in editor.text
    assert "Reemplazar esta" in editor.text
    assert "Omitir" in editor.text
    assert "Ir al capítulo" in editor.text
    assert "Reemplazar todas las pendientes" in editor.text
    assert "¿Reemplazar todas las coincidencias pendientes?" in editor.text
    assert 'estado: "omitida"' in editor.text
    assert "<mark>" in editor.text
    assert "Reemplazar en capítulo actual" not in editor.text
    assert 'body.append("updated_at_" + campo, getKnownUpdatedAt(campo));' in editor.text

    conteo = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/contar",
        data={
            "buscar": "Anexo B",
            "contenido_resumen_ejecutivo": "Referencia al Anexo B y otra referencia al Anexo B.",
            "contenido_metodologia": "Texto con Anexo B pendiente.",
        },
    )
    assert conteo.status_code == 200
    assert conteo.json()["total"] == 3
    assert conteo.json()["pendientes"] == 3
    assert conteo.json()["reemplazadas"] == 0
    assert conteo.json()["omitidas"] == 0
    assert len(conteo.json()["coincidencias"]) == 3
    primera = conteo.json()["coincidencias"][0]
    assert primera["clave"] == "resumen_ejecutivo"
    assert primera["titulo"] == "Resumen ejecutivo"
    assert primera["encontrado"] == "Anexo B"
    assert primera["estado"] == "pendiente"
    assert "Referencia al " in primera["contexto_antes"]
    assert " y otra referencia" in primera["contexto_despues"]

    vacio = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/contar",
        data={"buscar": ""},
    )
    assert vacio.status_code == 400
    assert vacio.json()["code"] == "empty_search"

    reemplazo_actual = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/reemplazar",
        data={
            "buscar": "Anexo B",
            "reemplazar": "Anexo A",
            "alcance": "seleccion",
            "coincidencias": json.dumps([primera]),
            "contenido_resumen_ejecutivo": "Referencia al Anexo B y otra referencia al Anexo B.",
            "updated_at_resumen_ejecutivo": "2026-06-10 12:00:00",
        },
    )
    assert reemplazo_actual.status_code == 200
    assert reemplazo_actual.json()["total"] == 1
    assert reemplazo_actual.json()["capitulos"][0]["clave"] == "resumen_ejecutivo"
    updated_at_resumen = reemplazo_actual.json()["capitulos"][0]["updated_at"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        filas = cur.execute(
            """
            SELECT clave, contenido, updated_at
            FROM informe_v2_capitulos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchall()
    finally:
        conn.close()
    por_clave = {fila["clave"]: fila for fila in filas}
    assert por_clave["resumen_ejecutivo"]["contenido"] == (
        "Referencia al Anexo A y otra referencia al Anexo B."
    )
    assert por_clave["metodologia"]["contenido"] == "Texto con Anexo B pendiente."

    conflicto = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/reemplazar",
        data={
            "buscar": "Anexo B",
            "reemplazar": "Anexo A",
            "alcance": "seleccion",
            "coincidencias": json.dumps(
                [
                    {
                        "clave": "metodologia",
                        "indice": 10,
                        "encontrado": "Anexo B",
                    }
                ]
            ),
            "contenido_metodologia": "Texto con Anexo B pendiente.",
            "updated_at_metodologia": "2026-06-10 11:59:00",
        },
    )
    assert conflicto.status_code == 409
    assert conflicto.json()["code"] == "conflict"

    obsoleta = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/reemplazar",
        data={
            "buscar": "Anexo B",
            "reemplazar": "Anexo A",
            "alcance": "seleccion",
            "coincidencias": json.dumps([primera]),
            "contenido_resumen_ejecutivo": "Referencia al Anexo A y otra referencia al Anexo B.",
            "updated_at_resumen_ejecutivo": updated_at_resumen,
        },
    )
    assert obsoleta.status_code == 409
    assert obsoleta.json()["code"] == "stale_match"

    reemplazo_todo = client.post(
        f"/informes-v2/{expediente_id}/buscar-reemplazar/reemplazar",
        data={
            "buscar": "Anexo B",
            "reemplazar": "Anexo A",
            "alcance": "seleccion",
            "coincidencias": json.dumps(
                [
                    {
                        "clave": "resumen_ejecutivo",
                        "indice": len("Referencia al Anexo A y otra referencia al "),
                        "encontrado": "Anexo B",
                    },
                    {
                        "clave": "metodologia",
                        "indice": len("Texto con "),
                        "encontrado": "Anexo B",
                    },
                ]
            ),
            "contenido_resumen_ejecutivo": "Referencia al Anexo A y otra referencia al Anexo B.",
            "updated_at_resumen_ejecutivo": updated_at_resumen,
            "contenido_metodologia": "Texto con Anexo B pendiente.",
            "updated_at_metodologia": "2026-06-10 12:01:00",
        },
    )
    assert reemplazo_todo.status_code == 200
    assert reemplazo_todo.json()["total"] == 2

    conn = get_connection()
    try:
        cur = conn.cursor()
        filas_finales = cur.execute(
            """
            SELECT clave, contenido
            FROM informe_v2_capitulos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchall()
    finally:
        conn.close()

    final_por_clave = {fila["clave"]: fila for fila in filas_finales}
    assert final_por_clave["resumen_ejecutivo"]["contenido"] == (
        "Referencia al Anexo A y otra referencia al Anexo A."
    )
    assert final_por_clave["metodologia"]["contenido"] == "Texto con Anexo A pendiente."


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
    assert data["metadatos"]["titulo_portada"] == ""
    assert data["metadatos"]["subtitulo_portada"] == ""
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
        cur.execute(
            """
            INSERT INTO informe_v2_metadatos (
                expediente_id, titulo_portada, subtitulo_portada, updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                expediente_id,
                "Título PDF personalizado",
                "Subtítulo PDF personalizado",
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
    assert "Exportar PDF" in editor_response.text
    assert "?perfil=master" in editor_response.text
    assert "?perfil=email" in editor_response.text
    assert "?perfil=judicial" in editor_response.text
    assert "?perfil=solo_informe" in editor_response.text
    assert "?perfil=informe_anexos" in editor_response.text
    assert "?perfil=anexo_fotografico" in editor_response.text
    assert classic_response.status_code == 200
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "Informe-EXP-PER-WB-1.pdf" in pdf_response.headers["content-disposition"]

    contexto = capturado["contexto"]
    html = capturado["html"]
    assert "Título PDF personalizado" in html
    assert "Subtítulo PDF personalizado" in html
    assert "Sistema Pericial" not in html
    assert "Informe V2" not in html
    resumen = [
        capitulo
        for capitulo in contexto["capitulos"]
        if capitulo["clave"] == "resumen_ejecutivo"
    ][0]
    assert resumen["contenido"] == "Resumen redactado por el técnico"
    assert contexto["capitulos_guardados"] == 1
    assert contexto["informe"]["titulo_portada"] == "Título PDF personalizado"
    assert contexto["informe"]["subtitulo_portada"] == "Subtítulo PDF personalizado"
    assert contexto["informe"]["titulo_portada_pdf"] == "Título PDF personalizado"
    assert contexto["informe"]["subtitulo_portada_pdf"] == "Subtítulo PDF personalizado"
    assert contexto["indice"][0]["titulo"] == "Portada"
    assert contexto["indice"][-2]["titulo"] == "Justificación de mediciones"
    assert contexto["indice"][-1]["titulo"] == "Documentación aportada al expediente"
    assert contexto["indice"][-1]["grupo"] == "documentacion"
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


def test_pdf_v2_export_profiles_configurados(isolated_import):
    main_module = isolated_import("app.main")

    perfiles = main_module.PDF_EXPORT_PROFILES
    assert set(perfiles) == {
        "master",
        "email",
        "judicial",
        "solo_informe",
        "informe_anexos",
        "anexo_fotografico",
    }
    assert perfiles["informe_anexos"]["incluye_anexos"] is True
    assert perfiles["solo_informe"]["incluye_anexos"] is False
    assert perfiles["email"]["objetivo_mb"] == 20
    assert perfiles["email"]["optimizar_imagenes"] is True
    assert perfiles["email"]["jpeg_quality"] == 75
    assert perfiles["email"]["max_dimension"] == 1400
    assert perfiles["email"]["remove_exif"] is True
    assert perfiles["judicial"]["objetivo_mb"] == 10
    assert perfiles["judicial"]["optimizar_imagenes"] is True
    assert perfiles["judicial"]["jpeg_quality"] == 60
    assert perfiles["judicial"]["max_dimension"] == 1200
    assert perfiles["master"]["optimizar_imagenes"] is False
    assert perfiles["anexo_fotografico"]["implementado"] is False


def test_pdf_image_optimizer_no_modifica_original_y_reduce_dimension(tmp_path):
    from PIL import Image

    from app.services.pdf_image_optimizer import optimizar_imagen_pdf

    ruta_original = tmp_path / "foto-original.jpg"
    imagen = Image.new("RGB", (2400, 1200), (150, 40, 40))
    exif = imagen.getexif()
    exif[305] = "Sistema Pericial Test"
    imagen.save(ruta_original, quality=95, exif=exif)
    bytes_originales = ruta_original.read_bytes()

    resultado = optimizar_imagen_pdf(
        ruta_original,
        {
            "codigo": "email",
            "optimizar_imagenes": True,
            "jpeg_quality": 70,
            "max_dimension": 600,
            "remove_exif": True,
        },
        carpeta_temporal=tmp_path / "optimizadas",
    )

    assert ruta_original.read_bytes() == bytes_originales
    assert resultado["ruta"] != ruta_original
    with Image.open(resultado["ruta"]) as optimizada:
        assert max(optimizada.size) <= 600
        assert not dict(optimizada.getexif())
    with Image.open(ruta_original) as original:
        assert original.size == (2400, 1200)
        assert dict(original.getexif())
    assert resultado["tamano_original"] > resultado["tamano_optimizado"]


def test_pdf_image_optimizer_conserva_orientacion_visual(tmp_path):
    from PIL import Image

    from app.services.pdf_image_optimizer import optimizar_imagen_pdf

    ruta_original = tmp_path / "foto-orientada.jpg"
    imagen = Image.new("RGB", (80, 160), (40, 90, 160))
    exif = imagen.getexif()
    exif[274] = 6
    imagen.save(ruta_original, quality=95, exif=exif)

    resultado = optimizar_imagen_pdf(
        ruta_original,
        {
            "codigo": "judicial",
            "optimizar_imagenes": True,
            "jpeg_quality": 65,
            "max_dimension": 200,
            "remove_exif": True,
        },
        carpeta_temporal=tmp_path / "optimizadas",
    )

    with Image.open(resultado["ruta"]) as optimizada:
        assert optimizada.size == (160, 80)
        assert not dict(optimizada.getexif())


def test_pdf_annex_optimizer_calcula_tamano_y_no_modifica_original(tmp_path, monkeypatch):
    from pypdf import PdfWriter

    from app.services import pdf_annex_optimizer

    ruta_original = tmp_path / "anexo.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)
    bytes_originales = ruta_original.read_bytes()

    peso = pdf_annex_optimizer.analizar_peso_pdf(ruta_original)
    assert peso["tamano_bytes"] == len(bytes_originales)
    assert peso["tamano_mb"] >= 0
    assert peso["paginas"] == 1

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: None)

    def fake_pypdf(origen, destino):
        destino.write_bytes(b"%PDF-1.4\n% optimizado\n%%EOF\n")
        return True

    monkeypatch.setattr(pdf_annex_optimizer, "_optimizar_con_pypdf", fake_pypdf)
    resultado = pdf_annex_optimizer.optimizar_pdf_externo(
        ruta_original,
        "email",
        carpeta_temporal=tmp_path / "tmp",
    )

    assert ruta_original.read_bytes() == bytes_originales
    assert resultado["ruta"] != ruta_original
    assert resultado["optimizado"] is True
    assert resultado["metodo"] == "pypdf"
    assert resultado["tamano_final"] < resultado["tamano_original"]


def test_pdf_annex_optimizer_master_no_optimiza(tmp_path):
    from pypdf import PdfWriter

    from app.services.pdf_annex_optimizer import optimizar_pdf_externo

    ruta_original = tmp_path / "anexo-master.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)

    resultado = optimizar_pdf_externo(
        ruta_original,
        "master",
        carpeta_temporal=tmp_path / "tmp",
    )

    assert resultado["ruta"] == ruta_original
    assert resultado["optimizado"] is False
    assert resultado["metodo"] == "none"


def test_pdf_annex_optimizer_ghostscript_email_construye_comando_y_adopta_temporal(
    tmp_path,
    monkeypatch,
):
    from pypdf import PdfWriter

    from app.services import pdf_annex_optimizer

    ruta_original = tmp_path / "anexo-email.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)
    ruta_original.write_bytes(ruta_original.read_bytes() + b"0" * 2048)
    comandos = []

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: "/usr/local/bin/gs")

    def fake_run(comando, check, timeout):
        comandos.append((comando, check, timeout))
        salida = next(arg for arg in comando if arg.startswith("-sOutputFile=")).split("=", 1)[1]
        Path(salida).write_bytes(b"%PDF-1.4\n% optimizado\n%%EOF\n")

    monkeypatch.setattr(pdf_annex_optimizer.subprocess, "run", fake_run)
    resultado = pdf_annex_optimizer.optimizar_pdf_externo(
        ruta_original,
        "email",
        carpeta_temporal=tmp_path / "tmp",
    )

    comando, check, timeout = comandos[0]
    assert comando[0] == "/usr/local/bin/gs"
    assert "-dPDFSETTINGS=/ebook" in comando
    assert check is True
    assert timeout == 120
    assert resultado["optimizado"] is True
    assert resultado["metodo"] == "ghostscript"
    assert resultado["ruta"] != ruta_original
    assert resultado["tamano_final"] < resultado["tamano_original"]
    assert "ghostscript" in resultado["mensaje"]


def test_pdf_annex_optimizer_ghostscript_judicial_usa_screen(
    tmp_path,
    monkeypatch,
):
    from pypdf import PdfWriter

    from app.services import pdf_annex_optimizer

    ruta_original = tmp_path / "anexo-judicial.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)
    ruta_original.write_bytes(ruta_original.read_bytes() + b"0" * 2048)
    comandos = []

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: "/opt/homebrew/bin/gs")

    def fake_run(comando, check, timeout):
        comandos.append(comando)
        salida = next(arg for arg in comando if arg.startswith("-sOutputFile=")).split("=", 1)[1]
        Path(salida).write_bytes(b"%PDF-1.4\n% optimizado\n%%EOF\n")

    monkeypatch.setattr(pdf_annex_optimizer.subprocess, "run", fake_run)
    resultado = pdf_annex_optimizer.optimizar_pdf_externo(
        ruta_original,
        {"codigo": "judicial"},
        carpeta_temporal=tmp_path / "tmp",
    )

    assert "-dPDFSETTINGS=/screen" in comandos[0]
    assert resultado["optimizado"] is True
    assert resultado["metodo"] == "ghostscript"


def test_pdf_annex_optimizer_descarta_ghostscript_si_aumenta_o_falla(
    tmp_path,
    monkeypatch,
):
    from pypdf import PdfWriter

    from app.services import pdf_annex_optimizer

    ruta_original = tmp_path / "anexo-mayor.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: "/usr/local/bin/gs")

    def fake_run_mayor(comando, check, timeout):
        salida = next(arg for arg in comando if arg.startswith("-sOutputFile=")).split("=", 1)[1]
        Path(salida).write_bytes(ruta_original.read_bytes() + b"0" * 2048)

    monkeypatch.setattr(pdf_annex_optimizer.subprocess, "run", fake_run_mayor)
    monkeypatch.setattr(pdf_annex_optimizer, "_optimizar_con_pypdf", lambda origen, destino: False)
    resultado_mayor = pdf_annex_optimizer.optimizar_pdf_externo(
        ruta_original,
        "email",
        carpeta_temporal=tmp_path / "tmp-mayor",
    )

    assert resultado_mayor["ruta"] == ruta_original
    assert resultado_mayor["optimizado"] is False
    assert resultado_mayor["metodo"] == "none"

    def fake_run_timeout(comando, check, timeout):
        raise pdf_annex_optimizer.subprocess.TimeoutExpired(comando, timeout)

    monkeypatch.setattr(pdf_annex_optimizer.subprocess, "run", fake_run_timeout)
    resultado_timeout = pdf_annex_optimizer.optimizar_pdf_externo(
        ruta_original,
        "judicial",
        carpeta_temporal=tmp_path / "tmp-timeout",
    )

    assert resultado_timeout["ruta"] == ruta_original
    assert resultado_timeout["optimizado"] is False
    assert resultado_timeout["metodo"] == "none"


def test_pdf_v2_endpoint_email_funciona_sin_ghostscript(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services import pdf_annex_optimizer
    from pypdf import PdfReader, PdfWriter

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_no_gs")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    def pdf_con_paginas(total):
        writer = PdfWriter()
        for _ in range(total):
            writer.add_blank_page(width=595, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: None)
    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: pdf_con_paginas(1),
    )
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=email")

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 1
    assert "Página 1 de 1" in (reader.pages[0].extract_text() or "")


def test_pdf_v2_paginacion_se_llama_en_todos_los_perfiles(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.pdf_pagination import paginar_pdf_final_bytes as paginar_real
    from pypdf import PdfReader

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_pagination_profiles")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    perfiles = ["master", "email", "judicial", "informe_anexos", "solo_informe"]
    llamadas = []

    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: _pdf_simple_bytes(1),
    )

    def registrar_paginacion(pdf_bytes, perfil="master", config=None, debug=False, debug_dir=None):
        codigo = perfil.get("codigo") if isinstance(perfil, dict) else perfil
        llamadas.append(codigo)
        return paginar_real(
            pdf_bytes,
            perfil=perfil,
            config=config,
            debug=debug,
            debug_dir=debug_dir,
        )

    monkeypatch.setattr(main_module, "paginar_pdf_final_bytes", registrar_paginacion)

    client = _autenticar_cliente(main_module, user_id)
    for perfil in perfiles:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil={perfil}")
        assert response.status_code == 200
        reader = PdfReader(BytesIO(response.content))
        assert "Página 1 de 1" in (reader.pages[0].extract_text() or "")

    assert llamadas == perfiles


def test_pdf_v2_file_response_conserva_pdf_paginado(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfReader

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_file_response_paginated")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(main_module, "PDF_V2_FILE_RESPONSE_THRESHOLD_BYTES", 1)
    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: _pdf_simple_bytes(2),
    )

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe")

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 2
    assert "Página 1 de 2" in (reader.pages[0].extract_text() or "")
    assert "Página 2 de 2" in (reader.pages[1].extract_text() or "")


def test_pdf_v2_debug_pipeline_devuelve_json_y_no_pdf(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_debug_pipeline")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_anexo = _crear_documento_pdf_expediente(
            main_module,
            cur,
            expediente_id,
            "anexo-debug.pdf",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(
            f"/generar-informe-v2-pdf/{expediente_id}?perfil=master&debug_pdf_pipeline=1"
        )
    finally:
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert not response.content.startswith(b"%PDF")
    payload = response.json()
    assert payload["perfil"] == "master"
    assert payload["anexos_detectados"] >= 1
    assert payload["anexo_a_mb"] >= 0
    assert payload["paginas_estimadas"] >= 1
    assert "fusion_anexos" in payload["pasos_previstos"]
    assert "ghostscript_disponible" in payload


def test_pdf_v2_debug_sin_paginacion_omite_segunda_pasada(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfReader

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_skip_pagination")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: _pdf_simple_bytes(1),
    )

    def fail_pagination(pdf_bytes, perfil=None):
        raise AssertionError("debug_sin_paginacion debe omitir la paginación final")

    monkeypatch.setattr(main_module, "paginar_pdf_final_bytes", fail_pagination)

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe&debug_sin_paginacion=1"
    )

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 1
    assert "Página 1 de 1" not in (reader.pages[0].extract_text() or "")


def test_pdf_v2_master_con_anexo_pequeno_responde(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfReader

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_master_anexo_smoke")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_anexo = _crear_documento_pdf_expediente(
            main_module,
            cur,
            expediente_id,
            "anexo-master-smoke.pdf",
        )
        conn.commit()
    finally:
        conn.close()

    pdf_original = _pdf_simple_bytes(1)
    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: pdf_original,
    )
    monkeypatch.setattr(
        main_module,
        "generar_paginas_portadilla_anexo_a_v2",
        lambda documento, pdf_integrado: [],
    )

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=master")
    finally:
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert response.status_code == 200
    assert response.content != pdf_original
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 2
    assert "Página 1 de 2" in (reader.pages[0].extract_text() or "")
    assert "ANEXO A. DOCUMENTACIÓN APORTADA" not in (reader.pages[1].extract_text() or "")
    assert "Página 2 de 2" in (reader.pages[1].extract_text() or "")


def test_pdf_v2_email_ghostscript_lento_hace_timeout_y_fallback(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services import pdf_annex_optimizer
    from pypdf import PdfReader

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_email_gs_timeout")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_anexo = _crear_documento_pdf_expediente(
            main_module,
            cur,
            expediente_id,
            "anexo-email-timeout.pdf",
        )
        conn.commit()
    finally:
        conn.close()

    comandos = []

    def fake_run(comando, check, timeout):
        comandos.append((comando, timeout))
        raise pdf_annex_optimizer.subprocess.TimeoutExpired(comando, timeout)

    monkeypatch.setattr(pdf_annex_optimizer.shutil, "which", lambda nombre: "/usr/local/bin/gs")
    monkeypatch.setattr(pdf_annex_optimizer.subprocess, "run", fake_run)
    monkeypatch.setattr(pdf_annex_optimizer, "_optimizar_con_pypdf", lambda origen, destino: False)
    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: _pdf_simple_bytes(1),
    )
    monkeypatch.setattr(
        main_module,
        "generar_paginas_portadilla_anexo_a_v2",
        lambda documento, pdf_integrado: [],
    )

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(
            f"/generar-informe-v2-pdf/{expediente_id}?perfil=email&debug_sin_paginacion=1"
        )
    finally:
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 2
    assert "ANEXO A. DOCUMENTACIÓN APORTADA" not in (reader.pages[1].extract_text() or "")
    assert comandos
    assert "-dPDFSETTINGS=/ebook" in comandos[0][0]
    assert comandos[0][1] == pdf_annex_optimizer.GHOSTSCRIPT_PROFILES["email"]["timeout"]


def test_pdf_pagination_servicio_numera_pdf_una_pagina(tmp_path):
    from pypdf import PdfReader, PdfWriter

    from app.services.pdf_pagination import paginar_pdf_final

    ruta_original = tmp_path / "una-pagina.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    with ruta_original.open("wb") as buffer:
        writer.write(buffer)
    bytes_originales = ruta_original.read_bytes()

    ruta_paginada = paginar_pdf_final(ruta_original, carpeta_temporal=tmp_path / "pag")

    assert ruta_original.read_bytes() == bytes_originales
    assert ruta_paginada != ruta_original
    reader = PdfReader(str(ruta_paginada))
    assert len(reader.pages) == 1
    assert "Página 1 de 1" in (reader.pages[0].extract_text() or "")
    assert ruta_paginada.stat().st_size > ruta_original.stat().st_size


def test_pdf_pagination_servicio_numera_multipagina_y_ultima(tmp_path):
    from pypdf import PdfReader, PdfWriter

    from app.services.pdf_pagination import paginar_pdf_final_bytes

    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    writer.add_blank_page(width=595, height=842)
    writer.add_blank_page(width=595, height=842)
    buffer = BytesIO()
    writer.write(buffer)

    paginado = paginar_pdf_final_bytes(buffer.getvalue())
    reader = PdfReader(BytesIO(paginado))

    assert len(reader.pages) == 3
    assert "Página 1 de 3" in (reader.pages[0].extract_text() or "")
    assert "Página 3 de 3" in (reader.pages[2].extract_text() or "")


def test_pdf_pagination_servicio_overlay_visible_sobre_fondo_oscuro(tmp_path):
    from reportlab.pdfgen import canvas
    from pypdf import PdfReader

    from app.services.pdf_pagination import paginar_pdf_final_bytes

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(595, 842))
    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.rect(0, 0, 595, 842, stroke=0, fill=1)
    c.showPage()
    c.save()

    paginado = paginar_pdf_final_bytes(buffer.getvalue(), debug=True, debug_dir=tmp_path)
    reader = PdfReader(BytesIO(paginado))
    contenido = reader.pages[0].get_contents().get_data()

    assert "Página 1 de 1" in (reader.pages[0].extract_text() or "")
    assert b" rg" in contenido
    assert b" re" in contenido
    assert (tmp_path / "final_antes_paginacion.pdf").exists()
    assert (tmp_path / "final_despues_paginacion.pdf").exists()
    assert (tmp_path / "overlay_test_page_1.pdf").exists()
    assert (tmp_path / "final_despues_paginacion.pdf").stat().st_size > (
        tmp_path / "final_antes_paginacion.pdf"
    ).stat().st_size


def test_pdf_pagination_servicio_funciona_horizontal_y_tamanos_distintos():
    from pypdf import PdfReader, PdfWriter

    from app.services.pdf_pagination import paginar_pdf_final_bytes

    writer = PdfWriter()
    writer.add_blank_page(width=842, height=595)
    writer.add_blank_page(width=612, height=1008)
    buffer = BytesIO()
    writer.write(buffer)

    paginado = paginar_pdf_final_bytes(buffer.getvalue())
    reader = PdfReader(BytesIO(paginado))

    assert len(reader.pages) == 2
    assert int(float(reader.pages[0].mediabox.width)) == 842
    assert int(float(reader.pages[0].mediabox.height)) == 595
    assert int(float(reader.pages[1].mediabox.width)) == 612
    assert int(float(reader.pages[1].mediabox.height)) == 1008
    assert "Página 1 de 2" in (reader.pages[0].extract_text() or "")
    assert "Página 2 de 2" in (reader.pages[1].extract_text() or "")


def test_pdf_pagination_servicio_funciona_con_pagina_rotada():
    from pypdf import PdfReader, PdfWriter

    from app.services.pdf_pagination import paginar_pdf_final_bytes

    writer = PdfWriter()
    pagina = writer.add_blank_page(width=842, height=595)
    pagina.rotate(90)
    buffer = BytesIO()
    writer.write(buffer)

    paginado = paginar_pdf_final_bytes(buffer.getvalue())
    reader = PdfReader(BytesIO(paginado))

    assert len(reader.pages) == 1
    assert int(reader.pages[0].get("/Rotate", 0) or 0) == 0
    assert int(float(reader.pages[0].mediabox.width)) == 595
    assert int(float(reader.pages[0].mediabox.height)) == 842
    assert "Página 1 de 1" in (reader.pages[0].extract_text() or "")


def test_pdf_pagination_si_falla_devuelve_original_y_registra_warning(
    monkeypatch,
    caplog,
):
    import logging

    from app.services import pdf_pagination

    pdf_original = _pdf_simple_bytes(1)

    def fail_overlay(ancho, alto, texto, config):
        raise RuntimeError("fallo pagination smoke")

    monkeypatch.setattr(pdf_pagination, "_crear_overlay_paginacion", fail_overlay)

    with caplog.at_level(logging.WARNING):
        resultado = pdf_pagination.paginar_pdf_final_bytes(pdf_original)

    assert resultado == pdf_original
    assert "No se pudo paginar el PDF final" in caplog.text


def test_pdf_v2_rechaza_perfil_exportacion_desconocido(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_perfil_invalido")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/generar-informe-v2-pdf/{expediente_id}?perfil=desconocido"
    )

    assert response.status_code == 400
    assert "Perfil de exportación PDF no válido" in response.text


def test_pdf_v2_perfil_solo_informe_no_fusiona_anexos(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_solo_informe")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    def fake_pdf_bytes(request, contexto):
        return b"%PDF-1.4\n%PDF solo informe\n"

    def fail_fusion(pdf_informe, documentos_anexo_a, pdf_mediciones):
        raise AssertionError("El perfil solo_informe no debe fusionar anexos")

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    monkeypatch.setattr(
        main_module,
        "fusionar_pdf_informe_v2_con_anexos_integrados",
        fail_fusion,
    )
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe"
    )

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4\n%PDF solo informe\n"
    assert "Informe-EXP-PER-WB-1-solo-informe.pdf" in response.headers["content-disposition"]


def test_pdf_v2_endpoint_solo_informe_devuelve_pdf_paginado(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfReader, PdfWriter

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_paginated_solo")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    def pdf_con_paginas(total):
        writer = PdfWriter()
        for _ in range(total):
            writer.add_blank_page(width=595, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: pdf_con_paginas(2),
    )
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe"
    )

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 2
    assert "Página 1 de 2" in (reader.pages[0].extract_text() or "")
    assert "Página 2 de 2" in (reader.pages[1].extract_text() or "")


def test_pdf_v2_perfil_email_diferencia_nombre_archivo(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from PIL import Image
    from urllib.parse import urlparse

    from app.database import get_connection

    conn = get_connection()
    ruta_foto = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_email")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        visita_id = cur.execute(
            "SELECT id FROM visitas WHERE expediente_id=? LIMIT 1",
            (expediente_id,),
        ).fetchone()["id"]
        nombre_foto = f"smoke_pdf_opt_{expediente_id}.jpg"
        ruta_foto = main_module.UPLOAD_PATH / nombre_foto
        Image.new("RGB", (2200, 1200), (120, 80, 60)).save(ruta_foto, quality=95)
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, 'exterior', ?, ?)
            """,
            (visita_id, nombre_foto, "Foto grande para optimización PDF"),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        diagnostico = contexto["optimizacion_imagenes_pdf"]["diagnostico"][0]
        capturado["ruta_optimizada_existe_durante_render"] = Path(
            diagnostico["ruta_optimizada"]
        ).exists()
        ruta_temporal = urlparse(diagnostico["url_optimizada"]).path
        capturado["ruta_temporal_http"] = ruta_temporal
        asset_response = TestClient(request.app).get(ruta_temporal)
        capturado["asset_status"] = asset_response.status_code
        capturado["asset_content_type"] = asset_response.headers.get("content-type", "")
        return b"%PDF-1.4\n%PDF email\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=email")
    finally:
        if ruta_foto:
            ruta_foto.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "Informe-EXP-PER-WB-1-email.pdf" in response.headers["content-disposition"]
    assert capturado["contexto"]["perfil_exportacion_pdf"]["codigo"] == "email"
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["imagenes"] >= 1
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["tamano_optimizado"] > 0
    assert "/pdf-temp-images/" in capturado["html"]
    assert "file://" not in capturado["html"]
    assert f"/uploads/{nombre_foto}" not in capturado["html"]
    assert capturado["ruta_optimizada_existe_durante_render"] is True
    assert capturado["asset_status"] == 200
    assert capturado["asset_content_type"].startswith("image/jpeg")
    ruta_optimizada = capturado["contexto"]["optimizacion_imagenes_pdf"]["diagnostico"][0]["ruta_optimizada"]
    assert Path(ruta_optimizada).exists() is False
    assert TestClient(main_module.app).get(capturado["ruta_temporal_http"]).status_code == 404


def test_pdf_v2_perfil_judicial_renderiza_ruta_optimizada(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from PIL import Image
    from urllib.parse import urlparse

    from app.database import get_connection

    conn = get_connection()
    ruta_foto = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_judicial")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        visita_id = cur.execute(
            "SELECT id FROM visitas WHERE expediente_id=? LIMIT 1",
            (expediente_id,),
        ).fetchone()["id"]
        nombre_foto = f"smoke_pdf_opt_judicial_{expediente_id}.jpg"
        ruta_foto = main_module.UPLOAD_PATH / nombre_foto
        Image.new("RGB", (2200, 1200), (120, 80, 60)).save(ruta_foto, quality=95)
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, 'exterior', ?, ?)
            """,
            (visita_id, nombre_foto, "Foto grande para optimización judicial"),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        diagnostico = contexto["optimizacion_imagenes_pdf"]["diagnostico"][0]
        capturado["ruta_optimizada_existe_durante_render"] = Path(
            diagnostico["ruta_optimizada"]
        ).exists()
        ruta_temporal = urlparse(diagnostico["url_optimizada"]).path
        capturado["ruta_temporal_http"] = ruta_temporal
        capturado["asset_status"] = TestClient(request.app).get(ruta_temporal).status_code
        return b"%PDF-1.4\n%PDF judicial\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=judicial")
    finally:
        if ruta_foto:
            ruta_foto.unlink(missing_ok=True)

    assert response.status_code == 200
    assert capturado["contexto"]["perfil_exportacion_pdf"]["codigo"] == "judicial"
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["imagenes"] >= 1
    assert "/pdf-temp-images/" in capturado["html"]
    assert "file://" not in capturado["html"]
    assert f"/uploads/{nombre_foto}" not in capturado["html"]
    assert capturado["ruta_optimizada_existe_durante_render"] is True
    assert capturado["asset_status"] == 200
    ruta_optimizada = capturado["contexto"]["optimizacion_imagenes_pdf"]["diagnostico"][0]["ruta_optimizada"]
    assert Path(ruta_optimizada).exists() is False
    assert TestClient(main_module.app).get(capturado["ruta_temporal_http"]).status_code == 404


def test_pdf_v2_perfil_master_renderiza_ruta_original(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from PIL import Image

    from app.database import get_connection

    conn = get_connection()
    ruta_foto = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_master")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        visita_id = cur.execute(
            "SELECT id FROM visitas WHERE expediente_id=? LIMIT 1",
            (expediente_id,),
        ).fetchone()["id"]
        nombre_foto = f"smoke_pdf_master_{expediente_id}.jpg"
        ruta_foto = main_module.UPLOAD_PATH / nombre_foto
        Image.new("RGB", (1600, 900), (120, 80, 60)).save(ruta_foto, quality=90)
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, 'exterior', ?, ?)
            """,
            (visita_id, nombre_foto, "Foto para perfil master"),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF master\n"

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=master")
    finally:
        if ruta_foto:
            ruta_foto.unlink(missing_ok=True)

    assert response.status_code == 200
    assert capturado["contexto"]["perfil_exportacion_pdf"]["codigo"] == "master"
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["imagenes"] == 0
    assert f"/uploads/{nombre_foto}" in capturado["html"]
    assert "file://" not in capturado["html"]


def test_pdf_v2_perfil_email_fallback_original_si_optimizacion_falla(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from PIL import Image

    from app.database import get_connection
    from app.services import pdf_image_optimizer

    conn = get_connection()
    ruta_foto = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_email_img_fallback")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        visita_id = cur.execute(
            "SELECT id FROM visitas WHERE expediente_id=? LIMIT 1",
            (expediente_id,),
        ).fetchone()["id"]
        nombre_foto = f"smoke_pdf_fallback_{expediente_id}.jpg"
        ruta_foto = main_module.UPLOAD_PATH / nombre_foto
        Image.new("RGB", (1200, 800), (40, 90, 130)).save(ruta_foto, quality=90)
        cur.execute(
            """
            INSERT INTO visita_fotos (visita_id, categoria, ruta, descripcion)
            VALUES (?, 'exterior', ?, ?)
            """,
            (visita_id, nombre_foto, "Foto fallback optimización PDF"),
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_optimizer(ruta_imagen, perfil="master", carpeta_temporal=None):
        ruta = Path(ruta_imagen)
        return {
            "ruta": ruta,
            "ruta_temporal": False,
            "tamano_original": ruta.stat().st_size,
            "tamano_optimizado": ruta.stat().st_size,
            "reduccion_porcentaje": 0,
        }

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return b"%PDF-1.4\n%PDF fallback image\n"

    monkeypatch.setattr(pdf_image_optimizer, "optimizar_imagen_pdf", fake_optimizer)
    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=email")
    finally:
        if ruta_foto:
            ruta_foto.unlink(missing_ok=True)

    assert response.status_code == 200
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["imagenes"] == 0
    assert capturado["contexto"]["optimizacion_imagenes_pdf"]["diagnostico"][0]["fallback_original"] is True
    assert f"/uploads/{nombre_foto}" in capturado["html"]
    assert "/pdf-temp-images/" not in capturado["html"]
    assert "file://" not in capturado["html"]


def test_informe_v2_editor_muestra_aviso_anexos_pdf_externos(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfWriter

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_annex_weight_ui")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_relativa = f"expediente_documentos/{expediente_id}/anexo-pesado.pdf"
        ruta_anexo = main_module.UPLOAD_PATH / ruta_relativa
        ruta_anexo.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with ruta_anexo.open("wb") as buffer:
            writer.write(buffer)
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
                "Anexo documental externo",
                "PDF externo aportado para anexo A.",
                "Documentación aportada",
                ruta_relativa,
                "anexo-pesado.pdf",
                10,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    finally:
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "Peso estimado del PDF" in response.text
    assert "El PDF final puede ser pesado porque contiene anexos externos" in response.text
    assert "Documentación aportada" in response.text
    assert "Anexo E" in response.text


def test_pdf_v2_diagnostico_anexos_devuelve_desglose_estable(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_annex_diag_helper")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_anexo = _crear_documento_pdf_expediente(
            main_module,
            cur,
            expediente_id,
            "anexo-helper.pdf",
            total_paginas=2,
        )
        conn.commit()
        documentos = [
            {
                "nombre": "Anexo helper",
                "archivo_ruta": f"expediente_documentos/{expediente_id}/anexo-helper.pdf",
                "mime_type": "application/pdf",
            }
        ]
        diagnostico = main_module.diagnosticar_peso_anexos_pdf_v2(
            documentos,
            None,
            b"12345",
        )
    finally:
        conn.close()
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert set(
        [
            "informe_principal_mb",
            "anexo_a_mb",
            "anexo_f_mb",
            "otros_anexos_mb",
            "total_estimado_mb",
            "anexos",
            "anexos_pesados",
            "avisos",
            "nivel",
        ]
    ).issubset(diagnostico)
    assert diagnostico["informe_principal_mb"] == 0.0
    assert diagnostico["anexo_a_mb"] >= 0
    assert diagnostico["anexo_f_mb"] == 0.0
    assert diagnostico["otros_anexos_mb"] == 0.0
    assert diagnostico["total_estimado_mb"] >= diagnostico["anexo_a_mb"]
    assert diagnostico["anexos"][0]["nombre"] == "Anexo helper"
    assert diagnostico["anexos"][0]["categoria"] == "anexo_a"
    assert diagnostico["anexos"][0]["paginas"] == 2


def test_informe_v2_editor_muestra_diagnostico_anexos_pesados(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    ruta_anexo = None
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_annex_diag_heavy")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        ruta_anexo = _crear_documento_pdf_expediente(
            main_module,
            cur,
            expediente_id,
            "anexo-a-22mb.pdf",
            total_paginas=3,
            padding_bytes=22 * 1024 * 1024,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    finally:
        if ruta_anexo:
            ruta_anexo.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "Peso estimado del PDF" in response.text
    assert "Total estimado" in response.text
    assert "Anexo documental smoke" in response.text
    assert "Hay anexos individuales de más de 10 MB" in response.text
    assert "El PDF final estimado supera 20 MB" in response.text
    assert "La documentación aportada representa más del 70 %" in response.text
    assert "El perfil Email/Judicial puede intentar comprimir anexos externos" in response.text


def test_informe_v2_editor_sin_anexos_muestra_panel_sin_romper(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_annex_diag_empty")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")

    assert response.status_code == 200
    assert "Peso estimado del PDF" in response.text
    assert "No constan anexos PDF externos incorporables al informe final." in response.text
    assert "Exportar PDF" in response.text


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
    assert contexto["anexos"]["analisis_partida_4"]["contenido_pdf"].startswith("D.1 Objeto")
    assert contexto["anexos"]["analisis_partida_4"]["guardado"] is False
    assert contexto["anexos"]["justificacion_mediciones"]["contenido_pdf"].startswith("E.1 Criterios de medición")
    assert contexto["anexos"]["justificacion_mediciones"]["guardado"] is False
    assert contexto["pdf_mediciones_anexo_f"] is None
    assert contexto["informe"]["titulo_portada"] == ""
    assert contexto["informe"]["subtitulo_portada"] == ""
    assert contexto["informe"]["titulo_portada_pdf"].startswith("DAÑOS POR ENTRADA DE AGUA DE LLUVIA")
    assert contexto["informe"]["subtitulo_portada_pdf"].startswith("Análisis técnico de los daños observados")


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
                "PDF de mediciones para Anexo E",
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

    def fake_fusion(pdf_informe, documentos_anexo_a, pdf_mediciones, **kwargs):
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
    assert "E.4 Desarrollo completo de mediciones" in html
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

    assert "Carlos Blanco | Arquitecto Técnico | Colegiado nº 5866" in bloque_v2
    assert "Arquitecto Técnico · Expediente" not in bloque_v2
    assert 'header_template = "<span></span>"' in bloque_v2
    assert "header_template=header_template" in bloque_v2
    assert "footer_template=footer_template" in bloque_v2
    assert "tipo_trabajo_label" not in bloque_v2
    assert "cabecera_informe" not in bloque_v2
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
            "numero_anexo": "A.1",
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
    bytes_anexo_original = ruta_anexo.read_bytes()

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
    monkeypatch.setattr(
        main_module,
        "generar_paginas_indice_anexo_a_v2",
        lambda documentos: (_ for _ in ()).throw(
            AssertionError("La tabla documental duplicada del Anexo A no debe insertarse")
        ),
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
    textos = [
        pagina.extract_text() or ""
        for pagina in PdfReader(BytesIO(fusionado)).pages
    ]
    assert "ANEXO A. DOCUMENTACIÓN APORTADA" not in textos[1]
    assert "Relación de documentación aportada" not in "\n".join(textos)
    assert ruta_anexo.read_bytes() == bytes_anexo_original


def test_pdf_v2_anexo_a_genera_indice_y_ficha_documental(isolated_import):
    main_module = isolated_import("app.main")

    from pypdf import PdfReader

    documento_1 = {
        "numero_anexo": "A.1",
        "numero_documento_label": "Documento 1",
        "nombre": "Proyecto Reforma Cubierta de Evaristo Pastor Catalán con Memoria Técnica Completa",
        "tipo": "Proyecto",
        "fecha": "2026-06-18",
        "descripcion": "Proyecto aportado por la propiedad.",
        "paginas": 102,
        "paginas_label": "102 págs.",
        "tamano_mb": 27.41,
        "tamano_label": "27.41 MB",
        "categoria": "Proyecto",
    }
    documento_2 = {
        "numero_anexo": "A.2",
        "numero_documento_label": "Documento 2",
        "nombre": "Ficha catastral",
        "tipo": "Ficha",
        "paginas": 1,
        "paginas_label": "1 pág.",
        "tamano_mb": 0.64,
        "tamano_label": "0.64 MB",
        "categoria": "Catastro",
    }

    indice = main_module.generar_paginas_indice_anexo_a_v2([documento_1, documento_2])
    ficha = main_module.generar_paginas_portadilla_anexo_a_v2(documento_1, True)

    assert len(indice) >= 1
    assert len(ficha) == 1
    texto_indice = indice[0].extract_text() or ""
    texto_ficha = ficha[0].extract_text() or ""
    assert "DOCUMENTACIÓN APORTADA AL EXPEDIENTE" in texto_indice
    assert "Documento 1" in texto_indice
    assert "Documento 2" in texto_indice
    assert "Proyecto Reforma Cubierta de Evaristo Pastor Catalán" in texto_indice
    assert "102 págs." not in texto_indice
    assert "27.41 MB" not in texto_indice
    assert "DOCUMENTACIÓN APORTADA AL EXPEDIENTE" in texto_ficha
    assert "Documento 1" in texto_ficha
    assert "ANEXO A" not in texto_ficha
    assert "A.1" not in texto_ficha
    assert "Proyecto Reforma Cubierta" in texto_ficha
    assert "Evaristo" in texto_ficha
    assert "Pastor Catalán" in texto_ficha
    assert "Memoria Técnica" in texto_ficha
    assert "Completa" in texto_ficha
    assert "Proyecto aportado por la propiedad." in texto_ficha
    assert "Documento incorporado a continuación." in texto_ficha
    assert "..." not in texto_ficha
    assert "Páginas:" not in texto_ficha
    assert "Tamaño:" not in texto_ficha
    assert "Fecha de incorporación:" not in texto_ficha
    assert "Categoría:" not in texto_ficha


def test_pdf_v2_agrega_bookmarks_jerarquicos(isolated_import):
    main_module = isolated_import("app.main")

    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject

    pdf_base = _pdf_texto_paginas(
        [
            "Dictamen técnico pericial",
            "1. Resumen ejecutivo",
            "2. Antecedentes y objeto",
            "13. Conclusiones",
            "ANEXO A\nREPORTAJE FOTOGRÁFICO",
            "ANEXO B\nFICHAS DE DAÑOS POR ESTANCIA",
            "ANEXO C\nVALORACIÓN ECONÓMICA DETALLADA",
            "ANEXO D\nANÁLISIS DE EJECUCIÓN DE LA PARTIDA Nº 4",
            "ANEXO E\nJUSTIFICACIÓN DE MEDICIONES",
            "DOCUMENTACIÓN APORTADA AL EXPEDIENTE\nRelación documental\nDocumento 1. Contrato de obra\nDocumento 2. Factura",
            "DOCUMENTACIÓN APORTADA AL EXPEDIENTE\nDocumento 1\nContrato de obra",
            "DOCUMENTACIÓN APORTADA AL EXPEDIENTE\nDocumento 2\nFactura",
        ]
    )
    reader_base = PdfReader(BytesIO(pdf_base))
    writer_base = PdfWriter()
    for pagina in reader_base.pages:
        writer_base.add_page(pagina)
    enlace_indice = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(0), NumberObject(0), NumberObject(120), NumberObject(18)]
            ),
            NameObject("/Dest"): NameObject("/pdf-target-anexo_a"),
        }
    )
    writer_base.pages[0][NameObject("/Annots")] = ArrayObject(
        [writer_base._add_object(enlace_indice)]
    )
    buffer_base = BytesIO()
    writer_base.write(buffer_base)
    pdf_base = buffer_base.getvalue()
    contexto = {
        "capitulos": [
            {"numero_pdf": 1, "titulo": "Resumen ejecutivo"},
            {"numero_pdf": 2, "titulo": "Antecedentes y objeto"},
        ],
        "conclusiones": {"numero": 13, "titulo": "Conclusiones"},
        "anexos": {
            "documentacion": [
                {"nombre": "Contrato de obra"},
                {"nombre": "Factura"},
            ],
        },
    }

    pdf_con_bookmarks = main_module.agregar_bookmarks_pdf_v2(pdf_base, contexto)
    reader = PdfReader(BytesIO(pdf_con_bookmarks))
    titulos = _outline_titles(reader.outline)
    titulos_raiz = _outline_top_titles(reader.outline)

    assert len(reader.pages) == 12
    assert titulos_raiz == [
        "Informe",
        "Anexos técnicos",
        "Documentación aportada al expediente",
    ]
    assert "Informe" in titulos
    assert "1. Resumen ejecutivo" in titulos
    assert "13. Conclusiones" in titulos
    assert "Anexos técnicos" in titulos
    assert "Anexo A. Reportaje fotográfico" in titulos
    assert "Anexo E. Justificación de mediciones" in titulos
    assert "Documentación aportada al expediente" in titulos
    assert "Relación de documentación aportada" in titulos
    assert "Documento 1. Contrato de obra" in titulos
    assert "Documento 2. Factura" in titulos
    annot = reader.pages[0]["/Annots"][0].get_object()
    assert "/Dest" not in annot
    assert annot["/A"]["/S"] == "/GoTo"
    assert annot["/A"]["/D"][1] == "/Fit"


def test_pdf_v2_fusion_integrada_usa_ruta_optimizada_si_procede(
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
    ruta_relativa = "expediente_documentos/1/anexo-original.pdf"
    ruta_original = main_module.UPLOAD_PATH / ruta_relativa
    ruta_original.parent.mkdir(parents=True, exist_ok=True)
    ruta_original.write_bytes(pdf_con_paginas([520]))

    ruta_optimizada = main_module.UPLOAD_PATH / "expediente_documentos/1/anexo-optimizado.pdf"
    ruta_optimizada.write_bytes(pdf_con_paginas([530]))

    class FakeSession:
        def optimizar(self, path, categoria=""):
            assert path == ruta_original
            assert categoria == "anexo_a"
            return {"ruta": ruta_optimizada, "optimizado": True, "metodo": "test"}

    monkeypatch.setattr(
        main_module,
        "generar_paginas_portadilla_anexo_a_v2",
        lambda documento, pdf_integrado: [],
    )

    fusionado = main_module.fusionar_pdf_informe_v2_con_anexos_integrados(
        informe,
        [
            {
                "nombre": "Documento integrado",
                "numero_anexo": "A.2",
                "archivo": "anexo-original.pdf",
                "archivo_ruta": ruta_relativa,
                "mime_type": "application/pdf",
            },
        ],
        None,
        perfil_pdf={"codigo": "email"},
        sesion_optimizacion_anexos=FakeSession(),
    )

    anchos = [
        int(float(pagina.mediabox.width))
        for pagina in PdfReader(BytesIO(fusionado)).pages
    ]
    assert anchos == [500, 530]


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

    def fake_merge(pdf_informe, documentos, pdf_mediciones, **kwargs):
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


def test_pdf_v2_endpoint_numera_pdf_final_con_anexos_fusionados(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from pypdf import PdfReader, PdfWriter

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_pdf_v2_paginated_annex")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    def pdf_con_paginas(total):
        writer = PdfWriter()
        for _ in range(total):
            writer.add_blank_page(width=595, height=842)
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()

    monkeypatch.setattr(
        main_module,
        "generar_informe_v2_pdf_bytes",
        lambda request, contexto: pdf_con_paginas(1),
    )
    monkeypatch.setattr(
        main_module,
        "fusionar_pdf_informe_v2_con_anexos_integrados",
        lambda pdf_informe, documentos, pdf_mediciones, **kwargs: pdf_con_paginas(3),
    )
    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=master")

    assert response.status_code == 200
    reader = PdfReader(BytesIO(response.content))
    assert len(reader.pages) == 3
    assert "Página 1 de 3" in (reader.pages[0].extract_text() or "")
    assert "Página 3 de 3" in (reader.pages[2].extract_text() or "")


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
                "ANEXO D. Análisis de ejecución de la partida nº 4",
                13,
                "E.1 Objeto\n\nContenido manual guardado del Anexo E.\n\nE.6 Conclusión\n\nConclusión manual del Anexo E.",
            ),
            (
                "anexo_f_mediciones",
                "ANEXO E. Justificación de mediciones",
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
    assert "Dictamen técnico pericial" in html
    assert "DAÑOS POR ENTRADA DE AGUA DE LLUVIA" in html
    assert "Análisis técnico de los daños observados" in html
    assert "Colegiado nº 5866" in html
    assert 'class="chapter report-chapter chapter-resumen_ejecutivo"' in html
    assert 'class="chapter report-chapter chapter-limitaciones"' in html
    assert 'class="chapter report-chapter chapter-conclusiones"' in html
    assert 'class="conclusion-block"' in html
    assert "consultation-panel" not in html
    assert "INFORME PERICIAL</span>" not in html
    assert "Arquitecto Técnico" in html
    assert "toc-row is-annex" in html
    assert 'id="pdf-target-portada"' in html
    assert 'id="pdf-target-indice"' in html
    assert 'href="#pdf-target-resumen_ejecutivo"' in html
    assert 'id="pdf-target-resumen_ejecutivo"' in html
    assert 'href="#pdf-target-conclusiones"' in html
    assert 'id="pdf-target-conclusiones"' in html
    assert 'href="#pdf-target-anexo_a"' in html
    assert 'id="pdf-target-anexo_a"' in html
    assert 'href="#pdf-target-anexo_b"' in html
    assert 'id="pdf-target-anexo_b"' in html
    assert 'href="#pdf-target-anexo_c"' in html
    assert 'id="pdf-target-anexo_c"' in html
    assert 'href="#pdf-target-anexo_d"' in html
    assert 'id="pdf-target-anexo_d"' in html
    assert 'href="#pdf-target-anexo_e"' in html
    assert 'id="pdf-target-anexo_e"' in html
    assert 'href="#pdf-target-documentacion_aportada"' in html
    assert 'id="pdf-target-documentacion_aportada"' in html
    assert 'href="#pdf-target-documentacion_doc_1"' in html
    assert 'href="#pdf-target-documentacion_doc_2"' in html
    assert 'id="pdf-target-documentacion_doc_1"' in html
    assert 'id="pdf-target-documentacion_doc_2"' in html
    assert "Documento 1." in html
    assert "Presupuesto pericial de reparación" in html
    assert "Documento 2." in html
    assert "Factura de reparación de cubierta" in html
    assert 'id="pdf-target-relacion_documental"' in html
    assert html.count('href="#pdf-target-') == len(contexto["indice"])
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
    assert "E.4 Desarrollo completo de mediciones" not in html
    assert html.count("13. Conclusiones") == 1
    assert len(contexto["conclusiones"]["bloques"]) == 1
    assert "Conclusión técnica redactada por el técnico." not in html
    assert "Conclusión pericial redactada por el técnico." in html
    assert "Conclusiones técnicas" not in html
    assert "Conclusiones periciales" not in html
    assert "14. Conclusiones periciales" not in html
    indice_por_clave = {item["clave"]: item for item in contexto["indice"]}
    assert indice_por_clave["anexo_a"]["titulo"] == "Reportaje fotográfico"
    assert indice_por_clave["anexo_b"]["titulo"] == "Fichas de daños por estancia"
    assert indice_por_clave["anexo_c"]["titulo"] == "Valoración económica detallada"
    assert indice_por_clave["anexo_d"]["titulo"] == "Análisis de ejecución de la partida nº 4"
    assert indice_por_clave["anexo_e"]["titulo"] == "Justificación de mediciones"
    assert (
        indice_por_clave["documentacion_aportada"]["titulo"]
        == "Documentación aportada al expediente"
    )
    assert [
        item["clave"]
        for item in contexto["indice"]
        if item["grupo"] in {"anexos", "documentacion"}
    ] == [
        "anexo_a",
        "anexo_b",
        "anexo_c",
        "anexo_d",
        "anexo_e",
        "documentacion_aportada",
    ]
    assert "ANEXO A. DOCUMENTACIÓN APORTADA" not in html
    assert "DOCUMENTACIÓN APORTADA AL EXPEDIENTE" in html
    assert html.count("Relación documental") == 1
    assert "A.1 Relación de documentación aportada" not in html
    assert "Documento 1" in html
    assert "Documento 2" in html
    assert "Presupuesto pericial de reparación" in html
    assert "Factura de reparación de cubierta" in html
    assert "Presupuesto base de valoración." in html
    assert "El documento queda referenciado, pero el PDF aportado no se pudo incorporar físicamente." not in html
    assert "Documento aportado por la propiedad." not in html
    assert "factura-original-privada.pdf" not in html
    assert "presupuesto-original-privado.pdf" not in html
    assert "presupuesto_hash.pdf" not in html
    assert "expediente_documentos/" not in html
    assert "ANEXO A. REPORTAJE FOTOGRÁFICO DE PATOLOGÍAS" in html
    assert "A.1 FILTRACIONES Y HUMEDADES" in html
    assert "A.2 DETERIORO DE REVESTIMIENTOS Y ACABADOS" in html
    assert "A.3 MOHOS Y COLONIZACIÓN BIOLÓGICA" in html
    assert "A.4 DAÑOS EN CARPINTERÍAS Y ELEMENTOS AUXILIARES" in html
    assert "A.5 DAÑOS EXTERIORES Y FACHADA" in html
    assert "A.6 OTRAS EVIDENCIAS FOTOGRÁFICAS" in html
    assert "Figura A-1" in html
    assert "Estancia asociada:" not in html
    assert "Patología de referencia:" not in html
    assert "Se muestran 6 fotografías representativas de 7 clasificadas en este grupo." in html
    assert "ANEXO B. FICHAS DE DAÑOS POR ESTANCIA" in html
    assert html.index('class="damage-section danos_observados"') < html.index(
        'class="damage-section observaciones"'
    )
    assert html.index('class="damage-section observaciones"') < html.index(
        'class="damage-section evidencias_fotograficas"'
    )
    assert "Daños observados:" in html
    assert "Observaciones:" in html
    assert "Evidencias fotográficas:" in html
    assert "ANEXO C. VALORACIÓN ECONÓMICA DETALLADA" in html
    assert "annex-section annex-valuation-landscape" in html
    assert "@page annex-valuation-landscape" in html
    assert "margin: 16mm 11mm 19mm;" in html
    assert "PRESUPUESTO DE EJECUCIÓN MATERIAL" in html
    assert "365,70 €" in html
    assert "8.616,00 €" in html
    assert "8.981,70 €" in html
    assert "10,00 m²" in html
    assert "185,00 m²" in html
    assert "10,0000 m2" not in html
    assert "8616.00 EUR" not in html
    assert '<td class="money amount">8.616,00 €</td>' in html
    assert "ANEXO D. ANÁLISIS DE EJECUCIÓN DE LA PARTIDA Nº 4" in html
    assert "E.1 Objeto" in html
    assert "Contenido manual guardado del Anexo E." in html
    assert "Conclusión manual del Anexo E." in html
    assert "[Completar conclusión técnica sobre la partida analizada.]" not in html
    assert "E.6 Conclusión" in html
    assert "ANEXO E. JUSTIFICACIÓN DE MEDICIONES" in html
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
    assert html.index("ANEXO A. REPORTAJE FOTOGRÁFICO") < html.index(
        "ANEXO B. FICHAS DE DAÑOS"
    )
    assert html.index("ANEXO E. JUSTIFICACIÓN DE MEDICIONES") < html.index(
        "DOCUMENTACIÓN APORTADA AL EXPEDIENTE"
    )
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


def test_informe_v2_laminas_fotograficas_crea_2_y_4_fotos(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_crear")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(4):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_crear_{expediente_id}_{indice}.jpg",
                f"Foto lámina {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response_2 = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas",
        data={
            "titulo": "Antes y después de reparación",
            "subtitulo": "Comparativa visual",
            "layout": "antes_despues",
            "foto_ids": [str(fotos[0]), str(fotos[1])],
        },
        follow_redirects=False,
    )
    response_4 = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas",
        data={
            "titulo": "Evolución cronológica",
            "layout": "cronologica",
            "foto_ids": [str(fotos[0]), str(fotos[1]), str(fotos[2]), str(fotos[3])],
        },
        follow_redirects=False,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        laminas = cur.execute(
            """
            SELECT id, titulo, layout
            FROM informe_v2_laminas_fotograficas
            WHERE expediente_id = ?
            ORDER BY orden ASC
            """,
            (expediente_id,),
        ).fetchall()
        totales = [
            cur.execute(
                "SELECT COUNT(*) AS total FROM informe_v2_lamina_fotos WHERE lamina_id = ?",
                (lamina["id"],),
            ).fetchone()["total"]
            for lamina in laminas
        ]
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response_2.status_code == 303
    assert response_4.status_code == 303
    assert [lamina["layout"] for lamina in laminas] == ["antes_despues", "cronologica"]
    assert totales == [2, 4]


def test_informe_v2_laminas_fotograficas_reordena_y_elimina(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_orden")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(2):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_orden_{expediente_id}_{indice}.jpg",
                f"Foto orden {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        ok_1, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Primera lámina",
            "",
            "dos_fotos",
            fotos,
        )
        ok_2, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Segunda lámina",
            "",
            "dos_fotos",
            fotos,
        )
        assert ok_1 and ok_2
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    conn = get_connection()
    try:
        cur = conn.cursor()
        segunda_id = cur.execute(
            """
            SELECT id FROM informe_v2_laminas_fotograficas
            WHERE expediente_id = ? AND titulo = 'Segunda lámina'
            """,
            (expediente_id,),
        ).fetchone()["id"]
    finally:
        conn.close()

    response_mover = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas/{segunda_id}/mover",
        data={"direccion": "arriba"},
        follow_redirects=False,
    )
    response_eliminar = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas/{segunda_id}/eliminar",
        follow_redirects=False,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        titulos = [
            fila["titulo"]
            for fila in cur.execute(
                """
                SELECT titulo FROM informe_v2_laminas_fotograficas
                WHERE expediente_id = ?
                ORDER BY orden ASC, id ASC
                """,
                (expediente_id,),
            ).fetchall()
        ]
        relaciones_huerfanas = cur.execute(
            "SELECT COUNT(*) AS total FROM informe_v2_lamina_fotos WHERE lamina_id = ?",
            (segunda_id,),
        ).fetchone()["total"]
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response_mover.status_code == 303
    assert response_eliminar.status_code == 303
    assert titulos == ["Primera lámina"]
    assert relaciones_huerfanas == 0


def test_informe_v2_editor_muestra_bloque_laminas_fotograficas(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_editor")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        for indice in range(2):
            _, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_editor_{expediente_id}_{indice}.jpg",
                f"Foto editor {indice + 1}",
            )
            rutas.append(ruta)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/expedientes/{expediente_id}/informe-v2-editor")
    finally:
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "Láminas comparativas" in response.text
    assert "Crear lámina" in response.text
    assert "Antes / Después" in response.text
    assert "Foto editor 1" in response.text


def test_pdf_v2_renderiza_laminas_sin_romper_anexos_b_c_ni_originales(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_pdf")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(4):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_pdf_{expediente_id}_{indice}.jpg",
                f"Foto PDF {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        original_bytes = rutas[0].read_bytes()
        ok_1, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Comparativa de daños y reparación",
            "Secuencia fotográfica del expediente",
            "cuatro_fotos",
            fotos,
        )
        ok_2, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Antes y después",
            "",
            "antes_despues",
            fotos[:2],
        )
        assert ok_1 and ok_2
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return _pdf_simple_bytes(2)

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe")
        html = capturado["html"]
        contexto = capturado["contexto"]
        original_actual = rutas[0].read_bytes()
    finally:
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "ANEXO A. REPORTAJE FOTOGRÁFICO DE PATOLOGÍAS" in html
    assert "ANEXO A. LÁMINAS COMPARATIVAS" in html
    assert "Comparativa de daños y reparación" in html
    assert "Antes" in html
    assert "Después" in html
    assert "ANEXO B. FICHAS DE DAÑOS POR ESTANCIA" in html
    assert len(contexto["anexos"]["laminas_fotograficas"]) == 2
    assert original_actual == original_bytes
    from pypdf import PdfReader

    texto_primera = PdfReader(BytesIO(response.content)).pages[0].extract_text()
    assert "Página 1 de" in texto_primera


def test_informe_v2_laminas_edita_pie_y_observacion(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_edita_pie")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(2):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_edita_pie_{expediente_id}_{indice}.jpg",
                f"Foto editable {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        ok, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Lámina con pies editables",
            "",
            "comparativa_2",
            fotos,
        )
        assert ok
        relacion_id = cur.execute(
            "SELECT id FROM informe_v2_lamina_fotos ORDER BY id ASC LIMIT 1",
        ).fetchone()["id"]
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas/fotos/{relacion_id}/actualizar",
        data={
            "pie_foto": "Desprendimiento de piezas cerámicas en fachada.",
            "observacion": "Existía riesgo de caída sobre la vía pública.",
        },
        follow_redirects=False,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        fila = cur.execute(
            "SELECT pie_foto, observacion FROM informe_v2_lamina_fotos WHERE id = ?",
            (relacion_id,),
        ).fetchone()
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response.status_code == 303
    assert fila["pie_foto"] == "Desprendimiento de piezas cerámicas en fachada."
    assert fila["observacion"] == "Existía riesgo de caída sobre la vía pública."


def test_informe_v2_laminas_crea_layouts_v2_antes_despues_y_cronologica(
    isolated_import,
):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_layouts_v2")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(4):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_layout_v2_{expediente_id}_{indice}.jpg",
                f"Foto layout V2 {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response_antes = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas",
        data={
            "titulo": "Antes después V2",
            "layout": "antes_despues",
            "foto_ids": [str(fotos[0]), str(fotos[1])],
        },
        follow_redirects=False,
    )
    response_crono = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas",
        data={
            "titulo": "Cronológica V2",
            "layout": "cronologica",
            "foto_ids": [str(fotos[0]), str(fotos[1]), str(fotos[2]), str(fotos[3])],
        },
        follow_redirects=False,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        layouts = [
            fila["layout"]
            for fila in cur.execute(
                """
                SELECT layout FROM informe_v2_laminas_fotograficas
                WHERE expediente_id = ?
                ORDER BY orden ASC
                """,
                (expediente_id,),
            ).fetchall()
        ]
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response_antes.status_code == 303
    assert response_crono.status_code == 303
    assert layouts == ["antes_despues", "cronologica"]


def test_informe_v2_laminas_ordena_fotografias(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_ordena_fotos")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(3):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_ordena_foto_{expediente_id}_{indice}.jpg",
                f"Foto ordenable {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        ok, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Secuencia ordenable",
            "",
            "cronologica",
            fotos,
        )
        assert ok
        tercera_relacion = cur.execute(
            """
            SELECT id FROM informe_v2_lamina_fotos
            WHERE foto_id = ?
            """,
            (fotos[2],),
        ).fetchone()["id"]
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expedientes/{expediente_id}/informe-v2-laminas/fotos/{tercera_relacion}/mover",
        data={"direccion": "arriba"},
        follow_redirects=False,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        orden_fotos = [
            fila["foto_id"]
            for fila in cur.execute(
                """
                SELECT foto_id FROM informe_v2_lamina_fotos
                ORDER BY orden ASC, id ASC
                """
            ).fetchall()
        ]
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response.status_code == 303
    assert orden_fotos[:3] == [fotos[0], fotos[2], fotos[1]]


def test_informe_v2_laminas_compatibilidad_layouts_v1(isolated_import):
    main_module = isolated_import("app.main")
    from app.database import get_connection

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_compat_v1")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(2):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_compat_v1_{expediente_id}_{indice}.jpg",
                f"Foto compat V1 {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        cur.execute(
            """
            INSERT INTO informe_v2_laminas_fotograficas
                (expediente_id, titulo, subtitulo, tipo, layout, orden)
            VALUES (?, 'Lámina V1', '', 'comparativa', 'dos_fotos', 10)
            """,
            (expediente_id,),
        )
        lamina_id = cur.lastrowid
        for orden, foto_id in enumerate(fotos, start=1):
            cur.execute(
                """
                INSERT INTO informe_v2_lamina_fotos (lamina_id, foto_id, orden, pie_foto)
                VALUES (?, ?, ?, ?)
                """,
                (lamina_id, foto_id, orden, f"Pie V1 {orden}"),
            )
        conn.commit()
        laminas = main_module.obtener_laminas_fotograficas_informe_v2(
            cur,
            expediente_id,
        )
    finally:
        conn.close()
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert laminas[0]["layout"] == "comparativa_2"
    assert laminas[0]["layout_nombre"] == "Comparativa 2"
    assert len(laminas[0]["fotos"]) == 2


def test_pdf_v2_laminas_renderiza_subtitulo_observacion_y_paginacion(
    isolated_import,
    monkeypatch,
):
    main_module = isolated_import("app.main")
    from app.database import get_connection
    from pypdf import PdfReader

    conn = get_connection()
    rutas = []
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "pericial_laminas_pdf_v2")
        expediente_id = _crear_expediente_patologias(cur, user_id)
        fotos = []
        for indice in range(2):
            foto_id, ruta = _crear_foto_visita_para_lamina(
                main_module,
                cur,
                expediente_id,
                f"lamina_pdf_v2_{expediente_id}_{indice}.jpg",
                f"Foto PDF V2 {indice + 1}",
            )
            fotos.append(foto_id)
            rutas.append(ruta)
        original_bytes = rutas[0].read_bytes()
        ok, _ = main_module.crear_lamina_fotografica_informe_v2(
            cur,
            expediente_id,
            "Evolución del desprendimiento",
            "Dormitorio 3. Secuencia de daños",
            "antes_despues",
            fotos,
        )
        assert ok
        relacion_id = cur.execute(
            "SELECT id FROM informe_v2_lamina_fotos ORDER BY id ASC LIMIT 1",
        ).fetchone()["id"]
        main_module.actualizar_foto_lamina_informe_v2(
            cur,
            expediente_id,
            relacion_id,
            "Desprendimiento de piezas cerámicas en fachada.",
            "Existía riesgo de caída sobre la vía pública.",
        )
        conn.commit()
    finally:
        conn.close()

    capturado = {}

    def fake_pdf_bytes(request, contexto):
        capturado["contexto"] = contexto
        template = request.app.state.templates.env.get_template("informes/v2_pdf.html")
        capturado["html"] = template.render({"request": request, **contexto})
        return _pdf_simple_bytes(2)

    monkeypatch.setattr(main_module, "generar_informe_v2_pdf_bytes", fake_pdf_bytes)
    client = _autenticar_cliente(main_module, user_id)
    try:
        response = client.get(f"/generar-informe-v2-pdf/{expediente_id}?perfil=solo_informe")
        html = capturado["html"]
        texto_primera = PdfReader(BytesIO(response.content)).pages[0].extract_text()
        original_actual = rutas[0].read_bytes()
    finally:
        for ruta in rutas:
            ruta.unlink(missing_ok=True)

    assert response.status_code == 200
    assert "LÁMINA COMPARATIVA Nº 1" in html
    assert "Dormitorio 3. Secuencia de daños" in html
    assert "Desprendimiento de piezas cerámicas en fachada." in html
    assert "Existía riesgo de caída sobre la vía pública." in html
    assert "Figura 1." in html
    assert "Página 1 de" in texto_primera
    assert original_actual == original_bytes
