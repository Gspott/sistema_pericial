import os

from app.config import UPLOAD_DIR


def formatear_plantas(plantas_bajo_rasante, plantas_sobre_baja):
    try:
        bajo = int(plantas_bajo_rasante or 0)
    except ValueError:
        bajo = 0

    try:
        sobre = int(plantas_sobre_baja or 0)
    except ValueError:
        sobre = 0

    partes = []

    if bajo == 1:
        partes.append("Sótano")
    elif bajo > 1:
        partes.append(f"{bajo} sótanos")

    if sobre == 0:
        partes.append("PB")
    else:
        partes.append(f"PB+{sobre}")

    return " + ".join(partes)


def borrar_foto_si_existe(nombre_foto):
    if nombre_foto:
        ruta = os.path.join(UPLOAD_DIR, nombre_foto)
        if os.path.exists(ruta):
            os.remove(ruta)
