import re
import unicodedata
from datetime import date, datetime

from app.database import get_connection


CAPITULOS_PRINCIPALES = (
    ("resumen_ejecutivo", "Resumen ejecutivo"),
    ("antecedentes_objeto", "Antecedentes y objeto"),
    ("metodologia", "Metodología"),
    ("analisis_causal", "Análisis causal"),
    ("inventario_resumido_danos", "Inventario resumido de daños"),
    ("conclusiones_periciales", "Conclusiones"),
)

CAPITULOS_REFERENCIA = {
    "conclusiones_periciales": "Conclusiones",
    "conclusiones_tecnicas": "Conclusiones técnicas",
}

ANEXOS_DERIVADOS = {
    "A": "Documentación aportada",
    "B": "Reportaje fotográfico",
    "C": "Fichas de daños",
    "E": "Análisis de ejecución de partida",
    "F": "Justificación de mediciones",
}

TIPOS_DOCUMENTALES_ANEXO_F = {"informe_v2_anexo_f_mediciones"}

REFERENCIA_FOTO_RE = re.compile(
    r"\b(?:figura|foto|fotografia|fotografía|imagen)\s*(?:n[úu]m\.?|n[ºo]\.?)?\s*(\d{1,3})\b",
    re.IGNORECASE,
)
REFERENCIA_ANEXO_RE = re.compile(r"\banexo\s+([a-z])\b", re.IGNORECASE)
REFERENCIA_ESTANCIA_RE = re.compile(
    r"\b("
    r"dormitorio(?:\s+\d+)?|habitaci[oó]n(?:\s+\d+)?|ba[ñn]o(?:\s+\d+)?|aseo(?:\s+\d+)?|"
    r"cocina(?:\s+\d+)?|sal[oó]n(?:\s+\d+)?|comedor(?:\s+\d+)?|pasillo(?:\s+\d+)?|"
    r"recibidor(?:\s+\d+)?|terraza(?:\s+\d+)?|patio(?:\s+\d+)?|galer[ií]a(?:\s+\d+)?"
    r")\b",
    re.IGNORECASE,
)

CONCLUSION_SOPORTE_KEYWORDS = (
    "daño",
    "dano",
    "lesión",
    "lesion",
    "riesgo",
    "urgente",
    "reparación",
    "reparacion",
    "sustitución",
    "sustitucion",
    "humedad",
    "filtración",
    "filtracion",
    "fisura",
    "grieta",
)

RISKY_STATEMENT_RULES = (
    {
        "codigo": "RISK_STRUCTURAL_COLLAPSE",
        "patrones": (
            "riesgo de colapso",
            "colapso estructural",
            "ruina inminente",
            "riesgo estructural grave",
        ),
        "mensaje": (
            "El texto contiene una afirmación de riesgo estructural grave. "
            "Conviene revisar que exista soporte técnico suficiente, como inspección específica, "
            "catas, ensayos, cálculo o documentación justificativa."
        ),
    },
    {
        "codigo": "RISK_MECHANICAL_PROPERTIES",
        "patrones": (
            "pérdida de propiedades mecánicas",
            "merma de capacidad resistente",
            "pérdida de resistencia",
            "agotamiento estructural",
        ),
        "mensaje": (
            "El texto menciona pérdida o merma de capacidad resistente. "
            "Revise si la afirmación está apoyada en ensayos, cálculo estructural, catas "
            "o documentación técnica suficiente."
        ),
    },
    {
        "codigo": "RISK_CAUSATION_CERTAINTY",
        "patrones": (
            "la causa es",
            "se determina como causa",
            "queda demostrado que",
            "origen demostrado",
            "causa directa",
        ),
        "mensaje": (
            "El texto formula causalidad en términos categóricos. "
            "Revise si procede matizar la certeza o reforzarla con indicios, ensayos, "
            "documentación y razonamiento técnico explícito."
        ),
    },
    {
        "codigo": "RISK_LEGAL_RESPONSIBILITY",
        "patrones": (
            "responsabilidad de",
            "negligencia",
            "mala praxis",
            "incumplimiento imputable",
            "culpable",
        ),
        "mensaje": (
            "El texto usa términos próximos a atribución jurídica de responsabilidad. "
            "Revise si el informe debe limitarse al soporte técnico y separar hechos, "
            "causalidad y valoración jurídica."
        ),
    },
    {
        "codigo": "RISK_CODE_COMPLIANCE",
        "patrones": (
            "incumple normativa",
            "incumple el CTE",
            "no cumple normativa",
            "infracción urbanística",
        ),
        "mensaje": (
            "El texto afirma posible incumplimiento normativo. "
            "Revise que se cite la norma aplicable, su versión, el precepto concreto "
            "y la comprobación técnica realizada."
        ),
    },
    {
        "codigo": "RISK_URGENT_DANGER",
        "patrones": (
            "peligro inminente",
            "riesgo inmediato",
            "actuación urgente imprescindible",
            "desalojo inmediato",
        ),
        "mensaje": (
            "El texto contiene una afirmación de peligro o actuación inmediata. "
            "Revise si existe soporte técnico suficiente y si procede documentar medidas "
            "preventivas, comunicación o comprobaciones adicionales."
        ),
    },
)
MAX_RISKY_STATEMENTS_PER_CODE = 5

