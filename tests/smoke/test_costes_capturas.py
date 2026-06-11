import json

from fastapi.testclient import TestClient


def test_costes_parser_detecta_texto_tipo_ive(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        RPE.010 m2 Picado y reposicion de revestimiento deteriorado
        Unidad: m2
        Precio partida 42,50 €
        MAT01 Mortero reparacion kg 2,50 4,00 10,00
        MO01 Oficial primera h 0,80 25,00 20,00
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "RPE.010"
    assert datos["unidad"] == "m2"
    assert "Picado" in datos["resumen"]
    assert datos["precio"] == 42.5
    assert len(datos["descompuestos"]) == 2
    assert datos["descompuestos"][0]["importe"] == 10.0
    assert resultado["version_parser"] == "costes-3b"


def test_costes_parser_detecta_captura_ive_con_ruido_y_miles(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Generador de precios IVE
        Provincia: Valencia
        Fecha base 2026/06/05
        Familia seleccionada: Revestimientos exteriores
        Opción seleccionada: reparación localizada

        ERPG.4aba m2 Reparación de revestimiento monocapa en fachada
        Descripción
        Reparación manual de zonas deterioradas, saneado previo, puente de unión
        y reposición de acabado compatible con el soporte existente.
        Precio partida 1.234,56 €/m2

        Código Resumen Ud Rendimiento Precio Importe
        MOOA.8a Oficial 1ª construcción h 0,850 24,50 20,83
        MOOA.9a Peón ordinario construcción h 0,425 21,10 8,97
        PBUW.8a Mortero reparación estructural kg 12,500 1,20 15,00
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "ERPG.4aba"
    assert datos["unidad"] == "m2"
    assert "monocapa" in datos["resumen"]
    assert datos["precio"] == 1234.56
    assert datos["provincia"] == "Valencia"
    assert datos["fecha_base"] == "2026-06-05"
    assert datos["familias_opciones"]
    assert len(datos["descompuestos"]) == 3
    assert datos["descompuestos"][0]["codigo"] == "MOOA.8a"
    assert datos["descompuestos"][0]["unidad"] == "h"
    assert datos["descompuestos"][0]["importe"] == 20.83
    assert resultado["campos_detectados"]["precio"] is True


def test_costes_parser_regresion_ive_real_erpg_4aba(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        IVE Generador de precios
        Base de precios de la construcción
        ERPG.4aba m2 Eliminación de pintura plástica en paramento vertical
        Descripción técnica:
        Eliminación de pintura plástica deteriorada en paramentos verticales interiores,
        mediante medios manuales, rascado, lijado superficial y limpieza del soporte,
        incluso retirada de restos y preparación para posterior revestimiento.
        Precio 16.77 €/m2

        Código Ud Resumen Cantidad Precio Importe
        MOOA.8a h Oficial 1ª construcción 0.100 23.42 2.34
        MOOA.9a h Peón ordinario construcción 0.100 20.62 2.06
        PBUW.8a kg Material auxiliar de reparación 1.000 0.13 0.13
        PRCP.1a m2 Medios auxiliares y limpieza 1.000 12.24 12.24
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "ERPG.4aba"
    assert datos["unidad"] == "m2"
    assert datos["precio"] == 16.77
    assert "pintura plástica" in datos["resumen"]
    assert "medios manuales" in datos["descripcion"]
    assert "Código Ud Resumen" not in datos["descripcion"]
    assert len(datos["descompuestos"]) == 4
    assert datos["descompuestos"][0]["codigo"] == "MOOA.8a"
    assert datos["descompuestos"][0]["unidad"] == "h"
    assert datos["descompuestos"][0]["rendimiento"] == 0.1
    assert datos["descompuestos"][0]["precio_unitario"] == 23.42
    assert datos["descompuestos"][0]["importe"] == 2.34
    assert round(sum(item["importe"] for item in datos["descompuestos"]), 2) == 16.77


def test_costes_parser_ive_real_guarnecido_descompuestos_completos(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        ER - Revestimientos
        ERP - Paramentos
        ERPG - Guarnecidos y enlucidos

        ERPG.4aba | m2 | Guarn-enl y YG/L maes vert 16.77€
        Guarnecido maestreado realizado con pasta de yeso YG/L sobre paramento vertical,
        incluso formación de maestras, repasos, limpieza y medios auxiliares.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOASa h Oficial 1ª construcción 26.93 € 0.175 471€
        MOOA11a h Peónespecializado construcción 23.28 € 0.175 407€
        PBPL3b m3 PastayesoYG/L 197.02 € 0.017 335€
        % % Costes directos complementarios 12.13 € 0.020 024€
        ERPG10a m2 Enlucido yeso pmto vertical 4.40 € 1.000 440€
        """
    )

    datos = resultado["datos_parseados"]
    assert resultado["version_parser"] == "costes-ive-1"
    assert datos["codigo"] == "ERPG.4aba"
    assert datos["unidad"] == "m2"
    assert datos["resumen"] == "Guarn-enl y YG/L maes vert"
    assert datos["precio"] == 16.77
    assert "Guarnecido maestreado" in datos["descripcion"]
    assert "Código Unidad Resumen" not in datos["descripcion"]
    assert len(datos["descompuestos"]) == 5
    codigos = [item["codigo"] for item in datos["descompuestos"]]
    assert codigos == ["MOOA.8a", "MOOA11a", "PBPL3b", "%", "ERPG10a"]
    assert datos["descompuestos"][0]["unidad"] == "h"
    assert datos["descompuestos"][0]["precio_unitario"] == 26.93
    assert datos["descompuestos"][0]["rendimiento"] == 0.175
    assert datos["descompuestos"][0]["importe"] == 4.71
    assert datos["descompuestos"][1]["resumen"] == "Peón especializado construcción"
    assert datos["descompuestos"][2]["resumen"] == "Pasta yeso YG/L"
    assert datos["descompuestos"][3]["codigo"] == "%"
    assert datos["descompuestos"][3]["unidad"] == "%"
    assert datos["descompuestos"][3]["resumen"] == "Costes directos complementarios"
    assert datos["descompuestos"][3]["precio_unitario"] == 12.13
    assert datos["descompuestos"][3]["rendimiento"] == 0.02
    assert datos["descompuestos"][3]["importe"] == 0.24
    assert datos["descompuestos"][4]["importe"] == 4.4
    assert abs(sum(item["importe"] for item in datos["descompuestos"]) - 16.77) <= 0.02
    assert any("MOOASa" in aviso for aviso in resultado["advertencias"])


def test_costes_parser_ive_auxiliar_porcentaje_sin_simbolos_ocr(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        ERPG.4aba m2 Guarn-enl y YG/L maes vert 16.77 €
        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOA.8a h Oficial 1ª construcción 26.93 € 0.175 4.71 €
        Costes directos complementarios 12.13 € 0.020 0.24 €
        ERPG10a m2 Enlucido yeso pmto vertical 4.40 € 1.000 4.40 €
        """
    )

    auxiliares = [
        item
        for item in resultado["datos_parseados"]["descompuestos"]
        if item["resumen"] == "Costes directos complementarios"
    ]
    assert len(auxiliares) == 1
    auxiliar = auxiliares[0]
    assert auxiliar["codigo"] == "%"
    assert auxiliar["unidad"] == "%"
    assert auxiliar["precio_unitario"] == 12.13
    assert auxiliar["rendimiento"] == 0.02
    assert auxiliar["importe"] == 0.24


def test_costes_parser_ive_partida_dos_descompuestos_porcentaje_final(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        DDDR.4a | m2 | Demolición falso techo cañizo | 6.51 €
        Demolición de falso techo continuo de cañizo, con medios manuales,
        retirada de escombros y carga manual.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOA12a h Peón ordinario construcción 21.08 € 0.300 6.32 €
        % % Costes directos complementarios 6.32 € 0.030 0.19 €
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "DDDR.4a"
    assert datos["unidad"] == "m2"
    assert datos["resumen"] == "Demolición falso techo cañizo"
    assert datos["precio"] == 6.51
    assert len(datos["descompuestos"]) == 2
    assert datos["descompuestos"][0] == {
        "codigo": "MOOA12a",
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Peón ordinario construcción",
        "precio_unitario": 21.08,
        "rendimiento": 0.3,
        "importe": 6.32,
        "orden": 1,
    }
    assert datos["descompuestos"][1] == {
        "codigo": "%",
        "tipo": "porcentaje",
        "unidad": "%",
        "resumen": "Costes directos complementarios",
        "precio_unitario": 6.32,
        "rendimiento": 0.03,
        "importe": 0.19,
        "orden": 2,
    }


def test_costes_parser_ive_codigo_auxiliar_sin_punto_dddr_6ba(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        DDDR.6ba | m2 | Picado enlucido paramento vertical | 10.75 €
        Picado de enlucido existente en paramento vertical, por medios manuales,
        con retirada de restos y limpieza del soporte.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOA12a h Peón ordinario construcción 21.08€ 0.500 10.54€
        % % Costes directos complementarios 10.54€ 0.020 0.21€
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "DDDR.6ba"
    assert datos["unidad"] == "m2"
    assert datos["resumen"] == "Picado enlucido paramento vertical"
    assert datos["precio"] == 10.75
    assert len(datos["descompuestos"]) == 2
    assert datos["descompuestos"][0] == {
        "codigo": "MOOA12a",
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Peón ordinario construcción",
        "precio_unitario": 21.08,
        "rendimiento": 0.5,
        "importe": 10.54,
        "orden": 1,
    }
    assert datos["descompuestos"][1] == {
        "codigo": "%",
        "tipo": "porcentaje",
        "unidad": "%",
        "resumen": "Costes directos complementarios",
        "precio_unitario": 10.54,
        "rendimiento": 0.02,
        "importe": 0.21,
        "orden": 2,
    }
    assert round(sum(item["importe"] for item in datos["descompuestos"]), 2) == 10.75
    assert not any("descuadre" in aviso.lower() for aviso in resultado["advertencias"])


def test_costes_parser_ive_normaliza_precio_porcentual_compacto_dddr_2b(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        DDDR.2b | m2 | Demolición pavimento entablado madera | 9.03 €
        Demolición de pavimento de entablado de madera por medios manuales.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MODA9a h Oficial 2* construcción 24.52 € 0.100 245€
        MOOA12a h Peón ordinario construcción 21.08€ 0.300 632€
        % % Costes directos complementarios 877€ 0.030 0.26€
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "DDDR.2b"
    assert datos["unidad"] == "m2"
    assert datos["resumen"] == "Demolición pavimento entablado madera"
    assert datos["precio"] == 9.03
    assert len(datos["descompuestos"]) == 3
    assert datos["descompuestos"][0]["codigo"] == "MODA9a"
    assert datos["descompuestos"][0]["importe"] == 2.45
    assert datos["descompuestos"][1]["codigo"] == "MOOA12a"
    assert datos["descompuestos"][1]["importe"] == 6.32
    assert datos["descompuestos"][2] == {
        "codigo": "%",
        "tipo": "porcentaje",
        "unidad": "%",
        "resumen": "Costes directos complementarios",
        "precio_unitario": 8.77,
        "rendimiento": 0.03,
        "importe": 0.26,
        "orden": 3,
    }
    assert round(sum(item["importe"] for item in datos["descompuestos"]), 2) == 9.03
    assert not any("suma de descompuestos" in aviso.lower() for aviso in resultado["advertencias"])
    assert any(
        "Precio unitario OCR de % corregido de 877.00 a 8.77" in aviso
        for aviso in resultado["advertencias"]
    )


def test_costes_parser_ive_rescata_previos_y_corrige_ddds_2a(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        DDDS.2a | m3 | Desescombro manual m³ plano horizontal | 48.38 €
        Desescombro manual sobre plano horizontal, con carga manual.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MODA12a h Peónordinario construcción 21.08€ 2.250 17.43€
        PBAAa m3 Agua 112€ 0.003 000€
        % % Costes directos complementarios 17.43€ 0.020 095€
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "DDDS.2a"
    assert datos["unidad"] == "m3"
    assert datos["resumen"] == "Desescombro manual m³ plano horizontal"
    assert datos["precio"] == 48.38
    assert len(datos["descompuestos"]) == 3
    assert datos["descompuestos"][0] == {
        "codigo": "MOOA12a",
        "tipo": "mano_obra",
        "unidad": "h",
        "resumen": "Peón ordinario construcción",
        "precio_unitario": 21.08,
        "rendimiento": 2.25,
        "importe": 47.43,
        "orden": 1,
    }
    assert datos["descompuestos"][1] == {
        "codigo": "PBAA.1a",
        "tipo": "material",
        "unidad": "m3",
        "resumen": "Agua",
        "precio_unitario": 1.12,
        "rendimiento": 0.003,
        "importe": 0.0,
        "orden": 2,
    }
    assert datos["descompuestos"][2] == {
        "codigo": "%",
        "tipo": "porcentaje",
        "unidad": "%",
        "resumen": "Costes directos complementarios",
        "precio_unitario": 47.43,
        "rendimiento": 0.02,
        "importe": 0.95,
        "orden": 3,
    }
    assert round(sum(item["importe"] for item in datos["descompuestos"]), 2) == 48.38
    assert not any("suma de descompuestos" in aviso.lower() for aviso in resultado["advertencias"])
    assert any("MODA12a corregido a MOOA12a" in aviso for aviso in resultado["advertencias"])
    assert any("PBAAa corregido a PBAA.1a" in aviso for aviso in resultado["advertencias"])
    assert any("Precio unitario OCR de % corregido de 17.43 a 47.43" in aviso for aviso in resultado["advertencias"])


def test_costes_parser_ive_partida_larga_falso_techo_ertc_3aaaa(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        ERTC.3aaaa | m2 | Fals tech y-12.5dirt niv
        36.57€
        Falso techo continuo de placas de yeso laminado, sistema directo nivelado,
        incluso perfilería, tornillería, pastas y medios auxiliares.

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOAa h Oficial 1 construcción 2551€ 0.250 638€
        MOOA12a h Peónordinario construcción 21.08€ 0.250 5.27€
        (>) PFPC.1ac m2 Placayeso laminado A 125mm 6.35€ 1.180 749€
        Ep PEPP11a m Maestrafjplyeso 70x30mm 267€ 1.400 3.4€
        Ep PFPP12a m Perfil simple U 30x30x0.6 mm 196€ 1.700 333€
        (>) PFPP15a u Tornillo 25mm p/pnl yeso 0.02 € 20.000 0.40 €
        (>) PFPPSa m Banda papel microperforado alt r 005 € 1.800 0.09€
        PFPP.8b kg Pastajunta panel yeso c/cinta 4,69 € 0.400 188€
        PFPP.7a kg Pasta ayuda panel yeso 2.25€ 0.400 090€
        PRTW13a u Anclaje directo 121€ 1.260 152€
        PRTW13c u Piezaempalme en cruz 291€ 1.500 4,37€
        Cp PRTW13d u Conector60x115x27 056€ 0.850 048€
        % % Costes directos complementarios 35.85€ 0.020 0.72€
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == "ERTC.3aaaa"
    assert datos["unidad"] == "m2"
    assert datos["resumen"] == "Fals tech y-12.5dirt niv"
    assert datos["precio"] == 36.57
    assert len(datos["descompuestos"]) == 13
    assert datos["descompuestos"] == [
        {
            "codigo": "MOOA.8a",
            "tipo": "mano_obra",
            "unidad": "h",
            "resumen": "Oficial 1ª construcción",
            "precio_unitario": 25.51,
            "rendimiento": 0.25,
            "importe": 6.38,
            "orden": 1,
        },
        {
            "codigo": "MOOA12a",
            "tipo": "mano_obra",
            "unidad": "h",
            "resumen": "Peón ordinario construcción",
            "precio_unitario": 21.08,
            "rendimiento": 0.25,
            "importe": 5.27,
            "orden": 2,
        },
        {
            "codigo": "PFPC.1ac",
            "tipo": "material",
            "unidad": "m2",
            "resumen": "Placa yeso laminado A 12.5mm",
            "precio_unitario": 6.35,
            "rendimiento": 1.18,
            "importe": 7.49,
            "orden": 3,
        },
        {
            "codigo": "PFPP11a",
            "tipo": "material",
            "unidad": "m",
            "resumen": "Maestra fij pl yeso 70x30mm",
            "precio_unitario": 2.67,
            "rendimiento": 1.4,
            "importe": 3.74,
            "orden": 4,
        },
        {
            "codigo": "PFPP12a",
            "tipo": "material",
            "unidad": "m",
            "resumen": "Perfil simple U 30x30x0.6 mm",
            "precio_unitario": 1.96,
            "rendimiento": 1.7,
            "importe": 3.33,
            "orden": 5,
        },
        {
            "codigo": "PFPP15a",
            "tipo": "material",
            "unidad": "ud",
            "resumen": "Tornillo 25mm p/pnl yeso",
            "precio_unitario": 0.02,
            "rendimiento": 20.0,
            "importe": 0.4,
            "orden": 6,
        },
        {
            "codigo": "PFPP.5a",
            "tipo": "material",
            "unidad": "m",
            "resumen": "Banda papel microperforado alt r",
            "precio_unitario": 0.05,
            "rendimiento": 1.8,
            "importe": 0.09,
            "orden": 7,
        },
        {
            "codigo": "PFPP.8b",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Pasta junta panel yeso c/cinta",
            "precio_unitario": 4.69,
            "rendimiento": 0.4,
            "importe": 1.88,
            "orden": 8,
        },
        {
            "codigo": "PFPP.7a",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Pasta ayuda panel yeso",
            "precio_unitario": 2.25,
            "rendimiento": 0.4,
            "importe": 0.9,
            "orden": 9,
        },
        {
            "codigo": "PRTW13a",
            "tipo": "material",
            "unidad": "ud",
            "resumen": "Anclaje directo",
            "precio_unitario": 1.21,
            "rendimiento": 1.26,
            "importe": 1.52,
            "orden": 10,
        },
        {
            "codigo": "PRTW13c",
            "tipo": "material",
            "unidad": "ud",
            "resumen": "Pieza empalme en cruz",
            "precio_unitario": 2.91,
            "rendimiento": 1.5,
            "importe": 4.37,
            "orden": 11,
        },
        {
            "codigo": "PRTW13d",
            "tipo": "material",
            "unidad": "ud",
            "resumen": "Conector 60x115x27",
            "precio_unitario": 0.56,
            "rendimiento": 0.85,
            "importe": 0.48,
            "orden": 12,
        },
        {
            "codigo": "%",
            "tipo": "porcentaje",
            "unidad": "%",
            "resumen": "Costes directos complementarios",
            "precio_unitario": 35.85,
            "rendimiento": 0.02,
            "importe": 0.72,
            "orden": 13,
        },
    ]
    assert round(sum(item["importe"] for item in datos["descompuestos"]), 2) == 36.57
    assert not any("suma de descompuestos" in aviso.lower() for aviso in resultado["advertencias"])


def test_costes_parser_ive_diccionario_recursos_frecuentes(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        ERTC.3aaaa | m2 | Fals tech y-12.5dirt niv | 14.52 €

        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOAa h Oficial 1 construcción 2551€ 0.250 638€
        MOOA12a h Peónordinario construcción 21.08€ 0.250 5.27€
        PFPPSa m Banda papel microperforado alt r 005 € 1.800 0.09€
        PFPP.8b kg Pastajunta panel yeso c/cinta 4,69 € 0.400 188€
        PFPP.7a kg Pasta ayuda panel yeso 2.25€ 0.400 090€
        """
    )

    descompuestos = resultado["datos_parseados"]["descompuestos"]
    assert descompuestos == [
        {
            "codigo": "MOOA.8a",
            "tipo": "mano_obra",
            "unidad": "h",
            "resumen": "Oficial 1ª construcción",
            "precio_unitario": 25.51,
            "rendimiento": 0.25,
            "importe": 6.38,
            "orden": 1,
        },
        {
            "codigo": "MOOA12a",
            "tipo": "mano_obra",
            "unidad": "h",
            "resumen": "Peón ordinario construcción",
            "precio_unitario": 21.08,
            "rendimiento": 0.25,
            "importe": 5.27,
            "orden": 2,
        },
        {
            "codigo": "PFPP.5a",
            "tipo": "material",
            "unidad": "m",
            "resumen": "Banda papel microperforado alt r",
            "precio_unitario": 0.05,
            "rendimiento": 1.8,
            "importe": 0.09,
            "orden": 3,
        },
        {
            "codigo": "PFPP.8b",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Pasta junta panel yeso c/cinta",
            "precio_unitario": 4.69,
            "rendimiento": 0.4,
            "importe": 1.88,
            "orden": 4,
        },
        {
            "codigo": "PFPP.7a",
            "tipo": "material",
            "unidad": "kg",
            "resumen": "Pasta ayuda panel yeso",
            "precio_unitario": 2.25,
            "rendimiento": 0.4,
            "importe": 0.9,
            "orden": 5,
        },
    ]
    assert any(
        "Recurso OCR MOOAa normalizado como MOOA.8a" in aviso
        for aviso in resultado["advertencias"]
    )
    assert any(
        "Recurso OCR PFPPSa normalizado como PFPP.5a" in aviso
        for aviso in resultado["advertencias"]
    )
    assert not any("suma de descompuestos" in aviso.lower() for aviso in resultado["advertencias"])


def test_costes_parser_ive_dddr_6ba_mooa12a_sin_euros_no_se_descarta(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Base de Datos de Construcción IVE
        DDDR.6ba | m2 | Picado enlucido paramento vertical | 10.75
        Código Unidad Resumen Precio unitario Rendimiento Importe
        MOOA12a h Peón ordinario construcción 21.08 0.500 10.54
        % % Costes directos complementarios 10.54 0.020 0.21
        """
    )

    descompuestos = resultado["datos_parseados"]["descompuestos"]
    assert descompuestos[0]["codigo"] == "MOOA12a"
    assert descompuestos[0]["unidad"] == "h"
    assert descompuestos[0]["resumen"] == "Peón ordinario construcción"
    assert descompuestos[0]["precio_unitario"] == 21.08
    assert descompuestos[0]["rendimiento"] == 0.5
    assert descompuestos[0]["importe"] == 10.54
    assert descompuestos[1]["codigo"] == "%"
    assert len(descompuestos) == 2
    assert resultado["advertencias"] == []


def test_costes_parser_advierte_si_faltan_campos_obligatorios(isolated_import):
    parser = isolated_import("app.services.costes_parser")
    resultado = parser.parsear_coste_desde_texto(
        """
        Pantalla IVE
        Opciones seleccionadas
        Reparación sin datos económicos visibles
        """
    )

    datos = resultado["datos_parseados"]
    assert datos["codigo"] == ""
    assert datos["precio"] is None
    assert resultado["campos_detectados"]["codigo"] is False
    assert resultado["campos_detectados"]["precio"] is False
    assert any("precio" in aviso.lower() for aviso in resultado["advertencias"])


def test_costes_ocr_degrada_sin_romper_si_no_hay_imagen(isolated_import, tmp_path):
    ocr = isolated_import("app.services.costes_ocr")
    resultado = ocr.extraer_coste_desde_imagen(tmp_path / "no_existe.png")

    assert resultado["ocr_disponible"] is False
    assert resultado["texto_detectado"] == ""
    assert resultado["datos_parseados"]["codigo"] == ""
    assert resultado["advertencias"]


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


def _payload_ocr_dddr_6ba_dos_descompuestos():
    return {
        "ocr_disponible": True,
        "texto_detectado": (
            "DDDR.6ba m2 Picado enlucido paramento vertical 10.75\n"
            "MOOA12a h Peón ordinario construcción 21.08 0.500 10.54\n"
            "% % Costes directos complementarios 10.54 0.020 0.21"
        ),
        "texto_ocr": (
            "DDDR.6ba m2 Picado enlucido paramento vertical 10.75\n"
            "MOOA12a h Peón ordinario construcción 21.08 0.500 10.54\n"
            "% % Costes directos complementarios 10.54 0.020 0.21"
        ),
        "datos_parseados": {
            "codigo": "DDDR.6ba",
            "unidad": "m2",
            "resumen": "Picado enlucido paramento vertical",
            "descripcion": "Picado de enlucido existente.",
            "precio": 10.75,
            "moneda": "EUR",
            "fecha_base": "",
            "provincia": "",
            "familias_opciones": [],
            "descompuestos": [
                {
                    "codigo": "MOOA12a",
                    "tipo": "mano_obra",
                    "unidad": "h",
                    "resumen": "Peón ordinario construcción",
                    "precio_unitario": 21.08,
                    "rendimiento": 0.5,
                    "importe": 10.54,
                    "orden": 1,
                },
                {
                    "codigo": "%",
                    "tipo": "porcentaje",
                    "unidad": "%",
                    "resumen": "Costes directos complementarios",
                    "precio_unitario": 10.54,
                    "rendimiento": 0.02,
                    "importe": 0.21,
                    "orden": 2,
                },
            ],
        },
        "advertencias": [],
        "confianza": {
            "score": 1.0,
            "campos_detectados": {
                "codigo": True,
                "unidad": True,
                "resumen": True,
                "precio": True,
                "descompuestos": True,
            },
        },
        "campos_detectados": {
            "codigo": True,
            "unidad": True,
            "resumen": True,
            "precio": True,
            "descompuestos": True,
        },
        "version_parser": "costes-ive-1",
    }


def _crear_captura_con_json(cur, datos_extraidos_json: str = ""):
    cur.execute(
        """
        INSERT INTO costes_fuentes (
            tipo_fuente, descripcion, archivo_original, observaciones
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "pantallazo",
            "Captura DDDR.6ba",
            "dddr_6ba.png",
            "Fixture smoke",
        ),
    )
    fuente_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO costes_capturas (
            fuente_id, archivo_imagen, estado, datos_extraidos_json, updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            fuente_id,
            "costes/capturas/dddr_6ba.png",
            "pendiente_revision",
            datos_extraidos_json,
        ),
    )
    return cur.lastrowid


def test_costes_captura_revision_muestra_todos_los_descompuestos_guardados(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_captura_json_owner")
        captura_id = _crear_captura_con_json(
            cur,
            json.dumps(_payload_ocr_dddr_6ba_dos_descompuestos(), ensure_ascii=False),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.get(f"/costes/capturas/{captura_id}")

    assert response.status_code == 200
    assert "Parser: costes-ive-1" in response.text
    assert "MOOA12a" in response.text
    assert "Peón ordinario construcción" in response.text
    assert "Costes directos complementarios" in response.text
    assert response.text.index("MOOA12a") < response.text.index("Costes directos complementarios")
    assert "Añadir descompuesto" in response.text
    assert "data-remove-descompuesto" in response.text
    assert "costes-descomp-table" in response.text
    assert "<th class=\"costes-col-resumen\">Resumen</th>" in response.text


def test_costes_captura_revision_post_crea_lineas_manuales_extra(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_ui_1_manual_extra")
        captura_id = _crear_captura_con_json(
            cur,
            json.dumps(_payload_ocr_dddr_6ba_dos_descompuestos(), ensure_ascii=False),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(
        f"/costes/capturas/{captura_id}",
        data={
            "base_id": "",
            "base_nombre": "Base captura UI",
            "base_descripcion": "Base temporal UI",
            "capitulo_id": "",
            "codigo": "UI.001",
            "unidad": "m2",
            "resumen": "Partida con descompuestos dinamicos",
            "descripcion": "Guardado desde revisión con filas manuales.",
            "precio": "15.75",
            "moneda": "EUR",
            "fecha_base": "2026-06-06",
            "provincia": "Madrid",
            "descomp_codigo": ["MOOA12a", "%", "MAT-EXTRA"],
            "descomp_tipo": ["mano_obra", "porcentaje", "material"],
            "descomp_unidad": ["h", "%", "ud"],
            "descomp_resumen": [
                "Peón ordinario construcción",
                "Costes directos complementarios",
                "Material añadido manualmente",
            ],
            "descomp_precio_unitario": ["21.08", "10.54", "5"],
            "descomp_rendimiento": ["0.500", "0.020", "1"],
            "descomp_importe": ["10.54", "0.21", ""],
            "descomp_orden": ["1", "2", "3"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT concepto_id FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        descompuestos = conn.execute(
            """
            SELECT codigo, importe
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            ORDER BY orden
            """,
            (captura["concepto_id"],),
        ).fetchall()
    finally:
        conn.close()

    assert [item["codigo"] for item in descompuestos] == ["MOOA12a", "%", "MAT-EXTRA"]
    assert descompuestos[2]["importe"] == 5.0


def test_costes_captura_revision_post_ignora_fila_vacia(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_ui_1_empty_row")
        captura_id = _crear_captura_con_json(cur)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(
        f"/costes/capturas/{captura_id}",
        data={
            "base_id": "",
            "base_nombre": "Base captura UI vacia",
            "base_descripcion": "Base temporal UI",
            "capitulo_id": "",
            "codigo": "UI.002",
            "unidad": "m2",
            "resumen": "Partida con fila vacia",
            "descripcion": "La fila sin datos debe ignorarse.",
            "precio": "10",
            "moneda": "EUR",
            "fecha_base": "2026-06-06",
            "provincia": "Madrid",
            "descomp_codigo": ["MAT-OK", ""],
            "descomp_tipo": ["material", "material"],
            "descomp_unidad": ["ud", ""],
            "descomp_resumen": ["Material válido", ""],
            "descomp_precio_unitario": ["10", ""],
            "descomp_rendimiento": ["1", ""],
            "descomp_importe": ["", ""],
            "descomp_orden": ["1", "2"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT concepto_id FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        descompuestos = conn.execute(
            """
            SELECT codigo
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            ORDER BY orden
            """,
            (captura["concepto_id"],),
        ).fetchall()
    finally:
        conn.close()

    assert [item["codigo"] for item in descompuestos] == ["MAT-OK"]


def test_costes_captura_revision_post_no_crea_sugerida_eliminada(isolated_import):
    main_module = isolated_import("app.main")

    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_ui_1_removed_row")
        captura_id = _crear_captura_con_json(
            cur,
            json.dumps(_payload_ocr_dddr_6ba_dos_descompuestos(), ensure_ascii=False),
        )
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(
        f"/costes/capturas/{captura_id}",
        data={
            "base_id": "",
            "base_nombre": "Base captura UI eliminada",
            "base_descripcion": "Base temporal UI",
            "capitulo_id": "",
            "codigo": "UI.003",
            "unidad": "m2",
            "resumen": "Partida con sugerida eliminada",
            "descripcion": "Solo se envía la fila porcentual.",
            "precio": "0.21",
            "moneda": "EUR",
            "fecha_base": "2026-06-06",
            "provincia": "Madrid",
            "descomp_codigo": ["%"],
            "descomp_tipo": ["porcentaje"],
            "descomp_unidad": ["%"],
            "descomp_resumen": ["Costes directos complementarios"],
            "descomp_precio_unitario": ["10.54"],
            "descomp_rendimiento": ["0.020"],
            "descomp_importe": ["0.21"],
            "descomp_orden": ["2"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT concepto_id FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        codigos = [
            row["codigo"]
            for row in conn.execute(
                """
                SELECT codigo
                FROM costes_descompuestos
                WHERE concepto_padre_id = ?
                ORDER BY orden
                """,
                (captura["concepto_id"],),
            ).fetchall()
        ]
    finally:
        conn.close()

    assert codigos == ["%"]


def test_costes_captura_extraer_guarda_y_muestra_dos_descompuestos(monkeypatch, isolated_import):
    main_module = isolated_import("app.main")

    from app.config import UPLOAD_DIR
    from app.database import get_connection
    from app.routers import costes as costes_router

    ruta = UPLOAD_DIR / "costes" / "capturas" / "dddr_6ba.png"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"\x89PNG\r\n\x1a\nsmoke")
    payload = _payload_ocr_dddr_6ba_dos_descompuestos()
    monkeypatch.setattr(
        costes_router,
        "extraer_coste_desde_imagen",
        lambda _ruta_imagen: dict(payload),
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_captura_extraer_owner")
        captura_id = _crear_captura_con_json(cur)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(f"/costes/capturas/{captura_id}/extraer", follow_redirects=False)
    assert response.status_code == 303

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT datos_extraidos_json FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        guardado = json.loads(captura["datos_extraidos_json"])
    finally:
        conn.close()

    descompuestos = guardado["datos_parseados"]["descompuestos"]
    assert [item["codigo"] for item in descompuestos] == ["MOOA12a", "%"]

    response = client.get(f"/costes/capturas/{captura_id}")
    assert response.status_code == 200
    assert "MOOA12a" in response.text
    assert "Costes directos complementarios" in response.text


def test_costes_ive_1e_ciclo_vida_mooa12a_021_en_revision(monkeypatch, isolated_import):
    main_module = isolated_import("app.main")

    from app.config import UPLOAD_DIR
    from app.database import get_connection
    from app.routers import costes as costes_router
    from app.services.costes_parser import parsear_coste_desde_texto

    texto_ocr = """
    Base de Datos de Construcción IVE
    DDDR.6ba | m2 | Picado enlucido paramento vertical | 10.75 €
    Código Unidad Resumen Precio unitario Rendimiento Importe
    MOOA12a h Peón ordinario construcción 21.08€ 0.500 10.54€
    % % Costes directos complementarios 10.54€ 0.020 021€
    """
    resultado_parser = parsear_coste_desde_texto(texto_ocr)
    datos_parseados = resultado_parser["datos_parseados"]
    assert any(
        d["codigo"] == "MOOA12a"
        for d in datos_parseados["descompuestos"]
    )
    assert len(datos_parseados["descompuestos"]) == 2
    assert datos_parseados["descompuestos"][0]["codigo"] == "MOOA12a"
    assert datos_parseados["descompuestos"][1]["codigo"] == "%"
    assert datos_parseados["descompuestos"][1]["importe"] == 0.21

    ruta = UPLOAD_DIR / "costes" / "capturas" / "dddr_6ba_021.png"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"\x89PNG\r\n\x1a\nsmoke")
    resultado_ocr = {
        "ocr_disponible": True,
        "texto_detectado": texto_ocr,
        "texto_ocr": texto_ocr,
        **resultado_parser,
    }
    monkeypatch.setattr(
        costes_router,
        "extraer_coste_desde_imagen",
        lambda _ruta_imagen: dict(resultado_ocr),
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_ive_1e_owner")
        captura_id = _crear_captura_con_json(cur)
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)
    response = client.post(f"/costes/capturas/{captura_id}/extraer", follow_redirects=False)
    assert response.status_code == 303

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT datos_extraidos_json FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        json_guardado = json.loads(captura["datos_extraidos_json"])
    finally:
        conn.close()

    descompuestos_json = json_guardado["datos_parseados"]["descompuestos"]
    assert any(
        d["codigo"] == "MOOA12a"
        for d in descompuestos_json
    )
    assert len(descompuestos_json) == 2

    contexto_capturado = {}
    render_original = costes_router.render_template

    def capturar_contexto(request, template_name, context=None):
        contexto_capturado.update(context or {})
        return render_original(request, template_name, context)

    monkeypatch.setattr(costes_router, "render_template", capturar_contexto)
    response = client.get(f"/costes/capturas/{captura_id}")
    assert response.status_code == 200

    descompuestos_contexto = contexto_capturado["descompuestos_sugeridos"]
    assert any(
        d["codigo"] == "MOOA12a"
        for d in descompuestos_contexto
    )
    assert len([d for d in descompuestos_contexto if d.get("codigo")]) == 2
    assert "MOOA12a" in response.text
    assert "Peón ordinario construcción" in response.text
    assert "Costes directos complementarios" in response.text


def test_costes_capturas_subida_revision_y_concepto_vinculado(isolated_import):
    main_module = isolated_import("app.main")

    from app.config import UPLOAD_DIR
    from app.database import get_connection

    conn = get_connection()
    try:
        cur = conn.cursor()
        owner_id = _crear_usuario(cur, "costes_capturas_owner")
        conn.commit()
    finally:
        conn.close()

    client = _autenticar_cliente(main_module, owner_id)

    response = client.get("/costes/capturas")
    assert response.status_code == 200
    assert "Capturas de costes" in response.text

    response = client.get("/costes/capturas/nueva")
    assert response.status_code == 200
    assert "Nueva captura" in response.text
    assert "Sin OCR automático" in response.text

    response = client.post(
        "/costes/capturas/nueva",
        data={"descripcion": "Archivo no permitido"},
        files={"archivo": ("captura.txt", b"texto", "text/plain")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=" in response.headers["location"]

    response = client.post(
        "/costes/capturas/nueva",
        data={
            "base_id": "",
            "descripcion": "Pantallazo tarifa demo",
            "provincia": "Madrid",
            "fecha_base": "2026-06-05",
            "observaciones": "Sin OCR real",
        },
        files={"archivo": ("captura.png", b"\x89PNG\r\n\x1a\nsmoke", "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/costes/capturas/")

    conn = get_connection()
    try:
        captura = conn.execute(
            """
            SELECT cc.*, cf.tipo_fuente, cf.descripcion, cf.archivo_original
            FROM costes_capturas cc
            JOIN costes_fuentes cf ON cf.id = cc.fuente_id
            ORDER BY cc.id DESC
            LIMIT 1
            """
        ).fetchone()
        assert captura is not None
        assert captura["estado"] == "pendiente_revision"
        assert captura["tipo_fuente"] == "pantallazo"
        assert captura["concepto_id"] is None
        assert captura["archivo_imagen"].startswith("costes/capturas/")
        assert (UPLOAD_DIR / captura["archivo_imagen"]).exists()
        captura_id = captura["id"]
    finally:
        conn.close()

    response = client.get(f"/costes/capturas/{captura_id}")
    assert response.status_code == 200
    assert "Revisión de captura" in response.text
    assert f"/uploads/{captura['archivo_imagen']}" in response.text
    assert "Guardar partida borrador" in response.text

    response = client.post(
        f"/costes/capturas/{captura_id}/extraer",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith(f"/costes/capturas/{captura_id}")

    conn = get_connection()
    try:
        captura_extraida = conn.execute(
            "SELECT * FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        assert captura_extraida["concepto_id"] is None
        assert captura_extraida["estado"] == "pendiente_revision"
        assert "ocr_disponible" in captura_extraida["datos_extraidos_json"]
        assert "datos_parseados" in captura_extraida["datos_extraidos_json"]
        assert "version_parser" in captura_extraida["datos_extraidos_json"]
        assert "campos_detectados" in captura_extraida["datos_extraidos_json"]
    finally:
        conn.close()

    response = client.get(f"/costes/capturas/{captura_id}")
    assert response.status_code == 200
    assert "Extraer desde imagen" in response.text
    assert "Advertencias de extracción" in response.text

    response = client.post(
        f"/costes/capturas/{captura_id}",
        data={
            "base_id": "",
            "base_nombre": "Base desde captura smoke",
            "base_descripcion": "Base temporal para smoke",
            "capitulo_id": "",
            "codigo": "CAP-01",
            "unidad": "m2",
            "resumen": "Reposicion manual desde pantallazo",
            "descripcion": "Partida creada desde captura sin OCR.",
            "precio": "42",
            "moneda": "EUR",
            "fecha_base": "2026-06-05",
            "provincia": "Madrid",
            "descomp_codigo": ["MAT-CAP", "MO-CAP"],
            "descomp_tipo": ["material", "mano_obra"],
            "descomp_unidad": ["ud", "h"],
            "descomp_resumen": ["Material captura", "Mano de obra captura"],
            "descomp_precio_unitario": ["10", "22"],
            "descomp_rendimiento": ["2", "1"],
            "descomp_importe": ["", ""],
            "descomp_orden": ["1", "2"],
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/costes/")

    conn = get_connection()
    try:
        captura = conn.execute(
            "SELECT * FROM costes_capturas WHERE id = ?",
            (captura_id,),
        ).fetchone()
        assert captura["estado"] == "revisada"
        assert captura["concepto_id"] is not None
        concepto_id = captura["concepto_id"]
        fuente = conn.execute(
            "SELECT * FROM costes_fuentes WHERE id = ?",
            (captura["fuente_id"],),
        ).fetchone()
        assert fuente["concepto_id"] == concepto_id
        concepto = conn.execute(
            "SELECT * FROM costes_conceptos WHERE id = ?",
            (concepto_id,),
        ).fetchone()
        assert concepto["codigo"] == "CAP-01"
        assert concepto["estado"] == "borrador"
        descompuestos = conn.execute(
            """
            SELECT *
            FROM costes_descompuestos
            WHERE concepto_padre_id = ?
            ORDER BY orden
            """,
            (concepto_id,),
        ).fetchall()
        assert len(descompuestos) == 2
        assert descompuestos[0]["importe"] == 20.0
        assert descompuestos[1]["importe"] == 22.0
    finally:
        conn.close()

    response = client.get(f"/costes/{concepto_id}")
    assert response.status_code == 200
    assert "Reposicion manual desde pantallazo" in response.text
