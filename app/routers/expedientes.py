from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.database import get_connection
from app.services.direccion import autocompletar_direccion, sugerir_direcciones
from app.utils.helpers import formatear_plantas

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return request.app.state.templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@router.get("/autocompletar-direccion")
async def autocompletar_direccion_endpoint(direccion: str = Query(..., min_length=3)):
    try:
        datos = await autocompletar_direccion(direccion)
        return JSONResponse(content=datos)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo autocompletar la dirección: {str(e)}",
        )


@router.get("/buscar-direcciones")
async def buscar_direcciones_endpoint(q: str = Query(..., min_length=3)):
    try:
        resultados = await sugerir_direcciones(q)
        return JSONResponse(content=resultados)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudieron obtener sugerencias: {str(e)}",
        )


@router.get("/expedientes", response_class=HTMLResponse)
def listar_expedientes(request: Request):
    conn = get_connection()
    cur = conn.cursor()

    expedientes = cur.execute(
        """
        SELECT *
        FROM expedientes
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    expedientes_procesados = []
    for expediente in expedientes:
        item = dict(expediente)
        item["descripcion_plantas"] = formatear_plantas(
            item.get("plantas_bajo_rasante"),
            item.get("plantas_sobre_baja"),
        )
        expedientes_procesados.append(item)

    return request.app.state.templates.TemplateResponse(
        "expedientes.html",
        {"request": request, "expedientes": expedientes_procesados},
    )


@router.get("/nuevo-expediente", response_class=HTMLResponse)
def nuevo_expediente(request: Request):
    return request.app.state.templates.TemplateResponse(
        "nuevo_expediente.html",
        {"request": request},
    )


@router.post("/guardar-expediente")
def guardar_expediente(
    numero_expediente: str = Form(...),
    cliente: str = Form(...),
    direccion: str = Form(...),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
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
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO expedientes (
            numero_expediente, cliente, direccion, codigo_postal, ciudad, provincia,
            tipo_inmueble, orientacion_inmueble, anio_construccion,
            plantas_bajo_rasante, plantas_sobre_baja, uso_inmueble,
            superficie, observaciones_generales, planta_unidad, puerta_unidad,
            superficie_unidad, dormitorios_unidad, banos_unidad,
            observaciones_bloque, observaciones_unidad, reformado,
            fecha_reforma, observaciones_reforma
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
            superficie,
            observaciones_generales,
            planta_unidad,
            puerta_unidad,
            superficie_unidad,
            dormitorios_unidad,
            banos_unidad,
            observaciones_bloque,
            observaciones_unidad,
            reformado,
            fecha_reforma,
            observaciones_reforma,
        ),
    )

    expediente_id = cur.lastrowid
    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@router.get("/detalle-expediente/{expediente_id}", response_class=HTMLResponse)
def detalle_expediente(request: Request, expediente_id: int):
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

    if not expediente:
        conn.close()
        return HTMLResponse("<h1>Expediente no encontrado</h1>", status_code=404)

    visitas_raw = cur.execute(
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
        WHERE v.expediente_id = ?
        ORDER BY v.id DESC
        """,
        (expediente_id,),
    ).fetchall()

    visitas = []

    for visita in visitas_raw:
        visita_dict = dict(visita)

        patologias = cur.execute(
            """
            SELECT rp.id,
                   rp.elemento,
                   rp.patologia,
                   rp.observaciones,
                   rp.foto,
                   rp.estancia_id,
                   e.nombre AS estancia_nombre
            FROM registros_patologias rp
            INNER JOIN estancias e ON rp.estancia_id = e.id
            WHERE rp.visita_id = ?
            ORDER BY e.nombre ASC, rp.id DESC
            """,
            (visita["id"],),
        ).fetchall()

        clima = cur.execute(
            """
            SELECT resumen
            FROM climatologia_visitas
            WHERE visita_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (visita["id"],),
        ).fetchone()

        visita_dict["patologias_detalle"] = [dict(p) for p in patologias]
        visita_dict["climatologia"] = clima["resumen"] if clima else None

        visitas.append(visita_dict)

    conn.close()

    expediente_dict = dict(expediente)
    expediente_dict["descripcion_plantas"] = formatear_plantas(
        expediente_dict.get("plantas_bajo_rasante"),
        expediente_dict.get("plantas_sobre_baja"),
    )

    return request.app.state.templates.TemplateResponse(
        "detalle_expediente.html",
        {
            "request": request,
            "expediente": expediente_dict,
            "visitas": visitas,
        },
    )


@router.get("/editar-expediente/{expediente_id}", response_class=HTMLResponse)
def editar_expediente(request: Request, expediente_id: int):
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
        "editar_expediente.html",
        {"request": request, "expediente": expediente},
    )


@router.post("/actualizar-expediente/{expediente_id}")
def actualizar_expediente(
    expediente_id: int,
    numero_expediente: str = Form(...),
    cliente: str = Form(...),
    direccion: str = Form(...),
    codigo_postal: str = Form(""),
    ciudad: str = Form(""),
    provincia: str = Form(""),
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
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE expedientes
        SET numero_expediente = ?,
            cliente = ?,
            direccion = ?,
            codigo_postal = ?,
            ciudad = ?,
            provincia = ?,
            tipo_inmueble = ?,
            orientacion_inmueble = ?,
            anio_construccion = ?,
            plantas_bajo_rasante = ?,
            plantas_sobre_baja = ?,
            uso_inmueble = ?,
            superficie = ?,
            observaciones_generales = ?,
            planta_unidad = ?,
            puerta_unidad = ?,
            superficie_unidad = ?,
            dormitorios_unidad = ?,
            banos_unidad = ?,
            observaciones_bloque = ?,
            observaciones_unidad = ?,
            reformado = ?,
            fecha_reforma = ?,
            observaciones_reforma = ?
        WHERE id = ?
        """,
        (
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
            superficie,
            observaciones_generales,
            planta_unidad,
            puerta_unidad,
            superficie_unidad,
            dormitorios_unidad,
            banos_unidad,
            observaciones_bloque,
            observaciones_unidad,
            reformado,
            fecha_reforma,
            observaciones_reforma,
            expediente_id,
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )
