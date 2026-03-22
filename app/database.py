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

    cur.execute(
        f"""
        INSERT INTO expedientes_new (
            id,
            numero_expediente,
            cliente,
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
            owner_user_id
        )
        SELECT
            id,
            numero_expediente,
            cliente,
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
            cliente TEXT NOT NULL,
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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS estancias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            tipo_estancia TEXT NOT NULL,
            planta TEXT,
            observaciones TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS climatologia_visitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visita_id INTEGER NOT NULL,
            resumen TEXT,
            FOREIGN KEY (visita_id) REFERENCES visitas (id)
        )
        """
    )

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
