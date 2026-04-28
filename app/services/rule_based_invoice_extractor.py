from __future__ import annotations

import re


AMOUNT_PATTERN = re.compile(
    r"(?<!\d)(\d{1,4}(?:[.\s]\d{3})*(?:[,.]\d{2})|\d+[,.]\d{2}|\d+)\s*(?:€|EUR)?",
    re.IGNORECASE,
)
VAT_RATE_PATTERN = re.compile(r"(\d{1,2}(?:[,.]\d{1,2})?)\s*%")
BASE_LABELS = ("subtotal", "base", "base imponible")
VAT_LABELS = ("iva", "vat", "tax")
TOTAL_LABELS = ("total",)
KNOWN_VAT_RATES = [21, 10, 4, 0]
BAD_TEXT_HINTS = (
    "hola",
    "contacto",
    "fecha",
    "date",
    "pedido",
    "order",
    "transaction",
    "transacción",
    "ver detalles",
    "subtotal",
    "total",
    "iva",
    "vat",
    "tax",
    "iban",
    "cuenta",
    "account",
    "cant.",
    "qty",
    "cantidad",
)
INVOICE_NUMBER_LABEL_PATTERN = re.compile(
    r"(?:"
    r"numero\s+factura|número\s+factura|factura\s*(?:nº|no|num|#)|"
    r"invoice\s*(?:number|no|#)|receipt\s*(?:number|no)|"
    r"ticket\s*(?:number|no)|order\s*(?:id|number)|"
    r"id\.?\s+de\s+pedido|pedido|transaction\s*(?:id|number)|"
    r"payment\s+id|reference|referencia|ref\."
    r")",
    re.IGNORECASE,
)


def parse_amount(value: str, force_cents: bool = False) -> float:
    cleaned = value.replace("€", "").replace("EUR", "").replace(" ", "").strip()
    has_decimal_separator = "," in cleaned or "." in cleaned
    if force_cents and not has_decimal_separator and cleaned.isdigit():
        return int(cleaned) / 100
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def should_force_cents(raw_amount: str, line: str, has_nearby_decimals: bool) -> bool:
    cleaned = raw_amount.replace("€", "").replace("EUR", "").replace(" ", "").strip()
    if not cleaned.isdigit() or int(cleaned) < 100:
        return False
    if "," in cleaned or "." in cleaned:
        return False
    normalized = line.lower()
    has_money_symbol = "€" in line or "eur" in normalized
    has_context_label = has_any_label(line, BASE_LABELS + VAT_LABELS + TOTAL_LABELS)
    return has_money_symbol and has_context_label and has_nearby_decimals


def line_has_decimal_amount(line: str) -> bool:
    return any(
        re.search(r"[,.]\d{2}$", match.group(1))
        for match in AMOUNT_PATTERN.finditer(line)
    )


def extract_amounts(line: str, has_nearby_decimals: bool = False) -> list[float]:
    amounts = []
    for match in AMOUNT_PATTERN.finditer(line):
        raw_amount = match.group(1)
        amounts.append(
            parse_amount(
                raw_amount,
                force_cents=should_force_cents(
                    raw_amount,
                    line,
                    has_nearby_decimals,
                ),
            )
        )
    return amounts


def extract_vat_rate(text: str) -> float:
    match = VAT_RATE_PATTERN.search(text)
    return parse_amount(match.group(1)) if match else 0.0


def has_any_label(line: str, labels: tuple[str, ...]) -> bool:
    normalized = line.lower()
    return any(label in normalized for label in labels)


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def looks_like_bad_text_line(line: str) -> bool:
    normalized = line.lower().strip()
    if not normalized:
        return True
    if "@" in normalized:
        return True
    if re.search(r"\+?\d[\d\s().-]{6,}", normalized):
        return True
    if any(hint in normalized for hint in BAD_TEXT_HINTS):
        return True
    return False


