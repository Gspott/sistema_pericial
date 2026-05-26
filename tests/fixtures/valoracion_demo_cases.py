import json


DEMO_OWNER = {
    "nombre": "Tecnico",
    "apellido1": "Demo",
    "apellido2": "Valoracion",
    "username": "demo_valoracion_qa",
    "password_hash": "hash-demo-valoracion-qa",
}


def _testigos(prefix: str, base_unitario: float, superficie_base: float):
    estados = [
        ("normal", "media", -0.02, 0.01, 0.00, 0.00, 0.01),
        ("buen estado", "media-alta", 0.00, -0.01, -0.01, -0.02, 0.00),
        ("reformado", "alta", 0.01, -0.02, -0.02, -0.03, -0.01),
        ("a actualizar", "media", -0.01, 0.02, 0.01, 0.02, 0.01),
        ("buen estado", "media", 0.02, 0.00, 0.00, 0.01, 0.00),
        ("normal", "media", 0.00, 0.01, 0.02, 0.01, 0.02),
    ]
    testigos = []
    for indice, (estado, calidad, a_sup, a_ubi, a_ant, a_cal, a_cons) in enumerate(
        estados,
        start=1,
    ):
        superficie = superficie_base + ((indice - 3) * 4)
        unitario = round(base_unitario * (0.96 + indice * 0.015), 2)
        precio = round(unitario * superficie, 2)
        coeficiente = round(1 + a_sup + a_ubi + a_ant + a_cal + a_cons, 4)
        testigos.append(
            {
                "direccion_testigo": f"{prefix} Testigo {indice}",
                "referencia_testigo": f"{prefix.upper().replace(' ', '-')}-{indice:02d}",
                "fuente_testigo": "Fuente demo de mercado interno",
                "url_fuente": f"https://example.invalid/{prefix.lower().replace(' ', '-')}/{indice}",
                "fecha_testigo": f"2026-04-{10 + indice:02d}",
                "codigo_postal": "00000",
                "municipio": "Municipio Ficticio",
                "provincia": "Provincia Demo",
                "precio_oferta": precio,
                "precio_cierre": round(precio * 0.97, 2),
                "superficie_construida": superficie,
                "superficie_util": round(superficie * 0.86, 2),
                "superficie_otros_usos": 0,
                "valor_unitario": unitario,
                "tipologia": "Vivienda" if "Local" not in prefix else "Local comercial",
                "planta": str(indice) if "Unifamiliar" not in prefix else "Baja+1",
                "dormitorios": 3 if "Local" not in prefix else 0,
                "banos": 2 if "Local" not in prefix else 1,
                "aseos": 0 if "Local" not in prefix else 1,
                "ascensor": 1 if "Unifamiliar" not in prefix else 0,
                "garaje": 1 if indice in {2, 4, 6} else 0,
                "trastero": 1 if indice in {1, 3, 5} else 0,
                "terraza": 1 if indice in {3, 6} else 0,
                "estado_conservacion": estado,
                "antiguedad": f"{12 + indice * 3} anos",
                "calidad_constructiva": calidad,
                "caracteristicas_constructivas": "Edificio demo comparable con estructura de hormigon y acabados coherentes.",
                "ubicacion": "Entorno demo comparable dentro del mismo mercado local.",
                "visitado": 0,
                "validacion_estado": "validado",
                "reutilizable": 1,
                "observaciones": "Testigo ficticio plausible creado para QA funcional.",
                "ajustes": {
                    "ajuste_superficie_construida": a_sup,
                    "ajuste_ubicacion": a_ubi,
                    "ajuste_antiguedad": a_ant,
                    "ajuste_calidades": a_cal,
                    "ajuste_caracteristicas_constructivas": a_cons,
                    "coeficiente_total": coeficiente,
                    "justificacion": "Ajuste demo por comparabilidad relativa de superficie, ubicacion, antiguedad y calidades.",
                },
            }
        )
    return testigos


