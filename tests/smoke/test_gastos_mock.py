import io
import importlib
import sqlite3


def test_gastos_router_imports_and_calculates_amounts(isolated_import):
    gastos = isolated_import("app.routers.gastos")

    iva_importe, total = gastos.calcular_importes(100, 21)
    form = gastos.preparar_gasto_form(
        fecha="2026-05-25",
        proveedor="Proveedor Demo",
        nif_proveedor="B00000000",
        numero_factura="G-001",
        concepto="Material demo",
        categoria="material",
        base_imponible="100,50",
        iva_porcentaje="21",
        deducible="1",
        notas="  demo  ",
    )

    assert iva_importe == 21
    assert total == 121
    assert form["base_imponible"] == 100.50
    assert form["iva_importe"] == 21.105
    assert form["total"] == 121.605
    assert form["deducible"] == 1
    assert form["notas"] == "demo"
    assert gastos.validar_gasto(form) == ""


def test_gasto_demo_is_inserted_in_temp_sqlite_db(isolated_import):
    isolated_import("app.main")

    from app.database import get_connection
    from app.routers.gastos import build_amount_summary, build_review_summary

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO gastos (
                fecha, proveedor, concepto, categoria, base_imponible,
                iva_porcentaje, iva_importe, total, deducible,
                archivo_path, notas, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-05-25",
                "Proveedor Demo",
                "Gasto demo",
                "material",
                100,
                21,
                21,
                121,
                1,
                "demo.pdf",
                "Rule review status: ok",
                1,
            ),
        )
        conn.commit()
        gastos = cur.execute("SELECT * FROM gastos WHERE owner_user_id = ?", (1,)).fetchall()
    finally:
        conn.close()

    amount_summary = build_amount_summary(gastos)
    review_summary = build_review_summary(gastos)

    assert len(gastos) == 1
    assert amount_summary == {"base": 100.0, "iva": 21.0, "total": 121.0}
    assert review_summary["ok"] == 1


def test_guardar_archivo_gasto_uses_temp_upload_path(isolated_import):
    gastos = isolated_import("app.routers.gastos")
    fake_upload = type(
        "FakeUpload",
        (),
        {
            "filename": "../recibos/reales/demo.pdf",
            "file": io.BytesIO(b"%PDF demo temporal"),
        },
    )()

    filename = gastos.guardar_archivo_gasto(fake_upload)
    saved_path = gastos.UPLOAD_PATH / filename

    assert filename.startswith("gasto_")
    assert filename.endswith(".pdf")
    assert saved_path.exists()
    assert saved_path.read_bytes() == b"%PDF demo temporal"
    assert "generated/uploads" in saved_path.as_posix()
    assert "sistema_pericial/uploads" not in saved_path.as_posix()


def test_importer_duplicate_detection_uses_temp_sqlite_only(isolated_import):
    isolated_import("app.main")
    importer = importlib.import_module("scripts.importar_gastos_icloud")

    from app.database import get_connection

    conn = get_connection()
    try:
        importer.insert_expense(
            conn,
            {
                "fecha": "2026-05-25",
                "proveedor": "Proveedor Demo",
                "nif_proveedor": "B00000000",
                "numero_factura": "G-001",
                "concepto": "Gasto demo",
                "categoria": "material",
                "base_imponible": 100,
                "iva_porcentaje": 21,
                "iva_importe": 21,
                "total": 121,
                "deducible": 1,
                "archivo_path": "gasto_demo.pdf",
                "notas": "Original file: demo.pdf\nOriginal sha256: abc123",
                "owner_user_id": importer.OWNER_USER_ID,
            },
        )
        conn.commit()

        assert importer.is_probable_duplicate(
            conn,
            {"proveedor": "Proveedor Demo", "numero_factura": "G-001"},
        )
        assert importer.is_duplicate_by_original_file(
            conn,
            {"archivo_imagen": "demo.pdf"},
            "abc123",
        )
    finally:
        conn.close()


def test_importer_degrades_without_ocr_or_ai_for_empty_local_text(monkeypatch, tmp_path):
    importer = importlib.import_module("scripts.importar_gastos_icloud")
    attachment = tmp_path / "demo.pdf"
    attachment.write_bytes(b"%PDF demo temporal")

    monkeypatch.setattr(importer, "extract_text_from_pdf", lambda path: "")
    monkeypatch.setattr(importer, "extract_text_from_image", lambda path: "")

    data = {
        "fecha_captura": "2026-05-25",
        "archivo_imagen": attachment.name,
        "ocr_text": "",
    }

    combined_text = importer.build_local_extraction_text(data, attachment)
    expense = importer.build_expense(
        data,
        uploaded_filename=None,
        original_sha256=None,
        resolved_filename=attachment.name,
        extraction_notes="WARNING: No OCR text could be extracted locally.",
    )

    assert combined_text == ""
    assert expense["concepto"] == "Factura importada desde iCloud"
    assert "WARNING: No OCR text could be extracted locally." in expense["notas"]
    assert expense["archivo_path"] is None