def looks_like_company_continuation(line: str) -> bool:
    if looks_like_bad_text_line(line):
        return False
    return bool(re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", line))


def clean_amount_suffix(line: str) -> str:
    return normalize_spaces(AMOUNT_PATTERN.sub("", line))


def clean_invoice_number_value(value: str) -> str:
    cleaned = INVOICE_NUMBER_LABEL_PATTERN.sub("", value)
    cleaned = cleaned.strip(" :#.-")
    cleaned = normalize_spaces(cleaned)
    return cleaned.rstrip(".,;")


def looks_like_invalid_invoice_number(value: str) -> bool:
    normalized = value.lower().strip()
    if not normalized:
        return True
    if "@" in normalized:
        return True
    if has_any_label(normalized, BASE_LABELS + VAT_LABELS + TOTAL_LABELS):
        return True
    if has_any_label(normalized, ("cant.", "qty", "cantidad")):
        return True
    if re.search(r"\d+[,.]\d{2}\s*(?:€|eur)?", normalized):
        return True
    if re.fullmatch(r"\+?\d[\d\s().-]{6,}", normalized):
        return True
    if re.fullmatch(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", normalized):
        return True
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalized):
        return True
    return not bool(re.search(r"[A-Za-z0-9]", value))


def extract_invoice_number(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]

    for index, line in enumerate(clean_lines):
        match = INVOICE_NUMBER_LABEL_PATTERN.search(line)
        if not match:
            continue

        inline_value = clean_invoice_number_value(line[match.end() :])
        if inline_value and not looks_like_invalid_invoice_number(inline_value):
            return inline_value

        for candidate in clean_lines[index + 1 : index + 4]:
            value = clean_invoice_number_value(candidate)
            if value and not looks_like_invalid_invoice_number(value):
                return value

    return ""


def extract_supplier_name(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]

    for index, line in enumerate(clean_lines):
        match = re.match(r"^(?:vendedor|seller)\s+(.+)$", line, re.IGNORECASE)
        if match:
            return normalize_spaces(match.group(1))

        if line.lower() in {"vendedor", "seller"}:
            for candidate in clean_lines[index + 1 : index + 4]:
                if looks_like_company_continuation(candidate):
                    return normalize_spaces(candidate)

    for index, line in enumerate(clean_lines):
        match = re.search(
            r"(?:ha pagado|paid)\b.*?\b(?:a|to)\s+(.+)$",
            line,
            re.IGNORECASE,
        )
        if not match:
            continue
        supplier = normalize_spaces(match.group(1))
        if index + 1 < len(clean_lines) and looks_like_company_continuation(
            clean_lines[index + 1]
        ):
            supplier = normalize_spaces(f"{supplier} {clean_lines[index + 1]}")
        return supplier

    return ""


def extract_concept(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]
    stop_labels = ("cant.", "qty", "cantidad", "subtotal", "iva", "vat", "total")

    for index, line in enumerate(clean_lines):
        if not has_any_label(line, stop_labels):
            continue
        for candidate in reversed(clean_lines[max(0, index - 4) : index]):
            if looks_like_bad_text_line(candidate):
                continue
            concept = clean_amount_suffix(candidate)
            if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", concept):
                return concept

    return ""


def infer_vat_rate(base: float, vat_amount: float) -> tuple[float, bool]:
    if base <= 0 or vat_amount <= 0:
        return 0.0
    raw_rate = vat_amount / base * 100
    vat_rate = min(KNOWN_VAT_RATES, key=lambda rate: abs(rate - raw_rate))
    if abs(vat_rate - raw_rate) > 3:
        return round(raw_rate, 2), True
    return float(vat_rate), False


def amounts_match(base: float, vat_amount: float, total: float) -> bool:
    return abs((base + vat_amount) - total) <= 0.05


def build_amount_result(
    base: float,
    vat_amount: float,
    total: float,
    reason: str,
) -> dict:
    vat_rate, unusual_vat_rate = infer_vat_rate(base, vat_amount)
    review_reasons = [reason]
    if unusual_vat_rate:
        review_reasons.append("Unusual VAT rate detected")

    return {
        "base": base,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total": total,
        "review_status": "revisar" if unusual_vat_rate else "ok",
        "confidence": 0.8,
        "review_reasons": review_reasons,
    }


def extract_labeled_amount_lines(lines: list[str]) -> dict:
    clean_lines = [line.strip() for line in lines if line.strip()]
    has_nearby_decimals = any(line_has_decimal_amount(line) for line in clean_lines)
    base = None
    vat_amount = None
    total = None

    for line in clean_lines:
        amounts = extract_amounts(line, has_nearby_decimals=has_nearby_decimals)
        if not amounts:
            continue
        amount = amounts[-1]
        if has_any_label(line, BASE_LABELS) and base is None:
            base = amount
        elif has_any_label(line, VAT_LABELS) and vat_amount is None:
            vat_amount = amount
        elif has_any_label(line, TOTAL_LABELS) and total is None:
            total = amount

    if base is not None and vat_amount is not None and total is not None:
        if amounts_match(base, vat_amount, total):
            return build_amount_result(
                base,
                vat_amount,
                total,
                "Amounts extracted from labeled subtotal/VAT/total lines",
            )

    return {}


def extract_vertical_amount_block(lines: list[str]) -> dict:
    """Detect blocks like Subtotal / IVA / Total followed by 4,54€ / 0,95€ / 5,49€."""
    clean_lines = [line.strip() for line in lines if line.strip()]

    for index, line in enumerate(clean_lines):
        if not has_any_label(line, BASE_LABELS):
            continue

        label_window = clean_lines[index : index + 8]
        vat_index = next(
            (
                offset
                for offset, candidate in enumerate(label_window[1:], start=1)
                if has_any_label(candidate, VAT_LABELS)
            ),
            None,
        )
        if vat_index is None:
            continue

        total_index = next(
            (
                offset
                for offset, candidate in enumerate(
                    label_window[vat_index + 1 :],
                    start=vat_index + 1,
                )
                if has_any_label(candidate, TOTAL_LABELS)
            ),
            None,
        )
        if total_index is None:
            continue

        amount_lines = clean_lines[index + total_index + 1 : index + total_index + 8]
        has_nearby_decimals = any(line_has_decimal_amount(line) for line in amount_lines)
        amounts: list[float] = []
        for amount_line in amount_lines:
            amounts.extend(
                extract_amounts(
                    amount_line,
                    has_nearby_decimals=has_nearby_decimals,
                )
            )
            if len(amounts) >= 3:
                break

        if len(amounts) >= 3:
            base, vat_amount, total = amounts[:3]
            if amounts_match(base, vat_amount, total):
                return build_amount_result(
                    base,
                    vat_amount,
                    total,
                    "Amounts extracted from vertical subtotal/VAT/total block",
                )

        if len(amounts) == 2:
            base, total = amounts
            vat_rate = extract_vat_rate(" ".join(label_window + amount_lines))
            vat_amount = round(base * vat_rate / 100, 2) if vat_rate else total - base
            if vat_amount > 0 and (
                not vat_rate or amounts_match(base, vat_amount, total)
            ):
                inferred_vat_rate, unusual_vat_rate = infer_vat_rate(base, vat_amount)
                final_vat_rate = vat_rate or inferred_vat_rate
                review_reasons = [
                    "Amounts extracted from vertical subtotal/VAT/total block"
                ]
                if unusual_vat_rate:
                    review_reasons.append("Unusual VAT rate detected")
                return {
                    "base": base,
                    "vat_rate": final_vat_rate,
                    "vat_amount": round(vat_amount, 2),
                    "total": (
                        total
                        if amounts_match(base, vat_amount, total)
                        else base + vat_amount
                    ),
                    "review_status": "revisar" if unusual_vat_rate else "ok",
                    "confidence": 0.8,
                    "review_reasons": review_reasons,
                }

    return {}


def enrich_text_fields(result: dict, lines: list[str]) -> dict:
    supplier_name = result.get("supplier_name") or extract_supplier_name(lines)
    concept = result.get("concept") or extract_concept(lines)
    invoice_number = result.get("invoice_number") or extract_invoice_number(lines)
    review_reasons = list(result.get("review_reasons") or [])
    confidence = float(result.get("confidence") or 0.0)

    if supplier_name:
        result["supplier_name"] = supplier_name
        review_reasons.append("Supplier extracted from seller/payment lines")
        confidence = min(0.95, confidence + 0.05)

    if concept:
        result["concept"] = concept
        review_reasons.append("Concept extracted from item line")
        confidence = min(0.95, confidence + 0.05)

    if invoice_number:
        result["invoice_number"] = invoice_number
        review_reasons.append(
            "Document identifier extracted from invoice/order/payment reference"
        )
        confidence = min(0.95, confidence + 0.05)

    result["confidence"] = confidence
    result["review_reasons"] = list(dict.fromkeys(review_reasons))
    return result


def build_extraction_response(amount_data: dict) -> dict:
    if amount_data:
        return {
            "tax_lines": [
                {
                    "base": amount_data["base"],
                    "vat_rate": amount_data["vat_rate"],
                    "vat_amount": amount_data["vat_amount"],
                }
            ],
            "total": amount_data["total"],
            "review_status": amount_data["review_status"],
            "confidence": amount_data["confidence"],
            "review_reasons": amount_data["review_reasons"],
            "supplier_name": "",
            "concept": "",
            "invoice_number": "",
        }
    return {
        "tax_lines": [],
        "total": 0.0,
        "review_status": "revisar",
        "confidence": 0.0,
        "review_reasons": [],
        "supplier_name": "",
        "concept": "",
        "invoice_number": "",
    }


def extract_invoice_data(text: str) -> dict:
    lines = text.splitlines()
    labeled_lines = extract_labeled_amount_lines(lines)
    if labeled_lines:
        return enrich_text_fields(build_extraction_response(labeled_lines), lines)

    vertical_block = extract_vertical_amount_block(lines)
    if vertical_block:
        return enrich_text_fields(build_extraction_response(vertical_block), lines)

    return enrich_text_fields(build_extraction_response({}), lines)
