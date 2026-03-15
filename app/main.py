import os
import sqlite3
import shutil
from uuid import uuid4

from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

DB_PATH = "pericial.db"
UPLOAD_DIR = "uploads"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def borrar_foto_si_existe(nombre_foto):
    if nombre_foto:
        ruta = os.path.join(UPLOAD_DIR, nombre_foto)
        if os.path.exists(ruta):
            os.remove(ruta)


# -------------------------------------------------------
# INICIO
# -------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
        SELECT *
        FROM visitas
        WHERE expediente_id=?
        ORDER BY id DESC
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
        "SELECT * FROM estancias WHERE visita_id=?",
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


# -------------------------------------------------------
# ACTUALIZAR ESTANCIA (MEJORADO)
# -------------------------------------------------------


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
# PATOLOGÍAS
# -------------------------------------------------------


@app.get("/registrar-patologias/{visita_id}", response_class=HTMLResponse)
def registrar_patologias(request: Request, visita_id: int):

    conn = get_connection()
    cur = conn.cursor()

    visita = cur.execute(
        "SELECT * FROM visitas WHERE id=?",
        (visita_id,),
    ).fetchone()

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=?",
        (visita_id,),
    ).fetchall()

    registros = cur.execute(
        """
        SELECT *
        FROM registros_patologias
        WHERE visita_id=?
        ORDER BY id DESC
        """,
        (visita_id,),
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        "registrar_patologias.html",
        {
            "request": request,
            "visita": visita,
            "estancias": estancias,
            "registros": registros,
        },
    )


# -------------------------------------------------------
# PING
# -------------------------------------------------------


@app.get("/ping")
def ping():
    return {"mensaje": "Servidor funcionando"}
