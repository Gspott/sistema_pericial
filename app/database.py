import sqlite3

from app.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def asegurar_columna(cur, tabla, columna, definicion):
    columnas = cur.execute(f"PRAGMA table_info({tabla})").fetchall()
    nombres = [col[1] for col in columnas]

    if columna not in nombres:
        cur.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def migrar_expedientes_superficies(cur):
    columnas = {
        col[1] for col in cur.execute("PRAGMA table_info(expedientes)").fetchall()
    }

    requiere_migracion = (
        "superficie" in columnas
        or "superficie_unidad" in columnas
        or "superficie_construida" not in columnas
        or "superficie_util" not in columnas
    )

    if not requiere_migracion:
        return

    cur.execute(
        """
        CREATE TABLE expedientes_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_expediente TEXT NOT NULL,
            cliente TEXT NOT NULL,
            referencia_catastral TEXT,
            direccion TEXT NOT NULL,
            codigo_postal TEXT,
            ciudad TEXT,
            provincia TEXT,
            tipo_inmueble TEXT,
            orientacion_inmueble TEXT,
            anio_construccion TEXT,
            plantas_bajo_rasante TEXT,
            plantas_sobre_baja TEXT,
            uso_inmueble TEXT,
            observaciones_generales TEXT,
            planta_unidad TEXT,
            puerta_unidad TEXT,
            superficie_construida TEXT,
            superficie_util TEXT,
            dormitorios_unidad TEXT,
            banos_unidad TEXT,
            observaciones_bloque TEXT,
            observaciones_unidad TEXT,
            reformado TEXT,
            fecha_reforma TEXT,
            observaciones_reforma TEXT,
            imagen_catastro TEXT,
            owner_user_id INTEGER,
            FOREIGN KEY (owner_user_id) REFERENCES usuarios (id)
        )
        """
    )

    superficie_construida_expr = (
        "superficie_construida"
        if "superficie_construida" in columnas
        else "superficie_unidad"
        if "superficie_unidad" in columnas
        else "NULL"
    )
    superficie_util_expr = "superficie_util" if "superficie_util" in columnas else "NULL"
    referencia_catastral_expr = (
        "referencia_catastral" if "referencia_catastral" in columnas else "NULL"
    )
    imagen_catastro_expr = "imagen_catastro" if "imagen_catastro" in columnas else "NULL"

    cur.execute(
        f"""
        INSERT INTO expedientes_new (
            id,
            numero_expediente,
            cliente,
            referencia_catastral,
            direccion,
            codigo_postal,
            ciudad,
            provincia,
            tipo_inmueble,
            orientacion_inmueble,
            anio_construccion,
            plantas_bajo_rasante,
            plantas_sobre_baja,
            uso_inmueble,
            observaciones_generales,
            planta_unidad,
            puerta_unidad,
            superficie_construida,
            superficie_util,
            dormitorios_unidad,
            banos_unidad,
            observaciones_bloque,
            observaciones_unidad,
            reformado,
            fecha_reforma,
            observaciones_reforma,
            imagen_catastro,
            owner_user_id
        )
        SELECT
            id,
            numero_expediente,
            cliente,
            {referencia_catastral_expr},
            direccion,
            codigo_postal,
            ciudad,
            provincia,
            tipo_inmueble,
            orientacion_inmueble,
            anio_construccion,
            plantas_bajo_rasante,
            plantas_sobre_baja,
            uso_inmueble,
            observaciones_generales,
            planta_unidad,
            puerta_unidad,
            {superficie_construida_expr},
            {superficie_util_expr},
            dormitorios_unidad,
            banos_unidad,
            observaciones_bloque,
            observaciones_unidad,
            reformado,
            fecha_reforma,
            observaciones_reforma,
            {imagen_catastro_expr},
            owner_user_id
        FROM expedientes
        """
    )

    cur.execute("DROP TABLE expedientes")
    cur.execute("ALTER TABLE expedientes_new RENAME TO expedientes")


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido1 TEXT NOT NULL,
            apellido2 TEXT NOT NULL,
            telefono TEXT,
            email TEXT,
            titulacion TEXT,
            numero_colegiado TEXT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expedientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_expediente TEXT NOT NULL,
            tipo_informe TEXT,
            destinatario TEXT,
            cliente TEXT NOT NULL,
            referencia_catastral TEXT,
            direccion TEXT NOT NULL,
            codigo_postal TEXT,
            ciudad TEXT,
            provincia TEXT,
            tipo_inmueble TEXT,
            orientacion_inmueble TEXT,
            anio_construccion TEXT,
            plantas_bajo_rasante TEXT,
            plantas_sobre_baja TEXT,
            uso_inmueble TEXT,
            observaciones_generales TEXT,
            planta_unidad TEXT,
            puerta_unidad TEXT,
            superficie_construida TEXT,
            superficie_util TEXT,
            dormitorios_unidad TEXT,
            banos_unidad TEXT,
            observaciones_bloque TEXT,
            observaciones_unidad TEXT,
            reformado TEXT,
            fecha_reforma TEXT,
            observaciones_reforma TEXT,
            procedimiento_judicial TEXT,
            juzgado TEXT,
            auto_judicial TEXT,
            parte_solicitante TEXT,
            objeto_pericia TEXT,
            alcance_limitaciones TEXT,
            metodologia_pericial TEXT,
            imagen_catastro TEXT,
            owner_user_id INTEGER,
            FOREIGN KEY (owner_user_id) REFERENCES usuarios (id)
        )
        """
    )

    migrar_expedientes_superficies(cur)

    asegurar_columna(cur, "expedientes", "codigo_postal", "TEXT")
    asegurar_columna(cur, "expedientes", "ciudad", "TEXT")
    asegurar_columna(cur, "expedientes", "provincia", "TEXT")
    asegurar_columna(cur, "expedientes", "owner_user_id", "INTEGER")
    asegurar_columna(cur, "expedientes", "superficie_construida", "TEXT")
    asegurar_columna(cur, "expedientes", "superficie_util", "TEXT")
    asegurar_columna(cur, "expedientes", "referencia_catastral", "TEXT")
    asegurar_columna(cur, "expedientes", "imagen_catastro", "TEXT")
    asegurar_columna(cur, "expedientes", "tipo_informe", "TEXT")
    asegurar_columna(cur, "expedientes", "destinatario", "TEXT")
    asegurar_columna(cur, "expedientes", "procedimiento_judicial", "TEXT")
    asegurar_columna(cur, "expedientes", "juzgado", "TEXT")
    asegurar_columna(cur, "expedientes", "auto_judicial", "TEXT")
    asegurar_columna(cur, "expedientes", "parte_solicitante", "TEXT")
    asegurar_columna(cur, "expedientes", "objeto_pericia", "TEXT")
    asegurar_columna(cur, "expedientes", "alcance_limitaciones", "TEXT")
    asegurar_columna(cur, "expedientes", "metodologia_pericial", "TEXT")
    asegurar_columna(cur, "expedientes", "ambito_patologias", "TEXT")
    asegurar_columna(cur, "expedientes", "descripcion_dano", "TEXT")
    asegurar_columna(cur, "expedientes", "causa_probable", "TEXT")
    asegurar_columna(cur, "expedientes", "pruebas_indicios", "TEXT")
    asegurar_columna(cur, "expedientes", "evolucion_preexistencia", "TEXT")
    asegurar_columna(cur, "expedientes", "propuesta_reparacion", "TEXT")
    asegurar_columna(cur, "expedientes", "urgencia_gravedad", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            observaciones_visita TEXT,
            FOREIGN KEY (expediente_id) REFERENCES expedientes (id)
        )
        """
    )
    asegurar_columna(cur, "visitas", "ambito_visita", "TEXT")
    asegurar_columna(cur, "visitas", "nivel_id", "INTEGER")
    asegurar_columna(cur, "visitas", "unidad_id", "INTEGER")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS estancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            tipo_estancia TEXT NOT NULL,
            ventilacion TEXT,
            planta TEXT,
            acabado_pavimento TEXT,
            acabado_paramento TEXT,
            acabado_techo TEXT,
            observaciones TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )
    asegurar_columna(cur, "estancias", "ventilacion", "TEXT")
    asegurar_columna(cur, "estancias", "acabado_pavimento", "TEXT")
    asegurar_columna(cur, "estancias", "acabado_paramento", "TEXT")
    asegurar_columna(cur, "estancias", "acabado_techo", "TEXT")
    asegurar_columna(cur, "estancias", "unidad_id", "INTEGER")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registros_patologias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            estancia_id INTEGER NOT NULL,
            elemento TEXT NOT NULL,
            patologia TEXT NOT NULL,
            observaciones TEXT,
            foto TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id),
            FOREIGN KEY (estancia_id) REFERENCES estancias (id)
        )
        """
    )
    asegurar_columna(cur, "registros_patologias", "localizacion_dano", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registros_patologias_exteriores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            zona_exterior TEXT,
            elemento_exterior TEXT,
            localizacion_dano_exterior TEXT,
            patologia TEXT,
            observaciones TEXT,
            foto TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inspeccion_general_visita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            puerta_entrada TEXT,
            vestibulo TEXT,
            ventilacion_cruzada TEXT,
            ventilacion_general_inmueble TEXT,
            iluminacion_natural_general TEXT,
            orientacion_general TEXT,
            reformado_cambio_uso TEXT,
            estructura_vertical TEXT,
            estructura_horizontal TEXT,
            forjados_voladizos TEXT,
            cubiertas TEXT,
            soleras_losas TEXT,
            instalacion_electrica_general TEXT,
            agua_acs TEXT,
            calefaccion TEXT,
            climatizacion TEXT,
            carpinterias_generales TEXT,
            persianas_generales TEXT,
            barandillas_generales TEXT,
            vierteaguas_generales TEXT,
            observaciones_generales_inspeccion TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inspeccion_estancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            estancia_id INTEGER NOT NULL,
            puerta TEXT,
            revestimiento TEXT,
            iluminacion TEXT,
            mobiliario TEXT,
            mecanismos_electricos TEXT,
            humedades TEXT,
            techo TEXT,
            pavimento TEXT,
            banera_ducha TEXT,
            mampara TEXT,
            lavabo TEXT,
            inodoro TEXT,
            bide TEXT,
            espejo TEXT,
            ventilacion_forzada TEXT,
            condensacion TEXT,
            griferia TEXT,
            sifones TEXT,
            desagues TEXT,
            llaves_paso TEXT,
            extractor TEXT,
            encimera TEXT,
            zona_coccion TEXT,
            frigorifico TEXT,
            horno TEXT,
            fregadero TEXT,
            conexion_lavavajillas TEXT,
            persiana TEXT,
            cajon_persiana TEXT,
            carpinteria_estancia TEXT,
            cierre_manivela TEXT,
            tomas_corriente TEXT,
            observaciones_estancia_inspeccion TEXT,
            UNIQUE (visita_id, estancia_id),
            FOREIGN KEY (visita_id) REFERENCES visitas (id),
            FOREIGN KEY (estancia_id) REFERENCES estancias (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inspeccion_exterior (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            fachadas TEXT,
            cubiertas_exteriores TEXT,
            patios_exteriores TEXT,
            terrazas_balcones TEXT,
            jardines TEXT,
            entorno_inmediato TEXT,
            carpinterias_exteriores TEXT,
            barandillas_exteriores TEXT,
            rejas_exteriores TEXT,
            toldos TEXT,
            tendederos TEXT,
            observaciones_exteriores TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inspeccion_elementos_comunes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            portal_acceso TEXT,
            vestibulo_comun TEXT,
            pasillos_comunes TEXT,
            escaleras TEXT,
            ascensor TEXT,
            patio_luces TEXT,
            patio_ventilacion TEXT,
            fachada_comun TEXT,
            cubierta_comun TEXT,
            cuarto_instalaciones_comunes TEXT,
            observaciones_elementos_comunes TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS habitabilidad_general_visita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            ventilacion_general TEXT,
            iluminacion_natural_general TEXT,
            salubridad_general TEXT,
            seguridad_uso TEXT,
            instalaciones_basicas TEXT,
            accesibilidad_basica TEXT,
            adecuacion_uso_residencial TEXT,
            conclusion_habitabilidad TEXT,
            observaciones_generales_habitabilidad TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS habitabilidad_estancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            estancia_id INTEGER NOT NULL,
            ventilacion TEXT,
            iluminacion TEXT,
            humedades_condensaciones TEXT,
            salubridad TEXT,
            seguridad_uso_estancia TEXT,
            observaciones_estancia_habitabilidad TEXT,
            UNIQUE (visita_id, estancia_id),
            FOREIGN KEY (visita_id) REFERENCES visitas (id),
            FOREIGN KEY (estancia_id) REFERENCES estancias (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS habitabilidad_exterior (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            patio_ventilacion TEXT,
            fachada_humedades TEXT,
            cubierta_filtraciones TEXT,
            observaciones_exterior_habitabilidad TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS valoracion_visita (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL UNIQUE,
            finalidad_valoracion TEXT,
            identificacion_bien TEXT,
            superficie_valoracion TEXT,
            estado_conservacion TEXT,
            antiguedad TEXT,
            calidades TEXT,
            ubicacion_valoracion TEXT,
            criterios_metodo_valoracion TEXT,
            testigos_comparables TEXT,
            valor_resultante TEXT,
            condicionantes_limitaciones_valoracion TEXT,
            observaciones_valoracion TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )
    asegurar_columna(cur, "valoracion_visita", "nombre_solicitante", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "nif_cif_solicitante", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "domicilio_solicitante", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "entidad_financiera", "TEXT")
    asegurar_columna(
        cur, "valoracion_visita", "finalidad_valoracion_detallada", "TEXT"
    )
    asegurar_columna(cur, "valoracion_visita", "documentacion_utilizada", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "datos_registrales", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "superficie_util", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "superficie_terraza", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "superficie_zonas_comunes", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "superficie_total", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "superficie_comprobada", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "situacion_ocupacion", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "situacion_urbanistica", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "servidumbres", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "linderos", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "descripcion_entorno", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "grado_consolidacion", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "antiguedad_entorno", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "rasgos_urbanos", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "nivel_renta", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "uso_predominante", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "equipamientos", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "infraestructuras", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "tipo_edificio", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "numero_portales", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "numero_escaleras", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "numero_ascensores", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "vistas", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "uso_residencial", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "estructura", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "cubierta", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "cerramientos", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "aislamiento", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "carpinteria", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "acristalamiento", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "instalaciones", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "estado_inmueble", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "regimen_ocupacion", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "inmueble_arrendado", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "fecha_visita", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "fecha_emision", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "fecha_caducidad", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "observaciones_testigos", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "variables_mercado", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "metodo_homogeneizacion", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "valor_unitario", "TEXT")
    asegurar_columna(cur, "valoracion_visita", "valor_tasacion_final", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comparables_valoracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            direccion_testigo TEXT,
            fuente_testigo TEXT,
            fecha_testigo TEXT,
            precio_oferta TEXT,
            valor_unitario TEXT,
            superficie_construida TEXT,
            superficie_util TEXT,
            tipologia TEXT,
            planta TEXT,
            dormitorios TEXT,
            banos TEXT,
            estado_conservacion TEXT,
            antiguedad TEXT,
            calidad_constructiva TEXT,
            visitado TEXT,
            observaciones TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mapas_patologia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            ambito_mapa TEXT,
            filas INTEGER NOT NULL DEFAULT 4,
            columnas INTEGER NOT NULL DEFAULT 4,
            imagen_base TEXT,
            observaciones TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )
    asegurar_columna(cur, "mapas_patologia", "visita_id", "INTEGER NOT NULL DEFAULT 0")
    asegurar_columna(cur, "mapas_patologia", "titulo", "TEXT")
    asegurar_columna(cur, "mapas_patologia", "descripcion", "TEXT")
    asegurar_columna(cur, "mapas_patologia", "ambito_mapa", "TEXT")
    asegurar_columna(cur, "mapas_patologia", "filas", "INTEGER NOT NULL DEFAULT 4")
    asegurar_columna(cur, "mapas_patologia", "columnas", "INTEGER NOT NULL DEFAULT 4")
    asegurar_columna(cur, "mapas_patologia", "imagen_base", "TEXT")
    asegurar_columna(cur, "mapas_patologia", "observaciones", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS cuadrantes_mapa_patologia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mapa_id INTEGER NOT NULL,
            codigo_cuadrante TEXT NOT NULL,
            descripcion TEXT,
            patologia_detectada TEXT,
            gravedad TEXT,
            foto_detalle TEXT,
            observaciones TEXT,
            FOREIGN KEY (mapa_id) REFERENCES mapas_patologia (id)
        )
        """
    )
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "mapa_id", "INTEGER NOT NULL DEFAULT 0")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "codigo_cuadrante", "TEXT")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "descripcion", "TEXT")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "patologia_detectada", "TEXT")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "patologia_id", "INTEGER")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "gravedad", "TEXT")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "foto_detalle", "TEXT")
    asegurar_columna(cur, "cuadrantes_mapa_patologia", "observaciones", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS niveles_edificio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id INTEGER NOT NULL,
            nombre_nivel TEXT NOT NULL,
            orden_nivel INTEGER,
            tipo_nivel TEXT,
            observaciones TEXT,
            FOREIGN KEY (expediente_id) REFERENCES expedientes (id)
        )
        """
    )
    asegurar_columna(cur, "niveles_edificio", "expediente_id", "INTEGER NOT NULL DEFAULT 0")
    asegurar_columna(cur, "niveles_edificio", "nombre_nivel", "TEXT")
    asegurar_columna(cur, "niveles_edificio", "orden_nivel", "INTEGER")
    asegurar_columna(cur, "niveles_edificio", "tipo_nivel", "TEXT")
    asegurar_columna(cur, "niveles_edificio", "observaciones", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS unidades_expediente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediente_id INTEGER NOT NULL,
            nivel_id INTEGER,
            identificador TEXT NOT NULL,
            tipo_unidad TEXT NOT NULL,
            uso TEXT,
            superficie TEXT,
            referencia_catastral_unidad TEXT,
            es_principal INTEGER NOT NULL DEFAULT 1,
            unidad_principal_id INTEGER,
            tipo_anejo TEXT,
            vinculo_unidad TEXT,
            observaciones TEXT,
            FOREIGN KEY (expediente_id) REFERENCES expedientes (id),
            FOREIGN KEY (nivel_id) REFERENCES niveles_edificio (id),
            FOREIGN KEY (unidad_principal_id) REFERENCES unidades_expediente (id)
        )
        """
    )
    asegurar_columna(cur, "unidades_expediente", "expediente_id", "INTEGER NOT NULL DEFAULT 0")
    asegurar_columna(cur, "unidades_expediente", "nivel_id", "INTEGER")
    asegurar_columna(cur, "unidades_expediente", "identificador", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "tipo_unidad", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "uso", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "superficie", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "referencia_catastral_unidad", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "es_principal", "INTEGER NOT NULL DEFAULT 1")
    asegurar_columna(cur, "unidades_expediente", "unidad_principal_id", "INTEGER")
    asegurar_columna(cur, "unidades_expediente", "tipo_anejo", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "vinculo_unidad", "TEXT")
    asegurar_columna(cur, "unidades_expediente", "observaciones", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS climatologia_visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            resumen TEXT,
            detalle_json TEXT,
            ubicacion TEXT,
            latitud REAL,
            longitud REAL,
            fecha_generacion TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )
    asegurar_columna(cur, "climatologia_visitas", "detalle_json", "TEXT")
    asegurar_columna(cur, "climatologia_visitas", "ubicacion", "TEXT")
    asegurar_columna(cur, "climatologia_visitas", "latitud", "REAL")
    asegurar_columna(cur, "climatologia_visitas", "longitud", "REAL")
    asegurar_columna(cur, "climatologia_visitas", "fecha_generacion", "TEXT")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS biblioteca_patologias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            causa TEXT,
            solucion TEXT
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM biblioteca_patologias")
    count = cur.fetchone()[0]

    if count == 0:
        cur.executemany(
            """
            INSERT INTO biblioteca_patologias (nombre, descripcion, causa, solucion)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "Condensación superficial",
                    "Formación de agua en superficies frías por exceso de humedad ambiental.",
                    "Ventilación insuficiente o presencia de puentes térmicos.",
                    "Mejora de la ventilación interior y del aislamiento térmico.",
                ),
                (
                    "Eflorescencias salinas",
                    "Cristalización de sales solubles en la superficie del paramento.",
                    "Migración de humedad a través del material y evaporación superficial.",
                    "Eliminar la causa de la humedad y limpiar o sanear los paramentos.",
                ),
                (
                    "Fisura estructural",
                    "Abertura lineal en elemento estructural con indicios de movimiento.",
                    "Asentamiento diferencial, deformaciones o sobrecargas.",
                    "Estudio estructural y reparación mediante cosido, refuerzo o recalce según proceda.",
                ),
                (
                    "Fisura no estructural",
                    "Abertura lineal superficial en revestimientos o tabiquería.",
                    "Retracciones, movimientos higrotérmicos o pequeñas deformaciones del soporte.",
                    "Sellado y reparación del revestimiento, previa comprobación de estabilidad.",
                ),
                (
                    "Humedad por capilaridad",
                    "Ascenso de humedad desde el terreno a través de los poros del material.",
                    "Ausencia o fallo de barrera impermeable horizontal.",
                    "Ejecución de barrera química o sistema equivalente y saneado posterior.",
                ),
                (
                    "Humedad por filtración",
                    "Entrada de agua a través de cerramientos o cubiertas.",
                    "Fallo de impermeabilización, juntas, fisuras o encuentros constructivos.",
                    "Reparación del punto de entrada de agua y reposición de acabados afectados.",
                ),
                (
                    "Moho superficial",
                    "Colonización biológica visible en superficies interiores.",
                    "Exceso de humedad, falta de ventilación y condensaciones recurrentes.",
                    "Limpieza específica, corrección de humedad y mejora de ventilación.",
                ),
            ],
        )

    conn.commit()
    conn.close()