CASOS_DEMO_VALORACION = [
    {
        "slug": "piso-urbano-estandar",
        "numero": "DEMO-VAL-001",
        "titulo": "Piso urbano estandar",
        "cliente": "Cliente Demo Piso Estandar",
        "direccion": "Calle Ficticia Centro 12, Municipio Ficticio",
        "tipo_inmueble": "Piso",
        "superficie": 92,
        "valoracion": {
            "finalidad_valoracion": "Compraventa",
            "finalidad_valoracion_detallada": "Estimacion de valor de mercado para operacion privada de compraventa.",
            "nombre_solicitante": "Solicitante Demo Estandar",
            "documentacion_utilizada": "Catastro demo, nota simple ficticia, visita y medicion orientativa.",
            "datos_registrales": "Finca registral ficticia 1001, sin cargas registrales conocidas en datos demo.",
            "identificacion_bien": "Piso exterior de tres dormitorios en edificio residencial plurifamiliar.",
            "superficie_valoracion": "92 m2 construidos",
            "superficie_construida": 92,
            "superficie_util": 79,
            "situacion_ocupacion": "Libre",
            "situacion_urbanistica": "Suelo urbano consolidado residencial.",
            "ubicacion_valoracion": "Barrio urbano consolidado con demanda residencial estable.",
            "descripcion_entorno": "Entorno residencial con comercio de proximidad, transporte publico y dotaciones suficientes.",
            "tipo_edificio": "Edificio plurifamiliar entre medianeras",
            "estado_conservacion": "Normal",
            "antiguedad": "22 anos",
            "calidades": "Calidades medias en buen estado de uso.",
            "estructura": "Hormigon armado",
            "cerramientos": "Fachada convencional con camara",
            "instalaciones": "Instalaciones privativas en funcionamiento aparente.",
            "metodo_comparacion_activo": 1,
            "metodo_coste_activo": 1,
            "criterios_metodo_valoracion": "Metodo de comparacion con testigos del mismo mercado residencial.",
            "variables_mercado": "Mercado liquido de vivienda usada con oferta suficiente.",
            "metodo_homogeneizacion": "Ajustes manuales por superficie, ubicacion, antiguedad, calidades y caracteristicas.",
            "condicionantes_limitaciones_valoracion": "Superficies no comprobadas con levantamiento topografico.",
            "observaciones_valoracion": "Caso demo completo para validar flujo estandar.",
        },
        "observaciones": {
            "estado_observado": "Estado normal, sin deterioros relevantes observados.",
            "reforma_observada": "No se observa reforma integral reciente.",
            "ocupacion_observada": "Libre",
            "observaciones_inspeccion_valoracion": "Inspeccion visual completa de zonas accesibles.",
            "incidencias_valoracion": "Sin incidencias relevantes.",
            "comprobaciones_fisicas": "Superficies contrastadas con documentacion demo.",
        },
        "testigos": _testigos("Piso Urbano Demo", 2450, 92),
    },
    {
        "slug": "piso-reformado-premium",
        "numero": "DEMO-VAL-002",
        "titulo": "Piso reformado premium",
        "cliente": "Cliente Demo Premium",
        "direccion": "Avenida Ficticia Mirador 8, Municipio Ficticio",
        "tipo_inmueble": "Piso",
        "superficie": 128,
        "valoracion": {
            "finalidad_valoracion": "Asesoramiento",
            "finalidad_valoracion_detallada": "Estimacion previa a negociacion de activo residencial reformado.",
            "nombre_solicitante": "Solicitante Demo Premium",
            "documentacion_utilizada": "Escritura demo, catastro demo, certificado energetico ficticio y visita.",
            "datos_registrales": "Finca registral ficticia 2002, descripcion coherente con vivienda reformada.",
            "identificacion_bien": "Vivienda exterior reformada con terraza y garaje anejo.",
            "superficie_valoracion": "128 m2 construidos",
            "superficie_construida": 128,
            "superficie_util": 111,
            "superficie_terraza": 14,
            "situacion_ocupacion": "Ocupado por propietario",
            "situacion_urbanistica": "Uso residencial permitido.",
            "ubicacion_valoracion": "Zona residencial de renta media-alta con buena accesibilidad.",
            "descripcion_entorno": "Entorno consolidado con servicios, zonas verdes y demanda solvente.",
            "tipo_edificio": "Edificio residencial con ascensor y garaje",
            "estado_conservacion": "Reformado",
            "antiguedad": "18 anos",
            "calidades": "Calidades altas, cocina equipada y carpinteria actualizada.",
            "estructura": "Hormigon armado",
            "carpinteria": "Carpinteria exterior con rotura de puente termico.",
            "acristalamiento": "Doble acristalamiento",
            "instalaciones": "Instalaciones renovadas en reforma reciente.",
            "metodo_comparacion_activo": 1,
            "metodo_coste_activo": 1,
            "criterios_metodo_valoracion": "Comparacion con testigos reformados y ajuste por calidades.",
            "variables_mercado": "Segmento premium con menor oferta y mayor sensibilidad a calidades.",
            "metodo_homogeneizacion": "Ajustes manuales conservadores sobre testigos no equivalentes.",
            "condicionantes_limitaciones_valoracion": "No se verifica documentacion tecnica completa de la reforma.",
            "observaciones_valoracion": "Caso demo para validar narrativa de calidad superior.",
        },
        "observaciones": {
            "estado_observado": "Reforma reciente y acabados en buen estado.",
            "reforma_observada": "Reforma integral observada en cocina, banos, carpinterias e instalaciones.",
            "ocupacion_observada": "Ocupado por propietario",
            "observaciones_inspeccion_valoracion": "La vivienda presenta imagen comercial superior a la media del entorno.",
            "incidencias_valoracion": "Sin incidencias visibles.",
            "comprobaciones_fisicas": "No se realizan catas ni comprobaciones invasivas.",
        },
        "testigos": _testigos("Piso Premium Demo", 4120, 128),
    },
    {
        "slug": "caso-incompleto-problematico",
        "numero": "DEMO-VAL-003",
        "titulo": "Caso incompleto problematico",
        "cliente": "Cliente Demo Incompleto",
        "direccion": "Travesia Ficticia Pendiente 4, Municipio Ficticio",
        "tipo_inmueble": "Piso",
        "superficie": 74,
        "sin_resultado": True,
        "valoracion": {
            "finalidad_valoracion": "Judicial",
            "nombre_solicitante": "Solicitante Demo Incompleto",
            "identificacion_bien": "Vivienda con documentacion incompleta y acceso parcial.",
            "superficie_valoracion": "",
            "superficie_construida": 74,
            "situacion_ocupacion": "Desconocido",
            "descripcion_entorno": "",
            "estado_conservacion": "A reformar",
            "antiguedad": "35 anos",
            "metodo_comparacion_activo": 1,
            "metodo_coste_activo": 0,
            "criterios_metodo_valoracion": "",
            "condicionantes_limitaciones_valoracion": "Sin nota simple, sin acceso completo y superficies no comprobadas.",
            "observaciones_valoracion": "Caso demo incompleto para validar advertencias no bloqueantes.",
        },
        "observaciones": {
            "estado_observado": "Estado heterogeneo con zonas no inspeccionadas.",
            "reforma_observada": "Reformas parciales antiguas sin documentacion.",
            "ocupacion_observada": "Desconocida",
            "observaciones_inspeccion_valoracion": "Acceso parcial; no se inspeccionan todas las dependencias.",
            "incidencias_valoracion": "Falta documentacion registral y medicion completa.",
            "comprobaciones_fisicas": "Superficies no comprobadas in situ.",
        },
        "testigos": _testigos("Piso Incompleto Demo", 1980, 74),
    },
    {
        "slug": "local-comercial",
        "numero": "DEMO-VAL-004",
        "titulo": "Local comercial",
        "cliente": "Cliente Demo Local",
        "direccion": "Plaza Ficticia Comercio 3, Municipio Ficticio",
        "tipo_inmueble": "Local comercial",
        "superficie": 180,
        "valoracion": {
            "finalidad_valoracion": "Garantia",
            "finalidad_valoracion_detallada": "Estimacion de valor para garantia interna sobre activo comercial.",
            "nombre_solicitante": "Entidad Demo Garantia",
            "documentacion_utilizada": "Catastro demo, escritura ficticia, visita y ficha urbanistica demo.",
            "datos_registrales": "Finca registral ficticia 4004, local en planta baja.",
            "identificacion_bien": "Local comercial en planta baja con fachada a via urbana.",
            "superficie_valoracion": "180 m2 construidos",
            "superficie_construida": 180,
            "superficie_util": 162,
            "situacion_ocupacion": "Arrendado",
            "situacion_urbanistica": "Uso comercial compatible con planeamiento demo.",
            "ubicacion_valoracion": "Eje comercial secundario con transito peatonal medio.",
            "descripcion_entorno": "Zona mixta residencial-comercial con locales en planta baja.",
            "tipo_edificio": "Edificio residencial con local en planta baja",
            "estado_conservacion": "Buen estado",
            "antiguedad": "28 anos",
            "calidades": "Acabados comerciales funcionales.",
            "estructura": "Hormigon armado",
            "instalaciones": "Instalacion electrica adaptada a actividad comercial generica.",
            "metodo_comparacion_activo": 1,
            "metodo_coste_activo": 1,
            "criterios_metodo_valoracion": "Comparacion con locales en ejes secundarios y ajuste por fachada y estado.",
            "variables_mercado": "Mercado con liquidez moderada y dependencia de renta potencial.",
            "metodo_homogeneizacion": "Ajustes manuales por superficie, ubicacion y estado comercial.",
            "condicionantes_limitaciones_valoracion": "No se analiza rentabilidad contractual real.",
            "observaciones_valoracion": "Caso demo para validar tipologia no residencial.",
        },
        "observaciones": {
            "estado_observado": "Local en uso aparente, con instalaciones visibles en estado correcto.",
            "reforma_observada": "Acondicionamiento comercial parcial.",
            "ocupacion_observada": "Arrendado",
            "observaciones_inspeccion_valoracion": "Inspeccion visual sin comprobacion de licencias de actividad.",
            "incidencias_valoracion": "No se aporta contrato de arrendamiento.",
            "comprobaciones_fisicas": "Medicion orientativa sobre documentacion demo.",
        },
        "testigos": _testigos("Local Comercial Demo", 1760, 180),
    },
    {
        "slug": "vivienda-unifamiliar",
        "numero": "DEMO-VAL-005",
        "titulo": "Vivienda unifamiliar",
        "cliente": "Cliente Demo Unifamiliar",
        "direccion": "Camino Ficticio Jardines 21, Municipio Ficticio",
        "tipo_inmueble": "Vivienda unifamiliar",
        "superficie": 220,
        "valoracion": {
            "finalidad_valoracion": "Herencia",
            "finalidad_valoracion_detallada": "Valor de mercado orientativo para reparto hereditario.",
            "nombre_solicitante": "Comunidad Hereditaria Demo",
            "documentacion_utilizada": "Catastro demo, escritura ficticia, IBI demo y visita exterior/interior.",
            "datos_registrales": "Finca registral ficticia 5005 con parcela vinculada.",
            "identificacion_bien": "Vivienda unifamiliar aislada con parcela privativa.",
            "superficie_valoracion": "220 m2 construidos",
            "superficie_construida": 220,
            "superficie_util": 188,
            "superficie_total": 420,
            "situacion_ocupacion": "Libre",
            "situacion_urbanistica": "Uso residencial unifamiliar en zona consolidada.",
            "ubicacion_valoracion": "Area residencial de baja densidad con demanda familiar.",
            "descripcion_entorno": "Entorno tranquilo con viviendas unifamiliares y servicios a distancia media.",
            "tipo_edificio": "Vivienda unifamiliar aislada",
            "estado_conservacion": "Buen estado",
            "antiguedad": "24 anos",
            "calidades": "Calidades medias-altas con parcela ajardinada.",
            "vistas": "Abiertas a entorno residencial",
            "estructura": "Hormigon y cerramientos tradicionales",
            "cubierta": "Cubierta inclinada",
            "cerramientos": "Fachada enfoscada y carpinterias exteriores renovadas.",
            "instalaciones": "Instalaciones en uso aparente.",
            "metodo_comparacion_activo": 1,
            "metodo_coste_activo": 1,
            "criterios_metodo_valoracion": "Comparacion con unifamiliares del mismo ambito y contraste por coste.",
            "variables_mercado": "Oferta limitada y elevada dispersion por parcela y estado.",
            "metodo_homogeneizacion": "Ajustes manuales por superficie, parcela, ubicacion y calidades.",
            "condicionantes_limitaciones_valoracion": "No se comprueba legalidad de ampliaciones no documentadas.",
            "observaciones_valoracion": "Caso demo para validar inmueble con parcela y tipologia singular.",
        },
        "observaciones": {
            "estado_observado": "Buen estado general con mantenimiento ordinario.",
            "reforma_observada": "Actualizaciones puntuales de carpinteria y banos.",
            "ocupacion_observada": "Libre",
            "observaciones_inspeccion_valoracion": "Inspeccion visual de vivienda y parcela accesible.",
            "incidencias_valoracion": "No se revisan instalaciones enterradas ni saneamiento.",
            "comprobaciones_fisicas": "Superficies contrastadas de forma orientativa.",
        },
        "testigos": _testigos("Unifamiliar Demo", 2120, 220),
    },
]


