def normalizar_numero(valor):
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto:
        return None
    texto = (
        texto.replace("€", "")
        .replace("EUR/m2", "")
        .replace("€/m²", "")
        .replace("m²", "")
        .replace("m2", "")
        .replace(" ", "")
    )
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def calcular_precio_unitario(precio, superficie):
    precio_num = normalizar_numero(precio)
    superficie_num = normalizar_numero(superficie)
    if precio_num is None or superficie_num is None or superficie_num <= 0:
        return None
    return precio_num / superficie_num


def preparar_testigo_comparacion(testigo: dict) -> dict:
    precio_oferta = testigo.get("precio_oferta")
    precio_depurado = testigo.get("precio_depurado")
    superficie_tomada = testigo.get("superficie_tomada")
    precio_base = precio_depurado if normalizar_numero(precio_depurado) is not None else precio_oferta
    precio_unitario_inicial = calcular_precio_unitario(precio_base, superficie_tomada)

    advertencias = []
    if normalizar_numero(precio_base) is None:
        advertencias.append("Testigo sin precio económico utilizable.")
    if normalizar_numero(superficie_tomada) is None:
        advertencias.append("Testigo sin superficie tomada.")
    if precio_unitario_inicial is None:
        advertencias.append("Precio unitario inicial no calculable.")
    oferta_num = normalizar_numero(precio_oferta)
    depurado_num = normalizar_numero(precio_depurado)
    if oferta_num is not None and depurado_num is not None and depurado_num > oferta_num:
        advertencias.append("Precio depurado superior al precio ofertado.")
    if not str(testigo.get("fuente_testigo") or testigo.get("fuente_detalle") or "").strip():
        advertencias.append("Testigo sin fuente.")
    if not str(testigo.get("fecha_testigo") or "").strip():
        advertencias.append("Testigo sin fecha.")
    if not str(testigo.get("fiabilidad_dato") or "").strip():
        advertencias.append("Fiabilidad del dato no informada.")

    return {
        "precio_base": precio_base,
        "precio_unitario_inicial": precio_unitario_inicial,
        "advertencias_calculo": advertencias,
    }


def normalizar_ajuste(valor):
    numero = normalizar_numero(valor)
    if numero is None:
        return None
    if abs(numero) > 1:
        return numero / 100
    return numero


def _aplicar_signo(valor, signo):
    if valor is None:
        return None
    texto_signo = str(signo or "+").strip()
    if texto_signo == "-":
        return -abs(valor)
    return abs(valor)


def aplicar_ajuste_unitario(valor_unitario, ajuste: dict):
    valor = normalizar_numero(valor_unitario)
    if valor is None:
        return None
    tipo = str(ajuste.get("tipo_ajuste") or "").strip()
    if tipo == "porcentaje":
        porcentaje = _aplicar_signo(
            normalizar_ajuste(ajuste.get("ajuste_porcentaje")),
            ajuste.get("signo"),
        )
        if porcentaje is None:
            return valor
        return valor * (1 + porcentaje)
    if tipo == "importe_m2":
        importe = _aplicar_signo(
            normalizar_numero(ajuste.get("ajuste_importe_m2")),
            ajuste.get("signo"),
        )
        if importe is None:
            return valor
        return valor + importe
    return valor


