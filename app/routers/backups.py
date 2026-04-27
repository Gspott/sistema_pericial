from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from app.services.backups import borrar_backup, crear_backup_zip, listar_backups, obtener_backup

router = APIRouter()


def get_current_user(request: Request):
    current_user = getattr(request.state, "current_user", None)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Sesión no válida")
    return current_user


def render_template(request: Request, template_name: str, context: dict | None = None):
    data = {
        "request": request,
        "current_user": getattr(request.state, "current_user", None),
    }
    if context:
        data.update(context)
    return request.app.state.templates.TemplateResponse(template_name, data)


def format_size(bytes_size: int) -> str:
    value = float(bytes_size or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def validar_nombre_zip(filename: str) -> str:
    if not filename.endswith(".zip") or "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    return filename


@router.get("/backups", response_class=HTMLResponse)
def index_backups(request: Request):
    get_current_user(request)
    return render_template(
        request,
        "backups/index.html",
        {
            "backups": listar_backups(),
            "format_size": format_size,
        },
    )


@router.post("/backups/crear")
def crear_backup(request: Request):
    current_user = get_current_user(request)
    crear_backup_zip(owner_user_id=current_user["id"])
    return RedirectResponse(url="/backups", status_code=303)


@router.get("/backups/descargar/{filename}")
def descargar_backup(request: Request, filename: str):
    get_current_user(request)
    nombre = validar_nombre_zip(filename)
    ruta = obtener_backup(nombre)
    if not ruta:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    return FileResponse(
        path=str(ruta),
        filename=nombre,
        media_type="application/zip",
    )


@router.post("/backups/eliminar/{filename}")
def eliminar_backup(request: Request, filename: str):
    get_current_user(request)
    nombre = validar_nombre_zip(filename)
    borrar_backup(nombre)
    return RedirectResponse(url="/backups", status_code=303)
