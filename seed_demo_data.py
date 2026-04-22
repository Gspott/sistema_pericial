import binascii
import hashlib
import secrets
from pathlib import Path

from app.config import UPLOAD_DIR, ensure_directories
from app.database import get_connection, init_db


DEMO_EXPEDIENTES = [
    "DEMO-PAT-001",
    "DEMO-PAT-002",
    "DEMO-INS-003",
    "DEMO-HAB-004",
    "DEMO-VAL-005",
]


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return (
        "pbkdf2_sha256$100000$"
        f"{binascii.hexlify(salt).decode()}$"
        f"{binascii.hexlify(digest).decode()}"
    )


def ensure_owner(cur):
    owner = cur.execute(
        "SELECT * FROM usuarios WHERE activo=1 ORDER BY id ASC LIMIT 1"
    ).fetchone()
    if owner:
        return owner["id"], False

    cur.execute(
        """
        INSERT INTO usuarios (
            nombre, apellido1, apellido2, telefono, email, titulacion,
            numero_colegiado, username, password_hash, activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            "Demo",
            "Sistema",
            "Pericial",
            "600000000",
            "demo@sistema-pericial.local",
            "Arquitecto técnico",
            "DEMO-001",
            "demo_seed",
            hash_password("Demo1234!"),
        ),
    )
    return cur.lastrowid, True


def expediente_exists(cur, numero_expediente: str) -> bool:
    row = cur.execute(
        "SELECT id FROM expedientes WHERE numero_expediente=?",
        (numero_expediente,),
    ).fetchone()
    return row is not None


def write_demo_image(filename: str, title: str) -> str:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return ""

    upload_path = Path(UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    target = upload_path / filename
    if target.exists():
        return filename

    image = Image.new("RGB", (1400, 900), color=(242, 244, 247))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle([(40, 40), (1360, 860)], outline=(120, 128, 140), width=3)
    draw.text((80, 80), title, fill=(30, 41, 59), font=font)
    draw.text(
        (80, 120),
        "Imagen demo para pruebas de mapas y cuadrantes",
        fill=(71, 85, 105),
        font=font,
    )
    image.save(target, format="PNG")
    return filename


def insert_expediente(cur, owner_id: int, data: dict) -> int:
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    cur.execute(
        f"INSERT INTO expedientes ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    return cur.lastrowid


def insert_visita(cur, data: dict) -> int:
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    cur.execute(
        f"INSERT INTO visitas ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    return cur.lastrowid


def insert_estancia(cur, data: dict) -> int:
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    cur.execute(
        f"INSERT INTO estancias ({columns}) VALUES ({placeholders})",
        tuple(data.values()),
    )
    return cur.lastrowid


def insert_nivel(cur, expediente_id: int, nombre: str, orden: int, tipo: str) -> int:
    cur.execute(
        """
        INSERT INTO niveles_edificio (expediente_id, nombre_nivel, orden_nivel, tipo_nivel)
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, nombre, orden, tipo),
    )
    return cur.lastrowid


