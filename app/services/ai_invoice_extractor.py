from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.getenv("OPENAI_INVOICE_MODEL", "gpt-4o-mini")
REQUEST_TIMEOUT = 45.0
RETRY_DELAYS = (2, 5, 10)
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

DOCUMENT_TYPES = {
    "factura_completa",
    "factura_simplificada",
    "ticket",
    "recibo_no_fiscal",
    "no_factura",
    "desconocido",
}
REVIEW_STATUSES = {"ok", "revisar", "rechazar"}


INVOICE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "document_type",
        "review_status",
        "language",
        "supplier_name",
        "supplier_tax_id",
        "invoice_number",
        "invoice_date",
        "concept",
        "currency",
        "tax_lines",
        "total",
        "is_probably_invoice",
        "is_vat_deductible_candidate",
        "confidence",
        "review_reasons",
    ],
    "properties": {
        "document_type": {
            "type": "string",
            "enum": sorted(DOCUMENT_TYPES),
        },
        "review_status": {
            "type": "string",
            "enum": sorted(REVIEW_STATUSES),
        },
        "language": {"type": "string"},
        "supplier_name": {"type": "string"},
        "supplier_tax_id": {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string"},
        "concept": {"type": "string"},
        "currency": {"type": "string", "enum": ["EUR"]},
        "tax_lines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["base", "vat_rate", "vat_amount"],
                "properties": {
                    "base": {"type": "number"},
                    "vat_rate": {"type": "number"},
                    "vat_amount": {"type": "number"},
                },
            },
        },
        "total": {"type": "number"},
        "is_probably_invoice": {"type": "boolean"},
        "is_vat_deductible_candidate": {"type": "boolean"},
        "confidence": {"type": "number"},
        "review_reasons": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


SYSTEM_PROMPT = """
You are a Spanish tax expert.
Analyze OCR text from invoices, simplified invoices, tickets, receipts, and
non-invoice documents in multiple languages.
Identify whether the document is a valid Spanish invoice or not.
Extract taxable base, VAT rates, VAT amounts, and total amount.
Support multiple VAT rates in a single document.
If required information is missing, set review_status to "revisar".
If the document is not an invoice, set review_status to "rechazar".
If there is any doubt, set review_status to "revisar".
Never invent data. If a value is not found, leave strings empty and numbers as 0.
Return only strict JSON matching the schema.
""".strip()


def default_invoice_data(review_reason: str = "") -> dict:
    reasons = [review_reason] if review_reason else []
    return {
        "document_type": "desconocido",
        "review_status": "revisar",
        "language": "",
        "supplier_name": "",
        "supplier_tax_id": "",
        "invoice_number": "",
        "invoice_date": "",
        "concept": "",
        "currency": "EUR",
        "tax_lines": [],
        "total": 0.0,
        "is_probably_invoice": False,
        "is_vat_deductible_candidate": False,
        "confidence": 0.0,
        "review_reasons": reasons,
    }


def to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def normalize_invoice_data(data: dict) -> dict:
    normalized = default_invoice_data()
    normalized.update({key: data.get(key, normalized[key]) for key in normalized})

    normalized["document_type"] = (
        normalized["document_type"]
        if normalized["document_type"] in DOCUMENT_TYPES
        else "desconocido"
    )
    normalized["review_status"] = (
        normalized["review_status"]
        if normalized["review_status"] in REVIEW_STATUSES
        else "revisar"
    )
    normalized["currency"] = "EUR"
    normalized["total"] = to_float(normalized["total"])
    normalized["confidence"] = max(0.0, min(1.0, to_float(normalized["confidence"])))
    normalized["is_probably_invoice"] = bool(normalized["is_probably_invoice"])
    normalized["is_vat_deductible_candidate"] = bool(
        normalized["is_vat_deductible_candidate"]
    )

    tax_lines = []
    for line in normalized.get("tax_lines") or []:
        if not isinstance(line, dict):
            continue
        tax_lines.append(
            {
                "base": to_float(line.get("base")),
                "vat_rate": to_float(line.get("vat_rate")),
                "vat_amount": to_float(line.get("vat_amount")),
            }
        )
    normalized["tax_lines"] = tax_lines

    reasons = normalized.get("review_reasons")
    normalized["review_reasons"] = [
        str(reason).strip() for reason in reasons or [] if str(reason).strip()
    ]

    for key in (
        "language",
        "supplier_name",
        "supplier_tax_id",
        "invoice_number",
        "invoice_date",
        "concept",
    ):
        normalized[key] = str(normalized.get(key) or "").strip()

    return normalized


def validate_invoice_data(data: dict) -> dict:
    validated = normalize_invoice_data(data)
    reasons = list(validated["review_reasons"])

    base_total = sum(line["base"] for line in validated["tax_lines"])
    vat_total = sum(line["vat_amount"] for line in validated["tax_lines"])
    expected_total = base_total + vat_total
    has_amounts = bool(validated["tax_lines"]) or validated["total"] > 0

    if has_amounts and abs(expected_total - validated["total"]) > 0.02:
        validated["review_status"] = "revisar"
        reasons.append("Totals do not match")

    if validated["confidence"] < 0.7:
        validated["review_status"] = "revisar"
        reasons.append("Low confidence")

    if validated["document_type"] == "no_factura":
        validated["review_status"] = "rechazar"
        reasons.append("Document is not an invoice")

    validated["review_reasons"] = list(dict.fromkeys(reasons))
    return validated


def build_notes_from_ai(data: dict) -> str:
    validated = validate_invoice_data(data)
    lines = [
        f"AI review status: {validated['review_status']}",
        f"AI document type: {validated['document_type']}",
        f"AI confidence: {validated['confidence']:.2f}",
        "",
        "Reasons:",
    ]
    if validated["review_reasons"]:
        lines.extend(f"- {reason}" for reason in validated["review_reasons"])
    else:
        lines.append("- None")
    return "\n".join(lines)


def extract_output_text(response_data: dict) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for item in response_data.get("output", []) or []:
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]
    return ""


def call_openai(text: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return default_invoice_data("OPENAI_API_KEY is not configured")

    payload = {
        "model": DEFAULT_MODEL,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text[:60_000]},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "invoice_extraction",
                "strict": True,
                "schema": INVOICE_SCHEMA,
            }
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    max_attempts = len(RETRY_DELAYS)
    response = None
    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        response = httpx.post(
            OPENAI_RESPONSES_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code not in RETRY_STATUS_CODES or attempt == max_attempts:
            break
        print(
            f"OpenAI retry {attempt}/{max_attempts} "
            f"after status {response.status_code}"
        )
        time.sleep(delay)

    response.raise_for_status()
    output_text = extract_output_text(response.json())
    if not output_text:
        return default_invoice_data("OpenAI response did not include JSON output")
    return json.loads(output_text)


def extract_invoice_data(text: str) -> dict:
    try:
        if not text.strip():
            return default_invoice_data("No OCR text available")
        return validate_invoice_data(call_openai(text))
    except Exception as exc:
        return validate_invoice_data(default_invoice_data(f"AI extraction error: {exc}"))
