import re


VERSION_PARSER = "costes-3b"
VERSION_PARSER_IVE = "costes-ive-1"
UNIDADES_CONOCIDAS = {
    "m",
    "m2",
    "m²",
    "m3",
    "m³",
    "kg",
    "t",
    "ud",
    "u",
    "h",
    "l",
    "pa",
    "%",
}
UNIDAD_NORMALIZADA = {
    "m²": "m2",
    "m³": "m3",
    "u": "ud",
}
TIPOS_DESCOMPUESTO = {
    "mano_obra",
    "material",
    "maquinaria",
    "porcentaje",
    "auxiliar",
    "partida",
}
CODIGO_RE = r"(?:[A-Z]{2,6}[A-Z0-9]*(?:[._/-][A-Za-z0-9]+)+|[A-Z]{2,6}\d+[A-Za-z0-9._/-]*)"
NUMERO_RE = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)|\d+"
PALABRAS_RUIDO = (
    "presupuesto",
    "generador",
    "base de precios",
    "capitulo",
    "capítulo",
    "medicion",
    "medición",
    "cantidad",
    "rendimiento",
    "importe",
    "precio",
    "total",
    "familia",
    "opciones",
)
CODIGO_IVE_PARTIDA_RE = r"[A-Z]{3,6}\.[A-Za-z0-9]+"
CODIGO_IVE_AUX_RE = r"[A-Z]{3,8}[A-Za-z0-9]*"
CODIGO_IVE_RE = rf"(?:%|{CODIGO_IVE_PARTIDA_RE}|{CODIGO_IVE_AUX_RE})"
RECURSOS_IVE_FRECUENTES = {
    "MOOA.8a": {
        "variantes": ("MOOAa", "MOOA8a", "MOOA.8a"),
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Oficial 1ª construcción",
        "precio_unitario": 25.51,
    },
    "MOOA12a": {
        "variantes": ("MOOA12a", "MODA12a", "MOOA.12a"),
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Peón ordinario construcción",
        "precio_unitario": 21.08,
    },
    "MOOA11a": {
        "variantes": ("MOOA11a", "MOOA.11a"),
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Peón especializado construcción",
        "precio_unitario": 23.28,
    },
    "PBAA.1a": {
        "variantes": ("PBAAa", "PBAA1a", "PBAA.1a"),
        "tipo": "material",
        "unidad": "m3",
        "resumen": "Agua",
        "precio_unitario": 1.12,
    },
    "PFPC.1ac": {
        "variantes": ("PFPC.1ac", "PFPC1ac"),
        "tipo": "material",
        "unidad": "m2",
        "resumen": "Placa yeso laminado A 12.5mm",
        "precio_unitario": 6.35,
    },
    "PFPP11a": {
        "variantes": ("PFPP11a", "PEPP11a", "PFPP.11a"),
        "tipo": "material",
        "unidad": "m",
        "resumen": "Maestra fij pl yeso 70x30mm",
        "precio_unitario": 2.67,
    },
    "PFPP12a": {
        "variantes": ("PFPP12a", "PFPP.12a"),
        "tipo": "material",
        "unidad": "m",
        "resumen": "Perfil simple U 30x30x0.6 mm",
        "precio_unitario": 1.96,
    },
    "PFPP15a": {
        "variantes": ("PFPP15a", "PFPP.15a"),
        "tipo": "material",
        "unidad": "ud",
        "resumen": "Tornillo 25mm p/pnl yeso",
        "precio_unitario": 0.02,
    },
    "PFPP.8b": {
        "variantes": ("PFPP.8b", "PFPP8b"),
        "tipo": "material",
        "unidad": "kg",
        "resumen": "Pasta junta panel yeso c/cinta",
        "precio_unitario": 4.69,
    },
    "PFPP.7a": {
        "variantes": ("PFPP.7a", "PFPP7a"),
        "tipo": "material",
        "unidad": "kg",
        "resumen": "Pasta ayuda panel yeso",
        "precio_unitario": 2.25,
    },
    "PFPP.5a": {
        "variantes": ("PFPPSa", "PFPP5a", "PFPP.5a"),
        "tipo": "material",
        "unidad": "m",
        "resumen": "Banda papel microperforado alt r",
        "precio_unitario": 0.05,
    },
    "PRTW13a": {
        "variantes": ("PRTW13a", "PRTW.13a"),
        "tipo": "material",
        "unidad": "ud",
        "resumen": "Anclaje directo",
        "precio_unitario": 1.21,
    },
    "PRTW13c": {
        "variantes": ("PRTW13c", "PRTW.13c"),
        "tipo": "material",
        "unidad": "ud",
        "resumen": "Pieza empalme en cruz",
        "precio_unitario": 2.91,
    },
    "PRTW13d": {
        "variantes": ("PRTW13d", "PRTW.13d"),
        "tipo": "material",
        "unidad": "ud",
        "resumen": "Conector 60x115x27",
        "precio_unitario": 0.56,
    },
}
RECURSOS_IVE_VARIANTES = {
    variante: codigo
    for codigo, recurso in RECURSOS_IVE_FRECUENTES.items()
    for variante in recurso["variantes"]
}


