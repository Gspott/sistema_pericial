import json
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image


def _crear_usuario(cur, username: str = "valoracion_testigos_form"):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _crear_expediente(cur, user_id: int, numero: str, tipo_informe: str = "valoracion"):
    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, tipo_informe, destinatario,
            cliente, direccion, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            numero,
            tipo_informe,
            "particular",
            f"Cliente {numero}",
            f"Calle {numero}",
            user_id,
        ),
    )
    return cur.lastrowid


def _campo_valor(campos, etiqueta: str) -> str:
    for campo in campos:
        if campo["label"] == etiqueta:
            return campo["value"]
    raise AssertionError(f"Campo no encontrado: {etiqueta}")


def _imagen_jpeg_demo() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(210, 210, 210)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _crear_testigo_biblioteca(
    cur,
    user_id: int,
    direccion: str,
    municipio: str,
    tipologia: str,
    precio: float | None,
    superficie: float | None,
    fuente: str,
    fecha: str,
    fiabilidad: str,
    verificado: int,
):
    unitario = precio / superficie if precio and superficie else None
    cur.execute(
        """
        INSERT INTO testigos_valoracion (
            owner_user_id, direccion_testigo, municipio, provincia, tipologia,
            precio_oferta, precio_depurado, superficie_tomada,
            tipo_superficie_tomada, precio_unitario_inicial, fuente_testigo,
            fecha_testigo, fiabilidad_dato, dato_verificado, reutilizable
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            direccion,
            municipio,
            "Madrid",
            tipologia,
            precio,
            precio - 5000 if precio else None,
            superficie,
            "construida",
            unitario,
            fuente,
            fecha,
            fiabilidad,
            verificado,
            1,
        ),
    )
    return cur.lastrowid


def test_testigos_reutilizables_crean_vinculan_snapshot_y_no_borran_base(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id = _crear_expediente(cur, user_id, "EXP-VAL-TESTIGOS-001")
        expediente_patologias_id = _crear_expediente(
            cur,
            user_id,
            "EXP-PAT-TESTIGOS-001",
            tipo_informe="patologias",
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)

    response = client.get("/valoracion/testigos")
    assert response.status_code == 200
    assert "Biblioteca de testigos" in response.text
    assert "Biblioteca desktop" in response.text
    assert 'href="/biblioteca-patologias">Biblioteca de patologías</a>' in response.text
    assert 'href="/valoracion/testigos">Biblioteca de testigos</a>' in response.text
    assert (
        response.text.index('href="/biblioteca-patologias"')
        < response.text.index('href="/valoracion/testigos"')
    )

    response = client.get("/valoracion/testigos/nuevo")
    assert response.status_code == 200
    assert "Nuevo testigo" in response.text

    response = client.post(
        "/valoracion/testigos/nuevo",
        data={
            "direccion_testigo": "Calle Testigo Reutilizable 1",
            "referencia_testigo": "REF-001",
            "fuente_testigo": "Portal demo",
            "url_fuente": "https://example.invalid/testigo",
            "fecha_testigo": "2026-05-26",
            "codigo_postal": "28000",
            "municipio": "Madrid",
            "provincia": "Madrid",
            "precio_oferta": "210000",
            "precio_cierre": "205000",
            "superficie_construida": "90",
            "superficie_util": "80",
            "superficie_otros_usos": "4",
            "valor_unitario": "2333.33",
            "tipologia": "Vivienda",
            "planta": "2",
            "dormitorios": "3",
            "banos": "2",
            "aseos": "1",
            "ascensor": "1",
            "garaje": "1",
            "trastero": "1",
            "terraza": "1",
            "estado_conservacion": "Buen estado",
            "antiguedad": "15 años",
            "calidad_constructiva": "Media",
            "caracteristicas_constructivas": "Edificio plurifamiliar",
            "ubicacion": "Barrio residencial",
            "visitado": "1",
            "validacion_estado": "validado",
            "reutilizable": "1",
            "observaciones": "Testigo demo sin datos reales.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        testigo = cur.execute(
            "SELECT * FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    assert testigo is not None
    testigo_id = testigo["id"]
    assert testigo["direccion_testigo"] == "Calle Testigo Reutilizable 1"
    assert testigo["reutilizable"] == 1

    response = client.get(f"/valoracion/testigos/{testigo_id}/editar")
    assert response.status_code == 200
    assert "Calle Testigo Reutilizable 1" in response.text
    assert "testigo-edit-wide" in response.text
    assert "Ver detalle" in response.text
    assert "Año de construcción" in response.text

    response = client.post(
        f"/valoracion/testigos/{testigo_id}/editar",
        data={
            "direccion_testigo": "Calle Testigo Reutilizable Editado",
            "referencia_testigo": "REF-001",
            "fuente_testigo": "Portal demo actualizado",
            "fecha_testigo": "2026-05-26",
            "codigo_postal": "28000",
            "municipio": "Madrid",
            "provincia": "Madrid",
            "precio_oferta": "215000",
            "superficie_construida": "90",
            "superficie_util": "82",
            "valor_unitario": "2388.89",
            "tipologia": "Vivienda",
            "planta": "4ª",
            "banos": "2",
            "ascensor": "1",
            "es_exterior": "1",
            "balcon": "1",
            "terraza": "1",
            "patio": "1",
            "ano_construccion": "1978",
            "ano_reforma": "2021",
            "aire_acondicionado": "1",
            "tipo_calefaccion": "Individual gas",
            "estado_conservacion": "Buen estado",
            "certificacion_energetica": "D",
            "garaje": "1",
            "trastero": "1",
            "validacion_estado": "validado",
            "reutilizable": "1",
            "observaciones": "Editado antes de vincular.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        testigo_editado = cur.execute(
            "SELECT * FROM testigos_valoracion WHERE id = ?",
            (testigo_id,),
        ).fetchone()
    finally:
        conn.close()
    assert testigo_editado["superficie_util"] == 82
    assert testigo_editado["planta"] == "4ª"
    assert testigo_editado["ascensor"] == 1
    assert testigo_editado["es_exterior"] == 1
    assert testigo_editado["balcon"] == 1
    assert testigo_editado["terraza"] == 1
    assert testigo_editado["patio"] == 1
    assert testigo_editado["ano_construccion"] == 1978
    assert testigo_editado["ano_reforma"] == 2021
    assert testigo_editado["aire_acondicionado"] == 1
    assert testigo_editado["tipo_calefaccion"] == "Individual gas"
    assert testigo_editado["certificacion_energetica"] == "D"
    assert testigo_editado["garaje"] == 1
    assert testigo_editado["trastero"] == 1

    response = client.get("/valoracion/testigos?q=Editado")
    assert response.status_code == 200
    assert "Calle Testigo Reutilizable Editado" in response.text
    assert "215.000 €" in response.text
    assert "90,00 m²" in response.text
    assert "2.389 €/m²" in response.text
    assert "Abrir fuente" not in response.text

    response = client.get(
        "/valoracion/testigos?tipologia=Vivienda&municipio=Madrid"
        "&validacion=validado&reutilizable=1"
    )
    assert response.status_code == 200
    assert "Calle Testigo Reutilizable Editado" in response.text

    response = client.get(f"/valoracion/testigos/{testigo_id}")
    assert response.status_code == 200
    assert "Detalle de testigo" in response.text
    assert "testigo-detalle-wide" in response.text
    assert "215.000 €" in response.text
    assert "90,00 m²" in response.text
    assert "2.389 €/m²" in response.text
    assert "Uso en expedientes" in response.text

    response = client.post(
        f"/valoracion/testigos/{testigo_id}/fotos",
        data={
            "descripcion": "Captura ficticia del anuncio",
            "origen": "manual",
        },
        files={
            "fotos": (
                "testigo-demo.jpg",
                _imagen_jpeg_demo(),
                "image/jpeg",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        foto = cur.execute(
            """
            SELECT *
            FROM testigos_valoracion_fotos
            WHERE testigo_id = ?
            """,
            (testigo_id,),
        ).fetchone()
    finally:
        conn.close()
    assert foto is not None
    assert foto["descripcion"] == "Captura ficticia del anuncio"
    assert foto["origen"] == "manual"

    response = client.get(f"/valoracion/testigos/{testigo_id}")
    assert response.status_code == 200
    assert "Captura ficticia del anuncio" in response.text
    assert "Ver foto" in response.text
    assert "testigo-gallery" in response.text

    response = client.get("/valoracion/testigos")
    assert response.status_code == 200
    assert "/uploads/" in response.text
    assert "Foto del testigo Calle Testigo Reutilizable Editado" in response.text

    response = client.get(
        f"/expedientes/{expediente_id}/valoracion/testigos?q=Editado"
    )
    assert response.status_code == 200
    assert "Calle Testigo Reutilizable Editado" in response.text

    response = client.get(
        f"/expedientes/{expediente_id}/valoracion/testigos?q=SinCoincidencias"
    )
    assert response.status_code == 200
    assert "Calle Testigo Reutilizable Editado" not in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/anadir",
        data={
            "testigo_id": str(testigo_id),
            "notas_seleccion": "Seleccionado por proximidad.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        vinculo = cur.execute(
            """
            SELECT *
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()
    finally:
        conn.close()
    assert vinculo is not None
    assert vinculo["testigo_id"] == testigo_id
    assert vinculo["incluido"] == 1
    snapshot = json.loads(vinculo["snapshot_json"])
    assert snapshot["direccion_testigo"] == "Calle Testigo Reutilizable Editado"
    assert snapshot["fuente_testigo"] == "Portal demo actualizado"

    contexto = build_informe_context(expediente_id)
    assert len(contexto["comparables_valoracion"]) == 1
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["origen"] == "modelo_nuevo"
    assert comparable["orden"] == 1
    assert comparable["incluido"] == 1
    assert comparable["notas_seleccion"] == "Seleccionado por proximidad."
    assert comparable["snapshot"]["direccion_testigo"] == (
        "Calle Testigo Reutilizable Editado"
    )
    assert _campo_valor(comparable["campos"], "Dirección") == (
        "Calle Testigo Reutilizable Editado"
    )

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo['id']}/actualizar",
        data={
            "orden": "2",
            "incluido": "1",
            "notas_seleccion": "Orden revisado.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    contexto = build_informe_context(expediente_id)
    comparable = contexto["comparables_valoracion"][0]
    assert comparable["orden"] == 2
    assert comparable["notas_seleccion"] == "Orden revisado."

    response = client.get(f"/expedientes/{expediente_id}/valoracion/testigos")
    assert response.status_code == 200
    assert "Valor unitario base:</strong> 2.389 €/m²" in response.text
    assert "Coeficiente total:</strong> —" in response.text
    assert f"/valoracion/testigos/biblioteca?expediente_id={expediente_id}" in response.text
    assert "Workbench de valoración" in response.text
    assert f"/expediente/{expediente_id}/valoracion/workbench" in response.text
    assert (
        "Análisis técnico de comparables, homogeneización y ponderación"
        in response.text
    )
    assert "danger-secondary" in response.text

    response = client.get(f"/informes/{expediente_id}/imprimir")
    assert response.status_code == 200
    assert "215.000 €" in response.text
    assert "2.389 €/m²" in response.text
    assert "90,00 m²" in response.text
    assert "TESTIGOS COMPARABLES" not in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/{vinculo['id']}/quitar",
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        testigo_base = cur.execute(
            "SELECT * FROM testigos_valoracion WHERE id = ?",
            (testigo_id,),
        ).fetchone()
        vinculos = cur.execute(
            "SELECT COUNT(*) FROM valoracion_expediente_testigos WHERE expediente_id = ?",
            (expediente_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert testigo_base is not None
    assert vinculos == 0

    response_patologias = client.get(f"/detalle-expediente/{expediente_patologias_id}")
    assert response_patologias.status_code == 200
    assert "Testigos de valoración" not in response_patologias.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        otro_user_id = _crear_usuario(cur, "valoracion_testigos_form_otro")
        cur.execute(
            """
            INSERT INTO testigos_valoracion (
                owner_user_id, direccion_testigo, reutilizable
            )
            VALUES (?, ?, ?)
            """,
            (otro_user_id, "Calle Testigo Otro Usuario", 1),
        )
        otro_testigo_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    response = client.get(f"/valoracion/testigos/{otro_testigo_id}")
    assert response.status_code == 404


def test_fotos_testigo_rechazan_extension_invalida(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_foto_invalida")
        testigo_id = _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Foto Inválida",
            "Madrid",
            "Piso",
            210000,
            84,
            "Idealista",
            "2026-06-02",
            "media",
            0,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/valoracion/testigos/{testigo_id}")
    assert response.status_code == 200
    assert "Evidencias auxiliares subidas manualmente" in response.text

    response = client.post(
        f"/valoracion/testigos/{testigo_id}/fotos",
        files={
            "fotos": (
                "captura.txt",
                BytesIO(b"no es una imagen"),
                "text/plain",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "extensi" in response.headers["location"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion_fotos WHERE testigo_id = ?",
            (testigo_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_fotos_testigo_rechazan_testigo_ajeno(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "valoracion_testigos_foto_owner")
        otro_id = _crear_usuario(cur, "valoracion_testigos_foto_otro")
        testigo_id = _crear_testigo_biblioteca(
            cur,
            owner_id,
            "Calle Foto Ajena",
            "Madrid",
            "Piso",
            230000,
            90,
            "Fotocasa",
            "2026-06-02",
            "alta",
            1,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, otro_id)
    response = client.post(
        f"/valoracion/testigos/{testigo_id}/fotos",
        files={
            "fotos": (
                "testigo-ajeno.jpg",
                _imagen_jpeg_demo(),
                "image/jpeg",
            )
        },
        follow_redirects=False,
    )
    assert response.status_code == 404

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion_fotos WHERE testigo_id = ?",
            (testigo_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_biblioteca_desktop_testigos_render_filtros_y_ordenacion(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_biblioteca")
        _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Centro",
            "Madrid",
            "Vivienda",
            300000,
            100,
            "Portal A",
            "2026-05-20",
            "alta",
            1,
        )
        _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Norte",
            "Alcobendas",
            "Local",
            180000,
            120,
            "Portal B",
            "2026-05-22",
            "media",
            0,
        )
        _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Incompleta",
            "Madrid",
            "Vivienda",
            None,
            None,
            "",
            "",
            "",
            0,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get("/valoracion/testigos/biblioteca")
    assert response.status_code == 200
    assert "testigos-desktop" in response.text
    assert "Biblioteca desktop de testigos" in response.text
    assert "Total testigos" in response.text
    assert "Calle Biblioteca Centro" in response.text
    assert "Calle Biblioteca Norte" in response.text
    assert "Calle Biblioteca Incompleta" in response.text
    assert "No guarda pesos, inclusión ni representatividad" in response.text
    assert "Nuevo testigo rápido" in response.text
    assert "/valoracion/testigos/biblioteca/nuevo" in response.text

    response = client.get(
        "/valoracion/testigos/biblioteca?municipio=Madrid&tipologia=Vivienda"
        "&fuente=Portal+A&fiabilidad=alta&verificacion=1"
    )
    assert response.status_code == 200
    assert "Calle Biblioteca Centro" in response.text
    assert "Calle Biblioteca Norte" not in response.text
    assert "Calle Biblioteca Incompleta" not in response.text

    response = client.get("/valoracion/testigos/biblioteca?ordenar=unitario&dir=desc")
    assert response.status_code == 200
    assert response.text.index("Calle Biblioteca Centro") < response.text.index(
        "Calle Biblioteca Norte"
    )

    response = client.get("/valoracion/testigos/biblioteca?ordenar=nope&dir=sideways")
    assert response.status_code == 200
    assert "La ordenación solicitada no existe" in response.text

    response = client.get("/valoracion/testigos/biblioteca?incompletos=1")
    assert response.status_code == 200
    assert "Calle Biblioteca Incompleta" in response.text
    assert "Calle Biblioteca Centro" not in response.text


def test_biblioteca_desktop_testigos_estado_vacio(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_biblioteca_empty")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get("/valoracion/testigos/biblioteca")
    assert response.status_code == 200
    assert "No hay testigos en la biblioteca con los filtros actuales." in response.text
    assert "Crear primer testigo" in response.text


def test_biblioteca_desktop_vincula_testigo_a_expediente(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_bib_vincula")
        expediente_id = _crear_expediente(cur, user_id, "EXP-VAL-BIB-VINCULA")
        testigo_id = _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Vinculable",
            "Madrid",
            "Piso",
            240000,
            96,
            "Idealista",
            "2026-06-02",
            "alta",
            1,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/valoracion/testigos/biblioteca?expediente_id={expediente_id}")
    assert response.status_code == 200
    assert "Añadir a este expediente" in response.text

    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/biblioteca/{testigo_id}/vincular",
        data={"return_to": "seleccion"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(
        f"/expedientes/{expediente_id}/valoracion/testigos"
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        vinculo = cur.execute(
            """
            SELECT *
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigo_id),
        ).fetchone()
        testigo = cur.execute(
            "SELECT * FROM testigos_valoracion WHERE id = ?",
            (testigo_id,),
        ).fetchone()
    finally:
        conn.close()

    assert vinculo is not None
    assert vinculo["incluido"] == 1
    assert vinculo["incluido_calculo"] == 1
    assert vinculo["peso_porcentaje"] is None
    assert vinculo["representatividad"] == ""
    assert "Calle Biblioteca Vinculable" in vinculo["snapshot_json"]
    assert vinculo["notas_seleccion"] == "Vinculado desde biblioteca desktop."
    assert testigo["direccion_testigo"] == "Calle Biblioteca Vinculable"

    response = client.get(f"/valoracion/testigos/biblioteca?expediente_id={expediente_id}")
    assert response.status_code == 200
    assert "Ya vinculado" in response.text


def test_biblioteca_desktop_vinculo_duplicado_no_crea_segundo(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_bib_duplicado")
        expediente_id = _crear_expediente(cur, user_id, "EXP-VAL-BIB-DUP")
        testigo_id = _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Duplicada",
            "Madrid",
            "Piso",
            220000,
            88,
            "Fotocasa",
            "2026-06-02",
            "media",
            0,
        )
        cur.execute(
            """
            INSERT INTO valoracion_expediente_testigos (
                expediente_id, testigo_id, orden, incluido, snapshot_json
            )
            VALUES (?, ?, 1, 1, ?)
            """,
            (
                expediente_id,
                testigo_id,
                json.dumps({"direccion_testigo": "Calle Biblioteca Duplicada"}),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expedientes/{expediente_id}/valoracion/testigos/biblioteca/{testigo_id}/vincular",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "ya%20est" in response.headers["location"]

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            """
            SELECT COUNT(*)
            FROM valoracion_expediente_testigos
            WHERE expediente_id = ? AND testigo_id = ?
            """,
            (expediente_id, testigo_id),
        ).fetchone()[0]
    finally:
        conn.close()

    assert total == 1


def test_biblioteca_desktop_vinculo_rechaza_no_valoracion_y_testigo_inexistente(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_bib_rechazos")
        expediente_patologias_id = _crear_expediente(
            cur,
            user_id,
            "EXP-PAT-BIB-RECHAZO",
            tipo_informe="patologias",
        )
        expediente_valoracion_id = _crear_expediente(
            cur,
            user_id,
            "EXP-VAL-BIB-RECHAZO",
        )
        testigo_id = _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Biblioteca Rechazo",
            "Madrid",
            "Piso",
            230000,
            90,
            "Idealista",
            "2026-06-02",
            "alta",
            1,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        f"/expedientes/{expediente_patologias_id}/valoracion/testigos/biblioteca/{testigo_id}/vincular",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(
        f"/detalle-expediente/{expediente_patologias_id}"
    )

    response = client.post(
        f"/expedientes/{expediente_valoracion_id}/valoracion/testigos/biblioteca/999999/vincular",
        follow_redirects=False,
    )
    assert response.status_code == 404

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM valoracion_expediente_testigos"
        ).fetchone()[0]
    finally:
        conn.close()

    assert total == 0


def test_alta_rapida_desktop_testigo_get_y_post_valido(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_rapido")
        expediente_id = _crear_expediente(cur, user_id, "EXP-VAL-RAPIDO")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(
        f"/valoracion/testigos/biblioteca/nuevo?expediente_id={expediente_id}"
    )
    assert response.status_code == 200
    assert "Nuevo testigo rápido" in response.text
    assert "quick-testigo" in response.text
    assert "quick-assist" in response.text
    assert "Pegado asistido desde anuncio" in response.text
    assert "Características" in response.text
    assert "Estado y calidades" in response.text
    assert "Equipamiento" in response.text
    assert "Idealista" in response.text
    assert f"/expedientes/{expediente_id}/valoracion/testigos" in response.text

    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "expediente_id": str(expediente_id),
            "fuente_tipo": "Idealista",
            "fuente_testigo": "",
            "url_fuente": "https://example.invalid/anuncio-rapido",
            "fecha_captura": "2026-06-02",
            "referencia_testigo": "Piso rápido desde portal",
            "direccion_testigo": "Calle Alta Rápida 1",
            "codigo_postal": "28080",
            "municipio": "Madrid",
            "provincia": "Madrid",
            "tipologia": "Piso",
            "precio_oferta": "250000",
            "precio_depurado": "240000",
            "superficie_tomada": "96",
            "tipo_superficie_tomada": "construida",
            "superficie_construida": "96",
            "superficie_util": "82",
            "fecha_testigo": "2026-06-02",
            "banos": "2",
            "planta": "4ª",
            "ascensor": "1",
            "es_exterior": "1",
            "balcon": "1",
            "terraza": "1",
            "patio": "1",
            "ano_construccion": "1960",
            "ano_reforma": "2020",
            "aire_acondicionado": "1",
            "tipo_calefaccion": "Individual eléctrica",
            "estado_conservacion": "reformado",
            "certificacion_energetica": "C",
            "garaje": "1",
            "trastero": "1",
            "fiabilidad_dato": "alta",
            "dato_verificado": "1",
            "observaciones": "Alta rápida ficticia.",
            "accion": "guardar",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/valoracion/testigos/")

    conn = get_connection()
    try:
        cur = conn.cursor()
        testigo = cur.execute(
            """
            SELECT *
            FROM testigos_valoracion
            WHERE owner_user_id = ? AND direccion_testigo = ?
            """,
            (user_id, "Calle Alta Rápida 1"),
        ).fetchone()
    finally:
        conn.close()

    assert testigo is not None
    assert testigo["fuente_testigo"] == "Idealista"
    assert testigo["referencia_testigo"] == "Piso rápido desde portal"
    assert testigo["precio_unitario_inicial"] == 2500
    assert testigo["dato_verificado"] == 1
    assert testigo["codigo_postal"] == "28080"
    assert testigo["superficie_construida"] == 96
    assert testigo["superficie_util"] == 82
    assert testigo["banos"] == 2
    assert testigo["planta"] == "4ª"
    assert testigo["ascensor"] == 1
    assert testigo["es_exterior"] == 1
    assert testigo["balcon"] == 1
    assert testigo["terraza"] == 1
    assert testigo["patio"] == 1
    assert testigo["ano_construccion"] == 1960
    assert testigo["ano_reforma"] == 2020
    assert testigo["aire_acondicionado"] == 1
    assert testigo["tipo_calefaccion"] == "Individual eléctrica"
    assert testigo["estado_conservacion"] == "reformado"
    assert testigo["certificacion_energetica"] == "C"
    assert testigo["garaje"] == 1
    assert testigo["trastero"] == 1


def test_alta_rapida_desktop_guardar_crear_otro_y_volver(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_rapido_acciones")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    data = {
        "fuente_tipo": "Fotocasa",
        "direccion_testigo": "Calle Acción Rápida",
        "municipio": "Valencia",
        "provincia": "Valencia",
        "precio_oferta": "180000",
        "superficie_tomada": "90",
        "accion": "crear_otro",
    }
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data=data,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(
        "/valoracion/testigos/biblioteca/nuevo"
    )

    data["direccion_testigo"] = "Calle Acción Biblioteca"
    data["municipio"] = "Sevilla"
    data["precio_oferta"] = "260000"
    data["superficie_tomada"] = "130"
    data["accion"] = "volver_biblioteca"
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data=data,
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/valoracion/testigos/biblioteca")


def test_alta_rapida_desktop_invalido_muestra_error_controlado(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_rapido_invalido")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "fuente_tipo": "Otro",
            "fuente_testigo": "",
            "url_fuente": "nota-url",
            "precio_oferta": "precio-raro",
            "superficie_tomada": "0",
            "accion": "volver_biblioteca",
        },
    )
    assert response.status_code == 200
    assert "Precio oferta debe ser numérico." in response.text
    assert "La superficie tomada debe ser mayor que cero." in response.text
    assert "La URL del anuncio debe empezar por http:// o https://." in response.text
    assert "Fuente no informada" in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_pegado_asistido_detecta_precio_superficie_y_portal(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_pegado")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    texto = """
    Piso reformado con terraza en Valencia
    Anuncio publicado en Fotocasa
    Precio 245.000 €
    98 m² construidos
    82 m² útiles
    3 habitaciones y 2 baños
    4ª planta exterior con ascensor, balcón, terraza y patio
    Construido en 1960. Reformado en 2020.
    Aire acondicionado
    Calefacción individual: eléctrica
    Certificado energético: C
    2.500 €/m²
    """
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "texto_anuncio_bruto": texto,
            "accion": "analizar_texto",
        },
    )

    assert response.status_code == 200
    assert "Previsualización detectada" in response.text
    assert "Confianza alta" in response.text
    assert 'value="245000"' in response.text
    assert 'value="98"' in response.text
    assert "Fotocasa" in response.text
    assert "2.500 €/m²" in response.text
    assert "3 habitaciones detectadas; 2 baños detectados." in response.text
    assert 'value="82"' in response.text
    assert 'value="2"' in response.text
    assert 'value="4ª"' in response.text
    assert 'id="ascensor" name="ascensor" type="checkbox" value="1" checked' in response.text
    assert 'id="es_exterior" name="es_exterior" type="checkbox" value="1" checked' in response.text
    assert 'id="balcon" name="balcon" type="checkbox" value="1" checked' in response.text
    assert 'id="aire_acondicionado" name="aire_acondicionado" type="checkbox" value="1" checked' in response.text
    assert 'value="1960"' in response.text
    assert 'value="2020"' in response.text
    assert 'value="eléctrica"' in response.text
    assert 'value="C"' in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 0


def test_pegado_asistido_sin_datos_no_rompe(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_pegado_vacio")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "texto_anuncio_bruto": "Texto comercial sin datos numéricos claros.",
            "accion": "analizar_texto",
        },
    )

    assert response.status_code == 200
    assert "Confianza baja" in response.text
    assert "No se ha detectado un precio claro." in response.text
    assert "No se ha detectado una superficie clara." in response.text


def test_alta_rapida_sin_duplicados_crea_normal(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_sin_duplicado")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "fuente_tipo": "Idealista",
            "url_fuente": "https://example.invalid/unico",
            "referencia_testigo": "Anuncio único",
            "direccion_testigo": "Calle Sin Duplicado",
            "municipio": "Madrid",
            "precio_oferta": "210000",
            "superficie_tomada": "90",
            "accion": "guardar",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 1


def test_alta_rapida_duplicado_url_avisa_y_confirmacion_guarda(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_duplicado_url")
        testigo_id = _crear_testigo_biblioteca(
            cur,
            user_id,
            "Calle Duplicado URL",
            "Madrid",
            "Piso",
            230000,
            92,
            "Idealista",
            "2026-06-02",
            "alta",
            1,
        )
        cur.execute(
            """
            UPDATE testigos_valoracion
            SET url_fuente = ?, referencia_testigo = ?
            WHERE id = ?
            """,
            (
                "https://example.invalid/duplicado",
                "Piso duplicado URL",
                testigo_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    data = {
        "fuente_tipo": "Idealista",
        "url_fuente": "https://example.invalid/duplicado",
        "referencia_testigo": "Piso duplicado URL",
        "direccion_testigo": "Calle Duplicado URL 2",
        "municipio": "Madrid",
        "precio_oferta": "231000",
        "superficie_tomada": "92",
        "accion": "guardar",
    }
    response = client.post("/valoracion/testigos/biblioteca/nuevo", data=data)
    assert response.status_code == 200
    assert "Posibles testigos duplicados." in response.text
    assert "Misma URL del anuncio." in response.text
    assert "Guardar de todos modos" in response.text

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 1

    data["accion"] = "guardar_confirmado"
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data=data,
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute(
            "SELECT COUNT(*) FROM testigos_valoracion WHERE owner_user_id = ?",
            (user_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    assert total == 2


def test_alta_rapida_duplicado_precio_superficie_avisa(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur, "valoracion_testigos_duplicado_similar")
        _crear_testigo_biblioteca(
            cur,
            user_id,
            "Zona Similar",
            "Valencia",
            "Piso",
            200000,
            100,
            "Fotocasa",
            "2026-06-02",
            "media",
            0,
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.post(
        "/valoracion/testigos/biblioteca/nuevo",
        data={
            "fuente_tipo": "Pisos.com",
            "direccion_testigo": "Otra zona cercana",
            "municipio": "Valencia",
            "precio_oferta": "204000",
            "superficie_tomada": "102",
            "accion": "guardar",
        },
    )

    assert response.status_code == 200
    assert "Posibles testigos duplicados." in response.text
    assert "Mismo municipio con precio y superficie parecidos." in response.text


def test_testigos_legacy_siguen_como_fallback_sin_vinculos_nuevos(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import build_informe_context

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        expediente_id = _crear_expediente(cur, user_id, "EXP-VAL-LEGACY-TESTIGOS")
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_id,
                "2026-05-26",
                "Tecnico Smoke",
                "Visita legacy.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, valor_unitario
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                visita_id,
                "Calle Comparable Legacy",
                "Portal legacy",
                "2200 EUR/m2",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/detalle-expediente/{expediente_id}")
    assert response.status_code == 200
    assert "Testigos de valoración" in response.text

    contexto = build_informe_context(expediente_id)
    assert len(contexto["comparables_valoracion"]) == 1
    assert contexto["comparables_valoracion"][0]["origen"] == "legacy"
    assert (
        _campo_valor(contexto["comparables_valoracion"][0]["campos"], "Dirección")
        == "Calle Comparable Legacy"
    )
