import binascii
import hashlib
import hmac
import json
import logging
import os
import secrets
import shutil
import sqlite3
from urllib.parse import quote_plus
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import (
    APP_HOST,
    APP_PORT,
    BASE_URL,
    DB_PATH,
    INFORMES_DIR,
    SESSION_SECRET_KEY,
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOAD_DIR,
    ensure_directories,
)
from app.database import init_db
from app.services.clima import geocodificar, obtener_climatologia
from app.services.direccion import autocompletar_direccion, sugerir_direcciones
from app.services.informe import generar_informe, limpiar_nombre_archivo
from app.utils.helpers import formatear_plantas

app = FastAPI()

STATIC_PATH = Path(STATIC_DIR)
TEMPLATES_PATH = Path(TEMPLATES_DIR)
UPLOAD_PATH = Path(UPLOAD_DIR)
DB_FILE = Path(DB_PATH)

ensure_directories()
init_db()

app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_PATH)), name="uploads")

templates = Jinja2Templates(directory=str(TEMPLATES_PATH))
app.state.base_url = BASE_URL
app.state.app_host = APP_HOST
app.state.app_port = APP_PORT

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    "/login",
    "/crear-usuario",
    "/logout",
    "/ping",
    "/manifest.json",
    "/sw.js",
    "/favicon.ico",
    "/apple-touch-icon.png",
}
PUBLIC_PREFIXES = ("/static/", "/uploads/")
AUTH_PAGES = {"/login", "/crear-usuario"}
SESSION_COOKIE_NAME = "sistema_pericial_session"
SESSION_COOKIE_SECURE = BASE_URL.startswith("https://")


def get_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def borrar_foto_si_existe(nombre_foto):
    if nombre_foto:
        ruta = UPLOAD_PATH / nombre_foto
        if ruta.exists():
            ruta.unlink()


