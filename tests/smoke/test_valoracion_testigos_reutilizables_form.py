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
            "valor_unitario": "2388.89",
            "tipologia": "Vivienda",
            "estado_conservacion": "Buen estado",
            "validacion_estado": "validado",
            "reutilizable": "1",
            "observaciones": "Editado antes de vincular.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

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
