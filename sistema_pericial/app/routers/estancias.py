from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection
from app.utils.helpers import borrar_foto_si_existe

router = APIRouter()


@router.get("/definir-estancias/{visita_id}", response_class=HTMLResponse)
def definir_estancias(request: Request, visita_id: int):

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
        ORDER BY id ASC
        """,
        (visita_id,),
    ).fetchall()

    conn.close()

    if not visita:
        return HTMLResponse("<h1>Visita no encontrada</h1>", status_code=404)

    return request.app.state.templates.TemplateResponse(
        "definir_estancias.html",
        {
            "request": request,
            "visita": visita,
            "estancias": estancias,
        },
    )


@router.post("/generar-estancias-base")
def generar_estancias_base(
    visita_id: int = Form(...),
    num_dormitorios: int = Form(0),
    num_banos: int = Form(0),
    incluir_salon: str = Form("no"),
    incluir_cocina: str = Form("no"),
    incluir_pasillo: str = Form("no"),
    incluir_terraza: str = Form("no"),
):

    conn = get_connection()
    cur = conn.cursor()

    existentes = cur.execute(
        """
        SELECT COUNT(*) AS total
        FROM estancias
        WHERE visita_id = ?
        """,
        (visita_id,),
    ).fetchone()

    total_existentes = existentes["total"] if existentes else 0

    if total_existentes == 0:
        if incluir_salon == "si":
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, "Salón", "Salón", "", ""),
            )

        if incluir_cocina == "si":
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, "Cocina", "Cocina", "", ""),
            )

        if incluir_pasillo == "si":
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, "Pasillo", "Pasillo", "", ""),
            )

        if incluir_terraza == "si":
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, "Terraza", "Terraza", "", ""),
            )

        for i in range(1, num_dormitorios + 1):
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, f"Dormitorio {i}", "Dormitorio", "", ""),
            )

        for i in range(1, num_banos + 1):
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visita_id, f"Baño {i}", "Baño", "", ""),
            )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@router.post("/guardar-estancia")
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
        INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
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


@router.post("/borrar-estancia/{estancia_id}")
def borrar_estancia(estancia_id: int):

    conn = get_connection()
    cur = conn.cursor()

    estancia = cur.execute(
        """
        SELECT visita_id
        FROM estancias
        WHERE id = ?
        """,
        (estancia_id,),
    ).fetchone()

    if not estancia:
        conn.close()
        return HTMLResponse("<h1>Estancia no encontrada</h1>", status_code=404)

    visita_id = estancia["visita_id"]

    registros = cur.execute(
        """
        SELECT foto
        FROM registros_patologias
        WHERE estancia_id = ?
        """,
        (estancia_id,),
    ).fetchall()

    for registro in registros:
        borrar_foto_si_existe(registro["foto"])

    cur.execute(
        "DELETE FROM registros_patologias WHERE estancia_id = ?",
        (estancia_id,),
    )

    cur.execute(
        "DELETE FROM estancias WHERE id = ?",
        (estancia_id,),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )
