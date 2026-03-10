import os
import shutil
from uuid import uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import UPLOAD_DIR
from app.database import get_connection
from app.utils.helpers import borrar_foto_si_existe
from app.services.clima import generar_resumen

router = APIRouter()


@router.get("/registrar-patologias/{visita_id}", response_class=HTMLResponse)
def registrar_patologias(request: Request, visita_id: int):

    conn = get_connection()
    cur = conn.cursor()

    visita = cur.execute(
        """
        SELECT v.*, e.numero_expediente, e.direccion
        FROM visitas v
        INNER JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.id = ?
        """,
        (visita_id,),
    ).fetchone()

    estancias = cur.execute(
        """
        SELECT *
        FROM estancias
        WHERE visita_id = ?
        ORDER BY nombre ASC
        """,
        (visita_id,),
    ).fetchall()

    patologias = cur.execute(
        """
        SELECT *
        FROM biblioteca_patologias
        ORDER BY nombre ASC
        """
    ).fetchall()

    registros = cur.execute(
        """
        SELECT rp.id, rp.elemento, rp.patologia, rp.observaciones, rp.foto,
               es.nombre AS estancia_nombre, rp.estancia_id
        FROM registros_patologias rp
        INNER JOIN estancias es ON rp.estancia_id = es.id
        WHERE rp.visita_id = ?
        ORDER BY rp.id DESC
        """,
        (visita_id,),
    ).fetchall()

    clima = cur.execute(
        """
        SELECT *
        FROM climatologia_visitas
        WHERE visita_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (visita_id,),
    ).fetchone()

    conn.close()

    if not visita:
        return HTMLResponse("<h1>Visita no encontrada</h1>", status_code=404)

    return request.app.state.templates.TemplateResponse(
        "registrar_patologias.html",
        {
            "request": request,
            "visita": visita,
            "estancias": estancias,
            "patologias": patologias,
            "registros": registros,
            "clima": clima,
        },
    )


@router.post("/guardar-registro")
def guardar_registro(
    visita_id: int = Form(...),
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    foto: UploadFile | None = File(None),
):

    nombre_foto = None

    if foto and foto.filename:

        extension = os.path.splitext(foto.filename)[1]
        nombre_foto = f"{uuid4().hex}{extension}"
        ruta_destino = os.path.join(UPLOAD_DIR, nombre_foto)

        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO registros_patologias (
            visita_id, estancia_id, elemento, patologia, observaciones, foto
        )
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


@router.get("/editar-registro/{registro_id}", response_class=HTMLResponse)
def editar_registro(request: Request, registro_id: int):

    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        """
        SELECT *
        FROM registros_patologias
        WHERE id = ?
        """,
        (registro_id,),
    ).fetchone()

    if not registro:
        conn.close()
        return HTMLResponse("<h1>Registro no encontrado</h1>", status_code=404)

    estancias = cur.execute(
        """
        SELECT *
        FROM estancias
        WHERE visita_id = ?
        ORDER BY nombre ASC
        """,
        (registro["visita_id"],),
    ).fetchall()

    patologias = cur.execute(
        """
        SELECT *
        FROM biblioteca_patologias
        ORDER BY nombre ASC
        """
    ).fetchall()

    conn.close()

    return request.app.state.templates.TemplateResponse(
        "editar_registro.html",
        {
            "request": request,
            "registro": registro,
            "estancias": estancias,
            "patologias": patologias,
        },
    )


@router.post("/actualizar-registro/{registro_id}")
def actualizar_registro(
    registro_id: int,
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    foto: UploadFile | None = File(None),
    eliminar_foto_actual: str = Form("no"),
):

    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        """
        SELECT *
        FROM registros_patologias
        WHERE id = ?
        """,
        (registro_id,),
    ).fetchone()

    if not registro:
        conn.close()
        return HTMLResponse("<h1>Registro no encontrado</h1>", status_code=404)

    visita_id = registro["visita_id"]
    nombre_foto = registro["foto"]

    if eliminar_foto_actual == "si" and nombre_foto:
        borrar_foto_si_existe(nombre_foto)
        nombre_foto = None

    if foto and foto.filename:

        if nombre_foto:
            borrar_foto_si_existe(nombre_foto)

        extension = os.path.splitext(foto.filename)[1]
        nombre_foto = f"{uuid4().hex}{extension}"

        ruta_destino = os.path.join(UPLOAD_DIR, nombre_foto)

        with open(ruta_destino, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)

    cur.execute(
        """
        UPDATE registros_patologias
        SET estancia_id = ?, elemento = ?, patologia = ?, observaciones = ?, foto = ?
        WHERE id = ?
        """,
        (estancia_id, elemento, patologia, observaciones, nombre_foto, registro_id),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@router.post("/borrar-registro/{registro_id}")
def borrar_registro(registro_id: int):

    conn = get_connection()
    cur = conn.cursor()

    registro = cur.execute(
        """
        SELECT visita_id, foto
        FROM registros_patologias
        WHERE id = ?
        """,
        (registro_id,),
    ).fetchone()

    if not registro:
        conn.close()
        return HTMLResponse("<h1>Registro no encontrado</h1>", status_code=404)

    visita_id = registro["visita_id"]

    borrar_foto_si_existe(registro["foto"])

    cur.execute(
        "DELETE FROM registros_patologias WHERE id = ?",
        (registro_id,),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )


@router.post("/anadir-climatologia/{visita_id}")
def anadir_climatologia(visita_id: int):

    conn = get_connection()
    cur = conn.cursor()

    direccion = cur.execute(
        """
        SELECT e.direccion
        FROM visitas v
        INNER JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.id = ?
        """,
        (visita_id,),
    ).fetchone()

    resumen = generar_resumen(direccion["direccion"])

    cur.execute(
        """
        INSERT INTO climatologia_visitas (visita_id, resumen)
        VALUES (?, ?)
        """,
        (visita_id, resumen),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{visita_id}",
        status_code=303,
    )