def calcular_unitario_homogeneizado(testigo: dict, ajustes: list[dict]):
    unitario_inicial = normalizar_numero(
        testigo.get("precio_unitario_inicial") or testigo.get("valor_unitario_base")
    )
    advertencias = []
    pasos = []
    if unitario_inicial is None:
        advertencias.append("Homogeneización no calculable por falta de €/m² inicial.")
        return {
            "unitario_inicial": None,
            "unitario_homogeneizado": None,
            "ajuste_total_porcentaje_equivalente": None,
            "ajuste_total_importe_m2": None,
            "pasos": pasos,
            "advertencias": advertencias,
        }

    actual = unitario_inicial
    for ajuste in sorted(ajustes or [], key=lambda item: item.get("orden") or 0):
        if str(ajuste.get("activo", 1)) in {"0", "false", "False"}:
            continue
        tipo = str(ajuste.get("tipo_ajuste") or "").strip()
        antes = actual
        despues = aplicar_ajuste_unitario(actual, ajuste)
        if despues is None:
            despues = actual
        efecto = despues - antes
        if tipo == "porcentaje" and normalizar_ajuste(ajuste.get("ajuste_porcentaje")) is None:
            advertencias.append("Ajuste porcentual sin porcentaje.")
        if tipo == "importe_m2" and normalizar_numero(ajuste.get("ajuste_importe_m2")) is None:
            advertencias.append("Ajuste por importe €/m² sin importe.")
        if tipo in {"porcentaje", "importe_m2"} and not str(ajuste.get("signo") or "").strip():
            advertencias.append("Ajuste cuantificado sin signo.")
        if not str(ajuste.get("justificacion") or "").strip():
            advertencias.append("Ajuste sin justificación.")
        pasos.append(
            {
                "variable": ajuste.get("variable") or ajuste.get("variable_otro") or "",
                "tipo_ajuste": tipo,
                "valor_inmueble": ajuste.get("valor_inmueble") or "",
                "valor_testigo": ajuste.get("valor_testigo") or "",
                "signo": ajuste.get("signo") or "",
                "ajuste_porcentaje": normalizar_ajuste(ajuste.get("ajuste_porcentaje")),
                "ajuste_importe_m2": normalizar_numero(ajuste.get("ajuste_importe_m2")),
                "unitario_antes": antes,
                "unitario_despues": despues,
                "efecto_importe_m2": efecto,
                "justificacion": ajuste.get("justificacion") or "",
            }
        )
        actual = despues

    ajuste_total_importe_m2 = actual - unitario_inicial
    porcentaje_equivalente = (
        ajuste_total_importe_m2 / unitario_inicial if unitario_inicial else None
    )
    if porcentaje_equivalente is not None and abs(porcentaje_equivalente) > 0.30:
        advertencias.append("Ajuste total superior al 30% acumulado.")
    if not [ajuste for ajuste in ajustes or [] if str(ajuste.get("activo", 1)) != "0"]:
        advertencias.append("Testigo sin ajustes de homogeneización activos.")
    return {
        "unitario_inicial": unitario_inicial,
        "unitario_homogeneizado": actual,
        "ajuste_total_porcentaje_equivalente": porcentaje_equivalente,
        "ajuste_total_importe_m2": ajuste_total_importe_m2,
        "pasos": pasos,
        "advertencias": advertencias,
    }


def preparar_matriz_homogeneizacion(testigo: dict, ajustes: list[dict]):
    calculo = calcular_unitario_homogeneizado(testigo, ajustes)
    return {
        **calculo,
        "ajustes": ajustes or [],
    }


def _incluido_en_calculo(testigo: dict) -> bool:
    valor = testigo.get("incluido_calculo")
    if valor is None or valor == "":
        valor = testigo.get("incluido", 1)
    return str(valor).strip().lower() not in {"0", "false", "no"}


def _unitario_para_resumen(testigo: dict):
    unitario = normalizar_numero(testigo.get("unitario_homogeneizado"))
    origen = "homogeneizado"
    if unitario is None:
        unitario = normalizar_numero(
            testigo.get("precio_unitario_inicial") or testigo.get("unitario_inicial")
        )
        origen = "inicial"
    return unitario, origen


def extraer_unitarios_homogeneizados(testigos):
    valores = []
    advertencias = []
    for indice, testigo in enumerate(testigos or [], start=1):
        if not _incluido_en_calculo(testigo):
            continue
        unitario, origen = _unitario_para_resumen(testigo)
        if unitario is None:
            advertencias.append(
                f"Testigo {indice} incluido sin unitario homogeneizado ni inicial."
            )
            continue
        if origen == "inicial":
            advertencias.append(
                f"Testigo {indice} incluido sin €/m² homogeneizado; se usa €/m² inicial."
            )
        valores.append(unitario)
    return valores, advertencias


def calcular_media_simple(valores):
    numeros = [normalizar_numero(valor) for valor in valores or []]
    numeros = [valor for valor in numeros if valor is not None]
    if not numeros:
        return None
    return sum(numeros) / len(numeros)


