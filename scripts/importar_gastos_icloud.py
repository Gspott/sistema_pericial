#!/usr/bin/env python3
"""Standalone expense importer for files captured from iCloud/Shortcuts."""

from __future__ import annotations

import json
import hashlib
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.rule_based_invoice_extractor import (
    extract_invoice_data as extract_rule_based_invoice_data,
)


OWNER_USER_ID = 1

DB_PATH = PROJECT_ROOT / "data" / "pericial.db"
UPLOADS_PATH = PROJECT_ROOT / "uploads"

PENDING_PATH = Path(
    "/Users/carlosblanco/Library/Mobile Documents/com~apple~CloudDocs/"
    "Casa/Trabajo Arquitecto Técnico/Facturas/Pendientes"
)
PROCESSED_PATH = PENDING_PATH.parent / "Procesadas"
ERROR_PATH = PENDING_PATH.parent / "Error"

ALLOWED_ATTACHMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".heic", ".heif"}
IMAGE_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


class DuplicateDetected(Exception):
    def __init__(self, attachment_path: Path | None):
        self.attachment_path = attachment_path
        super().__init__("Duplicate detected")


@dataclass(frozen=True)
class ImportResult:
    attachment_path: Path | None


def clean_text(value: object) -> str:
    return str(value or "").strip()


