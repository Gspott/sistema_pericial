from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image


def _crear_usuario(cur):
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Smoke", "", "valoracion_nueva_visita_ux", "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _imagen_jpeg_demo() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color=(220, 220, 220)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_nueva_visita_valoracion_muestra_solo_bloques_de_visita_fisica(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-VAL-NV-UX",
                "valoracion",
                "particular",
                "Cliente Valoracion Nueva Visita",
                "Calle Valoracion Nueva Visita",
                user_id,
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
                "2026-05-26",
                "Tecnico Smoke",
                "Observaciones esenciales de visita.",
            ),
        )
        visita_id = cur.lastrowid
        cur.execute(
            """
                INSERT INTO valoracion_visita (
                    visita_id, finalidad_valoracion, documentacion_utilizada,
                    criterios_metodo_valoracion, condicionantes_limitaciones_valoracion
                )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                visita_id,
                "Finalidad legacy que no debe mostrarse",
                "Documentacion legacy que no debe mostrarse",
                "Metodo legacy que no debe mostrarse",
                "Limitaciones legacy que no deben mostrarse",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/nueva-visita/{expediente_id}?visita_id={visita_id}")

    assert response.status_code == 200
    html = response.text
    assert "Exterior del edificio" in html
    assert "Reforma observada" in html
    assert "Portal y contadores" in html
    assert "Observaciones del portal" in html
    assert "Observaciones del cuadro de contadores" in html
    assert "Añadir fotos de portal/contadores" in html
    assert "Datos esenciales" in html
    assert "Registro de estancias" in html
    assert f"/definir-estancias/{visita_id}" in html

    assert "Climatología" not in html
    assert "Ámbito de la visita" not in html
    assert "Finalidad legacy que no debe mostrarse" not in html
    assert "Documentacion legacy que no debe mostrarse" not in html
    assert "Metodo legacy que no debe mostrarse" not in html
    assert "Limitaciones legacy que no deben mostrarse" not in html
    assert "Comparables / testigos" not in html
    assert "Registrar patología exterior" not in html

    response = client.post(
        f"/guardar-visita/{expediente_id}",
        data={
            "visita_id": str(visita_id),
            "fecha": "2026-05-26",
            "tecnico": "Tecnico Smoke",
            "observaciones_visita": "Observaciones actualizadas.",
            "ambito_visita": "edificio_completo",
            "nivel_id": "",
            "unidad_id": "",
            "observaciones_portal": "Portal con acabado correcto.",
            "observaciones_cuadro_contadores": "Cuadro de contadores localizado.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    response = client.post(
        f"/visitas/{visita_id}/fotos",
        data={
            "categoria": "portal_contadores",
            "descripcion": "Foto demo portal contadores",
            "next": f"/nueva-visita/{expediente_id}?visita_id={visita_id}#portal-contadores",
        },
        files={
            "fotos": (
                "portal-contadores.jpg",
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
        legacy = cur.execute(
            """
            SELECT finalidad_valoracion, documentacion_utilizada,
                   criterios_metodo_valoracion, condicionantes_limitaciones_valoracion
            FROM valoracion_visita
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone()
        observaciones = cur.execute(
            """
            SELECT observaciones_portal, observaciones_cuadro_contadores
            FROM valoracion_visita_observaciones
            WHERE visita_id = ?
            """,
            (visita_id,),
        ).fetchone()
        foto = cur.execute(
            """
            SELECT categoria, descripcion
            FROM visita_fotos
            WHERE visita_id = ? AND categoria = ?
            """,
            (visita_id, "portal_contadores"),
        ).fetchone()
    finally:
        conn.close()

    assert observaciones["observaciones_portal"] == "Portal con acabado correcto."
    assert (
        observaciones["observaciones_cuadro_contadores"]
        == "Cuadro de contadores localizado."
    )
    assert foto["categoria"] == "portal_contadores"
    assert foto["descripcion"] == "Foto demo portal contadores"
    assert legacy["finalidad_valoracion"] == "Finalidad legacy que no debe mostrarse"
    assert legacy["documentacion_utilizada"] == (
        "Documentacion legacy que no debe mostrarse"
    )
    assert legacy["criterios_metodo_valoracion"] == (
        "Metodo legacy que no debe mostrarse"
    )
    assert legacy["condicionantes_limitaciones_valoracion"] == (
        "Limitaciones legacy que no deben mostrarse"
    )


def test_nueva_visita_patologias_conserva_climatologia_y_ambito(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        user_id = _crear_usuario(cur)
        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario,
                cliente, direccion, ambito_patologias, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "EXP-PAT-NV-UX",
                "patologias",
                "particular",
                "Cliente Patologias Nueva Visita",
                "Calle Patologias Nueva Visita",
                "interior_exterior",
                user_id,
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
                "2026-05-26",
                "Tecnico Smoke",
                "Visita patologias.",
            ),
        )
        visita_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, user_id)
    response = client.get(f"/nueva-visita/{expediente_id}?visita_id={visita_id}")

    assert response.status_code == 200
    assert "Climatología" in response.text
    assert "Ámbito de la visita" in response.text
    assert "Registrar patología exterior" in response.text