def require_row(row, detail: str):
    if row is None:
        raise HTTPException(status_code=404, detail=detail)
    return row


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
        columnas = {
            row["name"]
            for row in cur.execute("PRAGMA table_info(climatologia_visitas)").fetchall()
        }
        if "detalle_json" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN detalle_json TEXT")
        if "ubicacion" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN ubicacion TEXT")
        if "latitud" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN latitud REAL")
        if "longitud" not in columnas:
            cur.execute("ALTER TABLE climatologia_visitas ADD COLUMN longitud REAL")
        if "fecha_generacion" not in columnas:
            cur.execute(
                "ALTER TABLE climatologia_visitas ADD COLUMN fecha_generacion TEXT"
            )
        tablas = {
            row["name"]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "climatologia" in tablas:
            cur.execute(
                """
                INSERT INTO climatologia_visitas (visita_id, resumen)
                SELECT c.visita_id, c.resumen
                FROM climatologia c
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM climatologia_visitas cv
                    WHERE cv.visita_id = c.visita_id
                      AND IFNULL(cv.resumen, '') = IFNULL(c.resumen, '')
                )
                """
            )
            cur.execute("DROP TABLE climatologia")
        conn.commit()
    finally:
        conn.close()


def limpiar_texto(valor) -> str:
    return str(valor or "").strip()


def parsear_float(valor):
    try:
        return float(str(valor).strip())
    except (TypeError, ValueError):
        return None


def resumen_diario_a_tarjetas(resumen_diario):
    tarjetas = []
    for dia in resumen_diario or []:
        temperatura = dia.get("temperatura") or {}
        temp_min = temperatura.get("min")
        temp_max = temperatura.get("max")
        temp_media = temperatura.get("media")

        tarjetas.append(
            {
                "fecha": dia.get("fecha", ""),
                "temperatura_texto": (
                    f"{temp_min} °C / {temp_max} °C"
                    if temp_min is not None and temp_max is not None
                    else "-"
                ),
                "temperatura_media_texto": (
                    f"{temp_media} °C" if temp_media is not None else "-"
                ),
                "humedad_texto": (
                    f"{dia.get('humedad_media')} %"
                    if dia.get("humedad_media") is not None
                    else "-"
                ),
                "viento_texto": (
                    f"{dia.get('viento_max_kmh')} km/h"
                    if dia.get("viento_max_kmh") is not None
                    else "-"
                ),
                "precipitacion_texto": (
                    f"{dia.get('precipitacion_total_mm')} mm"
                    if dia.get("precipitacion_total_mm") is not None
                    else "-"
                ),
            }
        )

    return tarjetas


def construir_resumen_climatologia(resumen_diario):
    if not resumen_diario:
        return "No se pudo obtener climatología para esta ubicación."

    temp_min = min(
        (
            dia.get("temperatura", {}).get("min")
            for dia in resumen_diario
            if dia.get("temperatura", {}).get("min") is not None
        ),
        default=None,
    )
    temp_max = max(
        (
            dia.get("temperatura", {}).get("max")
            for dia in resumen_diario
            if dia.get("temperatura", {}).get("max") is not None
        ),
        default=None,
    )
    viento_max = max(
        (
            dia.get("viento_max_kmh")
            for dia in resumen_diario
            if dia.get("viento_max_kmh") is not None
        ),
        default=None,
    )
    precipitacion_total = round(
        sum(dia.get("precipitacion_total_mm") or 0 for dia in resumen_diario),
        2,
    )

    return (
        "Última semana registrada: "
        f"temperaturas entre {temp_min} °C y {temp_max} °C, "
        f"viento hasta {viento_max} km/h "
        f"y precipitación acumulada de {precipitacion_total} mm."
    )


def obtener_climatologia_guardada(cur, visita_id: int):
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

    detalle = []
    if clima and clima["detalle_json"]:
        try:
            payload = json.loads(clima["detalle_json"])
            if isinstance(payload, dict):
                detalle = resumen_diario_a_tarjetas(payload.get("resumen_diario") or [])
            elif isinstance(payload, list):
                detalle = payload
            else:
                detalle = []
        except json.JSONDecodeError:
            detalle = []

    return clima, detalle


def persistir_climatologia(cur, visita_id: int, climatologia: dict):
    cur.execute("DELETE FROM climatologia_visitas WHERE visita_id=?", (visita_id,))
    resumen_diario = climatologia.get("resumen_diario") or []
    resumen = climatologia.get("resumen") or construir_resumen_climatologia(resumen_diario)
    coordenadas = climatologia.get("coordenadas") or {}
    cur.execute(
        """
        INSERT INTO climatologia_visitas (
            visita_id,
            resumen,
            detalle_json,
            ubicacion,
            latitud,
            longitud,
            fecha_generacion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            resumen,
            json.dumps(climatologia, ensure_ascii=False),
            climatologia.get("ubicacion"),
            coordenadas.get("lat"),
            coordenadas.get("lon"),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


async def solicitar_climatologia_open_meteo(
    *,
    latitud,
    longitud,
    municipio: str,
    ubicacion_label: str,
):
    lat = parsear_float(latitud)
    lon = parsear_float(longitud)

    if lat is None or lon is None:
        lat, lon = await geocodificar(municipio)

    climatologia = await obtener_climatologia(lat, lon)
    climatologia["ubicacion"] = limpiar_texto(ubicacion_label) or limpiar_texto(municipio)
    climatologia["resumen"] = construir_resumen_climatologia(
        climatologia.get("resumen_diario") or []
    )
    return climatologia


def crear_visita_si_no_existe(
    cur,
    expediente,
    visita_id,
    fecha: str,
    tecnico: str,
    observaciones_visita: str,
):
    if visita_id:
        return visita_id, False

    cur.execute(
        """
        INSERT INTO visitas
        (expediente_id, fecha, tecnico, observaciones_visita)
        VALUES (?, ?, ?, ?)
        """,
        (
            expediente["id"],
            fecha,
            tecnico,
            observaciones_visita,
        ),
    )
    nueva_visita_id = cur.lastrowid
    copiado = copiar_estancias_visita_anterior(cur, expediente["id"], nueva_visita_id)

    if not copiado:
        crear_estancias_base(
            cur,
            nueva_visita_id,
            expediente["tipo_inmueble"] or "",
            expediente["dormitorios_unidad"],
            expediente["banos_unidad"],
        )

    return nueva_visita_id, True


def propagar_acabados_estancia(
    cur,
    expediente_id: int,
    estancia_id: int,
    acabados_anteriores: dict,
    acabados_nuevos: dict,
):
    for campo, valor_nuevo in acabados_nuevos.items():
        valor_limpio = limpiar_texto(valor_nuevo)
        valor_anterior = limpiar_texto(acabados_anteriores.get(campo))

        if valor_anterior or not valor_limpio:
            continue

        existe_previo = cur.execute(
            f"""
            SELECT 1
            FROM estancias es
            INNER JOIN visitas v ON es.visita_id = v.id
            WHERE v.expediente_id = ?
              AND es.id <> ?
              AND TRIM(IFNULL(es.{campo}, '')) <> ''
            LIMIT 1
            """,
            (expediente_id, estancia_id),
        ).fetchone()

        if existe_previo:
            continue

        cur.execute(
            f"""
            UPDATE estancias
            SET {campo} = ?
            WHERE id IN (
                SELECT es.id
                FROM estancias es
                INNER JOIN visitas v ON es.visita_id = v.id
                WHERE v.expediente_id = ?
                  AND es.id <> ?
                  AND TRIM(IFNULL(es.{campo}, '')) = ''
            )
            """,
            (valor_limpio, expediente_id, estancia_id),
        )


def generar_numero_expediente():
    sufijo_anio = datetime.now().strftime("%y")

    conn = get_connection()
    cur = conn.cursor()
    try:
        row = cur.execute(
            """
            SELECT MAX(CAST(SUBSTR(numero_expediente, 1, 3) AS INTEGER)) AS ultima_secuencia
            FROM expedientes
            WHERE numero_expediente GLOB ?
            """,
            (f"[0-9][0-9][0-9]-{sufijo_anio}",),
        ).fetchone()
    finally:
        conn.close()

    ultima_secuencia = row["ultima_secuencia"] or 0
    return f"{ultima_secuencia + 1:03d}-{sufijo_anio}"


def generar_numero_expediente_desde_cursor(cur):
    sufijo_anio = datetime.now().strftime("%y")
    row = cur.execute(
        """
        SELECT MAX(CAST(SUBSTR(numero_expediente, 1, 3) AS INTEGER)) AS ultima_secuencia
        FROM expedientes
        WHERE numero_expediente GLOB ?
        """,
        (f"[0-9][0-9][0-9]-{sufijo_anio}",),
    ).fetchone()
    ultima_secuencia = row["ultima_secuencia"] or 0
    return f"{ultima_secuencia + 1:03d}-{sufijo_anio}"


def parsear_entero_positivo(valor) -> int:
    try:
        numero = int(str(valor or "").strip())
        return max(numero, 0)
    except (TypeError, ValueError):
        return 0


def crear_estancias_base(cur, visita_id: int, tipo_inmueble: str, dormitorios, banos):
    existentes = cur.execute(
        "SELECT COUNT(*) AS total FROM estancias WHERE visita_id=?",
        (visita_id,),
    ).fetchone()

    if existentes and existentes["total"] > 0:
        return

    estancias_base = [("Salón", "Salón"), ("Cocina", "Cocina")]

    if tipo_inmueble == "Piso":
        estancias_base.append(("Pasillo", "Pasillo"))

    for nombre, tipo_estancia in estancias_base:
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, nombre, tipo_estancia, "", "", "", "", "", ""),
        )

    for i in range(1, parsear_entero_positivo(dormitorios) + 1):
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, f"Dormitorio {i}", "Dormitorio", "", "", "", "", "", ""),
        )

    for i in range(1, parsear_entero_positivo(banos) + 1):
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (visita_id, f"Baño {i}", "Baño", "", "", "", "", "", ""),
        )


def copiar_estancias_visita_anterior(cur, expediente_id: int, nueva_visita_id: int) -> bool:
    existentes = cur.execute(
        "SELECT COUNT(*) AS total FROM estancias WHERE visita_id=?",
        (nueva_visita_id,),
    ).fetchone()

    if existentes and existentes["total"] > 0:
        return False

    ultima_visita = cur.execute(
        """
        SELECT id
        FROM visitas
        WHERE expediente_id = ? AND id <> ?
          AND EXISTS (
              SELECT 1
              FROM estancias
              WHERE visita_id = visitas.id
          )
        ORDER BY id DESC
        LIMIT 1
        """,
        (expediente_id, nueva_visita_id),
    ).fetchone()

    if not ultima_visita:
        return False

    estancias_previas = cur.execute(
        """
        SELECT
            nombre,
            tipo_estancia,
            ventilacion,
            planta,
            acabado_pavimento,
            acabado_paramento,
            acabado_techo,
            observaciones
        FROM estancias
        WHERE visita_id = ?
        ORDER BY id ASC
        """,
        (ultima_visita["id"],),
    ).fetchall()

    if not estancias_previas:
        return False

    for estancia in estancias_previas:
        cur.execute(
            """
            INSERT INTO estancias (
                visita_id,
                nombre,
                tipo_estancia,
                ventilacion,
                planta,
                acabado_pavimento,
                acabado_paramento,
                acabado_techo,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nueva_visita_id,
                estancia["nombre"],
                estancia["tipo_estancia"],
                estancia["ventilacion"],
                estancia["planta"],
                estancia["acabado_pavimento"],
                estancia["acabado_paramento"],
                estancia["acabado_techo"],
                estancia["observaciones"],
            ),
        )

    return True


def eliminar_expediente_completo(cur, expediente_id: int):
    visitas = cur.execute(
        "SELECT id FROM visitas WHERE expediente_id=?",
        (expediente_id,),
    ).fetchall()
    visita_ids = [visita["id"] for visita in visitas]

    if visita_ids:
        placeholders = ",".join(["?"] * len(visita_ids))
        fotos = cur.execute(
            f"""
            SELECT foto
            FROM registros_patologias
            WHERE visita_id IN ({placeholders}) AND foto IS NOT NULL AND foto <> ''
            """,
            visita_ids,
        ).fetchall()

        for foto in fotos:
            borrar_foto_si_existe(foto["foto"])

        cur.execute(
            f"DELETE FROM climatologia_visitas WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM registros_patologias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM estancias WHERE visita_id IN ({placeholders})",
            visita_ids,
        )
        cur.execute(
            f"DELETE FROM visitas WHERE id IN ({placeholders})",
            visita_ids,
        )

    cur.execute("DELETE FROM expedientes WHERE id=?", (expediente_id,))


def get_informe_path(nombre_archivo: str) -> Path:
    nombre_seguro = Path(nombre_archivo).name
    ruta = (Path(INFORMES_DIR) / nombre_seguro).resolve()
    base = Path(INFORMES_DIR).resolve()

    if ruta.parent != base or not ruta.exists():
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return ruta


def get_informe_path_for_expediente(expediente, nombre_archivo: str) -> Path:
    ruta = get_informe_path(nombre_archivo)
    prefijo = limpiar_nombre_archivo(
        f"{expediente['numero_expediente']}_{expediente['cliente']}"
    )
    nombre_esperado = f"informe_{prefijo}_"

    if not ruta.name.startswith(nombre_esperado):
        raise HTTPException(status_code=404, detail="Informe no encontrado")

    return ruta


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2_sha256$100000${binascii.hexlify(salt).decode()}${binascii.hexlify(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = binascii.unhexlify(salt_hex.encode())
        expected = binascii.unhexlify(digest_hex.encode())
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, binascii.Error):
        return False


def get_user_by_id(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        return cur.execute(
            "SELECT * FROM usuarios WHERE id=? AND activo=1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()


def sign_session_value(value: str) -> str:
    return hmac.new(
        SESSION_SECRET_KEY.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_session_user_id(request: Request):
    raw_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw_cookie or ":" not in raw_cookie:
        return None

    user_id_str, signature = raw_cookie.split(":", 1)
    expected = sign_session_value(user_id_str)

    if not hmac.compare_digest(signature, expected):
        return None

    try:
        return int(user_id_str)
    except ValueError:
        return None


def get_current_user_optional(request: Request):
    cached_user = getattr(request.state, "current_user", None)
    if cached_user is not None:
        return cached_user

    user_id = get_session_user_id(request)
    if not user_id:
        return None

    user = get_user_by_id(user_id)
    if user is not None:
        request.state.current_user = user
    return user


def get_current_user(request: Request):
    user = get_current_user_optional(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return user


def render_template(request: Request, template_name: str, context: dict | None = None):
    data = {
        "request": request,
        "current_user": get_current_user_optional(request),
    }
    if context:
        data.update(context)
    return templates.TemplateResponse(template_name, data)


def is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def get_owned_expediente(cur, expediente_id: int, user_id: int):
    return cur.execute(
        "SELECT * FROM expedientes WHERE id=? AND owner_user_id=?",
        (expediente_id, user_id),
    ).fetchone()


def get_owned_visita(cur, visita_id: int, user_id: int):
    return cur.execute(
        """
        SELECT v.*,
               e.numero_expediente,
               e.direccion,
               e.owner_user_id,
               e.tipo_inmueble,
               e.dormitorios_unidad,
               e.banos_unidad
        FROM visitas v
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE v.id=? AND e.owner_user_id=?
        """,
        (visita_id, user_id),
    ).fetchone()


def get_owned_estancia(cur, estancia_id: int, user_id: int):
    return cur.execute(
        """
        SELECT es.*, v.expediente_id
        FROM estancias es
        JOIN visitas v ON es.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE es.id=? AND e.owner_user_id=?
        """,
        (estancia_id, user_id),
    ).fetchone()


def get_owned_registro(cur, registro_id: int, user_id: int):
    return cur.execute(
        """
        SELECT rp.*, v.expediente_id
        FROM registros_patologias rp
        JOIN visitas v ON rp.visita_id = v.id
        JOIN expedientes e ON v.expediente_id = e.id
        WHERE rp.id=? AND e.owner_user_id=?
        """,
        (registro_id, user_id),
    ).fetchone()


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    user_id = get_session_user_id(request)
    user = get_user_by_id(user_id) if user_id else None
    request.state.current_user = user

    if user is None and not is_public_path(path):
        response = RedirectResponse(url="/login", status_code=303)
        if user_id:
            response.delete_cookie(SESSION_COOKIE_NAME)
        return response

    if user is not None and path in AUTH_PAGES:
        return RedirectResponse(url="/", status_code=303)

    return await call_next(request)


# -------------------------------------------------------
# PWA / ARCHIVOS MÓVIL
# -------------------------------------------------------


@app.get("/manifest.json")
def manifest():
    return FileResponse(
        str(STATIC_PATH / "manifest.json"),
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/sw.js")
def service_worker():
    return FileResponse(
        str(STATIC_PATH / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.get("/favicon.ico")
def favicon():
    return FileResponse(
        str(STATIC_PATH / "favicon.png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/apple-touch-icon.png")
def apple_touch_icon():
    return FileResponse(
        str(STATIC_PATH / "icon-192.png"),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# -------------------------------------------------------
# AUTENTICACIÓN
# -------------------------------------------------------


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_template(request, "login.html")


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    conn = get_connection()
    cur = conn.cursor()

    user = cur.execute(
        "SELECT * FROM usuarios WHERE username=? AND activo=1",
        (username.strip(),),
    ).fetchone()

    conn.close()

    if user is None or not verify_password(password, user["password_hash"]):
        return render_template(
            request,
            "login.html",
            {
                "error": "Usuario o contraseña incorrectos.",
                "form_data": {"username": username},
            },
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        f"{user['id']}:{sign_session_value(str(user['id']))}",
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
        path="/",
    )
    return response


@app.get("/crear-usuario", response_class=HTMLResponse)
def crear_usuario_page(request: Request):
    return render_template(request, "crear_usuario.html")


@app.post("/crear-usuario", response_class=HTMLResponse)
def crear_usuario(
    request: Request,
    nombre: str = Form(...),
    apellido1: str = Form(...),
    apellido2: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    titulacion: str = Form(""),
    numero_colegiado: str = Form(""),
    username: str = Form(...),
    password: str = Form(...),
    confirmar_password: str = Form(...),
):
    form_data = {
        "nombre": nombre,
        "apellido1": apellido1,
        "apellido2": apellido2,
        "telefono": telefono,
        "email": email,
        "titulacion": titulacion,
        "numero_colegiado": numero_colegiado,
        "username": username,
    }

    if password != confirmar_password:
        return render_template(
            request,
            "crear_usuario.html",
            {
                "error": "Las contraseñas no coinciden.",
                "form_data": form_data,
            },
        )

    conn = get_connection()
    cur = conn.cursor()

    existing = cur.execute(
        "SELECT id FROM usuarios WHERE username=?",
        (username.strip(),),
    ).fetchone()

    if existing:
        conn.close()
        return render_template(
            request,
            "crear_usuario.html",
            {
                "error": "El usuario ya existe.",
                "form_data": form_data,
            },
        )

    cur.execute(
        """
        INSERT INTO usuarios (
            nombre,
            apellido1,
            apellido2,
            telefono,
            email,
            titulacion,
            numero_colegiado,
            username,
            password_hash,
            activo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            nombre.strip(),
            apellido1.strip(),
            apellido2.strip(),
            telefono.strip(),
            email.strip(),
            titulacion.strip(),
            numero_colegiado.strip(),
            username.strip(),
            hash_password(password),
        ),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(url="/login", status_code=303)


@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/autocompletar-direccion")
async def autocompletar_direccion_endpoint(
    request: Request,
    direccion: str = Query(..., min_length=3),
):
    get_current_user(request)
    try:
        datos = await autocompletar_direccion(direccion)
        return JSONResponse(content=datos or {})
    except Exception:
        return JSONResponse(content={})


@app.get("/buscar-direcciones")
async def buscar_direcciones_endpoint(
    request: Request,
    q: str = Query(..., min_length=3),
):
    get_current_user(request)
    try:
        resultados = await sugerir_direcciones(q)
        return JSONResponse(content=resultados or [])
    except Exception:
        return JSONResponse(content=[])


@app.get("/biblioteca-patologias", response_class=HTMLResponse)
def biblioteca_patologias(request: Request):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()
    conn.close()

    return render_template(
        request,
        "biblioteca_patologias.html",
        {"patologias": patologias},
    )


@app.post("/biblioteca-patologias")
def guardar_patologia_biblioteca(
    request: Request,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    causa: str = Form(""),
    solucion: str = Form(""),
):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO biblioteca_patologias (nombre, descripcion, causa, solucion)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, descripcion, causa, solucion),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url="/biblioteca-patologias", status_code=303)


@app.get("/biblioteca-patologias/{patologia_id}/editar", response_class=HTMLResponse)
def editar_patologia_biblioteca(request: Request, patologia_id: int):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    patologia = cur.execute(
        "SELECT * FROM biblioteca_patologias WHERE id=?",
        (patologia_id,),
    ).fetchone()
    require_row(patologia, "Patología no encontrada")

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()
    conn.close()

    return render_template(
        request,
        "biblioteca_patologias.html",
        {
            "patologias": patologias,
            "patologia_edicion": patologia,
        },
    )


@app.post("/biblioteca-patologias/{patologia_id}/editar")
def actualizar_patologia_biblioteca(
    request: Request,
    patologia_id: int,
    nombre: str = Form(...),
    descripcion: str = Form(""),
    causa: str = Form(""),
    solucion: str = Form(""),
):
    get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    updated = cur.execute(
        """
        UPDATE biblioteca_patologias
        SET nombre=?, descripcion=?, causa=?, solucion=?
        WHERE id=?
        """,
        (nombre, descripcion, causa, solucion, patologia_id),
    )
    if updated.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Patología no encontrada")
    conn.commit()
    conn.close()

    return RedirectResponse(url="/biblioteca-patologias", status_code=303)


# -------------------------------------------------------
# INICIO
# -------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = ""):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    search = q.strip()
    if search:
        expedientes = cur.execute(
            """
            SELECT *
            FROM expedientes
            WHERE owner_user_id=?
              AND (
                  numero_expediente LIKE ?
                  OR direccion LIKE ?
                  OR cliente LIKE ?
              )
            ORDER BY id DESC
            """,
            (
                current_user["id"],
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
            ),
        ).fetchall()
    else:
        expedientes = cur.execute(
            """
            SELECT *
            FROM expedientes
            WHERE owner_user_id=?
            ORDER BY id DESC
            """,
            (current_user["id"],),
        ).fetchall()

    conn.close()

    return render_template(
        request,
        "index.html",
        {
            "expedientes": expedientes,
            "search_query": search,
        },
    )


@app.get("/ping")
def ping():
    return {"mensaje": "Servidor funcionando"}


# -------------------------------------------------------
# EXPEDIENTES
# -------------------------------------------------------


@app.get("/expedientes", response_class=HTMLResponse)
def listar_expedientes(request: Request):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expedientes = cur.execute(
        """
        SELECT *
        FROM expedientes
        WHERE owner_user_id=?
        ORDER BY id DESC
        """,
        (current_user["id"],),
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

    return render_template(
        request,
        "expedientes.html",
        {"expedientes": expedientes_procesados},
    )


@app.get("/nuevo-expediente", response_class=HTMLResponse)
def nuevo_expediente(request: Request):
    return render_template(
        request,
        "nuevo_expediente.html",
        {
            "numero_expediente_sugerido": generar_numero_expediente(),
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
        },
    )


@app.post("/guardar-expediente")
def guardar_expediente(
    request: Request,
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
    observaciones_generales: str = Form(""),
    planta_unidad: str = Form(""),
    puerta_unidad: str = Form(""),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    dormitorios_unidad: str = Form(""),
    banos_unidad: str = Form(""),
    observaciones_bloque: str = Form(""),
    observaciones_unidad: str = Form(""),
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
):
    current_user = get_current_user(request)
    expediente_id = None

    for _ in range(3):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN IMMEDIATE")
            numero_expediente = generar_numero_expediente_desde_cursor(cur)

            existe = cur.execute(
                """
                SELECT id
                FROM expedientes
                WHERE numero_expediente=?
                """,
                (numero_expediente,),
            ).fetchone()

            if existe:
                conn.rollback()
                conn.close()
                continue

            cur.execute(
                """
                INSERT INTO expedientes (
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    current_user["id"],
                ),
            )

            expediente_id = cur.lastrowid
            conn.commit()
            conn.close()
            break
        except sqlite3.IntegrityError:
            conn.rollback()
            conn.close()

    if expediente_id is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo generar un número de expediente único.",
        )

    return RedirectResponse(
        url=f"/detalle-expediente/{expediente_id}",
        status_code=303,
    )


@app.get("/detalle-expediente/{expediente_id}", response_class=HTMLResponse)
def detalle_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

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

    expediente_data = dict(expediente)
    expediente_data["descripcion_plantas"] = formatear_plantas(
        expediente_data.get("plantas_bajo_rasante"),
        expediente_data.get("plantas_sobre_baja"),
    )

    return render_template(
        request,
        "detalle_expediente.html",
        {
            "expediente": expediente_data,
            "visitas": visitas,
        },
    )


@app.get("/editar-expediente/{expediente_id}", response_class=HTMLResponse)
def editar_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    conn.close()

    return render_template(
        request,
        "editar_expediente.html",
        {
            "expediente": expediente,
            "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
        },
    )


@app.post("/actualizar-expediente/{expediente_id}")
def actualizar_expediente(
    request: Request,
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
    observaciones_generales: str = Form(""),
    planta_unidad: str = Form(""),
    puerta_unidad: str = Form(""),
    superficie_construida: str = Form(""),
    superficie_util: str = Form(""),
    dormitorios_unidad: str = Form(""),
    banos_unidad: str = Form(""),
    observaciones_bloque: str = Form(""),
    observaciones_unidad: str = Form(""),
    reformado: str = Form("No"),
    fecha_reforma: str = Form(""),
    observaciones_reforma: str = Form(""),
):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()

    expediente_existente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente_existente, "Expediente no encontrado")

    duplicado = cur.execute(
        """
        SELECT id
        FROM expedientes
        WHERE numero_expediente=? AND id<>?
        LIMIT 1
        """,
        (numero_expediente, expediente_id),
    ).fetchone()

    if duplicado:
        conn.close()
        expediente_form = {
            "id": expediente_id,
            "numero_expediente": numero_expediente,
            "cliente": cliente,
            "direccion": direccion,
            "codigo_postal": codigo_postal,
            "ciudad": ciudad,
            "provincia": provincia,
            "tipo_inmueble": tipo_inmueble,
            "orientacion_inmueble": orientacion_inmueble,
            "anio_construccion": anio_construccion,
            "plantas_bajo_rasante": plantas_bajo_rasante,
            "plantas_sobre_baja": plantas_sobre_baja,
            "uso_inmueble": uso_inmueble,
            "observaciones_generales": observaciones_generales,
            "planta_unidad": planta_unidad,
            "puerta_unidad": puerta_unidad,
            "superficie_construida": superficie_construida,
            "superficie_util": superficie_util,
            "dormitorios_unidad": dormitorios_unidad,
            "banos_unidad": banos_unidad,
            "observaciones_bloque": observaciones_bloque,
            "observaciones_unidad": observaciones_unidad,
            "reformado": reformado,
            "fecha_reforma": fecha_reforma,
            "observaciones_reforma": observaciones_reforma,
        }
        return render_template(
            request,
            "editar_expediente.html",
            {
                "error": "Ya existe otro expediente con ese número.",
                "expediente": expediente_form,
                "anios_disponibles": list(range(datetime.now().year, 1899, -1)),
            },
        )

    columnas = get_table_columns("expedientes")

    valores = {
        "numero_expediente": numero_expediente,
        "cliente": cliente,
        "direccion": direccion,
        "codigo_postal": codigo_postal,
        "ciudad": ciudad,
        "provincia": provincia,
        "tipo_inmueble": tipo_inmueble,
        "orientacion_inmueble": orientacion_inmueble,
        "anio_construccion": anio_construccion,
        "plantas_bajo_rasante": plantas_bajo_rasante,
        "plantas_sobre_baja": plantas_sobre_baja,
        "uso_inmueble": uso_inmueble,
        "observaciones_generales": observaciones_generales,
        "planta_unidad": planta_unidad,
        "puerta_unidad": puerta_unidad,
        "superficie_construida": superficie_construida,
        "superficie_util": superficie_util,
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
    params = [valores[campo] for campo in campos_actualizables] + [
        expediente_id,
        current_user["id"],
    ]

    updated = cur.execute(
        f"UPDATE expedientes SET {sets} WHERE id=? AND owner_user_id=?",
        params,
    )

    if updated.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

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
def nueva_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Query(None),
    clima_error: str = Query(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    visita = None
    clima = None
    clima_detalle = []
    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        clima, clima_detalle = obtener_climatologia_guardada(cur, visita_id)

    conn.close()

    visita_form = {
        "id": visita["id"] if visita else "",
        "fecha": (visita["fecha"] if visita else datetime.now().strftime("%Y-%m-%d")),
        "tecnico": (
            visita["tecnico"]
            if visita
            else f"{current_user['nombre']} {current_user['apellido1']}".strip()
            or current_user["username"]
        ),
        "observaciones_visita": visita["observaciones_visita"] if visita else "",
    }

    return render_template(
        request,
        "nueva_visita.html",
        {
            "expediente": expediente,
            "visita": visita,
            "visita_form": visita_form,
            "clima": clima,
            "clima_detalle": clima_detalle,
            "clima_error": clima_error,
        },
    )


@app.post("/guardar-visita/{expediente_id}")
def guardar_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Form(None),
    fecha: str = Form(...),
    tecnico: str = Form(...),
    observaciones_visita: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_limpia = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_limpio = limpiar_texto(tecnico) or current_user["username"]
    observaciones_limpias = observaciones_visita or ""

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?
            WHERE id=?
            """,
            (fecha_limpia, tecnico_limpio, observaciones_limpias, visita_id),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_limpia,
            tecnico_limpio,
            observaciones_limpias,
        )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-visita/{visita_id}", response_class=HTMLResponse)
def editar_visita(request: Request, visita_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    conn.close()

    return render_template(
        request,
        "editar_visita.html",
        {"visita": visita},
    )


@app.post("/actualizar-visita/{visita_id}")
def actualizar_visita(
    request: Request,
    visita_id: int,
    fecha: str = Form(...),
    tecnico: str = Form(...),
    observaciones_visita: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    cur.execute(
        """
        UPDATE visitas
        SET fecha=?, tecnico=?, observaciones_visita=?
        WHERE id=?
        """,
        (fecha, tecnico, observaciones_visita, visita_id),
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/detalle-expediente/{visita['expediente_id']}",
        status_code=303,
    )


# -------------------------------------------------------
# ESTANCIAS
# -------------------------------------------------------


@app.get("/definir-estancias/{visita_id}", response_class=HTMLResponse)
def definir_estancias(request: Request, visita_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
        (visita_id,),
    ).fetchall()

    conn.close()

    dormitorios_sugeridos = int(visita["dormitorios_unidad"] or 0) if str(
        visita["dormitorios_unidad"] or ""
    ).isdigit() else 0
    banos_sugeridos = int(visita["banos_unidad"] or 0) if str(
        visita["banos_unidad"] or ""
    ).isdigit() else 0

    return render_template(
        request,
        "definir_estancias.html",
        {
            "visita": visita,
            "estancias": estancias,
            "dormitorios_sugeridos": dormitorios_sugeridos,
            "banos_sugeridos": banos_sugeridos,
        },
    )


@app.post("/generar-estancias-base")
def generar_estancias_base(
    request: Request,
    visita_id: int = Form(...),
    num_dormitorios: int = Form(0),
    num_banos: int = Form(0),
    incluir_salon: str = Form("no"),
    incluir_cocina: str = Form("no"),
    incluir_pasillo: str = Form("no"),
    incluir_terraza: str = Form("no"),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

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
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, "Salón", "Salón", "", "", "", "", "", ""),
            )

        if incluir_cocina == "si":
            cur.execute(
                """
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, "Cocina", "Cocina", "", "", "", "", "", ""),
            )

        if incluir_pasillo == "si":
            cur.execute(
                """
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, "Pasillo", "Pasillo", "", "", "", "", "", ""),
            )

        if incluir_terraza == "si":
            cur.execute(
                """
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, "Terraza", "Terraza", "", "", "", "", "", ""),
            )

        for i in range(1, num_dormitorios + 1):
            cur.execute(
                """
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, f"Dormitorio {i}", "Dormitorio", "", "", "", "", "", ""),
            )

        for i in range(1, num_banos + 1):
            cur.execute(
                """
                INSERT INTO estancias (
                    visita_id,
                    nombre,
                    tipo_estancia,
                    ventilacion,
                    planta,
                    acabado_pavimento,
                    acabado_paramento,
                    acabado_techo,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (visita_id, f"Baño {i}", "Baño", "", "", "", "", "", ""),
            )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@app.post("/guardar-estancia")
def guardar_estancia(
    request: Request,
    visita_id: int = Form(...),
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    ventilacion: str = Form(""),
    planta: str = Form(""),
    acabado_pavimento: str = Form(""),
    acabado_paramento: str = Form(""),
    acabado_techo: str = Form(""),
    observaciones: str = Form(""),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    cur.execute(
        """
        INSERT INTO estancias
        (
            visita_id,
            nombre,
            tipo_estancia,
            ventilacion,
            planta,
            acabado_pavimento,
            acabado_paramento,
            acabado_techo,
            observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            visita_id,
            nombre,
            tipo_estancia,
            limpiar_texto(ventilacion),
            planta,
            limpiar_texto(acabado_pavimento),
            limpiar_texto(acabado_paramento),
            limpiar_texto(acabado_techo),
            observaciones,
        ),
    )
    nueva_estancia_id = cur.lastrowid

    propagar_acabados_estancia(
        cur,
        visita["expediente_id"],
        nueva_estancia_id,
        {
            "acabado_pavimento": "",
            "acabado_paramento": "",
            "acabado_techo": "",
        },
        {
            "acabado_pavimento": acabado_pavimento,
            "acabado_paramento": acabado_paramento,
            "acabado_techo": acabado_techo,
        },
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/definir-estancias/{visita_id}",
        status_code=303,
    )


@app.get("/editar-estancia/{estancia_id}", response_class=HTMLResponse)
def editar_estancia(request: Request, estancia_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")

    conn.close()

    return render_template(
        request,
        "editar_estancia.html",
        {"estancia": estancia},
    )


@app.post("/actualizar-estancia/{estancia_id}")
def actualizar_estancia(
    request: Request,
    estancia_id: int,
    nombre: str = Form(...),
    tipo_estancia: str = Form(...),
    ventilacion: str = Form(""),
    planta: str = Form(""),
    acabado_pavimento: str = Form(""),
    acabado_paramento: str = Form(""),
    acabado_techo: str = Form(""),
    observaciones: str = Form(""),
    siguiente: str = Form("estancias"),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")

    visita_id = estancia["visita_id"]
    acabados_anteriores = {
        "acabado_pavimento": estancia["acabado_pavimento"],
        "acabado_paramento": estancia["acabado_paramento"],
        "acabado_techo": estancia["acabado_techo"],
    }
    acabados_nuevos = {
        "acabado_pavimento": acabado_pavimento,
        "acabado_paramento": acabado_paramento,
        "acabado_techo": acabado_techo,
    }

    cur.execute(
        """
        UPDATE estancias
        SET nombre=?, tipo_estancia=?, ventilacion=?, planta=?,
            acabado_pavimento=?, acabado_paramento=?, acabado_techo=?, observaciones=?
        WHERE id=?
        """,
        (
            nombre,
            tipo_estancia,
            limpiar_texto(ventilacion),
            planta,
            limpiar_texto(acabado_pavimento),
            limpiar_texto(acabado_paramento),
            limpiar_texto(acabado_techo),
            observaciones,
            estancia_id,
        ),
    )

    propagar_acabados_estancia(
        cur,
        estancia["expediente_id"],
        estancia_id,
        acabados_anteriores,
        acabados_nuevos,
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
def borrar_estancia(request: Request, estancia_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    estancia = get_owned_estancia(cur, estancia_id, current_user["id"])
    require_row(estancia, "Estancia no encontrada")

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


@app.post("/registrar-climatologia-visita/{expediente_id}")
async def registrar_climatologia_visita(
    request: Request,
    expediente_id: int,
    visita_id: int | None = Form(None),
    fecha: str = Form(""),
    tecnico: str = Form(""),
    observaciones_visita: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    ubicacion_referencia: str = Form(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_final = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_final = (
        limpiar_texto(tecnico)
        or f"{current_user['nombre']} {current_user['apellido1']}".strip()
        or current_user["username"]
    )

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?
            WHERE id=?
            """,
            (fecha_final, tecnico_final, observaciones_visita, visita_id),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_final,
            tecnico_final,
            observaciones_visita,
        )

    clima_error = ""
    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=latitud,
            longitud=longitud,
            municipio=expediente["direccion"],
            ubicacion_label=limpiar_texto(ubicacion_referencia) or expediente["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        clima_error = "No se pudo obtener la climatología en este momento. La visita sigue guardada y puedes intentarlo de nuevo."

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/nueva-visita/{expediente_id}?visita_id={visita_id}"
            + (
                f"&clima_error={quote_plus(clima_error)}"
                if clima_error
                else ""
            )
        ),
        status_code=303,
    )


@app.post("/anadir-climatologia/{visita_id}")
async def anadir_climatologia(request: Request, visita_id: int):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    clima_error = ""
    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=None,
            longitud=None,
            municipio=visita["direccion"],
            ubicacion_label=visita["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        clima_error = "No se pudo obtener la climatología en este momento. La visita sigue disponible y puedes intentarlo de nuevo."

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=(
            f"/nueva-visita/{visita['expediente_id']}?visita_id={visita_id}"
            + (
                f"&clima_error={quote_plus(clima_error)}"
                if clima_error
                else ""
            )
        ),
        status_code=303,
    )


@app.post("/api/climatologia")
async def api_climatologia(
    request: Request,
    expediente_id: int = Form(...),
    visita_id: int | None = Form(None),
    fecha: str = Form(""),
    tecnico: str = Form(""),
    observaciones_visita: str = Form(""),
    latitud: str = Form(""),
    longitud: str = Form(""),
    municipio: str = Form(""),
    ubicacion_referencia: str = Form(""),
):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    fecha_final = limpiar_texto(fecha) or datetime.now().strftime("%Y-%m-%d")
    tecnico_final = (
        limpiar_texto(tecnico)
        or f"{current_user['nombre']} {current_user['apellido1']}".strip()
        or current_user["username"]
    )
    observaciones_finales = observaciones_visita or ""

    if visita_id:
        visita = get_owned_visita(cur, visita_id, current_user["id"])
        require_row(visita, "Visita no encontrada")
        if visita["expediente_id"] != expediente_id:
            conn.close()
            raise HTTPException(status_code=404, detail="Visita no encontrada")
        cur.execute(
            """
            UPDATE visitas
            SET fecha=?, tecnico=?, observaciones_visita=?
            WHERE id=?
            """,
            (fecha_final, tecnico_final, observaciones_finales, visita_id),
        )
    else:
        visita_id, _ = crear_visita_si_no_existe(
            cur,
            expediente,
            None,
            fecha_final,
            tecnico_final,
            observaciones_finales,
        )

    try:
        climatologia = await solicitar_climatologia_open_meteo(
            latitud=latitud,
            longitud=longitud,
            municipio=municipio or expediente["direccion"],
            ubicacion_label=limpiar_texto(ubicacion_referencia) or municipio or expediente["direccion"],
        )
        persistir_climatologia(cur, visita_id, climatologia)
        conn.commit()
        conn.close()

        return JSONResponse(
            {
                "ok": True,
                "visita_id": visita_id,
                "clima": {
                    "ubicacion": climatologia.get("ubicacion"),
                    "resumen": climatologia.get("resumen"),
                    "resumen_diario": climatologia.get("resumen_diario") or [],
                },
            }
        )
    except Exception as exc:
        logger.error("[ERROR climatología] %s", exc)
        conn.commit()
        conn.close()
        return JSONResponse(
            {
                "ok": False,
                "visita_id": visita_id,
                "clima_error": "No se pudo obtener la climatología. Puedes seguir trabajando y volver a intentarlo.",
            },
            status_code=200,
        )


# -------------------------------------------------------
# PATOLOGÍAS
# -------------------------------------------------------


@app.get("/registrar-patologias/{visita_id}", response_class=HTMLResponse)
def registrar_patologias(request: Request, visita_id: int):
    current_user = get_current_user(request)
    ensure_climatologia_table()

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

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

    clima, clima_detalle = obtener_climatologia_guardada(cur, visita_id)

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()

    conn.close()

    return render_template(
        request,
        "registrar_patologias.html",
        {
            "visita": visita,
            "estancias": estancias,
            "registros": registros,
            "clima": clima,
            "clima_detalle": clima_detalle,
            "patologias": patologias,
        },
    )


@app.post("/guardar-registro")
def guardar_registro(
    request: Request,
    visita_id: int = Form(...),
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    foto: UploadFile | None = File(None),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    visita = get_owned_visita(cur, visita_id, current_user["id"])
    require_row(visita, "Visita no encontrada")

    estancia = cur.execute(
        "SELECT id FROM estancias WHERE id=? AND visita_id=?",
        (estancia_id, visita_id),
    ).fetchone()
    require_row(estancia, "Estancia no encontrada")

    nombre_foto = None

    if foto and foto.filename:
        extension = os.path.splitext(foto.filename)[1].lower()
        nombre_foto = f"{uuid4().hex}{extension}"
        ruta_destino = UPLOAD_PATH / nombre_foto

        with ruta_destino.open("wb") as buffer:
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
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    estancias = cur.execute(
        "SELECT * FROM estancias WHERE visita_id=? ORDER BY id ASC",
        (registro["visita_id"],),
    ).fetchall()

    patologias = cur.execute(
        "SELECT * FROM biblioteca_patologias ORDER BY nombre ASC"
    ).fetchall()

    conn.close()

    return render_template(
        request,
        "editar_registro.html",
        {
            "registro": registro,
            "estancias": estancias,
            "patologias": patologias,
        },
    )


@app.post("/actualizar-registro/{registro_id}")
def actualizar_registro(
    request: Request,
    registro_id: int,
    estancia_id: int = Form(...),
    elemento: str = Form(...),
    patologia: str = Form(...),
    observaciones: str = Form(""),
    eliminar_foto_actual: str = Form("no"),
    foto: UploadFile | None = File(None),
):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    visita_id = registro["visita_id"]
    nombre_foto = registro["foto"]

    estancia = cur.execute(
        "SELECT id FROM estancias WHERE id=? AND visita_id=?",
        (estancia_id, visita_id),
    ).fetchone()
    require_row(estancia, "Estancia no encontrada")

    if eliminar_foto_actual == "si" and nombre_foto:
        borrar_foto_si_existe(nombre_foto)
        nombre_foto = None

    if foto and foto.filename:
        if nombre_foto:
            borrar_foto_si_existe(nombre_foto)

        extension = os.path.splitext(foto.filename)[1].lower()
        nombre_foto = f"{uuid4().hex}{extension}"
        ruta_destino = UPLOAD_PATH / nombre_foto

        with ruta_destino.open("wb") as buffer:
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
def borrar_registro(request: Request, registro_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    registro = get_owned_registro(cur, registro_id, current_user["id"])
    require_row(registro, "Registro no encontrado")

    if registro["foto"]:
        borrar_foto_si_existe(registro["foto"])

    cur.execute("DELETE FROM registros_patologias WHERE id=?", (registro_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/registrar-patologias/{registro['visita_id']}",
        status_code=303,
    )


@app.get("/generar-informe/{expediente_id}")
def generar_informe_endpoint(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")

    ruta_archivo, nombre_archivo = generar_informe(expediente_id)

    return RedirectResponse(
        url=f"/descargar-informe/{expediente_id}/{nombre_archivo}",
        status_code=303,
    )


@app.get("/descargar-informe/{expediente_id}/{nombre_archivo}")
def descargar_informe(request: Request, expediente_id: int, nombre_archivo: str):
    current_user = get_current_user(request)
    conn = get_connection()
    cur = conn.cursor()
    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    conn.close()

    require_row(expediente, "Expediente no encontrado")
    ruta = get_informe_path_for_expediente(expediente, nombre_archivo)

    return FileResponse(
        path=str(ruta),
        filename=ruta.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.post("/borrar-expediente/{expediente_id}")
def borrar_expediente(request: Request, expediente_id: int):
    current_user = get_current_user(request)

    conn = get_connection()
    cur = conn.cursor()

    expediente = get_owned_expediente(cur, expediente_id, current_user["id"])
    require_row(expediente, "Expediente no encontrado")

    eliminar_expediente_completo(cur, expediente_id)

    conn.commit()
    conn.close()

    return RedirectResponse(url="/expedientes", status_code=303)
