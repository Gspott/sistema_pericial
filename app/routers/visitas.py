from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import get_connection

router = APIRouter()


@router.get("/nueva-visita/{expediente_id}", response_class=HTMLResponse)
def nueva_visita(request: Request, expediente_id: int):
    conn = get_connection()
    cur = conn.cursor()

    expediente = cur.execute(
        """
        SELECT *
        FROM expedientes
        WHERE id = ?
        """,
        (expediente_id,),
    ).fetchone()

    conn.close()

    if not expediente:
        return HTMLResponse("<h1>Expediente no encontrado</h1>", status_code=404)

    return request.app.state.templates.TemplateResponse(
        "nueva_visita.html",
        {"request": request, "expediente": expediente},
    )


@router.post("/guardar-visita/{expediente_id}")
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
        INSERT INTO visitas (expediente_id, fecha, tecnico, observaciones_visita)
        VALUES (?, ?, ?, ?)
        """,
        (expediente_id, fecha, tecnico, observaciones_visita),
    )

    nueva_visita_id = cur.lastrowid

    ultima_visita = cur.execute(
        """
        SELECT id
        FROM visitas
        WHERE expediente_id = ? AND id <> ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (expediente_id, nueva_visita_id),
    ).fetchone()

    if ultima_visita:
        estancias_previas = cur.execute(
            """
            SELECT nombre, tipo_estancia, planta, observaciones
            FROM estancias
            WHERE visita_id = ?
            ORDER BY id ASC
            """,
            (ultima_visita["id"],),
        ).fetchall()

        for estancia in estancias_previas:
            cur.execute(
                """
                INSERT INTO estancias (visita_id, nombre, tipo_estancia, planta, observaciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    nueva_visita_id,
                    estancia["nombre"],
                    estancia["tipo_estancia"],
                    estancia["planta"],
                    estancia["observaciones"],
                ),
            )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{nueva_visita_id}",
        status_code=303,
    )
