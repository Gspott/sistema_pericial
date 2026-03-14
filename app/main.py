from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, TEMPLATES_DIR, UPLOAD_DIR, ensure_directories
from app.database import init_db
from app.routers import estancias, expedientes, patologias, visitas

app = FastAPI(title="Sistema Pericial")

ensure_directories()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.state.templates = templates

init_db()

app.include_router(expedientes.router)
app.include_router(visitas.router)
app.include_router(estancias.router)
app.include_router(patologias.router)


@app.get("/ping")
def ping():
    return {"mensaje": "Servidor funcionando"}