LEGAL_REVIEW_RULES = (
    {
        "codigo": "LEGAL_EXCESSIVE_CERTAINTY",
        "patrones": (
            "queda demostrado",
            "queda probado",
            "se acredita plenamente",
            "sin ninguna duda",
            "de forma concluyente",
            "indiscutiblemente probado",
            "se prueba de manera concluyente",
        ),
        "mensaje": (
            "El texto utiliza una formulación de certeza muy elevada. "
            "Revise si el soporte probatorio justifica dicha afirmación."
        ),
        "sugerencia": (
            "Valore fórmulas como: 'De los indicios observados se desprende...', "
            "'Resulta compatible con...' o 'Puede considerarse razonablemente probable...'."
        ),
    },
    {
        "codigo": "LEGAL_ABSOLUTE_CAUSATION",
        "patrones": (
            "la causa es",
            "la causa directa es",
            "el origen es",
            "fue provocado por",
            "se produjo exclusivamente por",
            "queda demostrado que la causa es",
        ),
        "mensaje": (
            "Se afirma una relación causal categórica que podría requerir mayor soporte técnico."
        ),
        "sugerencia": (
            "Valore fórmulas como: 'Los daños observados resultan compatibles con...' "
            "o 'Los indicios permiten considerar probable...'."
        ),
    },
    {
        "codigo": "LEGAL_ATTRIBUTION_OF_LIABILITY",
        "patrones": (
            "es responsable",
            "resulta responsable",
            "es culpa de",
            "la negligencia de",
            "el promotor es responsable",
            "la constructora es responsable",
            "el técnico es responsable",
        ),
        "mensaje": (
            "El informe puede estar entrando en atribuciones de responsabilidad jurídica."
        ),
        "sugerencia": (
            "El presente informe describe hechos y compatibilidades técnicas sin prejuzgar "
            "eventuales responsabilidades jurídicas."
        ),
    },
    {
        "codigo": "LEGAL_INTENTIONALITY",
        "patrones": (
            "deliberadamente",
            "intencionadamente",
            "a sabiendas",
            "consciente de",
            "ocultó",
            "engañó",
            "actuó voluntariamente",
        ),
        "mensaje": (
            "Se utilizan expresiones que implican valoración sobre la intención o conocimiento "
            "de terceros."
        ),
        "sugerencia": (
            "Si no existe soporte documental específico, valore describir únicamente hechos "
            "observados y documentación disponible."
        ),
    },
    {
        "codigo": "LEGAL_OVERCONCLUSIVE_LANGUAGE",
        "patrones": (
            "inequívocamente",
            "indiscutiblemente",
            "sin lugar a dudas",
            "de manera categórica",
            "absolutamente",
            "con total certeza",
        ),
        "mensaje": "El lenguaje empleado puede resultar excesivamente concluyente.",
        "sugerencia": (
            "Valore fórmulas como: 'Resulta compatible con...', "
            "'Con la información disponible...' o 'Desde un punto de vista técnico...'."
        ),
    },
)
MAX_LEGAL_REVIEW_PER_CODE = 5

