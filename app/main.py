import os
import sqlite3
import shutil
from uuid import uuid4

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

DB_PATH = "pericial.db"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def borrar_foto_si_existe(nombre_foto):
    if nombre_foto:
        ruta = os.path.join(UPLOAD_DIR, nombre_foto)
        if os.path.exists(ruta):
            os.remove(ruta)


def get_table_columns(table_name: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        rows = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}
    finally:
        conn.close()


def ensure_climatologia_table():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS climatologia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visita_id INTEGER NOT NULL,
                resumen TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


# -------------------------------------------------------
# PWA / ARCHIVOS MÓVIL
# -------------------------------------------------------


@app.get("/manifest.json")
def manifest():
    return FileResponse(
        "static/manifest.json",
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        "static/sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


# -------------------------------------------------------
# INICIO
# -------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/ping")
def ping():
    return {"mensaje": "Servidor funcionando"}


# -------------------------------------------------------
# EXPEDIENTES
# -------------------------------------------------------


@app.get("/expedientes", response_class=HTMLResponse)
def listar_expedientes(request: Request):
    conn = get_connection()
    cur = conn.cursor()

    expedientes = cur.execute("SELECT * FROM expedientes ORDER BY id DESC").fetchall()

    conn.close()

    return templates.TemplateResponse(
        "expedientes.html",
        {"request": request, "expedientes": expedientes},
    )


@app.get("/nuevo-expediente", response_class=HTMLResponse)
def nuevo_expediente(request: Request):
    return templates.TemplateResponse("nuevo_expediente.html", {"request": request})


@app.post("/guardar-expediente")
def guardar_expediente(
    numero_expediente: str = Form(...),
    cliente: str = Form(...),
    direccion: str = Form(...),
    tipo_inmueble: str = Form(""),
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente,
            cliente,
            direccion,
            tipo_inmueble
        )
        VALUES (?, ?, ?, ?)
        """,
        (numero_expediente, cliente, direccion, tipo_inmueble),
    )

    expediente_id = cur.lastrowid

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@app.get("/detalle-expediente/{expediente_id}", response_class=HTMLResponse)
def detalle_expediente(request: Request, expediente_id: int):
    conn = get_connection()
    cur = conn.cursor()

    expediente = cur.execute(
        "SELECT * FROM expedientes WHERE id=?",
        (expediente_id,),
    ).fetchone()

    visitas = cur.execute(
        """
        SELECT v.*,
               (
                   SELECT COUNT(*)
                   FROM estancias e
                   WHERE e.visita_id = v.id
               ) AS total_estancias,
               (
                   SELECT COUNT(*)
                   FROM registros_patologias rp
                   WHERE rp.visita_id = v.id
               ) AS total_patologias
        FROM visitas v
        WHERE v.expediente_id=?
        ORDER BY v.id DESC
        """,
        (expediente_id,),
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "detalle_expediente.html",
        {
            "request": request,
            "expediente": expediente,
            "visitas": visitas,
        },
    )


@app.get("/editar-expediente/{expediente_id}", response_class=HTMLResponse)
def editar_expediente(request: Request, expediente_id: int):
    conn = get_connection()
    cur = conn.cursor()

    expediente = cur.execute(
        "SELECT * FROM expedientes WHERE id=?",
        (expediente_id,),
    ).fetchone()

    conn.close()

    return templates.TemplateResponse(
        "editar_expediente.html",
        {
            "request": request,
            "expediente": expediente,
        },
    )


@app.post("/actualizar-expediente/{expediente_id}")
def actualizar_expediente(
    expediente_id: int,
    numero_expediente: str = Form(...),
    cliente: str = Form(...),
    direccion: str = Form(...),
    tipo_inmueble: str = Form(""),
    orientacion_inmueble: str = Form(""),
    anio_construccion: str = Form(""),
    plantas_bajo_rasante: str = Form("0"),
    plantas_sobre_baja: str = Form("0"),
    uso_inmueble: str = Form(""),
    superficie: str = Form(""),
    observaciones_generales: str = Form(""),
    planta_unidad: str = Form(""),
    puerta_unidad: str = Form(""),
    superficie_unidad: str = Form(""),
    dormitorios_unidad: str = Form(""),
    banos_unidad: str = Form(""),
    observaciones_bloque: str = Form(""),
    observaciones_unidad: str = Form(""),
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
):
    columnas = get_table_columns("expedientes")

    valores = {
        "numero_expediente": numero_expediente,
        "cliente": cliente,
        "direccion": direccion,
        "tipo_inmueble": tipo_inmueble,
        "orientacion_inmueble": orientacion_inmueble,
        "anio_construccion": anio_construccion,
        "plantas_bajo_rasante": plantas_bajo_rasante,
        "plantas_sobre_baja": plantas_sobre_baja,
        "uso_inmueble": uso_inmueble,
        "superficie": superficie,
        "observaciones_generales": observaciones_generales,
        "planta_unidad": planta_unidad,
        "puerta_unidad": puerta_unidad,
        "superficie_unidad": superficie_unidad,
        "dormitorios_unidad": dormitorios_unidad,
        "banos_unidad": banos_unidad,
        "observaciones_bloque": observaciones_bloque,
        "observaciones_unidad": observaciones_unidad,
        "reformado": reformado,
        "fecha_reforma": fecha_reforma,
        "observaciones_reforma": observaciones_reforma,
    }

    campos_actualizables = [campo for campo in valores.keys() if campo in columnas]

    sets = ", ".join([f"{campo}=?" for campo in campos_actualizables])
    params = [valores[campo] for campo in campos_actualizables] + [expediente_id]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        f"UPDATE expedientes SET {sets} WHERE id=?",
        params,
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


# -------------------------------------------------------
# VISITAS
# -------------------------------------------------------


@app.get("/nueva-visita/{expediente_id}", response_class=HTMLResponse)
def nueva_visita(request: Request, expediente_id: int):
    conn = get_connection()
    cur = conn.cursor()

    expediente = cur.execute(
        "SELECT * FROM expedientes WHERE id=?",
        (expediente_id,),
    ).fetchone()

    conn.close()

    return templates.TemplateResponse(
        "nueva_visita.html",
        {
            "request": request,
            "expediente": expediente,
        },
    )


@app.post("/guardar-visita/{expediente_id}")
def guardar_visita(
    expediente_id: int,
    fecha: str = Form(...),
    tecnico: str = Form(...),
    observaciones_visita: str = Form(""),
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO visitas
        (expediente_id, fecha, tecnico, observaciones_visita)
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, fecha, tecnico, observaciones_visita),
    )

    visita_id = cur.lastrowid

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


# -------------------------------------------------------
# ESTANCIAS
# -------------------------------------------------------


@app.get("/definir-estancias/{visita_id}", response_class=HTMLResponse)
def definir_estancias(request: Request, visita_id: int):
    conn = get_connection()
    cur = conn.cursor()

    visita = cur.execute(
        """
        SELECT v.*, e.numero_expediente, e.direccion
        FROM visitas v
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.id=?
        """,
        (visita_id,),
    ).fetchone()

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
        (visita_id,),
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "definir_estancias.html",
        {
            "request": request,
            "visita": visita,
            "estancias": estancias,
        },
    )


@app.post("/guardar-estancia")
def guardar_estancia(
    visita_id: int = Form(...),
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    planta: str = Form(""),
    observaciones: str = Form(""),
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO estancias
        (visita_id, nombre, tipo_estancia, planta, observaciones)
        VALUES (?, ?, ?, ?, ?)
        """,
        (visita_id, nombre, tipo_estancia, planta, observaciones),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-estancia/{estancia_id}", response_class=HTMLResponse)
def editar_estancia(request: Request, estancia_id: int):
    conn = get_connection()
    cur = conn.cursor()

    estancia = cur.execute(
        "SELECT * FROM estancias WHERE id=?",
        (estancia_id,),
    ).fetchone()

    conn.close()

    return templates.TemplateResponse(
        "editar_estancia.html",
        {
            "request": request,
            "estancia": estancia,
        },
    )


@app.post("/actualizar-estancia/{estancia_id}")
def actualizar_estancia(
    estancia_id: int,
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    planta: str = Form(""),
    observaciones: str = Form(""),
    siguiente: str = Form("estancias"),
):
    conn = get_connection()
    cur = conn.cursor()

    estancia = cur.execute(
        "SELECT visita_id FROM estancias WHERE id=?",
        (estancia_id,),
    ).fetchone()

    visita_id = estancia["visita_id"]

    cur.execute(
        """
        UPDATE estancias
        SET nombre=?, tipo_estancia=?, planta=?, observaciones=?
        WHERE id=?
        """,
        (nombre, tipo_estancia, planta, observaciones, estancia_id),
    )

    conn.commit()
    conn.close()

    if siguiente == "patologias":
        return RedirectResponse(
            url=f"/registrar-patologias/{visita_id}",
            status_code=303,
        )

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@app.post("/borrar-estancia/{estancia_id}")
def borrar_estancia(estancia_id: int):
    conn = get_connection()
    cur = conn.cursor()

    estancia = cur.execute(
        "SELECT visita_id FROM estancias WHERE id=?",
        (estancia_id,),
    ).fetchone()

    visita_id = estancia["visita_id"]

    cur.execute("DELETE FROM estancias WHERE id=?", (estancia_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


# -------------------------------------------------------
# CLIMATOLOGÍA
# -------------------------------------------------------


@app.post("/anadir-climatologia/{visita_id}")
def anadir_climatologia(visita_id: int):
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM climatologia WHERE visita_id=?",
        (visita_id,),
    )

    cur.execute(
        """
        INSERT INTO climatologia (visita_id, resumen)
        VALUES (?, ?)
        """,
        (visita_id, "Climatología pendiente de completar."),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


# -------------------------------------------------------
# PATOLOGÍAS
# -------------------------------------------------------


@app.get("/registrar-patologias/{visita_id}", response_class=HTMLResponse)
def registrar_patologias(request: Request, visita_id: int):
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = cur.execute(
        """
        SELECT v.*, e.numero_expediente, e.direccion
        FROM visitas v
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.id=?
        """,
        (visita_id,),
    ).fetchone()

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
        (visita_id,),
    ).fetchall()

    registros = cur.execute(
        """
        SELECT rp.*, e.nombre AS estancia_nombre
        FROM registros_patologias rp
        LEFT JOIN estancias e ON rp.estancia_id = e.id
        WHERE rp.visita_id=?
        ORDER BY rp.id DESC
        """,
        (visita_id,),
    ).fetchall()

    clima = cur.execute(
        """
        SELECT *
        FROM climatologia
        WHERE visita_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (visita_id,),
    ).fetchone()

    patologias = []
    try:
        patologias = cur.execute(
            "SELECT * FROM patologias_base ORDER BY nombre ASC"
        ).fetchall()
    except sqlite3.OperationalError:
        patologias = []

    conn.close()

    return templates.TemplateResponse(
        "registrar_patologias.html",
        {
            "request": request,
            "visita": visita,
            "estancias": estancias,
            "registros": registros,
            "clima": clima,
            "patologias": patologias,
        },
    )


@app.post("/guardar-registro")
def guardar_registro(
    visita_id: int = Form(...),
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    foto: UploadFile | None = File(None),
):
    conn = get_connection()
    cur = conn.cursor()

    nombre_foto = None

    if foto and foto.filename:
        extension = os.path.splitext(foto.filename)[1].lower()
        nombre_foto = f"{uuid4().hex}{extension}"
        ruta_destino = os.path.join(UPLOAD_DIR, nombre_foto)

        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

    cur.execute(
        """
        INSERT INTO registros_patologias
        (visita_id, estancia_id, elemento, patologia, observaciones, foto)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (visita_id, estancia_id, elemento, patologia, observaciones, nombre_foto),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-registro/{registro_id}", response_class=HTMLResponse)
def editar_registro(request: Request, registro_id: int):
    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        "SELECT * FROM registros_patologias WHERE id=?",
        (registro_id,),
    ).fetchone()

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
        (registro["visita_id"],),
    ).fetchall()

    patologias = []
    try:
        patologias = cur.execute(
            "SELECT * FROM patologias_base ORDER BY nombre ASC"
        ).fetchall()
    except sqlite3.OperationalError:
        patologias = []

    conn.close()

    return templates.TemplateResponse(
        "editar_registro.html",
        {
            "request": request,
            "registro": registro,
            "estancias": estancias,
            "patologias": patologias,
        },
    )


@app.post("/actualizar-registro/{registro_id}")
def actualizar_registro(
    registro_id: int,
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    eliminar_foto_actual: str = Form("no"),
    foto: UploadFile | None = File(None),
):
    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        "SELECT * FROM registros_patologias WHERE id=?",
        (registro_id,),
    ).fetchone()

    visita_id = registro["visita_id"]
    nombre_foto = registro["foto"]

    if eliminar_foto_actual == "si" and nombre_foto:
        borrar_foto_si_existe(nombre_foto)
        nombre_foto = None

    if foto and foto.filename:
        if nombre_foto:
            borrar_foto_si_existe(nombre_foto)

        extension = os.path.splitext(foto.filename)[1].lower()
        nombre_foto = f"{uuid4().hex}{extension}"
        ruta_destino = os.path.join(UPLOAD_DIR, nombre_foto)

        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

    cur.execute(
        """
        UPDATE registros_patologias
        SET estancia_id=?, elemento=?, patologia=?, observaciones=?, foto=?
        WHERE id=?
        """,
        (estancia_id, elemento, patologia, observaciones, nombre_foto, registro_id),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@app.post("/borrar-registro/{registro_id}")
def borrar_registro(registro_id: int):
    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        "SELECT visita_id, foto FROM registros_patologias WHERE id=?",
        (registro_id,),
    ).fetchone()

    if registro["foto"]:
        borrar_foto_si_existe(registro["foto"])

    cur.execute("DELETE FROM registros_patologias WHERE id=?", (registro_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}",
        status_code=303,
    )