def _insertar_usuario_demo(cur):
    existente = cur.execute(
        """
        SELECT id
        FROM usuarios
        WHERE username = ?
        """,
        (DEMO_OWNER["username"],),
    ).fetchone()
    if existente:
        return existente["id"]
    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, username, password_hash
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            DEMO_OWNER["nombre"],
            DEMO_OWNER["apellido1"],
            DEMO_OWNER["apellido2"],
            DEMO_OWNER["username"],
            DEMO_OWNER["password_hash"],
        ),
    )
    return cur.lastrowid


def _insertar_valoracion_expediente(cur, expediente_id: int, datos: dict):
    columnas = ["expediente_id"] + list(datos.keys())
    placeholders = ", ".join(["?"] * len(columnas))
    cur.execute(
        f"""
        INSERT INTO valoracion_expediente ({", ".join(columnas)})
        VALUES ({placeholders})
        """,
        [expediente_id] + [datos[campo] for campo in datos],
    )


def _insertar_observaciones(cur, expediente_id: int, visita_id: int, datos: dict):
    columnas = ["visita_id", "expediente_id"] + list(datos.keys())
    placeholders = ", ".join(["?"] * len(columnas))
    cur.execute(
        f"""
        INSERT INTO valoracion_visita_observaciones ({", ".join(columnas)})
        VALUES ({placeholders})
        """,
        [visita_id, expediente_id] + [datos[campo] for campo in datos],
    )


