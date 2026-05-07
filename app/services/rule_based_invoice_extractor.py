from __future__ import annotations

import re
import unicodedata


AMOUNT_PATTERN = re.compile(
    r"(?<!\d)(\d{1,4}(?:[.\s]\d{3})*(?:[,.]\d{2})|\d+[,.]\d{2}|\d+)\s*(?:€|EUR)?",
    re.IGNORECASE,
)
VAT_RATE_PATTERN = re.compile(r"(\d{1,2}(?:[,.]\d{1,2})?)\s*%")
TAX_ID_PATTERN = re.compile(r"\b(?:CIF|NIF|VAT)\s*:?\s*([A-Z]\d{7,8}[A-Z0-9]?)\b", re.IGNORECASE)
BASE_LABELS = ("subtotal", "base", "base imponible")
VAT_LABELS = ("iva", "vat", "tax")
TOTAL_LABELS = ("total",)
TAX_QUOTA_LABELS = ("cuota",)
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
    "base",
    "cuota",
    "descripcion",
    "descripción",
    "letra",
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
    r"ticket\s*(?:number|no)?|n\.?\s*tpv|order\s*(?:id|number)|"
    r"id\.?\s+de\s+pedido|pedido|transaction\s*(?:id|number)|"
    r"payment\s+id|reference|referencia|ref\."
    r")",
    re.IGNORECASE,
)
PRODUCT_IGNORE_LABELS = (
    "eu",
    "importe",
    "litros",
    "total",
    "base",
    "cuota",
    "descripcion",
    "descripción",
    "letra",
    "su producto",
)
CATEGORY_RULES = (
    (
        "combustible",
        (
            "gasoleo",
            "gasolina",
            "diesel",
            "carburante",
            "repsol",
            "cepsa",
            "bp",
            "galp",
            "shell",
            "alcampo gasolinera",
            "litros",
        ),
    ),
    (
        "telefonia_internet",
        (
            "movistar",
            "vodafone",
            "orange",
            "yoigo",
            "digi",
            "pepephone",
            "o2",
            "simyo",
            "telefono",
            "internet",
            "fibra",
            "movil",
            "lowi",
            "jazztel",
            "masmovil",
        ),
    ),
    (
        "suscripciones",
        (
            "hbo",
            "netflix",
            "spotify",
            "apple",
            "google",
            "microsoft",
            "adobe",
            "openai",
            "dropbox",
            "icloud",
            "canva",
            "notion",
            "github",
            "chatgpt",
            "suscripcion",
            "subscription",
        ),
    ),
    (
        "material_oficina",
        (
            "papeleria",
            "folios",
            "papel",
            "boligrafo",
            "toner",
            "cartucho",
            "impresora",
            "oficina",
        ),
    ),
    (
        "informatica",
        (
            "ordenador",
            "laptop",
            "macbook",
            "monitor",
            "teclado",
            "raton",
            "disco duro",
            "ssd",
            "usb",
            "cable",
            "adaptador",
            "informatica",
        ),
    ),
    (
        "transporte",
        ("taxi", "cabify", "uber", "renfe", "ave", "autobus", "metro", "tren", "billete"),
    ),
    (
        "alojamiento",
        ("hotel", "booking", "airbnb", "alojamiento", "hostal"),
    ),
    (
        "comidas",
        (
            "restaurante",
            "bar",
            "cafeteria",
            "comida",
            "menu",
            "desayuno",
            "almuerzo",
            "cena",
            "supermercado",
            "alimentacion",
            "batido",
            "aceite",
            "leche",
            "agua",
            "cafe",
            "pan",
            "fruta",
            "gourmet",
            "chocolate",
            "mercadona",
            "contramuslo",
            "burger",
            "tomate",
            "aceituna",
            "huevos",
            "coles",
            "magdalena",
            "bifidus",
            "sardina",
            "fuet",
        ),
    ),
    (
        "suministros",
        ("luz", "electricidad", "gas natural", "agua", "endesa", "iberdrola", "naturgy"),
    ),
    (
        "herramientas",
        (
            "herramienta",
            "herramientas",
            "ferreteria",
            "leroy",
            "bricomart",
            "bauhaus",
            "tornillo",
            "taladro",
        ),
    ),
    (
        "parking_peajes",
        ("parking", "aparcamiento", "peaje", "autopista"),
    ),
)
FOOD_CATEGORY_KEYWORDS = (
    "mercadona",
    "supermercado",
    "alimentacion",
    "batido",
    "aceite",
    "leche",
    "cafe",
    "pan",
    "fruta",
    "gourmet",
    "chocolate",
    "contramuslo",
    "burger",
    "tomate",
    "aceituna",
    "huevos",
    "coles",
    "magdalena",
    "bifidus",
    "sardina",
    "fuet",
)
FUEL_CATEGORY_KEYWORDS = CATEGORY_RULES[0][1]