def insert_unidad(
    cur,
    expediente_id: int,
    identificador: str,
    tipo_unidad: str,
    vinculo_unidad: str,
    nivel_id=None,
    uso="",
    superficie="",
    referencia="",
    es_principal=1,
    unidad_principal_id=None,
    tipo_anejo="",
    observaciones="",
) -> int:
    cur.execute(
        """
        INSERT INTO unidades_expediente (
            expediente_id, nivel_id, identificador, tipo_unidad, uso, superficie,
            referencia_catastral_unidad, es_principal, unidad_principal_id,
            tipo_anejo, vinculo_unidad, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expediente_id,
            nivel_id,
            identificador,
            tipo_unidad,
            uso,
            superficie,
            referencia,
            es_principal,
            unidad_principal_id,
            tipo_anejo,
            vinculo_unidad,
            observaciones,
        ),
    )
    return cur.lastrowid


def insert_mapa(cur, visita_id: int, titulo: str, ambito_mapa: str, filas: int, columnas: int, imagen_base: str, descripcion="", observaciones="") -> int:
    cur.execute(
        """
        INSERT INTO mapas_patologia (
            visita_id, titulo, descripcion, ambito_mapa, filas, columnas, imagen_base, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (visita_id, titulo, descripcion, ambito_mapa, filas, columnas, imagen_base, observaciones),
    )
    return cur.lastrowid


def generate_quadrants(cur, mapa_id: int, filas: int, columnas: int):
    quadrant_ids = {}
    for row_index in range(filas):
        row_letter = chr(65 + row_index)
        for col_index in range(1, columnas + 1):
            code = f"{row_letter}{col_index}"
            cur.execute(
                """
                INSERT INTO cuadrantes_mapa_patologia (mapa_id, codigo_cuadrante)
                VALUES (?, ?)
                """,
                (mapa_id, code),
            )
            quadrant_ids[code] = cur.lastrowid
    return quadrant_ids


def update_quadrant(cur, cuadrante_id: int, **fields):
    assignments = ", ".join(f"{key}=?" for key in fields.keys())
    cur.execute(
        f"UPDATE cuadrantes_mapa_patologia SET {assignments} WHERE id=?",
        (*fields.values(), cuadrante_id),
    )


def seed_expediente_1(cur, owner_id: int):
    expediente_id = insert_expediente(
        cur,
        owner_id,
        {
            "numero_expediente": "DEMO-PAT-001",
            "tipo_informe": "patologias",
            "destinatario": "particular",
            "cliente": "DEMO Cliente Unifamiliar",
            "referencia_catastral": "1111111VK4711S0001AA",
            "direccion": "Calle Magnolia 12",
            "codigo_postal": "28001",
            "ciudad": "Madrid",
            "provincia": "Madrid",
            "tipo_inmueble": "Vivienda unifamiliar",
            "orientacion_inmueble": "Sur",
            "anio_construccion": "1998",
            "plantas_bajo_rasante": "0",
            "plantas_sobre_baja": "2",
            "uso_inmueble": "Residencial",
            "observaciones_generales": "Expediente demo de patologías interiores con apoyo de mapa de fachada.",
            "planta_unidad": "Baja y primera",
            "puerta_unidad": "Vivienda única",
            "superficie_construida": "186 m2",
            "superficie_util": "154 m2",
            "dormitorios_unidad": "4",
            "banos_unidad": "3",
            "observaciones_bloque": "",
            "observaciones_unidad": "La vivienda presenta signos de humedades en varias estancias.",
            "reformado": "Sí",
            "fecha_reforma": "2019",
            "observaciones_reforma": "Reforma parcial de acabados y cocina.",
            "ambito_patologias": "interior_exterior",
            "descripcion_dano": "Fisuras y humedades en paramentos interiores, con manifestación exterior en fachada.",
            "causa_probable": "Entrada de agua por fisuración de revestimiento y puentes térmicos localizados.",
            "pruebas_indicios": "Inspección visual, contraste de manchas y lectura higrométrica puntual.",
            "evolucion_preexistencia": "Daño progresivo apreciable en los últimos dos inviernos.",
            "propuesta_reparacion": "Sellado de fisuras, revisión de revestimiento exterior y saneado interior.",
            "urgencia_gravedad": "Media",
            "owner_user_id": owner_id,
        },
    )
    nivel_baja = insert_nivel(cur, expediente_id, "Planta baja", 0, "baja")
    vivienda = insert_unidad(
        cur,
        expediente_id,
        "Vivienda principal",
        "vivienda",
        "principal",
        nivel_id=nivel_baja,
        uso="Residencial",
        superficie="186 m2",
        referencia="1111111VK4711S0001AA",
    )
    visita_id = insert_visita(
        cur,
        {
            "expediente_id": expediente_id,
            "fecha": "2026-02-10",
            "tecnico": "Carlos Blanco",
            "observaciones_visita": "Visita única con toma de datos interior y revisión puntual de fachada.",
            "ambito_visita": "unidad",
            "nivel_id": nivel_baja,
            "unidad_id": vivienda,
        },
    )
    salon = insert_estancia(
        cur,
        {
            "visita_id": visita_id,
            "nombre": "Salón",
            "tipo_estancia": "salón",
            "ventilacion": "Ventana a fachada principal",
            "planta": "Baja",
            "acabado_pavimento": "Tarima",
            "acabado_paramento": "Pintura lisa",
            "acabado_techo": "Yeso pintado",
            "observaciones": "Manchas en paramento norte.",
            "unidad_id": vivienda,
        },
    )
    dormitorio = insert_estancia(
        cur,
        {
            "visita_id": visita_id,
            "nombre": "Dormitorio principal",
            "tipo_estancia": "dormitorio",
            "ventilacion": "Ventana abatible",
            "planta": "Primera",
            "acabado_pavimento": "Laminado",
            "acabado_paramento": "Pintura lisa",
            "acabado_techo": "Escayola",
            "observaciones": "Fisura vertical junto a carpintería.",
            "unidad_id": vivienda,
        },
    )
    cocina = insert_estancia(
        cur,
        {
            "visita_id": visita_id,
            "nombre": "Cocina",
            "tipo_estancia": "cocina",
            "ventilacion": "Ventilación natural y extractor",
            "planta": "Baja",
            "acabado_pavimento": "Gres",
            "acabado_paramento": "Alicatado y pintura",
            "acabado_techo": "Pintura plástica",
            "observaciones": "Condensaciones ligeras en encuentro con fachada.",
            "unidad_id": vivienda,
        },
    )
    cur.execute(
        """
        INSERT INTO registros_patologias
        (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            salon,
            "paramento",
            "paramento",
            "Humedad por filtración",
            "Mancha activa en paramento norte del salón.",
            "",
        ),
    )
    pat_1 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO registros_patologias
        (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            dormitorio,
            "paramento",
            "paramento",
            "Fisura vertical",
            "Fisura fina junto a carpintería exterior.",
            "",
        ),
    )
    pat_2 = cur.lastrowid
    cur.execute(
        """
        INSERT INTO registros_patologias
        (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            cocina,
            "techo",
            "techo",
            "Condensación superficial",
            "Oscurecimiento puntual en encuentro de techo y fachada.",
            "",
        ),
    )
    cur.execute(
        """
        INSERT INTO registros_patologias_exteriores
        (visita_id, zona_exterior, elemento_exterior, localizacion_dano_exterior, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "fachada",
            "revestimiento",
            "vertical",
            "Fisuración del revestimiento",
            "Fisuras verticales sobre la crujía del salón.",
            "",
        ),
    )
    fachada_map = insert_mapa(
        cur,
        visita_id,
        "Fachada principal",
        "unidad",
        4,
        4,
        write_demo_image("demo_pat_001_fachada.png", "DEMO-PAT-001 · Fachada principal"),
        descripcion="Mapa base para localizar daños en fachada principal.",
    )
    qids = generate_quadrants(cur, fachada_map, 4, 4)
    update_quadrant(
        cur,
        qids["A2"],
        descripcion="Fisura vertical alineada con el salón.",
        patologia_detectada="Humedad por filtración",
        patologia_id=pat_1,
        gravedad="media",
        observaciones="Zona con pérdida de revestimiento.",
    )
    update_quadrant(
        cur,
        qids["B3"],
        descripcion="Fisura en paño superior junto a hueco.",
        patologia_detectada="Fisura vertical",
        patologia_id=pat_2,
        gravedad="leve",
        observaciones="Relacionada con movimiento diferencial.",
    )


def seed_expediente_2(cur, owner_id: int):
    expediente_id = insert_expediente(
        cur,
        owner_id,
        {
            "numero_expediente": "DEMO-PAT-002",
            "tipo_informe": "patologias",
            "destinatario": "judicial",
            "cliente": "DEMO Juzgado de Primera Instancia",
            "referencia_catastral": "2222222VK4722S0001BB",
            "direccion": "Avenida del Prado 45",
            "codigo_postal": "41001",
            "ciudad": "Sevilla",
            "provincia": "Sevilla",
            "tipo_inmueble": "Edificio plurifamiliar",
            "orientacion_inmueble": "Este-Oeste",
            "anio_construccion": "1984",
            "plantas_bajo_rasante": "1",
            "plantas_sobre_baja": "4",
            "uso_inmueble": "Residencial",
            "observaciones_generales": "Expediente demo judicial con visitas por unidad, zona común y exterior.",
            "planta_unidad": "",
            "puerta_unidad": "",
            "superficie_construida": "",
            "superficie_util": "",
            "dormitorios_unidad": "",
            "banos_unidad": "",
            "observaciones_bloque": "Fachadas revocadas y cubierta plana transitable.",
            "observaciones_unidad": "",
            "reformado": "No",
            "fecha_reforma": "",
            "observaciones_reforma": "",
            "procedimiento_judicial": "Proc. ordinario 214/2026",
            "juzgado": "Juzgado de Primera Instancia nº 8 de Sevilla",
            "auto_judicial": "Auto de fecha 03/01/2026",
            "parte_solicitante": "Comunidad de propietarios y codemandados",
            "objeto_pericia": "Determinación de origen y alcance de daños por humedades y fisuras.",
            "alcance_limitaciones": "Inspección visual sin apertura de calas destructivas.",
            "metodologia_pericial": "Inspección presencial, reportaje fotográfico y comparación de daños por ámbitos.",
            "ambito_patologias": "interior_exterior",
            "descripcion_dano": "Patologías repartidas entre dos viviendas, portal y fachada norte.",
            "causa_probable": "Entrada de agua desde cubierta y fisuración de fachada.",
            "pruebas_indicios": "Coincidencia vertical de manchas, fisuras exteriores y degradación de revestimientos.",
            "evolucion_preexistencia": "Daños reiterados tras episodios de lluvia intensa.",
            "propuesta_reparacion": "Intervenir cubierta, fachada y saneado interior por ámbitos.",
            "urgencia_gravedad": "Alta",
            "owner_user_id": owner_id,
        },
    )
    nivel_baja = insert_nivel(cur, expediente_id, "Planta baja", 0, "baja")
    nivel_primera = insert_nivel(cur, expediente_id, "Planta primera", 1, "sobre_rasante")
    nivel_cubierta = insert_nivel(cur, expediente_id, "Cubierta", 4, "cubierta")
    vivienda_1a = insert_unidad(cur, expediente_id, "Vivienda 1A", "vivienda", "principal", nivel_id=nivel_primera, uso="Residencial", superficie="92 m2")
    vivienda_1b = insert_unidad(cur, expediente_id, "Vivienda 1B", "vivienda", "principal", nivel_id=nivel_primera, uso="Residencial", superficie="88 m2")
    portal = insert_unidad(cur, expediente_id, "Portal de acceso", "zona_comun", "comun", nivel_id=nivel_baja, uso="Común", superficie="28 m2")
    fachada_norte = insert_unidad(cur, expediente_id, "Fachada norte", "exterior", "exterior", nivel_id=nivel_cubierta, uso="Envolvente", superficie="140 m2")

    visita_1a = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-01-14", "tecnico": "Carlos Blanco", "observaciones_visita": "Inspección interior vivienda 1A.", "ambito_visita": "unidad", "nivel_id": nivel_primera, "unidad_id": vivienda_1a})
    visita_1b = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-01-15", "tecnico": "Carlos Blanco", "observaciones_visita": "Inspección interior vivienda 1B.", "ambito_visita": "unidad", "nivel_id": nivel_primera, "unidad_id": vivienda_1b})
    visita_portal = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-01-16", "tecnico": "Carlos Blanco", "observaciones_visita": "Inspección de portal y zonas comunes inmediatas.", "ambito_visita": "zona_comun", "nivel_id": nivel_baja, "unidad_id": portal})
    visita_fachada = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-01-16", "tecnico": "Carlos Blanco", "observaciones_visita": "Inspección de fachada norte y coronación.", "ambito_visita": "exterior", "nivel_id": nivel_cubierta, "unidad_id": fachada_norte})

    salon_1a = insert_estancia(cur, {"visita_id": visita_1a, "nombre": "Salón 1A", "tipo_estancia": "salón", "ventilacion": "Balconera", "planta": "Primera", "acabado_pavimento": "Tarima", "acabado_paramento": "Pintura", "acabado_techo": "Yeso", "observaciones": "Mancha en esquina con fachada norte.", "unidad_id": vivienda_1a})
    dormitorio_1b = insert_estancia(cur, {"visita_id": visita_1b, "nombre": "Dormitorio 1B", "tipo_estancia": "dormitorio", "ventilacion": "Ventana corredera", "planta": "Primera", "acabado_pavimento": "Laminado", "acabado_paramento": "Pintura", "acabado_techo": "Escayola", "observaciones": "Fisura diagonal sobre hueco.", "unidad_id": vivienda_1b})
    portal_estancia = insert_estancia(cur, {"visita_id": visita_portal, "nombre": "Portal", "tipo_estancia": "recibidor", "ventilacion": "Ventilación natural", "planta": "Baja", "acabado_pavimento": "Piedra", "acabado_paramento": "Enfoscado pintado", "acabado_techo": "Yeso", "observaciones": "Desconchados en encuentro con fachada.", "unidad_id": portal})

    cur.execute("INSERT INTO registros_patologias (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto) VALUES (?, ?, ?, ?, ?, ?, ?)", (visita_1a, salon_1a, "paramento", "paramento", "Humedad en esquina", "Mancha recurrente en salón orientado a fachada norte.", ""))
    pat_1a = cur.lastrowid
    cur.execute("INSERT INTO registros_patologias (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto) VALUES (?, ?, ?, ?, ?, ?, ?)", (visita_1b, dormitorio_1b, "paramento", "paramento", "Fisura diagonal", "Fisura sobre cargadero de hueco exterior.", ""))
    pat_1b = cur.lastrowid
    cur.execute("INSERT INTO registros_patologias (visita_id, estancia_id, elemento, localizacion_dano, patologia, observaciones, foto) VALUES (?, ?, ?, ?, ?, ?, ?)", (visita_portal, portal_estancia, "paramento", "paramento", "Desconchado de revestimiento", "Desprendimiento superficial en portal.", ""))
    pat_portal = cur.lastrowid
    cur.execute("INSERT INTO registros_patologias_exteriores (visita_id, zona_exterior, elemento_exterior, localizacion_dano_exterior, patologia, observaciones, foto) VALUES (?, ?, ?, ?, ?, ?, ?)", (visita_fachada, "fachada", "revestimiento", "vertical", "Fisuras verticales en fachada", "Fisuras en paño central y coronación.", ""))
    pat_ext = cur.lastrowid

    mapa_fachada = insert_mapa(cur, visita_fachada, "Fachada norte", "exterior", 5, 4, write_demo_image("demo_pat_002_fachada_norte.png", "DEMO-PAT-002 · Fachada norte"), descripcion="Paño principal de fachada norte.")
    q_fachada = generate_quadrants(cur, mapa_fachada, 5, 4)
    update_quadrant(cur, q_fachada["A1"], descripcion="Fisura en coronación.", patologia_detectada="Fisuras verticales en fachada", patologia_id=pat_ext, gravedad="grave", observaciones="Afecta encuentro superior.")
    update_quadrant(cur, q_fachada["C2"], descripcion="Fisura junto a hueco de vivienda 1A.", patologia_detectada="Humedad en esquina", patologia_id=pat_1a, gravedad="media", observaciones="Coincidencia con daño interior.")

    mapa_portal = insert_mapa(cur, visita_portal, "Portal de acceso", "zona_comun", 3, 3, write_demo_image("demo_pat_002_portal.png", "DEMO-PAT-002 · Portal de acceso"), descripcion="Mapa de paramentos del portal.")
    q_portal = generate_quadrants(cur, mapa_portal, 3, 3)
    update_quadrant(cur, q_portal["B2"], descripcion="Desconchado central en paramento.", patologia_detectada="Desconchado de revestimiento", patologia_id=pat_portal, gravedad="media", observaciones="Coincide con arranque capilar.")
    update_quadrant(cur, q_portal["C1"], descripcion="Fisura diagonal secundaria.", patologia_detectada="Fisura diagonal", patologia_id=pat_1b, gravedad="leve", observaciones="Referencia comparativa por daños de edificio.")


def seed_expediente_3(cur, owner_id: int):
    expediente_id = insert_expediente(
        cur,
        owner_id,
        {
            "numero_expediente": "DEMO-INS-003",
            "tipo_informe": "inspeccion",
            "destinatario": "particular",
            "cliente": "DEMO Familia Romero",
            "referencia_catastral": "3333333VK4733S0001CC",
            "direccion": "Plaza Nueva 8",
            "codigo_postal": "46001",
            "ciudad": "Valencia",
            "provincia": "Valencia",
            "tipo_inmueble": "Vivienda en bloque",
            "orientacion_inmueble": "Sureste",
            "anio_construccion": "2007",
            "plantas_bajo_rasante": "1",
            "plantas_sobre_baja": "6",
            "uso_inmueble": "Residencial",
            "observaciones_generales": "Expediente demo de inspección integral.",
            "planta_unidad": "3ª",
            "puerta_unidad": "B",
            "superficie_construida": "104 m2",
            "superficie_util": "86 m2",
            "dormitorios_unidad": "3",
            "banos_unidad": "2",
            "observaciones_bloque": "Edificio con zonas comunes en estado de uso normal.",
            "observaciones_unidad": "Vivienda con mantenimiento medio.",
            "reformado": "Sí",
            "fecha_reforma": "2020",
            "observaciones_reforma": "Actualización de cocina y baños.",
            "owner_user_id": owner_id,
        },
    )
    nivel_tercera = insert_nivel(cur, expediente_id, "Planta tercera", 3, "sobre_rasante")
    nivel_baja = insert_nivel(cur, expediente_id, "Planta baja", 0, "baja")
    vivienda = insert_unidad(cur, expediente_id, "Vivienda 3B", "vivienda", "principal", nivel_id=nivel_tercera, uso="Residencial", superficie="104 m2")
    portal = insert_unidad(cur, expediente_id, "Portal", "zona_comun", "comun", nivel_id=nivel_baja, uso="Común", superficie="30 m2")
    visita_id = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-02-18", "tecnico": "Carlos Blanco", "observaciones_visita": "Inspección general con revisión de vivienda y elementos comunes.", "ambito_visita": "unidad", "nivel_id": nivel_tercera, "unidad_id": vivienda})
    salon = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Salón", "tipo_estancia": "salón", "ventilacion": "Ventanal corredero", "planta": "3ª", "acabado_pavimento": "Tarima", "acabado_paramento": "Pintura lisa", "acabado_techo": "Yeso", "observaciones": "", "unidad_id": vivienda})
    cocina = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Cocina", "tipo_estancia": "cocina", "ventilacion": "Extractor y ventana", "planta": "3ª", "acabado_pavimento": "Gres", "acabado_paramento": "Alicatado", "acabado_techo": "Pintura", "observaciones": "", "unidad_id": vivienda})
    bano = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Baño principal", "tipo_estancia": "baño", "ventilacion": "Forzada", "planta": "3ª", "acabado_pavimento": "Gres antideslizante", "acabado_paramento": "Alicatado", "acabado_techo": "Pintura", "observaciones": "", "unidad_id": vivienda})
    cur.execute(
        """
        INSERT INTO inspeccion_general_visita (
            visita_id, puerta_entrada, vestibulo, ventilacion_cruzada, ventilacion_general_inmueble,
            iluminacion_natural_general, orientacion_general, reformado_cambio_uso,
            estructura_vertical, estructura_horizontal, forjados_voladizos, cubiertas, soleras_losas,
            instalacion_electrica_general, agua_acs, calefaccion, climatizacion,
            carpinterias_generales, persianas_generales, barandillas_generales, vierteaguas_generales,
            observaciones_generales_inspeccion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id, "no_necesita_reparacion", "no_necesita_reparacion", "no_inspeccionado",
            "no_necesita_reparacion", "no_necesita_reparacion", "no_inspeccionado",
            "no_aplica", "no_necesita_reparacion", "no_necesita_reparacion",
            "necesita_reparacion", "necesita_reparacion", "no_necesita_reparacion",
            "no_necesita_reparacion", "no_necesita_reparacion", "no_inspeccionado",
            "no_necesita_reparacion", "no_necesita_reparacion", "necesita_reparacion",
            "no_necesita_reparacion", "necesita_reparacion",
            "Cubierta con mantenimiento pendiente y persianas con ajustes menores.",
        ),
    )
    for estancia_id, extra in [
        (salon, {"persiana": "necesita_reparacion", "cajon_persiana": "necesita_reparacion", "carpinteria_estancia": "no_necesita_reparacion", "cierre_manivela": "no_necesita_reparacion", "tomas_corriente": "no_necesita_reparacion"}),
        (cocina, {"extractor": "necesita_reparacion", "encimera": "no_necesita_reparacion", "zona_coccion": "no_necesita_reparacion", "frigorifico": "no_inspeccionado", "horno": "no_inspeccionado", "fregadero": "no_necesita_reparacion", "griferia": "necesita_reparacion", "sifones": "no_necesita_reparacion", "desagues": "no_necesita_reparacion", "llaves_paso": "no_inspeccionado", "conexion_lavavajillas": "no_aplica"}),
        (bano, {"banera_ducha": "no_necesita_reparacion", "mampara": "necesita_reparacion", "lavabo": "no_necesita_reparacion", "inodoro": "no_necesita_reparacion", "bide": "no_aplica", "espejo": "no_necesita_reparacion", "ventilacion_forzada": "necesita_reparacion", "condensacion": "necesita_reparacion", "griferia": "no_necesita_reparacion", "sifones": "no_necesita_reparacion", "desagues": "no_necesita_reparacion", "llaves_paso": "no_inspeccionado"}),
    ]:
        base = {
            "visita_id": visita_id,
            "estancia_id": estancia_id,
            "puerta": "no_necesita_reparacion",
            "revestimiento": "no_necesita_reparacion",
            "iluminacion": "no_necesita_reparacion",
            "mobiliario": "no_inspeccionado",
            "mecanismos_electricos": "no_necesita_reparacion",
            "humedades": "necesita_reparacion" if estancia_id == bano else "no_necesita_reparacion",
            "techo": "no_necesita_reparacion",
            "pavimento": "no_necesita_reparacion",
            "observaciones_estancia_inspeccion": "Checklist demo de inspección.",
        }
        base.update(extra)
        columns = ", ".join(base.keys())
        placeholders = ", ".join(["?"] * len(base))
        cur.execute(f"INSERT INTO inspeccion_estancias ({columns}) VALUES ({placeholders})", tuple(base.values()))
    cur.execute(
        """
        INSERT INTO inspeccion_exterior (
            visita_id, fachadas, cubiertas_exteriores, patios_exteriores, terrazas_balcones,
            jardines, entorno_inmediato, carpinterias_exteriores, barandillas_exteriores,
            rejas_exteriores, toldos, tendederos, observaciones_exteriores
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id, "no_necesita_reparacion", "necesita_reparacion", "no_aplica",
            "no_necesita_reparacion", "no_aplica", "no_necesita_reparacion",
            "necesita_reparacion", "no_necesita_reparacion", "no_aplica",
            "no_aplica", "no_aplica", "Cubierta con revisión pendiente de impermeabilización.",
        ),
    )
    cur.execute(
        """
        INSERT INTO inspeccion_elementos_comunes (
            visita_id, portal_acceso, vestibulo_comun, pasillos_comunes, escaleras, ascensor,
            patio_luces, patio_ventilacion, fachada_comun, cubierta_comun, cuarto_instalaciones_comunes,
            observaciones_elementos_comunes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id, "no_necesita_reparacion", "no_necesita_reparacion", "no_necesita_reparacion",
            "no_necesita_reparacion", "necesita_reparacion", "no_inspeccionado", "no_inspeccionado",
            "no_necesita_reparacion", "necesita_reparacion", "no_inspeccionado",
            "Ascensor con ruidos en parada y cubierta común con mantenimiento pendiente.",
        ),
    )


def seed_expediente_4(cur, owner_id: int):
    expediente_id = insert_expediente(
        cur,
        owner_id,
        {
            "numero_expediente": "DEMO-HAB-004",
            "tipo_informe": "habitabilidad",
            "destinatario": "judicial",
            "cliente": "DEMO Letrado Judicial",
            "referencia_catastral": "4444444VK4744S0001DD",
            "direccion": "Calle Mayor 67",
            "codigo_postal": "50001",
            "ciudad": "Zaragoza",
            "provincia": "Zaragoza",
            "tipo_inmueble": "Vivienda",
            "orientacion_inmueble": "Oeste",
            "anio_construccion": "1976",
            "plantas_bajo_rasante": "0",
            "plantas_sobre_baja": "1",
            "uso_inmueble": "Residencial",
            "observaciones_generales": "Expediente demo de habitabilidad con encargo judicial.",
            "planta_unidad": "1ª",
            "puerta_unidad": "A",
            "superficie_construida": "78 m2",
            "superficie_util": "65 m2",
            "dormitorios_unidad": "2",
            "banos_unidad": "1",
            "observaciones_bloque": "",
            "observaciones_unidad": "Vivienda con ventilación escasa en baño y cocina.",
            "reformado": "No",
            "fecha_reforma": "",
            "observaciones_reforma": "",
            "procedimiento_judicial": "Diligencias previas 91/2026",
            "juzgado": "Juzgado Contencioso nº 2 de Zaragoza",
            "auto_judicial": "Oficio de 18/02/2026",
            "parte_solicitante": "Parte arrendataria",
            "objeto_pericia": "Evaluación de condiciones mínimas de habitabilidad.",
            "alcance_limitaciones": "Evaluación visual y funcional básica.",
            "metodologia_pericial": "Checklist de habitabilidad y visita al inmueble.",
            "owner_user_id": owner_id,
        },
    )
    nivel_primera = insert_nivel(cur, expediente_id, "Planta primera", 1, "sobre_rasante")
    vivienda = insert_unidad(cur, expediente_id, "Vivienda 1A", "vivienda", "principal", nivel_id=nivel_primera, uso="Residencial", superficie="78 m2")
    visita_id = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-03-02", "tecnico": "Carlos Blanco", "observaciones_visita": "Visita de habitabilidad con revisión general y por estancia.", "ambito_visita": "unidad", "nivel_id": nivel_primera, "unidad_id": vivienda})
    salon = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Salón", "tipo_estancia": "salón", "ventilacion": "Ventana a patio", "planta": "1ª", "acabado_pavimento": "Gres", "acabado_paramento": "Pintura", "acabado_techo": "Pintura", "observaciones": "", "unidad_id": vivienda})
    cocina = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Cocina", "tipo_estancia": "cocina", "ventilacion": "Ventana pequeña", "planta": "1ª", "acabado_pavimento": "Gres", "acabado_paramento": "Alicatado", "acabado_techo": "Pintura", "observaciones": "", "unidad_id": vivienda})
    bano = insert_estancia(cur, {"visita_id": visita_id, "nombre": "Baño", "tipo_estancia": "baño", "ventilacion": "Sin ventana", "planta": "1ª", "acabado_pavimento": "Gres", "acabado_paramento": "Alicatado", "acabado_techo": "Pintura", "observaciones": "", "unidad_id": vivienda})
    cur.execute(
        """
        INSERT INTO habitabilidad_general_visita (
            visita_id, ventilacion_general, iluminacion_natural_general, salubridad_general,
            seguridad_uso, instalaciones_basicas, accesibilidad_basica, adecuacion_uso_residencial,
            conclusion_habitabilidad, observaciones_generales_habitabilidad
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id, "no_cumple", "cumple", "no_cumple", "cumple",
            "cumple", "no_aplica", "cumple", "apto_con_deficiencias",
            "La vivienda resulta apta con deficiencias por ventilación y condensaciones en zonas húmedas.",
        ),
    )
    for estancia_id, ventilacion, iluminacion, humedades, salubridad, seguridad, obs in [
        (salon, "cumple", "cumple", "no_inspeccionado", "cumple", "cumple", "Salón con iluminación suficiente."),
        (cocina, "no_cumple", "cumple", "cumple", "cumple", "cumple", "Ventilación natural insuficiente."),
        (bano, "no_cumple", "no_aplica", "no_cumple", "no_cumple", "cumple", "Condensaciones y ausencia de ventilación natural."),
    ]:
        cur.execute(
            """
            INSERT INTO habitabilidad_estancias (
                visita_id, estancia_id, ventilacion, iluminacion,
                humedades_condensaciones, salubridad, seguridad_uso_estancia,
                observaciones_estancia_habitabilidad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, estancia_id, ventilacion, iluminacion, humedades, salubridad, seguridad, obs),
        )
    cur.execute(
        """
        INSERT INTO habitabilidad_exterior (
            visita_id, patio_ventilacion, fachada_humedades, cubierta_filtraciones, observaciones_exterior_habitabilidad
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            "no_cumple",
            "cumple",
            "no_inspeccionado",
            "El patio interior aporta escasa ventilación a cocina y baño.",
        ),
    )


def seed_expediente_5(cur, owner_id: int):
    expediente_id = insert_expediente(
        cur,
        owner_id,
        {
            "numero_expediente": "DEMO-VAL-005",
            "tipo_informe": "valoracion",
            "destinatario": "particular",
            "cliente": "DEMO Inversiones Levante SL",
            "referencia_catastral": "5555555VK4755S0001EE",
            "direccion": "Passeig Marítim 18",
            "codigo_postal": "07001",
            "ciudad": "Palma",
            "provincia": "Illes Balears",
            "tipo_inmueble": "Vivienda con anejos",
            "orientacion_inmueble": "Sureste",
            "anio_construccion": "2012",
            "plantas_bajo_rasante": "1",
            "plantas_sobre_baja": "5",
            "uso_inmueble": "Residencial",
            "observaciones_generales": "Expediente demo de valoración con vivienda y anejos.",
            "planta_unidad": "2ª",
            "puerta_unidad": "C",
            "superficie_construida": "112 m2",
            "superficie_util": "95 m2",
            "dormitorios_unidad": "3",
            "banos_unidad": "2",
            "observaciones_bloque": "Edificio residencial con piscina comunitaria.",
            "observaciones_unidad": "Vivienda con plaza de garaje y trastero vinculados.",
            "reformado": "No",
            "fecha_reforma": "",
            "observaciones_reforma": "",
            "owner_user_id": owner_id,
        },
    )
    nivel_segunda = insert_nivel(cur, expediente_id, "Planta segunda", 2, "sobre_rasante")
    nivel_sotano = insert_nivel(cur, expediente_id, "Sótano -1", -1, "bajo_rasante")
    vivienda = insert_unidad(cur, expediente_id, "Vivienda 2C", "vivienda", "principal", nivel_id=nivel_segunda, uso="Residencial", superficie="112 m2", referencia="5555555VK4755S0001EE")
    garaje = insert_unidad(cur, expediente_id, "Garaje G-14", "garaje", "anejo", nivel_id=nivel_sotano, uso="Aparcamiento", superficie="15 m2", es_principal=0, unidad_principal_id=vivienda, tipo_anejo="garaje")
    trastero = insert_unidad(cur, expediente_id, "Trastero T-8", "trastero", "anejo", nivel_id=nivel_sotano, uso="Almacenaje", superficie="6 m2", es_principal=0, unidad_principal_id=vivienda, tipo_anejo="trastero")
    visita_id = insert_visita(cur, {"expediente_id": expediente_id, "fecha": "2026-03-05", "tecnico": "Carlos Blanco", "observaciones_visita": "Visita de valoración de vivienda principal y comprobación de anejos vinculados.", "ambito_visita": "unidad", "nivel_id": nivel_segunda, "unidad_id": vivienda})
    cur.execute(
        """
        INSERT INTO valoracion_visita (
            visita_id, finalidad_valoracion, identificacion_bien, superficie_valoracion,
            estado_conservacion, antiguedad, calidades, ubicacion_valoracion,
            criterios_metodo_valoracion, testigos_comparables, valor_resultante,
            condicionantes_limitaciones_valoracion, observaciones_valoracion,
            nombre_solicitante, nif_cif_solicitante, domicilio_solicitante, entidad_financiera,
            finalidad_valoracion_detallada, documentacion_utilizada, datos_registrales,
            superficie_util, superficie_terraza, superficie_zonas_comunes, superficie_total,
            superficie_comprobada, situacion_ocupacion, situacion_urbanistica, servidumbres,
            linderos, descripcion_entorno, grado_consolidacion, antiguedad_entorno,
            rasgos_urbanos, nivel_renta, uso_predominante, equipamientos, infraestructuras,
            tipo_edificio, numero_portales, numero_escaleras, numero_ascensores, vistas,
            uso_residencial, estructura, cubierta, cerramientos, aislamiento, carpinteria,
            acristalamiento, instalaciones, estado_inmueble, regimen_ocupacion,
            inmueble_arrendado, fecha_visita, fecha_emision, fecha_caducidad,
            observaciones_testigos, variables_mercado, metodo_homogeneizacion,
            valor_unitario, valor_tasacion_final
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id, "Valor de mercado", "Vivienda 2C con garaje G-14 y trastero T-8", "112 m2",
            "Bueno", "2012", "Medias-altas", "Frente marítimo consolidado",
            "Método de comparación", "Testigos en radio de 1 km", "468000 €",
            "Sin visita interior de todas las viviendas testigo.", "La vivienda dispone de buenos acabados y anejos vinculados.",
            "DEMO Inversiones Levante SL", "B12345678", "Passeig Marítim 18, Palma", "Sin entidad financiera",
            "Obtención de valor orientativo para toma de decisiones patrimoniales.", "Nota simple, catastro, visita, planos y comparables publicados.", "Finca registral 12345 de Palma",
            "95 m2", "12 m2", "18 m2", "125 m2", "112 m2",
            "Libre", "Conforme a planeamiento", "No constan", "Linderos según catastro y nota simple",
            "Entorno residencial consolidado próximo al mar", "Alto", "15 años", "Zona urbana consolidada con servicios completos",
            "Media-alta", "Residencial", "Centros educativos, sanitarios y ocio", "Viales urbanos, transporte público y dotaciones",
            "Bloque plurifamiliar", "1", "2", "2", "Vistas parciales al mar",
            "Sí", "Hormigón armado", "Cubierta plana", "Fábrica revestida", "Aislamiento medio", "Aluminio lacado",
            "Doble acristalamiento", "Instalaciones actualizadas", "Bueno", "Libre", "No",
            "2026-03-05", "2026-03-10", "2026-09-10",
            "Mercado activo pero con menor rotación en producto premium.", "Ubicación, estado, superficie útil y anejos", "Homogeneización básica por estado, altura y anejos",
            "4.180 €/m2", "468000 €"
        ),
    )
    comparables = [
        ("Calle del Mar 21", "Portal inmobiliario", "2026-02-20", "475000 €", "4.210 €/m2", "113 m2", "96 m2", "Piso", "2ª", "3", "2", "Bueno", "2011", "Media-alta", "No", "Con plaza de garaje."),
        ("Avinguda Port 9", "Agencia local", "2026-02-28", "452000 €", "4.050 €/m2", "111 m2", "94 m2", "Piso", "3ª", "3", "2", "Bueno", "2010", "Media", "Sí", "Sin vistas al mar."),
        ("Passeig Marítim 30", "Portal inmobiliario", "2026-03-01", "489000 €", "4.360 €/m2", "112 m2", "95 m2", "Piso", "4ª", "3", "2", "Muy bueno", "2013", "Alta", "No", "Con terraza mayor."),
        ("Carrer de la Marina 4", "Agencia local", "2026-03-03", "461000 €", "4.120 €/m2", "112 m2", "95 m2", "Piso", "2ª", "3", "2", "Bueno", "2012", "Media-alta", "Sí", "Trastero no incluido en precio."),
    ]
    for comparable in comparables:
        cur.execute(
            """
            INSERT INTO comparables_valoracion (
                visita_id, direccion_testigo, fuente_testigo, fecha_testigo, precio_oferta,
                valor_unitario, superficie_construida, superficie_util, tipologia, planta,
                dormitorios, banos, estado_conservacion, antiguedad, calidad_constructiva,
                visitado, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, *comparable),
        )


def main():
    ensure_directories()
    init_db()

    conn = get_connection()
    cur = conn.cursor()

    owner_id, created_demo_user = ensure_owner(cur)
    created = []
    skipped = []

    seeds = [
        ("DEMO-PAT-001", seed_expediente_1),
        ("DEMO-PAT-002", seed_expediente_2),
        ("DEMO-INS-003", seed_expediente_3),
        ("DEMO-HAB-004", seed_expediente_4),
        ("DEMO-VAL-005", seed_expediente_5),
    ]

    for numero, seed_fn in seeds:
        if expediente_exists(cur, numero):
            skipped.append(numero)
            continue
        seed_fn(cur, owner_id)
        created.append(numero)

    conn.commit()
    conn.close()

    print("Seed demo completado.")
    if created_demo_user:
        print("Usuario demo creado: demo_seed / Demo1234!")
    if created:
        print("Expedientes creados:")
        for numero in created:
            print(f" - {numero}")
    if skipped:
        print("Expedientes omitidos por existir ya:")
        for numero in skipped:
            print(f" - {numero}")


if __name__ == "__main__":
    main()