def _insertar_testigo(cur, owner_user_id: int, testigo: dict):
    datos = {clave: valor for clave, valor in testigo.items() if clave != "ajustes"}
    columnas = ["owner_user_id"] + list(datos.keys())
    placeholders = ", ".join(["?"] * len(columnas))
    cur.execute(
        f"""
        INSERT INTO testigos_valoracion ({", ".join(columnas)})
        VALUES ({placeholders})
        """,
        [owner_user_id] + [datos[campo] for campo in datos],
    )
    return cur.lastrowid


def _insertar_vinculo_y_ajustes(
    cur,
    expediente_id: int,
    testigo_id: int,
    orden: int,
    testigo: dict,
):
    snapshot = json.dumps(
        {clave: valor for clave, valor in testigo.items() if clave != "ajustes"},
        ensure_ascii=False,
        sort_keys=True,
    )
    ajuste = testigo["ajustes"]
    valor_unitario_base = testigo["valor_unitario"]
    valor_unitario_ajustado = round(valor_unitario_base * ajuste["coeficiente_total"], 2)
    cur.execute(
        """
        INSERT INTO valoracion_expediente_testigos (
            expediente_id, testigo_id, orden, incluido, snapshot_json,
            notas_seleccion, valor_unitario_base, valor_unitario_ajustado
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            testigo_id,
            orden,
            1,
            snapshot,
            "Seleccion demo para contraste de mercado.",
            valor_unitario_base,
            valor_unitario_ajustado,
        ),
    )
    vinculo_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO valoracion_testigo_ajustes (
            expediente_testigo_id, ajuste_superficie_construida,
            ajuste_ubicacion, ajuste_antiguedad, ajuste_calidades,
            ajuste_caracteristicas_constructivas, coeficiente_total,
            justificacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            vinculo_id,
            ajuste["ajuste_superficie_construida"],
            ajuste["ajuste_ubicacion"],
            ajuste["ajuste_antiguedad"],
            ajuste["ajuste_calidades"],
            ajuste["ajuste_caracteristicas_constructivas"],
            ajuste["coeficiente_total"],
            ajuste["justificacion"],
        ),
    )
    return valor_unitario_ajustado


def _insertar_resultado_borrador(cur, expediente_id: int, superficie: float, ajustados: list[float]):
    if not ajustados:
        return None
    valor_unitario = round(sum(ajustados) / len(ajustados), 2)
    valor_resultante = round(valor_unitario * superficie, 2)
    valor_tasacion = round(valor_resultante / 1000) * 1000
    datos_calculo = {
        "tipo": "borrador_demo",
        "testigos": len(ajustados),
        "valor_unitario_medio_ajustado": valor_unitario,
        "superficie": superficie,
    }
    cur.execute(
        """
        INSERT INTO valoracion_resultados (
            expediente_id, metodo, version, valor_unitario, valor_resultante,
            valor_tasacion_final, resumen_calculo, datos_calculo_json, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            "comparacion_borrador_demo",
            1,
            valor_unitario,
            valor_resultante,
            valor_tasacion,
            "Borrador demo calculado como media simple de valores unitarios ajustados.",
            json.dumps(datos_calculo, sort_keys=True),
            1,
        ),
    )
    return {
        "valor_unitario": valor_unitario,
        "valor_resultante": valor_resultante,
        "valor_tasacion_final": valor_tasacion,
    }