def parse_float(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = clean_text(value)
    if not text:
        return default

    text = text.replace("€", "").replace(" ", "")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return default


def parse_bool(value: object) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if value == 1 else 0
    return 1 if clean_text(value).lower() in {"true", "1"} else 0


def get_free_destination_path(destination: Path, filename: str) -> Path:
    candidate = destination / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    for index in range(1, 10_000):
        candidate = destination / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Could not find a free destination name for {filename}")


def move_without_collision(source: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    destination_path = get_free_destination_path(destination, source.name)
    return Path(shutil.move(str(source), str(destination_path)))


def move_import_files(
    json_path: Path,
    attachment_path: Path | None,
    destination_dir: Path,
) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_label = destination_dir.name

    if json_path.exists():
        try:
            json_destination = get_free_destination_path(destination_dir, json_path.name)
            shutil.move(str(json_path), str(json_destination))
            print(f"Moved JSON to {destination_label}: {json_destination.name}")
        except Exception as exc:
            print(f"Warning: could not move JSON to {destination_label}: {exc}")
    else:
        print(f"Warning: JSON file does not exist: {json_path}")

    if attachment_path and attachment_path.exists():
        try:
            attachment_destination = get_free_destination_path(
                destination_dir,
                attachment_path.name,
            )
            shutil.move(str(attachment_path), str(attachment_destination))
            print(
                f"Moved attachment to {destination_label}: "
                f"{attachment_destination.name}"
            )
        except Exception as exc:
            print(f"Warning: could not move attachment to {destination_label}: {exc}")

    if json_path.exists():
        print(f"WARNING: JSON still in pending after move attempt: {json_path.name}")


def load_shortcuts_json(json_path: Path) -> dict:
    raw = json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        repaired = raw.replace("\r", "\\n").replace("\t", " ")
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError:
            return {
                "fecha_captura": json_path.stem[:10],
                "origen": "shortcut_mac",
                "ambito": "trabajo",
                "estado": "revisar_json_malformado",
                "archivo_imagen": json_path.name.replace(".json", ".jpg"),
                "ocr_text": raw,
                "proveedor": "",
                "concepto": "REVISAR - JSON malformado de Shortcuts",
                "deducible": True,
                "es_factura_probable": "",
                "_json_parse_warning": True,
            }
    if not isinstance(data, dict):
        raise ValueError("JSON content is not an object")
    return data


def load_json(json_path: Path) -> dict:
    return load_shortcuts_json(json_path)


def ensure_readable_file(file_path: Path) -> None:
    if not file_path.is_file():
        raise ValueError("path is not a file")
    if file_path.stat().st_size == 0:
        raise ValueError("file is empty")
    with file_path.open("rb") as file_handle:
        file_handle.read(1)


def calculate_file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as exc:
        print(f"Warning: could not calculate sha256 for {path.name}: {exc}")
        return None


def auto_create_missing_json_files() -> None:
    today = date.today().isoformat()

    for attachment_path in sorted(PENDING_PATH.iterdir()):
        if attachment_path.suffix.lower() not in ALLOWED_ATTACHMENT_EXTENSIONS:
            continue

        json_path = attachment_path.with_suffix(".json")
        if json_path.exists():
            continue

        try:
            ensure_readable_file(attachment_path)
            payload = {
                "fecha_captura": today,
                "origen": "email_auto",
                "ambito": "trabajo",
                "estado": "pendiente",
                "archivo_imagen": attachment_path.name,
                "ocr_text": "",
                "proveedor": "",
                "nif_proveedor": "",
                "numero_factura": "",
                "concepto": "Factura importada automáticamente",
                "base_imponible": "",
                "iva_porcentaje": "",
                "iva_importe": "",
                "total": "",
                "deducible": True,
                "es_factura_probable": "SI",
            }
            json_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"JSON auto-created for {attachment_path.name}")
        except Exception as exc:
            print(f"Warning: could not auto-create JSON for {attachment_path.name}: {exc}")


def resolve_attachment_path(pending_dir: Path, filename: str | None) -> Path | None:
    attachment_name = clean_text(filename)
    if not attachment_name:
        return None

    relative_path = Path(attachment_name)
    if relative_path.name != attachment_name:
        raise ValueError(f"Unsafe attachment name: {attachment_name}")

    direct_path = pending_dir / attachment_name
    if direct_path.exists():
        return direct_path

    for extension in ALLOWED_ATTACHMENT_EXTENSIONS:
        candidate = pending_dir / f"{relative_path.stem}{extension}"
        if candidate.exists():
            return candidate

    return None


def resolve_attachment(data: dict) -> Path | None:
    return resolve_attachment_path(PENDING_PATH, data.get("archivo_imagen"))


def resolve_attachment_for_error(json_path: Path) -> Path | None:
    try:
        return resolve_attachment(load_json(json_path))
    except Exception:
        return None


def copy_attachment_to_uploads(attachment_path: Path | None) -> str | None:
    if attachment_path is None:
        return None

    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)
    upload_filename = f"gasto_{uuid4().hex}{attachment_path.suffix.lower()}"
    shutil.copy2(attachment_path, UPLOADS_PATH / upload_filename)
    return upload_filename


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        import pdfplumber

        with pdfplumber.open(file_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as exc:
        print(f"Warning: could not extract PDF text from {file_path.name}: {exc}")
        return ""


def extract_text_from_image(file_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps

        with Image.open(file_path) as image:
            prepared_image = ImageOps.exif_transpose(image).convert("L")
            prepared_image = ImageEnhance.Contrast(prepared_image).enhance(1.5)
            try:
                return pytesseract.image_to_string(prepared_image, lang="spa+eng")
            except Exception:
                return pytesseract.image_to_string(prepared_image, lang="eng")
    except Exception as exc:
        print(f"Warning: could not extract image OCR from {file_path.name}: {exc}")
        return ""


def get_shortcut_text(data: dict) -> str:
    for key in ("ocr_text", "text", "pdf_text"):
        value = clean_text(data.get(key))
        if value:
            return value
    return ""


def build_local_extraction_text(data: dict, attachment_path: Path | None) -> str:
    shortcut_text = get_shortcut_text(data)
    pdf_text = ""
    mac_ocr_text = ""

    if attachment_path and attachment_path.suffix.lower() == ".pdf":
        if not shortcut_text:
            pdf_text = extract_text_from_pdf(attachment_path)
            print(f"Extracted PDF text length: {len(pdf_text)}")
    elif attachment_path and attachment_path.suffix.lower() in IMAGE_ATTACHMENT_EXTENSIONS:
        print(f"Running local OCR for image: {attachment_path.name}")
        mac_ocr_text = extract_text_from_image(attachment_path)
        print(f"Mac OCR text length: {len(mac_ocr_text)}")

    data["_shortcut_text"] = shortcut_text
    data["_mac_ocr_text"] = mac_ocr_text
    data["_pdf_text"] = pdf_text

    if pdf_text:
        return f"\n\n--- PDF TEXT ---\n{pdf_text}"
    if shortcut_text or mac_ocr_text:
        return (
            f"\n\n--- SHORTCUT OCR ---\n{shortcut_text}"
            f"\n\n--- MAC OCR ---\n{mac_ocr_text}"
        ).strip()
    return ""


def apply_rule_based_invoice_data(data: dict, extracted_data: dict) -> str:
    if clean_text(extracted_data.get("supplier_name")):
        data["proveedor"] = extracted_data["supplier_name"]

    if clean_text(extracted_data.get("concept")):
        data["concepto"] = extracted_data["concept"]

    if clean_text(extracted_data.get("invoice_number")):
        data["numero_factura"] = extracted_data["invoice_number"]

    tax_lines = extracted_data.get("tax_lines") or []
    if tax_lines:
        base_total = sum(parse_float(line.get("base")) for line in tax_lines)
        vat_total = sum(parse_float(line.get("vat_amount")) for line in tax_lines)
        data["base_imponible"] = f"{base_total:.2f}"
        data["iva_importe"] = f"{vat_total:.2f}"
        if base_total:
            data["iva_porcentaje"] = f"{(vat_total / base_total * 100):.2f}"

    total = parse_float(extracted_data.get("total"))
    if total:
        data["total"] = f"{total:.2f}"

    reasons = extracted_data.get("review_reasons") or []
    if not reasons:
        return ""

    lines = [
        f"Rule review status: {clean_text(extracted_data.get('review_status'))}",
        f"Rule confidence: {parse_float(extracted_data.get('confidence')):.2f}",
        "",
        "Reasons:",
    ]
    lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines)


def build_notes(
    data: dict,
    original_sha256: str | None,
    resolved_filename: str | None,
    extraction_notes: str = "",
) -> str:
    shortcut_text = clean_text(data.get("_shortcut_text")) or get_shortcut_text(data)
    mac_ocr_text = clean_text(data.get("_mac_ocr_text"))
    pdf_text = clean_text(data.get("_pdf_text"))
    original_filename = clean_text(data.get("archivo_imagen"))
    parts = [
        "Importado automáticamente desde iCloud/Shortcuts.",
        f"Origen: {clean_text(data.get('origen'))}",
        f"Ámbito: {clean_text(data.get('ambito'))}",
        f"Estado OCR: {clean_text(data.get('estado'))}",
        f"Factura probable: {clean_text(data.get('es_factura_probable'))}",
        f"Original file: {original_filename}",
        f"Original sha256: {original_sha256 or ''}",
        f"Shortcut OCR length: {len(shortcut_text)}",
        f"Mac OCR length: {len(mac_ocr_text)}",
        f"PDF text length: {len(pdf_text)}",
    ]
    if data.get("_json_parse_warning"):
        parts.append("WARNING: Original JSON could not be parsed cleanly.")
    if resolved_filename and resolved_filename != original_filename:
        parts.append(f"Resolved file: {resolved_filename}")
    if extraction_notes:
        parts.extend(["", extraction_notes])
    parts.extend(
        [
            "",
            "--- SHORTCUT OCR ---",
            shortcut_text,
            "",
            "--- MAC OCR ---",
            mac_ocr_text,
            "",
            "--- PDF TEXT ---",
            pdf_text,
        ]
    )
    return "\n".join(parts).strip()


def build_expense(
    data: dict,
    uploaded_filename: str | None,
    original_sha256: str | None,
    resolved_filename: str | None,
    extraction_notes: str = "",
) -> dict:
    capture_date = clean_text(data.get("fecha_captura"))
    expense_date = capture_date[:10] if capture_date else date.today().isoformat()

    original_supplier = clean_text(data.get("proveedor"))
    supplier = original_supplier or "Pendiente de revisión"
    description = (
        clean_text(data.get("concepto"))
        or original_supplier
        or "Factura importada desde iCloud"
    )

    taxable_base = parse_float(data.get("base_imponible"), 0.0)
    vat_rate = parse_float(data.get("iva_porcentaje"), 21.0)
    vat_amount = parse_float(data.get("iva_importe"), 0.0)
    if not clean_text(data.get("iva_importe")) and taxable_base:
        vat_amount = taxable_base * vat_rate / 100

    total = parse_float(data.get("total"), 0.0)
    if not clean_text(data.get("total")) and (taxable_base or vat_amount):
        total = taxable_base + vat_amount

    return {
        "fecha": expense_date,
        "proveedor": supplier,
        "nif_proveedor": clean_text(data.get("nif_proveedor")),
        "numero_factura": clean_text(data.get("numero_factura")),
        "concepto": description,
        "categoria": clean_text(data.get("categoria")),
        "base_imponible": taxable_base,
        "iva_porcentaje": vat_rate,
        "iva_importe": vat_amount,
        "total": total,
        "deducible": parse_bool(data.get("deducible")),
        "archivo_path": uploaded_filename,
        "notas": build_notes(
            data,
            original_sha256,
            resolved_filename,
            extraction_notes,
        ),
        "owner_user_id": OWNER_USER_ID,
    }


def is_probable_duplicate(conn: sqlite3.Connection, data: dict) -> bool:
    supplier = clean_text(data.get("proveedor"))
    invoice_number = clean_text(data.get("numero_factura"))
    if not supplier or not invoice_number:
        return False

    row = conn.execute(
        """
        SELECT id
        FROM gastos
        WHERE owner_user_id = ?
          AND proveedor = ?
          AND numero_factura = ?
        LIMIT 1
        """,
        (OWNER_USER_ID, supplier, invoice_number),
    ).fetchone()
    return row is not None


def is_duplicate_by_original_file(
    conn: sqlite3.Connection,
    data: dict,
    original_sha256: str | None,
) -> bool:
    original_file = clean_text(data.get("archivo_imagen"))
    if original_file:
        row = conn.execute(
            """
            SELECT id
            FROM gastos
            WHERE owner_user_id = ?
              AND notas LIKE ?
            LIMIT 1
            """,
            (OWNER_USER_ID, f"%Original file: {original_file}%"),
        ).fetchone()
        if row is not None:
            return True

    if original_sha256:
        row = conn.execute(
            """
            SELECT id
            FROM gastos
            WHERE owner_user_id = ?
              AND notas LIKE ?
            LIMIT 1
            """,
            (OWNER_USER_ID, f"%Original sha256: {original_sha256}%"),
        ).fetchone()
        if row is not None:
            return True

    return False


def insert_expense(conn: sqlite3.Connection, expense: dict) -> None:
    conn.execute(
        """
        INSERT INTO gastos (
            fecha, proveedor, nif_proveedor, numero_factura, concepto,
            categoria, base_imponible, iva_porcentaje, iva_importe, total,
            deducible, archivo_path, notas, owner_user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expense["fecha"],
            expense["proveedor"],
            expense["nif_proveedor"],
            expense["numero_factura"],
            expense["concepto"],
            expense["categoria"],
            expense["base_imponible"],
            expense["iva_porcentaje"],
            expense["iva_importe"],
            expense["total"],
            expense["deducible"],
            expense["archivo_path"],
            expense["notas"],
            expense["owner_user_id"],
        ),
    )


def import_expense(
    conn: sqlite3.Connection,
    json_path: Path,
    attachment_path: Path | None,
) -> ImportResult:
    data = load_json(json_path)
    if attachment_path is None:
        attachment_path = resolve_attachment(data)
    if attachment_path is None and clean_text(data.get("archivo_imagen")):
        print(f"Attachment not found for {json_path.name}; JSON will still be moved")
    original_sha256 = (
        calculate_file_sha256(attachment_path) if attachment_path is not None else None
    )
    extraction_notes = ""

    if is_probable_duplicate(conn, data) or is_duplicate_by_original_file(
        conn,
        data,
        original_sha256,
    ):
        print(f"Duplicate detected for {json_path.name}")
        raise DuplicateDetected(attachment_path)

    combined_text = build_local_extraction_text(data, attachment_path)
    if not clean_text(combined_text):
        data["concepto"] = "REVISAR - Factura importada automáticamente"
        extraction_notes = "WARNING: No OCR text could be extracted locally."
    else:
        rule_data = extract_rule_based_invoice_data(combined_text)
        extraction_notes = apply_rule_based_invoice_data(data, rule_data)

    uploaded_filename = copy_attachment_to_uploads(attachment_path)
    expense = build_expense(
        data,
        uploaded_filename=uploaded_filename,
        original_sha256=original_sha256,
        resolved_filename=attachment_path.name if attachment_path else None,
        extraction_notes=extraction_notes,
    )

    try:
        with conn:
            insert_expense(conn, expense)
    except Exception:
        if uploaded_filename:
            upload_path = UPLOADS_PATH / uploaded_filename
            if upload_path.exists():
                upload_path.unlink()
        raise

    return ImportResult(attachment_path=attachment_path)


def main() -> int:
    if not DB_PATH.exists():
        print(f"Error: expected database does not exist: {DB_PATH}")
        return 1

    if not PENDING_PATH.exists():
        print(f"Error: pending folder does not exist: {PENDING_PATH}")
        return 1

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    ERROR_PATH.mkdir(parents=True, exist_ok=True)

    auto_create_missing_json_files()

    imported = 0
    errors = 0
    duplicates = 0

    with sqlite3.connect(DB_PATH) as conn:
        for json_path in sorted(PENDING_PATH.glob("*.json")):
            print(f"Processing JSON: {json_path.name}")
            attachment_path = None
            try:
                initial_data = load_json(json_path)
                attachment_path = resolve_attachment_path(
                    PENDING_PATH,
                    initial_data.get("archivo_imagen"),
                )
            except Exception:
                attachment_path = None

            try:
                result = import_expense(conn, json_path, attachment_path)
                move_import_files(json_path, result.attachment_path, PROCESSED_PATH)
                imported += 1
            except DuplicateDetected as exc:
                duplicates += 1
                move_import_files(
                    json_path,
                    exc.attachment_path or attachment_path,
                    ERROR_PATH,
                )
            except Exception as exc:
                errors += 1
                print(f"Error importing {json_path.name}: {exc}")
                try:
                    move_import_files(json_path, attachment_path, ERROR_PATH)
                except Exception as move_exc:
                    print(f"Could not move import files to Error: {move_exc}")
            finally:
                if json_path.exists():
                    try:
                        move_without_collision(json_path, ERROR_PATH)
                        print(f"Forced move of leftover JSON to Error: {json_path.name}")
                    except Exception as force_exc:
                        print(f"Could not force move leftover JSON to Error: {force_exc}")

    print(f"importados: {imported}")
    print(f"errores: {errors}")
    print(f"duplicados: {duplicates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
