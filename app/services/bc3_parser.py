from pathlib import Path


VERSION_PARSER = "costes-3"
CODIFICACIONES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def normalizar_numero_bc3(valor: str | None) -> float | None:
    texto = (valor or "").strip().replace("€", "").replace(" ", "")
    texto = texto.rstrip(".,;:")
    if not texto:
        return None
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _leer_texto(ruta: str | Path) -> tuple[str, str, list[str]]:
    contenido = Path(ruta).read_bytes()
    advertencias = []
    for encoding in CODIFICACIONES:
        try:
            return contenido.decode(encoding), encoding, advertencias
        except UnicodeDecodeError:
            continue
    advertencias.append("No se pudo detectar codificación; se usa latin-1 con sustitución.")
    return contenido.decode("latin-1", errors="replace"), "latin-1", advertencias


def _normalizar_registros(texto: str) -> list[str]:
    registros = []
    actual = []
    for linea in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("~"):
            if actual:
                registros.append(" ".join(actual).strip())
            actual = [linea]
        elif actual:
            actual.append(linea)
    if actual:
        registros.append(" ".join(actual).strip())
    return registros


def _limpiar_campo(valor: str | None) -> str:
    return (valor or "").strip().strip(";")


def _inferir_tipo(codigo: str, unidad: str, resumen: str) -> str:
    texto = f"{codigo} {unidad} {resumen}".lower()
    if unidad == "h" or any(palabra in texto for palabra in ("oficial", "peon", "peón", "mano de obra")):
        return "mano_obra"
    if any(palabra in texto for palabra in ("maquinaria", "maquina", "máquina", "camion", "camión")):
        return "maquinaria"
    if unidad == "%" or "%" in texto:
        return "porcentaje"
    if any(palabra in texto for palabra in ("auxiliar", "medio auxiliar")):
        return "auxiliar"
    return "partida" if "." in codigo else "material"


def _parsear_c(registro: str, advertencias: list[str]) -> dict | None:
    partes = registro.split("|")
    if len(partes) < 2:
        advertencias.append(f"Registro ~C ignorado por formato incompleto: {registro[:80]}")
        return None

    codigo = _limpiar_campo(partes[1])
    if not codigo:
        advertencias.append("Registro ~C sin código ignorado.")
        return None

    unidad = _limpiar_campo(partes[2]) if len(partes) > 2 else ""
    resumen = _limpiar_campo(partes[3]) if len(partes) > 3 else ""
    precio = None
    for campo in partes[4:]:
        precio = normalizar_numero_bc3(campo)
        if precio is not None:
            break

    return {
        "codigo": codigo,
        "tipo": _inferir_tipo(codigo, unidad.lower(), resumen),
        "unidad": unidad,
        "resumen": resumen,
        "descripcion": "",
        "precio": precio if precio is not None else 0.0,
        "moneda": "EUR",
    }


def _partes_descompuesto(registro: str) -> list[str]:
    partes_pipe = [_limpiar_campo(parte) for parte in registro.split("|")]
    if len(partes_pipe) >= 4:
        return [parte for parte in partes_pipe if parte]
    normalizado = registro.replace("\\", "|")
    return [parte for parte in (_limpiar_campo(parte) for parte in normalizado.split("|")) if parte]


def _parsear_d(registro: str, advertencias: list[str]) -> list[dict]:
    partes = _partes_descompuesto(registro)
    if len(partes) < 3:
        advertencias.append(f"Registro ~D ignorado por formato incompleto: {registro[:80]}")
        return []

    padre = _limpiar_campo(partes[1])
    descompuestos = []
    payload = partes[2:]
    if len(payload) >= 2 and len(payload) % 4 != 0:
        codigo_hijo = payload[0]
        rendimiento = normalizar_numero_bc3(payload[1]) if len(payload) > 1 else None
        precio = normalizar_numero_bc3(payload[2]) if len(payload) > 2 else None
        importe = normalizar_numero_bc3(payload[3]) if len(payload) > 3 else None
        payload = [codigo_hijo, rendimiento, precio, importe]

    for index in range(0, len(payload), 4):
        grupo = payload[index : index + 4]
        if len(grupo) < 2:
            continue
        codigo_hijo = _limpiar_campo(str(grupo[0]))
        if not codigo_hijo:
            continue
        rendimiento = normalizar_numero_bc3(str(grupo[1])) or 0.0
        precio_unitario = normalizar_numero_bc3(str(grupo[2])) if len(grupo) > 2 else None
        importe = normalizar_numero_bc3(str(grupo[3])) if len(grupo) > 3 else None
        descompuestos.append(
            {
                "codigo_padre": padre,
                "codigo_hijo": codigo_hijo,
                "precio_unitario": precio_unitario,
                "rendimiento": rendimiento,
                "importe": importe,
                "orden": (index // 4) + 1,
            }
        )
    if not descompuestos:
        advertencias.append(f"Registro ~D sin líneas útiles para {padre or 'padre desconocido'}.")
    return descompuestos


def _parsear_t(registro: str, advertencias: list[str]) -> dict | None:
    partes = registro.split("|", 2)
    if len(partes) < 3:
        advertencias.append(f"Registro ~T ignorado por formato incompleto: {registro[:80]}")
        return None
    codigo = _limpiar_campo(partes[1])
    texto = _limpiar_campo(partes[2]).replace("\\n", "\n")
    if not codigo or not texto:
        return None
    return {"codigo": codigo, "texto": texto}


def parsear_bc3_desde_texto(texto: str) -> dict:
    advertencias: list[str] = []
    conceptos: dict[str, dict] = {}
    descompuestos: list[dict] = []
    textos: list[dict] = []
    registros = _normalizar_registros(texto or "")

    for registro in registros:
        tipo = registro[:2].upper()
        if tipo == "~C":
            concepto = _parsear_c(registro, advertencias)
            if concepto:
                if concepto["codigo"] in conceptos:
                    advertencias.append(f"Concepto duplicado en archivo saltado: {concepto['codigo']}")
                else:
                    conceptos[concepto["codigo"]] = concepto
        elif tipo == "~D":
            descompuestos.extend(_parsear_d(registro, advertencias))
        elif tipo == "~T":
            texto_registro = _parsear_t(registro, advertencias)
            if texto_registro:
                textos.append(texto_registro)
        else:
            advertencias.append(f"Registro {tipo or 'desconocido'} no soportado e ignorado.")

    for texto_registro in textos:
        concepto = conceptos.get(texto_registro["codigo"])
        if concepto:
            concepto["descripcion"] = texto_registro["texto"]

    return {
        "conceptos": list(conceptos.values()),
        "descompuestos": descompuestos,
        "textos": textos,
        "advertencias": advertencias,
        "estadisticas": {
            "registros": len(registros),
            "conceptos": len(conceptos),
            "descompuestos": len(descompuestos),
            "textos": len(textos),
        },
        "version_parser": VERSION_PARSER,
    }


def parsear_bc3(ruta: str | Path) -> dict:
    texto, encoding, advertencias = _leer_texto(ruta)
    resultado = parsear_bc3_desde_texto(texto)
    resultado["advertencias"] = advertencias + resultado["advertencias"]
    resultado["estadisticas"]["encoding"] = encoding
    return resultado