def normalizar_numero(valor: str | None) -> float | None:
    if not valor:
        return None
    texto = valor.strip().replace("€", "").replace(" ", "")
    texto = texto.rstrip(".,;:")
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _normalizar_unidad(valor: str | None) -> str:
    unidad = (valor or "").strip().lower().rstrip(".,;:")
    return UNIDAD_NORMALIZADA.get(unidad, unidad)


def _normalizar_espacios(texto: str) -> str:
    texto = (texto or "").replace("\t", " ")
    texto = texto.replace("€/ ", "€/").replace(" /", "/")
    return re.sub(r"[ \u00a0]+", " ", texto)


def _normalizar_texto_ive(texto: str) -> str:
    texto = _normalizar_espacios(texto)
    reemplazos = {
        "PastayesoYG/L": "Pasta yeso YG/L",
        "Pasta yesoYG/L": "Pasta yeso YG/L",
        "Placayeso": "Placa yeso",
        "Maestrafjplyeso": "Maestra fij pl yeso",
        "Pastajunta": "Pasta junta",
        "Piezaempalme": "Pieza empalme",
        "Conector60x115x27": "Conector 60x115x27",
        "Peónordinario": "Peón ordinario",
        "Peonordinario": "Peón ordinario",
        "Peónespecializado": "Peón especializado",
        "Peon especializado": "Peón especializado",
        "Guarn-enl": "Guarn-enl",
    }
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)
    texto = re.sub(r"\bOficial 1 construcción\b", "Oficial 1ª construcción", texto)
    texto = re.sub(r"\b125mm\b", "12.5mm", texto)
    texto = re.sub(r"(?<=\d)€", " €", texto)
    texto = re.sub(r"€(?=\d)", "€ ", texto)
    texto = re.sub(r"\s*\|\s*", " | ", texto)
    return _normalizar_espacios(texto)


def _limpiar_prefijo_ocr_ive(linea: str) -> str:
    linea = _normalizar_espacios(linea).strip()
    linea = re.sub(r"^\s*(?:\([^)]{1,4}\)|[|>]+)\s*", "", linea)
    linea = re.sub(r"^\s*(?:Ep|Cp)\s+(?=[A-Z]{3,8}[A-Za-z0-9.]*)", "", linea, flags=re.IGNORECASE)
    return _normalizar_espacios(linea).strip()


def _limpiar_lineas(texto: str) -> list[str]:
    return [
        _limpiar_prefijo_ocr_ive(linea)
        for linea in (texto or "").splitlines()
        if _limpiar_prefijo_ocr_ive(linea)
    ]


def _parece_texto_ive(texto: str, lineas: list[str]) -> bool:
    texto_lower = texto.lower()
    if any(indicador in texto_lower for indicador in ("fiebdc", " bdc ", "base de datos de construcción", "base de datos de construccion")):
        return True
    if re.search(r"c[oó]digo\s+unidad\s+resumen\s+precio\s+unitario\s+rendimiento\s+importe", texto_lower):
        return True
    if any(re.search(r"\b[A-Z]{4,6}\.[A-Za-z0-9]*[a-z][A-Za-z0-9]*\b", linea) for linea in lineas):
        return True
    return False


def _es_ruido(linea: str) -> bool:
    texto = linea.lower()
    return any(palabra in texto for palabra in PALABRAS_RUIDO) and not re.search(CODIGO_RE, linea)


def _detectar_tipo(linea: str) -> str:
    texto = linea.lower()
    if any(palabra in texto for palabra in ("oficial", "peon", "peón", "mano de obra", "mo ")):
        return "mano_obra"
    if any(palabra in texto for palabra in ("maquinaria", "maquina", "máquina", "retro", "camion", "camión")):
        return "maquinaria"
    if "%" in texto or "porcentaje" in texto:
        return "porcentaje"
    if any(palabra in texto for palabra in ("auxiliar", "medio auxiliar")):
        return "auxiliar"
    if re.match(rf"^{CODIGO_RE}\s", linea.strip()):
        return "partida"
    return "material"


def _numeros_en_linea(linea: str) -> list[float]:
    valores = []
    for match in re.finditer(NUMERO_RE, linea):
        numero = normalizar_numero(match.group(0))
        if numero is not None:
            valores.append(numero)
    return valores


