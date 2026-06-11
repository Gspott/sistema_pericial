from fastapi.testclient import TestClient


BC3_MINIMO = """~C|01||Demoliciones|0|
~C|01.01|m2|Picado de revestimiento deteriorado|18,00|
~C|MOOA.8a|h|Oficial 1ª construcción|24,00|
~C|PBUW.8a|kg|Mortero de reparación|3,00|
~D|01.01|MOOA.8a|0,500|24,00|12,00|PBUW.8a|2,000|3,00|6,00|
~T|01.01|Texto descriptivo de la partida importada desde BC3.
~K|registro no soportado para smoke|
"""


def _crear_usuario(cur, username: str) -> int:
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Tecnico", "Costes", "", username, "hash-demo"),
    )
    return cur.lastrowid


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def test_bc3_parser_minimo_extrae_conceptos_descompuestos_y_textos(isolated_import):
    parser = isolated_import("app.services.bc3_parser")

    resultado = parser.parsear_bc3_desde_texto(BC3_MINIMO)

    assert resultado["version_parser"] == "costes-3"
    assert resultado["estadisticas"]["conceptos"] == 4
    assert resultado["estadisticas"]["descompuestos"] == 2
    conceptos = {item["codigo"]: item for item in resultado["conceptos"]}
    assert conceptos["01.01"]["unidad"] == "m2"
    assert conceptos["01.01"]["precio"] == 18.0
    assert "Texto descriptivo" in conceptos["01.01"]["descripcion"]
    assert resultado["descompuestos"][0]["codigo_padre"] == "01.01"
    assert resultado["descompuestos"][0]["codigo_hijo"] == "MOOA.8a"
    assert resultado["descompuestos"][0]["importe"] == 12.0
    assert any("no soportado" in aviso for aviso in resultado["advertencias"])


def test_costes_bc3_importa_base_fuente_conceptos_y_evita_duplicados(isolated_import):
    main_module = isolated_import("app.main")

    from app.config import UPLOAD_DIR
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_bc3_owner")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get("/costes/bc3/importar")
    assert response.status_code == 200
    assert "Importar BC3" in response.text

    response = client.post(
        "/costes/bc3/importar",
        data={
            "base_id": "",
            "base_nombre": "Base BC3 smoke",
            "descripcion": "Importación BC3 smoke",
            "fecha_base": "2026-06-05",
            "provincia": "Valencia",
            "observaciones": "Fixture mínimo",
        },
        files={"archivo": ("smoke.bc3", BC3_MINIMO.encode("cp1252"), "text/plain")},
    )
    assert response.status_code == 200
    assert "BC3 importado" in response.text
    assert "Conceptos importados" in response.text

    conn = get_connection()
    try:
        base = conn.execute(
            "SELECT * FROM costes_bases WHERE nombre = ?",
            ("Base BC3 smoke",),
        ).fetchone()
        assert base is not None
        assert base["origen"] == "bc3"
        fuente = conn.execute(
            """
            SELECT *
            FROM costes_fuentes
            WHERE base_id = ? AND tipo_fuente = 'bc3'
            ORDER BY id DESC
            LIMIT 1
            """,
            (base["id"],),
        ).fetchone()
        assert fuente is not None
        assert fuente["archivo_original"].startswith("costes/bc3/")
        assert (UPLOAD_DIR / fuente["archivo_original"]).exists()
        conceptos = conn.execute(
            """
            SELECT *
            FROM costes_conceptos
            WHERE base_id = ?
            ORDER BY codigo
            """,
            (base["id"],),
        ).fetchall()
        assert len(conceptos) == 3
        assert {item["estado"] for item in conceptos} == {"borrador"}
        partida = next(item for item in conceptos if item["codigo"] == "01.01")
        assert partida["descripcion"].startswith("Texto descriptivo")
        assert partida["provincia"] == "Valencia"
        descompuestos = conn.execute(
            """
            SELECT *
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            ORDER BY orden
            """,
            (partida["id"],),
        ).fetchall()
        assert len(descompuestos) == 2
        assert descompuestos[0]["codigo"] == "MOOA.8a"
        assert descompuestos[0]["importe"] == 12.0
        base_id = base["id"]
    finally:
        conn.close()

    response = client.get("/costes/bc3/importaciones")
    assert response.status_code == 200
    assert "Importaciones BC3" in response.text
    response = client.get(f"/costes/bc3/importaciones/{fuente['id']}")
    assert response.status_code == 200
    assert "Base BC3 smoke" in response.text

    response = client.post(
        "/costes/bc3/importar",
        data={
            "base_id": str(base_id),
            "base_nombre": "",
            "descripcion": "Importación BC3 duplicada",
            "fecha_base": "2026-06-05",
            "provincia": "Valencia",
            "observaciones": "Duplicado",
        },
        files={"archivo": ("smoke.bc3", BC3_MINIMO.encode("utf-8"), "text/plain")},
    )
    assert response.status_code == 200
    assert "Duplicados saltados" in response.text

    conn = get_connection()
    try:
        total_conceptos = conn.execute(
            "SELECT COUNT(*) AS total FROM costes_conceptos WHERE base_id = ?",
            (base_id,),
        ).fetchone()["total"]
        assert total_conceptos == 3
        total_descompuestos = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM costes_descompuestos d
            JOIN costes_conceptos c ON c.id = d.concepto_padre_id
            WHERE c.base_id = ?
            """,
            (base_id,),
        ).fetchone()["total"]
        assert total_descompuestos == 2
    finally:
        conn.close()