def normalize_for_rules(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", normalized).strip()


def infer_expense_category(supplier_name: str, concept: str, text: str) -> str:
    haystack = normalize_for_rules(f"{supplier_name} {concept} {text}")
    if any(keyword in haystack for keyword in FUEL_CATEGORY_KEYWORDS):
        return "combustible"
    if any(keyword in haystack for keyword in FOOD_CATEGORY_KEYWORDS):
        return "comidas"
    for category, keywords in CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return "otros"


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


def parse_invoice_date_parts(day: str, month: str, year: str) -> str:
    year_number = int(year)
    if year_number < 100:
        year_number += 2000
    return f"{year_number:04d}-{int(month):02d}-{int(day):02d}"


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


def looks_like_bad_supplier_line(line: str) -> bool:
    normalized = line.lower().strip()
    if looks_like_bad_text_line(line):
        return True
    if any(
        hint in normalized
        for hint in (
            "calle",
            "c/",
            "avda",
            "avenida",
            "carretera",
            "cp ",
            "factura simplificada",
            "telefono",
            "teléfono",
            "tel.",
            "ticket",
            "n. tpv",
        )
    ):
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


def normalize_company_name(value: str) -> str:
    cleaned = normalize_spaces(value).strip(" -")
    cleaned = re.sub(r"\bS\.?\s*A\.?$", "S.A.", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bS\.?\s*L\.?$", "S.L.", cleaned, flags=re.IGNORECASE)
    if normalize_for_rules(cleaned).startswith("mercadona"):
        return "Mercadona, S.A."
    return cleaned


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

    for line in clean_lines:
        match = re.search(
            r"\bfactura\s+simplificada\s*:?\s*([A-Za-z0-9/-]+)",
            line,
            re.IGNORECASE,
        )
        if match:
            value = match.group(1).strip()
            if re.fullmatch(r"[A-Za-z0-9/-]{4,}", value):
                return value

    for line in clean_lines:
        match = re.search(r"\bticket\s*:?\s*([A-Za-z0-9/-]+)\b", line, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if not looks_like_invalid_invoice_number(value):
                return value

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


def extract_invoice_date(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]
    for line in clean_lines:
        match = re.search(
            r"\b(?:fecha|date)\s*:?\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b",
            line,
            re.IGNORECASE,
        )
        if match:
            year, month, day = match.groups()
            return parse_invoice_date_parts(day, month, year)

        match = re.search(
            r"\b(?:fecha|date)\s*:?\s*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b",
            line,
            re.IGNORECASE,
        )
        if match:
            day, month, year = match.groups()
            return parse_invoice_date_parts(day, month, year)

        match = re.search(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b", line)
        if match:
            day, month, year = match.groups()
            return parse_invoice_date_parts(day, month, year)

    return ""


def extract_supplier_tax_id(lines: list[str]) -> str:
    for line in lines:
        match = TAX_ID_PATTERN.search(line)
        if match:
            return match.group(1).upper()
        match = re.search(r"\b([A-Z])\s*-\s*(\d{8})\b", line, re.IGNORECASE)
        if match:
            return f"{match.group(1).upper()}{match.group(2)}"
    return ""


def extract_supplier_name(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]

    for line in clean_lines[:8]:
        if "mercadona" in normalize_for_rules(line):
            return "Mercadona, S.A."
        if re.search(r"\bS\.?\s*[AL]\s*[-.]?$", line, re.IGNORECASE):
            return normalize_company_name(line)

    for index, line in enumerate(clean_lines):
        if not TAX_ID_PATTERN.search(line):
            continue
        for candidate in reversed(clean_lines[max(0, index - 4) : index]):
            if looks_like_bad_supplier_line(candidate):
                continue
            if re.search(r"\b(?:s\.?a\.?|s\.?l\.?|sa|sl)\b", candidate, re.IGNORECASE):
                return normalize_company_name(candidate)
            if re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", candidate):
                return normalize_company_name(candidate)

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


def looks_like_product_line(line: str) -> bool:
    normalized = normalize_spaces(line).lower()
    if not normalized:
        return False
    if normalized in PRODUCT_IGNORE_LABELS:
        return False
    if any(label in normalized for label in PRODUCT_IGNORE_LABELS):
        return False
    if re.fullmatch(r"[\d\s.,/%€eur-]+", normalized):
        return False
    if re.fullmatch(r"[a-z]{1,2}", normalized):
        return False
    if re.search(r"\d+[,.]\d{2}", normalized):
        return False
    return bool(re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}", line))


def looks_like_weak_concept(value: str) -> bool:
    cleaned = normalize_spaces(value).strip(" :;,.")
    if len(cleaned) < 4:
        return True
    if value.rstrip().endswith(":"):
        return True
    if re.fullmatch(r"[\W\d_]+", cleaned):
        return True
    return False


def is_ignored_item_line(line: str) -> bool:
    normalized = normalize_for_rules(line)
    return any(
        hint in normalized
        for hint in (
            "tarjeta",
            "terminal",
            "entidad",
            "aid",
            "visa",
            "respuesta",
            "fecha",
            "hora",
            "cajera",
            "cajero",
        )
    )


def clean_item_concept(line: str) -> str:
    cleaned = re.sub(r"^\s*\d+(?:[,.]\d{1,2})?\s+", "", line)
    cleaned = re.sub(r"\b\d+[,.]\d{1,2}\s*$", "", cleaned)
    cleaned = re.sub(r"\b\d{2,}\s*$", "", cleaned)
    cleaned = re.sub(r"\b\d+[/:]\d+[,.]?\s*\d*\b.*$", "", cleaned)
    cleaned = re.sub(r"\bca['´`]?.*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^\wÁÉÍÓÚÜÑáéíóúüñ ]+", " ", cleaned)
    cleaned = normalize_spaces(cleaned)
    cleaned = re.sub(r"\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]$", "", cleaned)
    return cleaned.strip(" :;,.")


def extract_item_concepts(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]
    concepts = []
    inside_items = False

    for line in clean_lines:
        normalized = normalize_for_rules(line)
        if (
            ("cant" in normalized and ("desc" in normalized or "ripcion" in normalized))
            or ("su producto" in normalized and "importe" in normalized)
        ):
            inside_items = True
            continue
        if inside_items and ("total" in normalized or "importe total" in normalized):
            break
        if not inside_items or is_ignored_item_line(line):
            continue
        if not re.match(r"^\s*\d+(?:[,.]\d{1,2})?\s+", line):
            continue

        concept = clean_item_concept(line)
        if looks_like_product_line(concept) and concept not in concepts:
            concepts.append(concept)
        if len(concepts) >= 3:
            break

    return " + ".join(concepts[:3])


def count_item_lines(lines: list[str]) -> int:
    count = 0
    for line in lines:
        if is_ignored_item_line(line):
            continue
        if re.match(r"^\s*\d+(?:[,.]\d{1,2})?\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", line):
            concept = clean_item_concept(line)
            if looks_like_product_line(concept):
                count += 1
    return count


def is_supermarket_receipt(lines: list[str]) -> bool:
    text = normalize_for_rules(" ".join(lines))
    if "mercadona" in text:
        return True
    return "factura simplificada" in text and count_item_lines(lines) >= 3


def extract_concept(lines: list[str]) -> str:
    clean_lines = [line.strip() for line in lines if line.strip()]
    stop_labels = ("cant.", "qty", "cantidad", "subtotal", "iva", "vat", "total")
    item_concepts = extract_item_concepts(lines)

    if is_supermarket_receipt(clean_lines) or count_item_lines(clean_lines) >= 3:
        return "Compra supermercado"

    for index, line in enumerate(clean_lines):
        if "su producto" not in line.lower():
            continue
        for candidate in clean_lines[index + 1 : index + 8]:
            concept = clean_amount_suffix(candidate)
            if looks_like_product_line(concept):
                if item_concepts and looks_like_weak_concept(concept):
                    return item_concepts
                return concept

    for index, line in enumerate(clean_lines):
        if not has_any_label(line, stop_labels):
            continue
        for candidate in reversed(clean_lines[max(0, index - 4) : index]):
            if looks_like_bad_text_line(candidate):
                continue
            concept = clean_amount_suffix(candidate)
            if looks_like_product_line(concept):
                if item_concepts and looks_like_weak_concept(concept):
                    return item_concepts
                return concept

    return item_concepts


def parse_noisy_total_amount(line: str, raw_amount: str) -> float:
    cleaned = raw_amount.replace("€", "").replace("EUR", "").replace("Eu", "")
    cleaned = cleaned.replace(" ", "").strip()
    if "," in cleaned or "." in cleaned:
        return parse_amount(cleaned)

    digits = re.sub(r"\D", "", cleaned)
    if not digits or len(digits) < 3 or len(digits) > 5:
        return 0.0
    if len(digits) == 4 and digits.startswith("9"):
        return parse_amount(f"{digits[0]},{digits[-2:]}")
    return int(digits) / 100


def extract_total_from_noisy_total_line(lines: list[str]) -> float:
    clean_lines = [line.strip() for line in lines if line.strip()]
    for index, line in enumerate(clean_lines):
        normalized = normalize_for_rules(line)
        if not (
            "total" in normalized
            or "importe" in normalized
            or "euros" in normalized
            or "entrega efectivo" in normalized
            or "devolucion" in normalized
        ):
            continue
        if any(hint in normalized for hint in ("fecha", "hora", "telefono", "tarjeta", "terminal")):
            continue

        matches = list(AMOUNT_PATTERN.finditer(line))
        for match in reversed(matches):
            amount = parse_noisy_total_amount(line, match.group(1))
            if amount > 0:
                return amount

        for candidate in clean_lines[index + 1 : index + 4]:
            candidate_normalized = normalize_for_rules(candidate)
            if any(
                hint in candidate_normalized
                for hint in ("base imponible", "cuota", "iva")
            ):
                break
            if any(
                hint in candidate_normalized
                for hint in ("fecha", "hora", "telefono", "tarjeta", "terminal")
            ):
                continue
            for match in reversed(list(AMOUNT_PATTERN.finditer(candidate))):
                amount = parse_noisy_total_amount(candidate, match.group(1))
                if amount > 0:
                    return amount

    return 0.0


def detect_incomplete_vat_table(lines: list[str]) -> bool:
    clean_lines = [line.strip() for line in lines if line.strip()]
    for index, line in enumerate(clean_lines):
        normalized = normalize_for_rules(line)
        if not ("base imponible" in normalized and "cuota" in normalized):
            continue
        for candidate in clean_lines[index + 1 : index + 4]:
            amounts = extract_amounts(candidate, has_nearby_decimals=True)
            if len(amounts) == 2:
                return True
    return False


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


def find_total_amount_near(
    lines: list[str],
    start_index: int,
    window_size: int,
    include_amount_label: bool = False,
) -> float:
    for index, line in enumerate(
        lines[start_index : start_index + window_size],
        start=start_index,
    ):
        normalized = line.lower()
        if not (
            "total euros" in normalized
            or "importe total" in normalized
            or (include_amount_label and "importe" in normalized)
            or has_any_label(line, TOTAL_LABELS)
        ):
            continue

        amounts = extract_amounts(line, has_nearby_decimals=True)
        if amounts:
            return amounts[-1]

        for candidate in lines[index + 1 : index + 4]:
            candidate_amounts = extract_amounts(candidate, has_nearby_decimals=True)
            if candidate_amounts:
                return candidate_amounts[0]

    return 0.0


def build_tax_table_result(
    base: float,
    vat_rate: float,
    vat_amount: float,
    total: float,
    reconstructed_vat: bool = False,
    reason: str = "",
) -> dict:
    if base <= 0 or vat_rate < 0 or vat_amount < 0 or total <= 0:
        return {}
    if abs(round(base * vat_rate / 100, 2) - vat_amount) > 0.05:
        return {}
    if not amounts_match(base, vat_amount, total):
        return {}

    final_reason = reason or (
        "VAT amount reconstructed from tax base and VAT rate"
        if reconstructed_vat
        else "Amounts extracted from tax base/rate/quota table"
    )
    return {
        "base": base,
        "vat_rate": vat_rate,
        "vat_amount": vat_amount,
        "total": total,
        "review_status": "ok",
        "confidence": 0.80 if reconstructed_vat else 0.85,
        "review_reasons": [final_reason],
    }


def extract_tax_table_amounts(lines: list[str]) -> dict:
    clean_lines = [line.strip() for line in lines if line.strip()]

    for index, line in enumerate(clean_lines):
        if not (
            has_any_label(line, BASE_LABELS)
            and has_any_label(line, TAX_QUOTA_LABELS)
        ):
            continue

        amount_row = None
        for candidate in clean_lines[index + 1 : index + 6]:
            amounts = extract_amounts(candidate, has_nearby_decimals=True)
            if len(amounts) >= 2:
                amount_row = amounts[:3]
                break
        if not amount_row:
            continue

        base, vat_rate = amount_row[:2]
        vat_amount = amount_row[2] if len(amount_row) >= 3 else round(base * vat_rate / 100, 2)
        total = find_total_amount_near(clean_lines, index + 1, 10)
        result = build_tax_table_result(
            base,
            vat_rate,
            vat_amount,
            total,
            reconstructed_vat=len(amount_row) < 3,
        )
        if result:
            return result

    for index, line in enumerate(clean_lines):
        if "descripcion" not in line.lower() and "descripción" not in line.lower():
            continue

        for candidate in clean_lines[index + 1 : index + 6]:
            amounts = extract_amounts(candidate, has_nearby_decimals=True)
            if len(amounts) < 2:
                continue

            base, vat_rate = amounts[:2]
            vat_amount = amounts[2] if len(amounts) >= 3 else round(base * vat_rate / 100, 2)
            total = find_total_amount_near(clean_lines, index + 1, 10)
            reason = ""
            if not total and len(amounts) < 3:
                total = find_total_amount_near(
                    clean_lines,
                    max(0, index - 8),
                    18,
                    include_amount_label=True,
                )
                reason = (
                    "VAT amount reconstructed from tax base/rate and total near "
                    "amount label"
                )
            result = build_tax_table_result(
                base,
                vat_rate,
                vat_amount,
                total,
                reconstructed_vat=len(amounts) < 3,
                reason=reason,
            )
            if result:
                return result

    for total_index, line in enumerate(clean_lines):
        total = find_total_amount_near(clean_lines, total_index, 1)
        if not total:
            continue

        previous_amounts = []
        for candidate in clean_lines[max(0, total_index - 8) : total_index]:
            amounts = extract_amounts(candidate, has_nearby_decimals=True)
            if len(amounts) == 1:
                previous_amounts.append(amounts[0])
            elif len(amounts) >= 2:
                previous_amounts.extend(amounts[:3])

        if len(previous_amounts) >= 3:
            base, vat_rate, vat_amount = previous_amounts[-3:]
            result = build_tax_table_result(base, vat_rate, vat_amount, total)
            if result:
                return result

        if len(previous_amounts) >= 2:
            base, vat_rate = previous_amounts[-2:]
            vat_amount = round(base * vat_rate / 100, 2)
            result = build_tax_table_result(
                base,
                vat_rate,
                vat_amount,
                total,
                reconstructed_vat=True,
            )
            if result:
                return result

    return {}


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
    supplier_tax_id = result.get("supplier_tax_id") or extract_supplier_tax_id(lines)
    concept = result.get("concept") or extract_concept(lines)
    invoice_number = result.get("invoice_number") or extract_invoice_number(lines)
    invoice_date = result.get("invoice_date") or extract_invoice_date(lines)
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

    if supplier_tax_id:
        result["supplier_tax_id"] = supplier_tax_id
        review_reasons.append("Supplier tax id extracted from CIF/NIF/VAT line")
        confidence = min(0.95, confidence + 0.05)

    if invoice_number:
        result["invoice_number"] = invoice_number
        review_reasons.append(
            "Document identifier extracted from invoice/order/payment reference"
        )
        confidence = min(0.95, confidence + 0.05)

    if invoice_date:
        result["invoice_date"] = invoice_date
        review_reasons.append("Invoice date extracted from ticket text")
        confidence = min(0.95, confidence + 0.05)

    if any("factura simplificada" in line.lower() for line in lines):
        result["document_type"] = "factura_simplificada"
        review_reasons.append("Document type detected as simplified invoice")
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
            "supplier_tax_id": "",
            "concept": "",
            "invoice_number": "",
            "invoice_date": "",
            "document_type": "",
        }
    return {
        "tax_lines": [],
        "total": 0.0,
        "review_status": "revisar",
        "confidence": 0.0,
        "review_reasons": [],
        "supplier_name": "",
        "supplier_tax_id": "",
        "concept": "",
        "invoice_number": "",
        "invoice_date": "",
        "document_type": "",
    }


def build_total_only_response(total: float) -> dict:
    result = build_extraction_response({})
    result["total"] = total
    result["confidence"] = 0.30
    result["review_reasons"] = [
        "Total extracted from noisy total line, VAT not reliable"
    ]
    return result


def build_review_only_response(reason: str) -> dict:
    result = build_extraction_response({})
    result["confidence"] = 0.30
    result["review_reasons"] = [reason]
    return result


def extract_invoice_data(text: str) -> dict:
    lines = text.splitlines()
    tax_table = extract_tax_table_amounts(lines)
    if tax_table:
        return enrich_text_fields(build_extraction_response(tax_table), lines)

    labeled_lines = extract_labeled_amount_lines(lines)
    if labeled_lines:
        return enrich_text_fields(build_extraction_response(labeled_lines), lines)

    vertical_block = extract_vertical_amount_block(lines)
    if vertical_block:
        return enrich_text_fields(build_extraction_response(vertical_block), lines)

    noisy_total = extract_total_from_noisy_total_line(lines)
    if noisy_total:
        response = build_total_only_response(noisy_total)
        if detect_incomplete_vat_table(lines):
            response["review_reasons"].append("Incomplete VAT table detected")
        return enrich_text_fields(response, lines)

    if detect_incomplete_vat_table(lines):
        return enrich_text_fields(
            build_review_only_response("Incomplete VAT table detected"),
            lines,
        )

    return enrich_text_fields(build_extraction_response({}), lines)