def calcular_mediana(valores):
    numeros = sorted(
        valor for valor in (normalizar_numero(valor) for valor in valores or [])
        if valor is not None
    )
    if not numeros:
        return None
    mitad = len(numeros) // 2
    if len(numeros) % 2:
        return numeros[mitad]
    return (numeros[mitad - 1] + numeros[mitad]) / 2


def calcular_minimo_maximo(valores):
    numeros = [normalizar_numero(valor) for valor in valores or []]
    numeros = [valor for valor in numeros if valor is not None]
    if not numeros:
        return None, None
    return min(numeros), max(numeros)


def calcular_suma_pesos(testigos):
    pesos = [
        normalizar_numero(testigo.get("peso_porcentaje"))
        for testigo in testigos or []
        if _incluido_en_calculo(testigo)
        and normalizar_numero(testigo.get("peso_porcentaje")) is not None
    ]
    if not pesos:
        return None
    return sum(pesos)


def calcular_media_ponderada(testigos):
    numerador = 0.0
    suma_pesos = 0.0
    for testigo in testigos or []:
        if not _incluido_en_calculo(testigo):
            continue
        peso = normalizar_numero(testigo.get("peso_porcentaje"))
        unitario, _ = _unitario_para_resumen(testigo)
        if peso is None or unitario is None:
            continue
        numerador += unitario * peso
        suma_pesos += peso
    if suma_pesos <= 0:
        return None
    return numerador / suma_pesos


def preparar_resumen_comparacion(testigos):
    testigos = list(testigos or [])
    incluidos = [testigo for testigo in testigos if _incluido_en_calculo(testigo)]
    excluidos = [testigo for testigo in testigos if not _incluido_en_calculo(testigo)]
    valores, advertencias = extraer_unitarios_homogeneizados(incluidos)
    unitario_minimo, unitario_maximo = calcular_minimo_maximo(valores)
    unitario_medio = calcular_media_simple(valores)
    unitario_mediana = calcular_mediana(valores)
    suma_pesos = calcular_suma_pesos(incluidos)
    pesos_validos = suma_pesos is not None and abs(suma_pesos - 100) <= 0.01
    unitario_ponderado = calcular_media_ponderada(incluidos) if suma_pesos else None

    if not incluidos:
        advertencias.append("No hay testigos incluidos en el cálculo comparativo.")
    elif len(incluidos) < 3:
        advertencias.append("Menos de 3 testigos incluidos en el cálculo comparativo.")
    if suma_pesos is not None and not pesos_validos:
        advertencias.append("Los pesos informados no suman 100%.")
    for indice, testigo in enumerate(testigos, start=1):
        if not _incluido_en_calculo(testigo):
            if not str(testigo.get("motivo_exclusion") or "").strip():
                advertencias.append(f"Testigo {indice} excluido sin motivo.")
            continue
        if normalizar_numero(testigo.get("peso_porcentaje")) is not None and not str(
            testigo.get("motivo_ponderacion") or ""
        ).strip():
            advertencias.append(f"Testigo {indice} ponderado sin motivo.")
    if unitario_minimo is not None and unitario_maximo is not None and unitario_mediana:
        dispersion = (unitario_maximo - unitario_minimo) / unitario_mediana
        if dispersion > 0.30:
            advertencias.append("Dispersión elevada entre unitarios comparables.")

    propuesta = unitario_ponderado if pesos_validos else unitario_mediana
    if propuesta is None:
        advertencias.append("Propuesta orientativa no calculable.")

    return {
        "testigos_incluidos": len(incluidos),
        "testigos_excluidos": len(excluidos),
        "unitario_minimo": unitario_minimo,
        "unitario_maximo": unitario_maximo,
        "unitario_medio": unitario_medio,
        "unitario_mediana": unitario_mediana,
        "unitario_ponderado": unitario_ponderado,
        "suma_pesos": suma_pesos,
        "pesos_validos": pesos_validos,
        "advertencias": list(dict.fromkeys(advertencias)),
        "propuesta_unitaria_orientativa": propuesta,
    }
