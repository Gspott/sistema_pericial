import io
import subprocess
import zipfile

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.valoracion_demo_cases import crear_casos_demo_valoracion


def _autenticar_cliente(main_module, user_id: int):
    client = TestClient(main_module.app)
    client.cookies.set(
        main_module.SESSION_COOKIE_NAME,
        f"{user_id}:{main_module.sign_session_value(str(user_id))}",
    )
    return client


def _docx_text(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        return docx.read("word/document.xml").decode("utf-8")


def test_valoracion_casos_demo_validan_contexto_html_docx_y_pdf_si_disponible(
    isolated_import,
):
    main_module = isolated_import("app.main")

    from app.database import get_connection
    from app.services.informe import (
        build_informe_context,
        generar_informe_docx_editable_bytes,
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        resultado = crear_casos_demo_valoracion(cur)
        conn.commit()
    finally:
        conn.close()

    casos = resultado["casos"]
    assert [caso["slug"] for caso in casos] == [
        "piso-urbano-estandar",
        "piso-reformado-premium",
        "caso-incompleto-problematico",
        "local-comercial",
        "vivienda-unifamiliar",
    ]

    client = _autenticar_cliente(main_module, resultado["owner_user_id"])
    incompleto = None
    for caso in casos:
        contexto = build_informe_context(caso["expediente_id"], base_url="http://testserver")
        assert contexto["tipo_informe"] == "valoracion"
        assert contexto["es_valoracion"] is True
        assert len(contexto["comparables_valoracion"]) == 6
        assert all(
            comparable["origen"] == "modelo_nuevo"
            for comparable in contexto["comparables_valoracion"]
        )
        assert all(
            comparable["ajustes"].get("coeficiente_total") not in ("", None)
            for comparable in contexto["comparables_valoracion"]
        )

        response_html = client.get(f"/informes/{caso['expediente_id']}/imprimir")
        assert response_html.status_code == 200
        assert "INFORME DE VALORACIÓN INMOBILIARIA" in response_html.text
        assert "Comparables" in response_html.text
        assert "Patologías interiores" not in response_html.text

        docx_bytes = generar_informe_docx_editable_bytes(caso["expediente_id"])
        texto_docx = _docx_text(docx_bytes)
        assert docx_bytes.startswith(b"PK")
        assert "INFORME DE VALORACIÓN INMOBILIARIA" in texto_docx
        assert caso["titulo"].split()[0] in texto_docx or "Comparables" in texto_docx
        assert "Patologías interiores" not in texto_docx

        if caso["slug"] == "caso-incompleto-problematico":
            incompleto = contexto
        else:
            assert contexto["completitud_valoracion"]["completo"] is True
            assert caso["resultado_borrador"]["valor_unitario"] > 0

    assert incompleto is not None
    assert incompleto["completitud_valoracion"]["completo"] is False
    claves = {
        advertencia["clave"]
        for advertencia in incompleto["completitud_valoracion"]["advertencias"]
    }
    assert {"superficies", "entorno", "metodo", "resultado"} & claves

    pytest.importorskip("playwright.sync_api")
    response_pdf = client.get(f"/generar-informe-pdf/{casos[0]['expediente_id']}")
    if response_pdf.status_code == 500:
        pytest.skip("PDF omitido: Playwright/Chromium no disponible en este entorno.")
    assert response_pdf.status_code == 200
    assert response_pdf.content.startswith(b"%PDF")


def test_script_valoracion_casos_demo_crea_sqlite_sandbox(isolated_import, tmp_path):
    isolated_import("app.main")
    db_path = tmp_path / "valoracion_demo_sandbox.db"
    result = subprocess.run(
        [
            "python3",
            "scripts/create_valoracion_demo_cases.py",
            "--db",
            str(db_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "piso-urbano-estandar" in result.stdout
    assert db_path.exists()