def crear_casos_demo_valoracion(cur, owner_user_id: int | None = None):
    owner_id = owner_user_id or _insertar_usuario_demo(cur)
    creados = []
    for caso in CASOS_DEMO_VALORACION:
        completado_existente = False
        existente = cur.execute(
            """
            SELECT id
            FROM expedientes
            WHERE numero_expediente = ?
            """,
            (caso["numero"],),
        ).fetchone()
        if existente:
            expediente_id = existente["id"]
            if not cur.execute(
                """
                SELECT 1
                FROM valoracion_expediente
                WHERE expediente_id = ?
                LIMIT 1
                """,
                (expediente_id,),
            ).fetchone():
                _insertar_valoracion_expediente(cur, expediente_id, caso["valoracion"])
                completado_existente = True

            visita = cur.execute(
                """
                SELECT id
                FROM visitas
                WHERE expediente_id = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (expediente_id,),
            ).fetchone()
            if visita:
                visita_id = visita["id"]
            else:
                cur.execute(
                    """
                    INSERT INTO visitas (
                        expediente_id, fecha, tecnico, observaciones_visita
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        expediente_id,
                        "2026-05-26",
                        "Tecnico Demo Valoracion",
                        f"Visita demo para {caso['titulo']}.",
                    ),
                )
                visita_id = cur.lastrowid
                completado_existente = True

            if not cur.execute(
                """
                SELECT 1
                FROM valoracion_visita_observaciones
                WHERE expediente_id = ?
                LIMIT 1
                """,
                (expediente_id,),
            ).fetchone():
                _insertar_observaciones(cur, expediente_id, visita_id, caso["observaciones"])
                completado_existente = True

            testigos_count = cur.execute(
                """
                SELECT COUNT(*)
                FROM valoracion_expediente_testigos
                WHERE expediente_id = ?
                """,
                (expediente_id,),
            ).fetchone()[0]
            ajustados = []
            if testigos_count == 0:
                for orden, testigo in enumerate(caso["testigos"], start=1):
                    testigo_id = _insertar_testigo(cur, owner_id, testigo)
                    ajustado = _insertar_vinculo_y_ajustes(
                        cur,
                        expediente_id,
                        testigo_id,
                        orden,
                        testigo,
                    )
                    ajustados.append(ajustado)
                testigos_count = len(caso["testigos"])
                completado_existente = True

            resultado = None
            resultado_existente = cur.execute(
                """
                SELECT 1
                FROM valoracion_resultados
                WHERE expediente_id = ?
                  AND COALESCE(activo, 1) = 1
                LIMIT 1
                """,
                (expediente_id,),
            ).fetchone()
            if not caso.get("sin_resultado") and not resultado_existente:
                if not ajustados:
                    ajustados = [
                        row["valor_unitario_ajustado"]
                        for row in cur.execute(
                            """
                            SELECT valor_unitario_ajustado
                            FROM valoracion_expediente_testigos
                            WHERE expediente_id = ?
                              AND valor_unitario_ajustado IS NOT NULL
                            ORDER BY COALESCE(orden, 9999) ASC, id ASC
                            """,
                            (expediente_id,),
                        ).fetchall()
                    ]
                resultado = _insertar_resultado_borrador(
                    cur,
                    expediente_id,
                    caso["superficie"],
                    ajustados,
                )
                completado_existente = True

            creados.append(
                {
                    "slug": caso["slug"],
                    "titulo": caso["titulo"],
                    "expediente_id": expediente_id,
                    "visita_id": visita_id,
                    "testigos": testigos_count,
                    "resultado_borrador": resultado,
                    "skipped_existing": True,
                    "completed_existing": completado_existente,
                }
            )
            continue

        cur.execute(
            """
            INSERT INTO expedientes (
                numero_expediente, tipo_informe, destinatario, cliente,
                direccion, tipo_inmueble, owner_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                caso["numero"],
                "valoracion",
                "particular",
                caso["cliente"],
                caso["direccion"],
                caso["tipo_inmueble"],
                owner_id,
            ),
        )
        expediente_id = cur.lastrowid
        _insertar_valoracion_expediente(cur, expediente_id, caso["valoracion"])
        cur.execute(
            """
            INSERT INTO visitas (
                expediente_id, fecha, tecnico, observaciones_visita
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                expediente_id,
                "2026-05-26",
                "Tecnico Demo Valoracion",
                f"Visita demo para {caso['titulo']}.",
            ),
        )
        visita_id = cur.lastrowid
        _insertar_observaciones(cur, expediente_id, visita_id, caso["observaciones"])

        ajustados = []
        for orden, testigo in enumerate(caso["testigos"], start=1):
            testigo_id = _insertar_testigo(cur, owner_id, testigo)
            ajustado = _insertar_vinculo_y_ajustes(
                cur,
                expediente_id,
                testigo_id,
                orden,
                testigo,
            )
            ajustados.append(ajustado)

        resultado = None
        if not caso.get("sin_resultado"):
            resultado = _insertar_resultado_borrador(
                cur,
                expediente_id,
                caso["superficie"],
                ajustados,
            )

        creados.append(
            {
                "slug": caso["slug"],
                "titulo": caso["titulo"],
                "expediente_id": expediente_id,
                "visita_id": visita_id,
                "testigos": len(caso["testigos"]),
                "resultado_borrador": resultado,
                "skipped_existing": False,
            }
        )
    return {"owner_user_id": owner_id, "casos": creados}