CONTENIDO_PLACEHOLDER_RE = re.compile(
    r"^\s*(?:"
    r"|pendiente(?:s)?(?:\s+de\s+redacci[oó]n)?\.?"
    r"|conclusiones periciales pendientes de redacci[oó]n\.?"
    r"|conclusiones t[eé]cnicas pendientes de redacci[oó]n\.?"
    r"|no consta(?:n)?[^.]{0,120}\.?"
    r"|\[completar[^\]]*\]"
    r")\s*$",
    re.IGNORECASE,
)


def limpiar_texto(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()


def normalizar_texto(valor) -> str:
    texto = limpiar_texto(valor).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def tabla_existe(cur, tabla: str) -> bool:
    fila = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (tabla,),
    ).fetchone()
    return fila is not None


def incidencia(
    codigo: str,
    severidad: str,
    categoria: str,
    mensaje: str,
    entidad: str,
    entidad_id=None,
    url: str | None = None,
    fragmento: str | None = None,
    sugerencia: str | None = None,
) -> dict:
    item = {
        "codigo": codigo,
        "severidad": severidad,
        "categoria": categoria,
        "mensaje": mensaje,
        "entidad": entidad,
        "entidad_id": entidad_id,
    }
    if url:
        item["url"] = url
    if fragmento:
        item["fragmento"] = fragmento
    if sugerencia:
        item["sugerencia"] = sugerencia
    return item


def contenido_relevante(texto: str) -> bool:
    limpio = limpiar_texto(texto)
    if len(normalizar_texto(limpio)) < 25:
        return False
    if CONTENIDO_PLACEHOLDER_RE.match(limpio):
        return False
    return True


def cargar_capitulos(cur, expediente_id: int) -> dict[str, dict]:
    if not tabla_existe(cur, "informe_v2_capitulos"):
        return {}
    filas = cur.execute(
        """
        SELECT id, clave, titulo, contenido
        FROM informe_v2_capitulos
        WHERE expediente_id = ?
        """,
        (expediente_id,),
    ).fetchall()
    return {limpiar_texto(fila["clave"]): dict(fila) for fila in filas}


def cargar_texto_informe(capitulos: dict[str, dict]) -> str:
    partes = []
    for capitulo in capitulos.values():
        partes.append(limpiar_texto(capitulo.get("titulo")))
        partes.append(limpiar_texto(capitulo.get("contenido")))
    return "\n\n".join(parte for parte in partes if parte)