def _extraer_precio_principal(lineas: list[str]) -> float | None:
    patrones = (
        rf"(?:precio|importe|total|p\.?u\.?)\s*(?:partida|unitario|final)?\s*[:=]?\s*({NUMERO_RE})\s*€?",
        rf"({NUMERO_RE})\s*€/([a-zA-Z0-9%²³]+)",
    )
    candidatos_columna_final = []
    for linea in lineas:
        texto = linea.lower()
        for patron in patrones:
            match = re.search(patron, texto)
            if match:
                return normalizar_numero(match.group(1))
        if re.search(CODIGO_RE, linea) and any(unidad in texto.split() for unidad in UNIDADES_CONOCIDAS):
            numeros = _numeros_en_linea(linea)
            if numeros:
                candidatos_columna_final.append(numeros[-1])
    return candidatos_columna_final[0] if candidatos_columna_final else None


def _extraer_codigo_y_resumen(lineas: list[str]) -> tuple[str, str, str]:
    for linea in lineas:
        match = re.search(rf"\b({CODIGO_RE})\b\s*(.*)", linea)
        if not match:
            continue
        codigo = match.group(1)
        resto = match.group(2).strip(" -·:\t")
        unidad = ""
        if resto:
            partes = resto.split()
            if partes and _normalizar_unidad(partes[0]) in UNIDADES_CONOCIDAS:
                unidad = _normalizar_unidad(partes[0])
                resto = " ".join(partes[1:]).strip()
        return codigo, unidad, resto
    return "", "", ""


def _extraer_unidad(texto: str, lineas: list[str], codigo: str, unidad_codigo: str) -> str:
    if unidad_codigo:
        return _normalizar_unidad(unidad_codigo)

    unidad_match = re.search(
        r"(?:unidad|ud\.?|medici[oó]n)\s*[:=]?\s*(m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\b",
        texto,
        re.IGNORECASE,
    )
    if unidad_match:
        return _normalizar_unidad(unidad_match.group(1))

    if codigo:
        for linea in lineas:
            if codigo not in linea:
                continue
            partes = [_normalizar_unidad(parte) for parte in linea.split()]
            for parte in partes:
                if parte in UNIDADES_CONOCIDAS:
                    return parte
    return ""


def _extraer_descripcion(lineas: list[str], resumen: str) -> str:
    descripcion = []
    capturando = False
    for linea in lineas:
        if re.match(r"^(descripci[oó]n|texto descriptivo)\b", linea, re.IGNORECASE):
            capturando = True
            resto = re.sub(r"^(descripci[oó]n|texto descriptivo)\s*[:.-]?\s*", "", linea, flags=re.IGNORECASE).strip()
            if resto:
                descripcion.append(resto)
            continue
        if _es_ruido(linea):
            continue
        if resumen and linea.strip() == resumen.strip():
            continue
        if re.match(rf"^{CODIGO_RE}\b", linea):
            continue
        if _parsear_linea_descompuesto(linea, 1):
            continue
        if re.search(r"\b(c[oó]digo|unidad|resumen|rendimiento|precio|importe)\b", linea, re.IGNORECASE):
            continue
        if len(linea) > 18:
            descripcion.append(linea)
        if len(descripcion) >= 6 or (descripcion and not capturando and len(descripcion) >= 3):
            break
    return "\n".join(descripcion)