def cargar_fotos(cur, expediente_id: int) -> list[dict]:
    fotos: list[dict] = []
    if not tabla_existe(cur, "visitas"):
        return fotos

    def agregar(entidad: str, entidad_id, archivo: str, descripcion: str = "") -> None:
        archivo = limpiar_texto(archivo)
        if not archivo:
            return
        fotos.append(
            {
                "numero": len(fotos) + 1,
                "entidad": entidad,
                "entidad_id": entidad_id,
                "archivo": archivo,
                "descripcion": limpiar_texto(descripcion),
            }
        )

    if tabla_existe(cur, "visita_fotos"):
        for fila in cur.execute(
            """
            SELECT vf.id, vf.ruta, vf.descripcion
            FROM visita_fotos vf
            JOIN visitas v ON v.id = vf.visita_id
            WHERE v.expediente_id = ?
            ORDER BY v.id ASC, vf.id ASC
            """,
            (expediente_id,),
        ).fetchall():
            agregar("visita_fotos", fila["id"], fila["ruta"], fila["descripcion"])

    if tabla_existe(cur, "estancia_fotos"):
        for fila in cur.execute(
            """
            SELECT ef.id, ef.archivo
            FROM estancia_fotos ef
            JOIN estancias e ON e.id = ef.estancia_id
            JOIN visitas v ON v.id = e.visita_id
            WHERE v.expediente_id = ?
            ORDER BY v.id ASC, e.id ASC, ef.id ASC
            """,
            (expediente_id,),
        ).fetchall():
            agregar("estancia_fotos", fila["id"], fila["archivo"])

    if tabla_existe(cur, "registro_patologia_fotos"):
        for fila in cur.execute(
            """
            SELECT rpf.id, rpf.archivo
            FROM registro_patologia_fotos rpf
            JOIN registros_patologias rp ON rp.id = rpf.registro_id
            JOIN visitas v ON v.id = rp.visita_id
            WHERE v.expediente_id = ?
            ORDER BY v.id ASC, rp.id ASC, rpf.id ASC
            """,
            (expediente_id,),
        ).fetchall():
            agregar("registro_patologia_fotos", fila["id"], fila["archivo"])

    if tabla_existe(cur, "registro_patologia_exterior_fotos"):
        for fila in cur.execute(
            """
            SELECT rpef.id, rpef.archivo
            FROM registro_patologia_exterior_fotos rpef
            JOIN registros_patologias_exteriores rpe ON rpe.id = rpef.registro_id
            JOIN visitas v ON v.id = rpe.visita_id
            WHERE v.expediente_id = ?
            ORDER BY v.id ASC, rpe.id ASC, rpef.id ASC
            """,
            (expediente_id,),
        ).fetchall():
            agregar("registro_patologia_exterior_fotos", fila["id"], fila["archivo"])

    return fotos