def _extraer_metadatos(texto: str) -> dict:
    fecha_match = re.search(r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b", texto)
    provincia_match = re.search(r"(?:provincia|ámbito|ambito)\s*[:=]\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ ]{3,40})", texto, re.IGNORECASE)
    familias = []
    for linea in _limpiar_lineas(texto):
        if re.search(r"(familia|opci[oó]n|seleccionad)", linea, re.IGNORECASE):
            familias.append(linea)
    return {
        "fecha_base": fecha_match.group(1).replace("/", "-") if fecha_match else "",
        "provincia": provincia_match.group(1).strip() if provincia_match else "",
        "familias_opciones": familias,
    }


def _parsear_linea_descompuesto(linea: str, orden: int) -> dict | None:
    patron_resumen_unidad = re.compile(
        rf"^(?P<codigo>{CODIGO_RE})\s+"
        r"(?P<resto>.+?)\s+"
        r"(?P<unidad>m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\s+"
        rf"(?P<rendimiento>{NUMERO_RE})\s+"
        rf"(?P<precio>{NUMERO_RE})"
        rf"(?:\s+(?P<importe>{NUMERO_RE}))?\s*€?\s*$",
        re.IGNORECASE,
    )
    patron_unidad_resumen = re.compile(
        rf"^(?P<codigo>{CODIGO_RE})\s+"
        r"(?P<unidad>m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\s+"
        r"(?P<resto>.+?)\s+"
        rf"(?P<rendimiento>{NUMERO_RE})\s+"
        rf"(?P<precio>{NUMERO_RE})"
        rf"(?:\s+(?P<importe>{NUMERO_RE}))?\s*€?\s*$",
        re.IGNORECASE,
    )
    match = patron_resumen_unidad.match(linea.strip()) or patron_unidad_resumen.match(linea.strip())
    if not match:
        return None

    rendimiento = normalizar_numero(match.group("rendimiento")) or 0
    precio_unitario = normalizar_numero(match.group("precio")) or 0
    importe = normalizar_numero(match.group("importe"))
    if importe is None:
        importe = round(precio_unitario * rendimiento, 2)
    return {
        "codigo": match.group("codigo").strip(),
        "tipo": _detectar_tipo(linea),
        "unidad": _normalizar_unidad(match.group("unidad")),
        "resumen": match.group("resto").strip(),
        "precio_unitario": round(precio_unitario, 4),
        "rendimiento": round(rendimiento, 4),
        "importe": round(importe, 2),
        "orden": orden,
    }


def _normalizar_importe_ive(valor: float, esperado: float, advertencias: list[str], codigo: str) -> float:
    if esperado <= 0:
        return round(valor, 2)
    candidatos = [valor]
    if valor >= 100:
        candidatos.extend([valor / 10, valor / 100, valor / 1000])
    elif valor >= 10 and esperado < 10:
        candidatos.extend([valor / 10, valor / 100])
    mejor = min(candidatos, key=lambda candidato: abs(candidato - esperado))
    if abs(mejor - valor) > 0.001:
        advertencias.append(
            f"Importe OCR de {codigo} corregido de {valor:.2f} a {mejor:.2f} por coherencia con rendimiento."
        )
    return round(mejor, 2)


def _normalizar_numero_token_ive(valor: str | None) -> float | None:
    texto = (valor or "").strip().replace("€", "").replace(" ", "")
    texto = texto.rstrip(".,;:")
    if re.fullmatch(r"0+\d{2,}", texto):
        return int(texto) / 100
    return normalizar_numero(texto)


def _variantes_compactas_ive(valor: float, token: str | None = None) -> list[float]:
    texto = (token or "").strip().replace("€", "").replace(" ", "").rstrip(".,;:")
    candidatos = [valor]
    if "," in texto or "." in texto:
        return candidatos
    if valor >= 100:
        candidatos.extend([valor / 10, valor / 100, valor / 1000])
    elif valor >= 10:
        candidatos.extend([valor / 10, valor / 100])
    return candidatos


def _normalizar_precio_importe_ive(
    precio_unitario: float,
    rendimiento: float,
    importe_detectado: float,
    advertencias: list[str],
    codigo: str,
    precio_token: str | None = None,
    importe_token: str | None = None,
) -> tuple[float, float]:
    if precio_unitario <= 0 or rendimiento <= 0:
        return round(precio_unitario, 4), round(importe_detectado, 2)

    candidatos = [
        (precio_candidato, importe_candidato)
        for precio_candidato in _variantes_compactas_ive(precio_unitario, precio_token)
        for importe_candidato in _variantes_compactas_ive(importe_detectado, importe_token)
    ]
    precio, importe = min(
        candidatos,
        key=lambda candidato: abs(
            round(candidato[0] * rendimiento, 2) - round(candidato[1], 2)
        ),
    )
    if abs(precio - precio_unitario) > 0.001:
        advertencias.append(
            "Precio unitario OCR de "
            f"{codigo} corregido de {precio_unitario:.2f} a {precio:.2f} "
            "por coherencia con rendimiento e importe."
        )
    if abs(importe - importe_detectado) > 0.001:
        advertencias.append(
            f"Importe OCR de {codigo} corregido de {importe_detectado:.2f} a {importe:.2f} "
            "por coherencia con rendimiento."
        )
    return round(precio, 4), round(importe, 2)


def normalizar_recurso_ive(
    codigo_ocr: str,
    resumen_ocr: str | None = None,
    unidad_ocr: str | None = None,
    precio_ocr: float | None = None,
    usar_precio_recurso: bool = False,
) -> dict | None:
    codigo_limpio = (codigo_ocr or "").strip()
    codigo_normalizado = RECURSOS_IVE_VARIANTES.get(codigo_limpio)
    if not codigo_normalizado:
        return None

    recurso = RECURSOS_IVE_FRECUENTES[codigo_normalizado]
    advertencias = []
    if codigo_limpio != codigo_normalizado:
        advertencias.append(f"Recurso OCR {codigo_limpio} normalizado como {codigo_normalizado}.")
        advertencias.append(f"Código OCR {codigo_limpio} corregido a {codigo_normalizado}.")
    precio_unitario = recurso["precio_unitario"] if usar_precio_recurso else precio_ocr
    if precio_unitario is None:
        precio_unitario = recurso["precio_unitario"]
    if (
        usar_precio_recurso
        and precio_ocr is not None
        and abs(float(precio_ocr) - recurso["precio_unitario"]) > 0.001
    ):
        advertencias.append(
            "Precio unitario OCR "
            f"{float(precio_ocr):.2f} sustituido por recurso frecuente "
            f"{codigo_normalizado} = {recurso['precio_unitario']:.2f}."
        )
    if unidad_ocr and _normalizar_unidad(unidad_ocr) != recurso["unidad"]:
        advertencias.append(
            f"Unidad OCR {unidad_ocr} sustituida por recurso frecuente {codigo_normalizado} = {recurso['unidad']}."
        )
    if resumen_ocr and _normalizar_espacios(resumen_ocr).strip() != recurso["resumen"]:
        advertencias.append(f"Resumen OCR sustituido por recurso frecuente {codigo_normalizado}.")

    return {
        "codigo": codigo_normalizado,
        "tipo": recurso["tipo"],
        "unidad": recurso["unidad"],
        "resumen": recurso["resumen"],
        "precio_unitario": precio_unitario,
        "advertencias": advertencias,
    }


def _normalizar_precio_unitario_ive(
    precio_unitario: float,
    rendimiento: float,
    importe_detectado: float,
    advertencias: list[str],
    codigo: str,
) -> float:
    if precio_unitario <= 0 or rendimiento <= 0:
        return precio_unitario

    candidatos = [precio_unitario]
    if precio_unitario >= 100:
        candidatos.extend([precio_unitario / 10, precio_unitario / 100, precio_unitario / 1000])
    elif precio_unitario >= 10 and importe_detectado < 1:
        candidatos.extend([precio_unitario / 10, precio_unitario / 100])

    mejor = min(
        candidatos,
        key=lambda candidato: abs(round(candidato * rendimiento, 2) - round(importe_detectado, 2)),
    )
    if abs(mejor - precio_unitario) > 0.001:
        advertencias.append(
            "Precio unitario OCR de "
            f"{codigo} corregido de {precio_unitario:.2f} a {mejor:.2f} "
            "por coherencia con rendimiento e importe."
        )
    return round(mejor, 4)


def _parsear_auxiliar_porcentaje_ive(linea: str, orden: int, advertencias: list[str]) -> dict | None:
    if not re.search(r"directos\s+complementarios", linea, re.IGNORECASE):
        return None

    numeros = [
        (match.group(0), normalizar_numero(match.group(0)))
        for match in re.finditer(NUMERO_RE, linea)
    ]
    valores = [
        _normalizar_numero_token_ive(texto)
        for texto, _valor in numeros
    ]
    valores = [valor for valor in valores if valor is not None]
    if len(valores) < 3:
        advertencias.append(
            "Concepto auxiliar IVE de costes directos complementarios sin importes suficientes."
        )
        return {
            "codigo": "%",
            "tipo": "porcentaje",
            "unidad": "%",
            "resumen": "Costes directos complementarios",
            "precio_unitario": 0,
            "rendimiento": 0,
            "importe": 0,
            "orden": orden,
        }

    precio_unitario, rendimiento, importe_detectado = valores[-3:]
    precio_unitario = _normalizar_precio_unitario_ive(
        precio_unitario,
        rendimiento,
        importe_detectado,
        advertencias,
        "%",
    )
    importe_calculado = round(precio_unitario * rendimiento, 2)
    importe = _normalizar_importe_ive(
        importe_detectado,
        importe_calculado,
        advertencias,
        "%",
    )
    if abs(importe - importe_calculado) > 0.03:
        advertencias.append(
            f"Importe de % recalculado por descuadre OCR ({importe:.2f} -> {importe_calculado:.2f})."
        )
        importe = importe_calculado

    return {
        "codigo": "%",
        "tipo": "porcentaje",
        "unidad": "%",
        "resumen": "Costes directos complementarios",
        "precio_unitario": round(precio_unitario, 4),
        "rendimiento": round(rendimiento, 4),
        "importe": round(importe, 2),
        "orden": orden,
    }


def _parsear_linea_descompuesto_ive(linea: str, orden: int, advertencias: list[str]) -> dict | None:
    auxiliar = _parsear_auxiliar_porcentaje_ive(linea, orden, advertencias)
    if auxiliar:
        return auxiliar

    patron = re.compile(
        rf"^(?P<codigo>{CODIGO_IVE_RE})\s+"
        r"(?P<unidad>m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\s+"
        r"(?P<resumen>.+?)\s+"
        rf"(?P<num1>{NUMERO_RE})\s*€?\s+"
        rf"(?P<num2>{NUMERO_RE})\s+"
        rf"(?P<importe>{NUMERO_RE})\s*€?\s*$",
        re.IGNORECASE,
    )
    match = patron.match(linea.strip())
    if not match:
        return None

    codigo = match.group("codigo").strip()
    codigo_ocr_original = codigo
    resumen = _normalizar_espacios(match.group("resumen")).strip()
    if codigo == "MOOASa":
        codigo = "MOOA.8a"
        advertencias.append("Código OCR MOOASa corregido a MOOA.8a.")
    es_agua = False
    if codigo == "PBAAa" and re.search(r"\bagua\b", resumen, re.IGNORECASE):
        es_agua = True
    num1_token = match.group("num1")
    num2_token = match.group("num2")
    importe_token = match.group("importe")
    num1 = _normalizar_numero_token_ive(num1_token) or 0
    num2 = _normalizar_numero_token_ive(num2_token) or 0
    importe_detectado = _normalizar_numero_token_ive(importe_token) or 0
    es_mano_obra = _detectar_tipo(f"{codigo} {resumen}") == "mano_obra"
    if num1 < 1 and num2 > num1 and not es_mano_obra:
        precio_unitario = num1
        precio_token = num1_token
        rendimiento = num2
    elif num1 > num2:
        precio_unitario = num1
        precio_token = num1_token
        rendimiento = num2
    else:
        rendimiento = num1
        precio_unitario = num2
        precio_token = num2_token
    precio_unitario, importe = _normalizar_precio_importe_ive(
        precio_unitario,
        rendimiento,
        importe_detectado,
        advertencias,
        codigo,
        precio_token,
        importe_token,
    )
    recurso_ive = normalizar_recurso_ive(
        codigo,
        resumen,
        match.group("unidad"),
        precio_unitario,
        usar_precio_recurso=(
            codigo_ocr_original != "MOOASa"
            and (
                codigo_ocr_original != codigo
                or codigo_ocr_original != RECURSOS_IVE_VARIANTES.get(codigo_ocr_original, codigo_ocr_original)
                or (precio_token and "." not in precio_token and "," not in precio_token)
            )
        ),
    )
    if recurso_ive:
        advertencias.extend(recurso_ive["advertencias"])
        codigo = recurso_ive["codigo"]
        resumen = recurso_ive["resumen"]
        precio_unitario = recurso_ive["precio_unitario"]
        es_mano_obra = recurso_ive["tipo"] == "mano_obra"
    importe_calculado = round(precio_unitario * rendimiento, 2)
    if abs(importe - importe_calculado) > 0.03:
        advertencias.append(
            f"Importe de {codigo} recalculado por descuadre OCR ({importe:.2f} -> {importe_calculado:.2f})."
        )
        importe = importe_calculado
    tipo_descompuesto = _detectar_tipo(f"{codigo} {resumen}")
    if recurso_ive:
        tipo_descompuesto = recurso_ive["tipo"]
    elif es_agua:
        tipo_descompuesto = "material"
    elif "." not in codigo and not es_mano_obra and tipo_descompuesto == "partida":
        tipo_descompuesto = "material"
    return {
        "codigo": codigo,
        "tipo": tipo_descompuesto,
        "unidad": recurso_ive["unidad"] if recurso_ive else _normalizar_unidad(match.group("unidad")),
        "resumen": resumen,
        "precio_unitario": round(precio_unitario, 4),
        "rendimiento": round(rendimiento, 4),
        "importe": round(importe, 2),
        "orden": orden,
    }


def _extraer_partida_principal_ive(lineas: list[str]) -> tuple[int, str, str, str, float | None]:
    patron_con_precio = re.compile(
        rf"\b(?P<codigo>{CODIGO_IVE_PARTIDA_RE})\b\s*(?:\|\s*)?"
        r"(?P<unidad>m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\b\s*(?:\|\s*)?"
        rf"(?P<resumen>.+?)\s+(?P<precio>{NUMERO_RE})\s*€?(?:/[A-Za-z0-9²³%]+)?\s*$",
        re.IGNORECASE,
    )
    patron_sin_precio = re.compile(
        rf"\b(?P<codigo>{CODIGO_IVE_PARTIDA_RE})\b\s*(?:\|\s*)?"
        r"(?P<unidad>m2|m²|m3|m³|kg|ud|u|h|m|t|l|pa|%)\b\s*(?:\|\s*)?"
        r"(?P<resumen>.+?)\s*$",
        re.IGNORECASE,
    )
    for indice, linea in enumerate(lineas):
        if re.search(r"\b(c[oó]digo\s+(?:unidad|ud)|precio\s+unitario\s+rendimiento\s+importe)\b", linea, re.IGNORECASE):
            break
        match = patron_con_precio.search(linea)
        tiene_precio_en_linea = True
        if not match:
            match = patron_sin_precio.search(linea)
            tiene_precio_en_linea = False
            if not match:
                continue
        codigo = match.group("codigo").strip()
        if "." not in codigo:
            continue
        resumen = _normalizar_espacios(match.group("resumen")).strip(" -·|")
        if not resumen or re.search(r"\b(c[oó]digo|unidad|rendimiento|importe)\b", resumen, re.IGNORECASE):
            continue
        precio = normalizar_numero(match.group("precio")) if tiene_precio_en_linea else None
        if precio is None:
            for linea_precio in lineas[indice + 1 :]:
                if re.search(r"\b(c[oó]digo\s+(?:unidad|ud)|precio\s+unitario\s+rendimiento\s+importe)\b", linea_precio, re.IGNORECASE):
                    break
                match_precio_suelto = re.fullmatch(
                    rf"({NUMERO_RE})\s*€?(?:/[A-Za-z0-9²³%]+)?",
                    linea_precio,
                    re.IGNORECASE,
                )
                if match_precio_suelto:
                    precio = normalizar_numero(match_precio_suelto.group(1))
                    break
                match_precio = re.search(
                    rf"(?:precio|importe|total)\s*(?:partida|final)?\s*[:=]?\s*({NUMERO_RE})\s*€?(?:/[A-Za-z0-9²³%]+)?",
                    linea_precio,
                    re.IGNORECASE,
                )
                if match_precio:
                    precio = normalizar_numero(match_precio.group(1))
                    break
        return indice, codigo, _normalizar_unidad(match.group("unidad")), resumen, precio
    return -1, "", "", "", None


def _extraer_descripcion_ive(lineas: list[str], indice_principal: int) -> str:
    descripcion = []
    for linea in lineas[indice_principal + 1 :]:
        if re.search(r"\b(c[oó]digo\s+unidad\s+resumen|precio\s+unitario\s+rendimiento\s+importe)\b", linea, re.IGNORECASE):
            break
        if _parsear_linea_descompuesto_ive(linea, 1, []):
            break
        if re.match(rf"^(?:{CODIGO_IVE_RE})\s+", linea):
            break
        linea_limpia = re.sub(r"^(descripci[oó]n|texto descriptivo|descripci[oó]n t[eé]cnica)\s*[:.-]?\s*", "", linea, flags=re.IGNORECASE).strip()
        if not linea_limpia:
            continue
        if _es_ruido(linea_limpia):
            continue
        if len(linea_limpia) > 12:
            descripcion.append(linea_limpia)
    return "\n".join(descripcion).strip()


def _parsear_coste_ive(texto: str) -> dict:
    texto_ive = _normalizar_texto_ive(texto or "")
    lineas = _limpiar_lineas(texto_ive)
    advertencias = []
    datos = {
        "codigo": "",
        "unidad": "",
        "resumen": "",
        "descripcion": "",
        "precio": None,
        "moneda": "EUR",
        "fecha_base": "",
        "provincia": "",
        "familias_opciones": [],
        "descompuestos": [],
    }

    indice, codigo, unidad, resumen, precio = _extraer_partida_principal_ive(lineas)
    datos["codigo"] = codigo
    datos["unidad"] = unidad
    datos["resumen"] = resumen
    datos["precio"] = precio
    datos["descripcion"] = _extraer_descripcion_ive(lineas, indice) if indice >= 0 else ""
    datos.update(_extraer_metadatos(texto_ive))

    if "MOOASa" in (texto or ""):
        advertencias.append("Código OCR MOOASa corregido a MOOA.8a.")

    orden = 1
    linea_anterior = ""
    for linea in lineas:
        descompuesto = _parsear_linea_descompuesto_ive(linea, orden, advertencias)
        if descompuesto is None:
            descompuesto = _parsear_linea_descompuesto(linea, orden)
        if descompuesto and descompuesto["codigo"] != datos["codigo"]:
            if (
                descompuesto["codigo"] == "%"
                and not datos["descompuestos"]
                and linea_anterior
            ):
                previo = _parsear_linea_descompuesto_ive(linea_anterior, orden, advertencias)
                if previo is None:
                    previo = _parsear_linea_descompuesto(linea_anterior, orden)
                if previo and previo["codigo"] != datos["codigo"] and previo["codigo"] != "%":
                    datos["descompuestos"].append(previo)
                    orden += 1
                    descompuesto["orden"] = orden
            datos["descompuestos"].append(descompuesto)
            orden += 1
        linea_anterior = linea

    if datos["precio"] is not None:
        for indice_item, descompuesto in enumerate(datos["descompuestos"]):
            if descompuesto["codigo"] != "%" or indice_item == 0:
                continue
            subtotal_previo = round(
                sum(item["importe"] for item in datos["descompuestos"][:indice_item]),
                2,
            )
            if subtotal_previo <= 0:
                continue
            importe_subtotal = round(
                subtotal_previo * float(descompuesto["rendimiento"] or 0),
                2,
            )
            total_actual = round(sum(item["importe"] for item in datos["descompuestos"]), 2)
            total_subtotal = round(total_actual - descompuesto["importe"] + importe_subtotal, 2)
            if (
                abs(total_subtotal - datos["precio"]) + 0.001 < abs(total_actual - datos["precio"])
                and abs(float(descompuesto["precio_unitario"] or 0) - subtotal_previo) > 0.03
            ):
                advertencias.append(
                    "Precio unitario OCR de % corregido de "
                    f"{float(descompuesto['precio_unitario'] or 0):.2f} a {subtotal_previo:.2f} "
                    "por subtotal previo de descompuestos."
                )
                descompuesto["precio_unitario"] = subtotal_previo
                descompuesto["importe"] = importe_subtotal

    if not datos["codigo"]:
        advertencias.append("No se ha detectado código principal IVE con confianza.")
    if not datos["unidad"]:
        advertencias.append("No se ha detectado unidad principal IVE con confianza.")
    if not datos["resumen"]:
        advertencias.append("No se ha detectado resumen principal IVE con confianza.")
    if datos["precio"] is None:
        advertencias.append("No se ha detectado precio principal IVE con confianza.")
    if not datos["descompuestos"]:
        advertencias.append("No se han detectado descompuestos IVE.")
    if datos["precio"] is not None and datos["descompuestos"]:
        suma = round(sum(item["importe"] for item in datos["descompuestos"]), 2)
        diferencia = round(datos["precio"] - suma, 2)
        if abs(diferencia) > 0.05:
            advertencias.append(
                "La suma de descompuestos IVE no coincide con el precio principal "
                f"(diferencia {diferencia:.2f} €)."
            )

    confianza = _calcular_confianza(datos, advertencias)
    return {
        "datos_parseados": datos,
        "advertencias": advertencias,
        "confianza": confianza,
        "campos_detectados": confianza["campos_detectados"],
        "version_parser": VERSION_PARSER_IVE,
    }


def _calcular_confianza(datos: dict, advertencias: list[str]) -> dict:
    campos = {
        "codigo": bool(datos["codigo"]),
        "unidad": bool(datos["unidad"]),
        "resumen": bool(datos["resumen"]),
        "precio": datos["precio"] is not None,
        "descompuestos": bool(datos["descompuestos"]),
    }
    detectados = sum(1 for valor in campos.values() if valor)
    total = len(campos)
    score = max(0.0, min(1.0, detectados / total - (0.05 * len(advertencias))))
    return {
        "score": round(score, 2),
        "campos_detectados": campos,
    }


def parsear_coste_desde_texto(texto: str) -> dict:
    texto_normalizado = _normalizar_espacios(texto or "")
    lineas = _limpiar_lineas(texto_normalizado)
    advertencias = []
    datos = {
        "codigo": "",
        "unidad": "",
        "resumen": "",
        "descripcion": "",
        "precio": None,
        "moneda": "EUR",
        "fecha_base": "",
        "provincia": "",
        "familias_opciones": [],
        "descompuestos": [],
    }

    if not lineas:
        advertencias.append("No hay texto OCR para parsear.")
        confianza = _calcular_confianza(datos, advertencias)
        return {
            "datos_parseados": datos,
            "advertencias": advertencias,
            "confianza": confianza,
            "campos_detectados": confianza["campos_detectados"],
            "version_parser": VERSION_PARSER,
        }

    if _parece_texto_ive(texto_normalizado, lineas):
        return _parsear_coste_ive(texto_normalizado)

    codigo, unidad_codigo, resumen = _extraer_codigo_y_resumen(lineas)
    datos["codigo"] = codigo
    datos["unidad"] = _extraer_unidad(texto_normalizado, lineas, codigo, unidad_codigo)
    datos["resumen"] = resumen
    if not datos["resumen"]:
        for linea in lineas:
            if _es_ruido(linea):
                continue
            if not re.search(r"\d+(?:[.,]\d+)?", linea) and len(linea) > 12:
                datos["resumen"] = linea
                break

    datos["descripcion"] = _extraer_descripcion(lineas, datos["resumen"])
    datos["precio"] = _extraer_precio_principal(lineas)
    metadatos = _extraer_metadatos(texto_normalizado)
    datos.update(metadatos)

    orden = 1
    for linea in lineas:
        descompuesto = _parsear_linea_descompuesto(linea, orden)
        if descompuesto and descompuesto["codigo"] != datos["codigo"]:
            datos["descompuestos"].append(descompuesto)
            orden += 1

    if not datos["codigo"]:
        advertencias.append("No se ha detectado un código de partida con confianza.")
    if not datos["unidad"]:
        advertencias.append("No se ha detectado unidad con confianza.")
    if not datos["resumen"]:
        advertencias.append("No se ha detectado resumen con confianza.")
    if datos["precio"] is None:
        advertencias.append("No se ha detectado precio principal con confianza.")
    if not datos["descompuestos"]:
        advertencias.append("No se han detectado líneas de descomposición.")
    if datos["precio"] is not None and datos["descompuestos"]:
        suma = round(sum(item["importe"] for item in datos["descompuestos"]), 2)
        diferencia = round(datos["precio"] - suma, 2)
        if abs(diferencia) > 0.05:
            advertencias.append(
                "La suma de descompuestos no coincide con el precio detectado "
                f"(diferencia {diferencia:.2f} €)."
            )

    confianza = _calcular_confianza(datos, advertencias)
    return {
        "datos_parseados": datos,
        "advertencias": advertencias,
        "confianza": confianza,
        "campos_detectados": confianza["campos_detectados"],
        "version_parser": VERSION_PARSER,
    }