def cargar_documentos(cur, expediente_id: int) -> list[dict]:
    if not tabla_existe(cur, "expediente_documentos"):
        return []
    return [
        dict(fila)
        for fila in cur.execute(
            """
            SELECT id, nombre_visible, descripcion, tipo_documento, archivo_nombre_original
            FROM expediente_documentos
            WHERE expediente_id = ?
            ORDER BY orden ASC, id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]


def cargar_estancias(cur, expediente_id: int) -> list[dict]:
    if not tabla_existe(cur, "estancias") or not tabla_existe(cur, "visitas"):
        return []
    return [
        dict(fila)
        for fila in cur.execute(
            """
            SELECT e.id, e.nombre, e.tipo_estancia
            FROM estancias e
            JOIN visitas v ON v.id = e.visita_id
            WHERE v.expediente_id = ?
            ORDER BY e.id ASC
            """,
            (expediente_id,),
        ).fetchall()
    ]


def contar_patologias(cur, expediente_id: int) -> int:
    total = 0
    if tabla_existe(cur, "registros_patologias"):
        total += cur.execute(
            """
            SELECT COUNT(*)
            FROM registros_patologias rp
            JOIN visitas v ON v.id = rp.visita_id
            WHERE v.expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()[0]
    if tabla_existe(cur, "registros_patologias_exteriores"):
        total += cur.execute(
            """
            SELECT COUNT(*)
            FROM registros_patologias_exteriores rpe
            JOIN visitas v ON v.id = rpe.visita_id
            WHERE v.expediente_id = ?
            """,
            (expediente_id,),
        ).fetchone()[0]
    return int(total or 0)


def anexos_disponibles(fotos: list[dict], documentos: list[dict], total_patologias: int, capitulos: dict[str, dict]) -> dict[str, str]:
    disponibles = {}
    if documentos:
        disponibles["A"] = ANEXOS_DERIVADOS["A"]
    if fotos:
        disponibles["B"] = ANEXOS_DERIVADOS["B"]
    if total_patologias:
        disponibles["C"] = ANEXOS_DERIVADOS["C"]
    if contenido_relevante(capitulos.get("anexo_e_partida_4", {}).get("contenido", "")):
        disponibles["E"] = ANEXOS_DERIVADOS["E"]
    if (
        contenido_relevante(capitulos.get("anexo_f_mediciones", {}).get("contenido", ""))
        or any(limpiar_texto(doc.get("tipo_documento")) in TIPOS_DOCUMENTALES_ANEXO_F for doc in documentos)
    ):
        disponibles["F"] = ANEXOS_DERIVADOS["F"]
    return disponibles


def extraer_referencias_fotos(texto: str) -> set[int]:
    return {int(match.group(1)) for match in REFERENCIA_FOTO_RE.finditer(texto or "")}


def extraer_referencias_anexos(texto: str) -> set[str]:
    return {match.group(1).upper() for match in REFERENCIA_ANEXO_RE.finditer(texto or "")}


def dividir_fragmentos_texto(texto: str) -> list[str]:
    texto = limpiar_texto(texto)
    if not texto:
        return []
    fragmentos = re.split(r"[\n\r]+|(?<=[.!?])\s+", texto)
    return [limpiar_texto(fragmento) for fragmento in fragmentos if limpiar_texto(fragmento)]


def recortar_fragmento(texto: str, limite: int = 220) -> str:
    texto = limpiar_texto(texto)
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


def detectar_afirmaciones_riesgo(capitulos: dict[str, dict], expediente_id: int) -> list[dict]:
    riesgos: list[dict] = []
    conteo_por_codigo: dict[str, int] = {}
    vistos: set[tuple[str, str, str]] = set()

    reglas_normalizadas = [
        {
            **regla,
            "patrones_norm": tuple(normalizar_texto(patron) for patron in regla["patrones"]),
        }
        for regla in RISKY_STATEMENT_RULES
    ]

    for clave, capitulo in capitulos.items():
        contenido = limpiar_texto(capitulo.get("contenido"))
        if not contenido:
            continue
        titulo = limpiar_texto(capitulo.get("titulo")) or clave
        entidad_id = capitulo.get("id") or clave
        url = f"/expedientes/{expediente_id}/informe-v2-editor#capitulo-{clave}"
        for fragmento in dividir_fragmentos_texto(contenido):
            fragmento_norm = normalizar_texto(fragmento)
            if not fragmento_norm:
                continue
            for regla in reglas_normalizadas:
                codigo = regla["codigo"]
                if conteo_por_codigo.get(codigo, 0) >= MAX_RISKY_STATEMENTS_PER_CODE:
                    continue
                patron_detectado = next(
                    (
                        patron
                        for patron in regla["patrones_norm"]
                        if patron and patron in fragmento_norm
                    ),
                    "",
                )
                if not patron_detectado:
                    continue
                clave_visto = (codigo, str(entidad_id), fragmento_norm[:180])
                if clave_visto in vistos:
                    continue
                vistos.add(clave_visto)
                conteo_por_codigo[codigo] = conteo_por_codigo.get(codigo, 0) + 1
                riesgos.append(
                    incidencia(
                        codigo,
                        "advertencia",
                        "riesgo_pericial",
                        f"{regla['mensaje']} Capítulo: {titulo}.",
                        "capitulo",
                        entidad_id,
                        url,
                        recortar_fragmento(fragmento),
                    )
                )

    return riesgos


def detectar_revision_juridica(capitulos: dict[str, dict], expediente_id: int) -> list[dict]:
    incidencias: list[dict] = []
    conteo_por_codigo: dict[str, int] = {}
    vistos: set[tuple[str, str, str]] = set()

    reglas_normalizadas = [
        {
            **regla,
            "patrones_norm": tuple(normalizar_texto(patron) for patron in regla["patrones"]),
        }
        for regla in LEGAL_REVIEW_RULES
    ]

    for clave, capitulo in capitulos.items():
        contenido = limpiar_texto(capitulo.get("contenido"))
        if not contenido:
            continue
        titulo = limpiar_texto(capitulo.get("titulo")) or clave
        entidad_id = capitulo.get("id") or clave
        url = f"/expedientes/{expediente_id}/informe-v2-editor#capitulo-{clave}"
        for fragmento in dividir_fragmentos_texto(contenido):
            fragmento_norm = normalizar_texto(fragmento)
            if not fragmento_norm:
                continue
            for regla in reglas_normalizadas:
                codigo = regla["codigo"]
                if conteo_por_codigo.get(codigo, 0) >= MAX_LEGAL_REVIEW_PER_CODE:
                    continue
                patron_detectado = next(
                    (
                        patron
                        for patron in regla["patrones_norm"]
                        if patron and patron in fragmento_norm
                    ),
                    "",
                )
                if not patron_detectado:
                    continue
                clave_visto = (codigo, str(entidad_id), fragmento_norm[:180])
                if clave_visto in vistos:
                    continue
                vistos.add(clave_visto)
                conteo_por_codigo[codigo] = conteo_por_codigo.get(codigo, 0) + 1
                incidencias.append(
                    incidencia(
                        codigo,
                        "warning",
                        "revision_juridica",
                        f"{regla['mensaje']} Capítulo: {titulo}.",
                        "capitulo",
                        entidad_id,
                        url,
                        recortar_fragmento(fragmento),
                        regla.get("sugerencia"),
                    )
                )

    return incidencias


def parse_fecha(valor: str) -> date | None:
    texto = limpiar_texto(valor)
    if not texto:
        return None
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto[:19], formato).date()
        except ValueError:
            continue
    return None


def limitar_score(valor: int) -> int:
    return max(0, min(100, int(valor)))


def nivel_score(score: int) -> str:
    if score >= 90:
        return "verde"
    if score >= 70:
        return "amarillo"
    return "rojo"


def calcular_dashboard_calidad(
    errores: list[dict],
    advertencias_coherencia: list[dict],
    riesgos_periciales: list[dict],
    revision_juridica: list[dict],
) -> dict:
    total_errores = len(errores)
    total_advertencias = len(advertencias_coherencia)
    total_riesgos = len(riesgos_periciales)
    total_revision_juridica = len(revision_juridica)
    conclusiones_sin_soporte = sum(
        1
        for item in advertencias_coherencia
        if item.get("codigo") == "UNSUPPORTED_CONCLUSION_BASIC"
    )

    score_global = limitar_score(
        100
        - total_errores * 20
        - total_advertencias * 5
        - total_riesgos * 7
        - total_revision_juridica * 5
    )
    score_integridad = limitar_score(
        100
        - total_errores * 25
        - total_advertencias * 5
    )
    score_riesgo_tecnico = limitar_score(
        100
        - total_riesgos * 10
        - conclusiones_sin_soporte * 10
    )
    score_riesgo_juridico = limitar_score(100 - total_revision_juridica * 10)

    total_incidencias = (
        total_errores
        + total_advertencias
        + total_riesgos
        + total_revision_juridica
    )
    if total_errores or total_riesgos >= 3 or total_revision_juridica >= 4 or score_global < 70:
        estado = "revision_necesaria"
    elif total_incidencias:
        estado = "con_advertencias"
    else:
        estado = "listo"

    return {
        "score_global": score_global,
        "score_integridad": score_integridad,
        "score_riesgo_tecnico": score_riesgo_tecnico,
        "score_riesgo_juridico": score_riesgo_juridico,
        "estado": estado,
        "nivel": nivel_score(score_global),
        "totales": {
            "errores": total_errores,
            "advertencias": total_advertencias,
            "riesgos_periciales": total_riesgos,
            "revision_juridica": total_revision_juridica,
        },
    }


def aplicar_reglas(cur, expediente_id: int) -> dict:
    capitulos = cargar_capitulos(cur, expediente_id)
    texto_informe = cargar_texto_informe(capitulos)
    texto_norm = normalizar_texto(texto_informe)
    fotos = cargar_fotos(cur, expediente_id)
    documentos = cargar_documentos(cur, expediente_id)
    estancias = cargar_estancias(cur, expediente_id)
    total_patologias = contar_patologias(cur, expediente_id)
    anexos = anexos_disponibles(fotos, documentos, total_patologias, capitulos)

    errores: list[dict] = []
    advertencias: list[dict] = []
    informacion: list[dict] = []
    riesgos_periciales = detectar_afirmaciones_riesgo(capitulos, expediente_id)
    revision_juridica = detectar_revision_juridica(capitulos, expediente_id)
    advertencias.extend(riesgos_periciales)
    advertencias.extend(revision_juridica)

    for clave, titulo in CAPITULOS_PRINCIPALES:
        capitulo = capitulos.get(clave)
        if not contenido_relevante(capitulo.get("contenido", "") if capitulo else ""):
            errores.append(
                incidencia(
                    "EMPTY_CHAPTER",
                    "error",
                    "capitulos",
                    f"El capítulo principal '{titulo}' está vacío o no tiene contenido técnico relevante.",
                    "informe_v2_capitulos",
                    capitulo.get("id") if capitulo else clave,
                    f"/expedientes/{expediente_id}/informe-v2-editor#capitulo-{clave}",
                )
            )

    referencias_fotos = extraer_referencias_fotos(texto_informe)
    total_fotos = len(fotos)
    for foto in fotos:
        numero = int(foto["numero"])
        if numero not in referencias_fotos:
            advertencias.append(
                incidencia(
                    "PHOTO_NOT_REFERENCED",
                    "advertencia",
                    "fotografias",
                    f"La fotografía {numero} existe, pero no aparece citada como Figura/Foto/Imagen {numero} en el informe.",
                    foto["entidad"],
                    foto["entidad_id"],
                )
            )
    for numero in sorted(ref for ref in referencias_fotos if ref < 1 or ref > total_fotos):
        errores.append(
            incidencia(
                "PHOTO_REFERENCE_BROKEN",
                "error",
                "fotografias",
                f"El informe cita Figura/Foto/Imagen {numero}, pero solo constan {total_fotos} fotografía(s).",
                "referencia_fotografica",
                numero,
                f"/expedientes/{expediente_id}/informe-v2-editor",
            )
        )

    referencias_anexos = extraer_referencias_anexos(texto_informe)
    for letra, titulo in anexos.items():
        if letra not in referencias_anexos:
            advertencias.append(
                incidencia(
                    "ANNEX_NOT_REFERENCED",
                    "advertencia",
                    "anexos",
                    f"El Anexo {letra} ({titulo}) está disponible, pero no aparece citado en el informe.",
                    "anexo",
                    letra,
                )
            )
    for letra in sorted(ref for ref in referencias_anexos if ref not in anexos):
        errores.append(
            incidencia(
                "ANNEX_REFERENCE_BROKEN",
                "error",
                "anexos",
                f"El informe cita el Anexo {letra}, pero ese anexo no está disponible con los datos actuales.",
                "anexo",
                letra,
                f"/expedientes/{expediente_id}/informe-v2-editor",
            )
        )

    if estancias:
        estancias_norm = {
            normalizar_texto(estancia.get("nombre"))
            for estancia in estancias
            if normalizar_texto(estancia.get("nombre"))
        }
        tipos_norm = {
            normalizar_texto(estancia.get("tipo_estancia"))
            for estancia in estancias
            if normalizar_texto(estancia.get("tipo_estancia"))
        }
        conocidas = estancias_norm | tipos_norm
        menciones = {
            normalizar_texto(match.group(1))
            for match in REFERENCIA_ESTANCIA_RE.finditer(texto_informe)
        }
        for mencion in sorted(m for m in menciones if m and m not in conocidas):
            base = re.sub(r"\s+\d+$", "", mencion)
            if base in conocidas and not re.search(r"\d+$", mencion):
                continue
            advertencias.append(
                incidencia(
                    "ROOM_REFERENCE_UNKNOWN",
                    "advertencia",
                    "estancias",
                    f"El informe menciona '{mencion}', pero no coincide con las estancias o tipos registrados.",
                    "estancia_referida",
                    mencion,
                )
            )

    conclusiones = "\n\n".join(
        limpiar_texto(capitulos.get(clave, {}).get("contenido"))
        for clave in CAPITULOS_REFERENCIA
    )
    conclusiones_norm = normalizar_texto(conclusiones)
    menciona_soporte = any(keyword in conclusiones_norm for keyword in CONCLUSION_SOPORTE_KEYWORDS)
    if menciona_soporte and not fotos and not documentos and total_patologias == 0:
        advertencias.append(
            incidencia(
                "UNSUPPORTED_CONCLUSION_BASIC",
                "advertencia",
                "conclusiones",
                "Las conclusiones mencionan daños, riesgos o medidas, pero no constan patologías, fotografías ni documentos de soporte.",
                "informe_v2_capitulos",
                "conclusiones_periciales",
                f"/expedientes/{expediente_id}/informe-v2-editor#capitulo-conclusiones_periciales",
            )
        )

    if tabla_existe(cur, "visitas"):
        hoy = date.today()
        visitas = cur.execute(
            "SELECT id, fecha FROM visitas WHERE expediente_id = ?",
            (expediente_id,),
        ).fetchall()
        for visita in visitas:
            fecha = parse_fecha(visita["fecha"])
            if fecha and fecha > hoy:
                advertencias.append(
                    incidencia(
                        "TIMELINE_INCONSISTENT_BASIC",
                        "advertencia",
                        "cronologia",
                        f"La visita {visita['id']} tiene fecha futura ({fecha.isoformat()}).",
                        "visitas",
                        visita["id"],
                    )
                )

    informacion.append(
        incidencia(
            "CONSISTENCY_SUMMARY",
            "info",
            "resumen",
            (
                f"Revisión V1 ejecutada sobre {len(capitulos)} capítulo(s), "
                f"{len(fotos)} fotografía(s), {len(documentos)} documento(s) y {len(estancias)} estancia(s)."
            ),
            "expedientes",
            expediente_id,
        )
    )

    score = max(0, 100 - len(errores) * 20 - len(advertencias) * 8 - len(informacion) * 2)
    advertencias_coherencia = [
        item
        for item in advertencias
        if item.get("categoria") not in {"riesgo_pericial", "revision_juridica"}
    ]
    dashboard_calidad = calcular_dashboard_calidad(
        errores,
        advertencias_coherencia,
        riesgos_periciales,
        revision_juridica,
    )
    return {
        "expediente_id": expediente_id,
        "errores": errores,
        "advertencias": advertencias,
        "advertencias_coherencia": advertencias_coherencia,
        "riesgos_periciales": riesgos_periciales,
        "revision_juridica": revision_juridica,
        "dashboard_calidad": dashboard_calidad,
        "informacion": informacion,
        "score": score,
        "resumen": {
            "errores": len(errores),
            "advertencias": len(advertencias),
            "advertencias_coherencia": len(advertencias_coherencia),
            "riesgos_periciales": len(riesgos_periciales),
            "revision_juridica": len(revision_juridica),
            "informacion": len(informacion),
            "fotografias": len(fotos),
            "documentos": len(documentos),
            "estancias": len(estancias),
            "patologias": total_patologias,
            "anexos_disponibles": sorted(anexos),
        },
    }


def analizar_consistencia_expediente(expediente_id: int) -> dict:
    conn = get_connection()
    try:
        return aplicar_reglas(conn.cursor(), expediente_id)
    finally:
        conn.close()
