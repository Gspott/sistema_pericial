import json
from collections import defaultdict
from datetime import datetime, timedelta

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalizar_texto(value) -> str:
    return str(value or "").strip()


def _formatear_numero(value, suffix: str = "") -> str:
    if value is None:
        return "-"

    numero = round(float(value), 1)
    if numero.is_integer():
        return f"{int(numero)}{suffix}"
    return f"{numero}{suffix}"


def obtener_coordenadas(direccion):
    direccion_limpia = _normalizar_texto(direccion)
    if not direccion_limpia:
        return None, None

    response = requests.get(
        GEOCODING_URL,
        params={
            "name": direccion_limpia,
            "count": 1,
            "language": "es",
            "format": "json",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if "results" not in data or not data["results"]:
        return None, None

    lugar = data["results"][0]
    return lugar["latitude"], lugar["longitude"]


def obtener_clima_semana(lat, lon):
    latitud = _parse_float(lat)
    longitud = _parse_float(lon)

    if latitud is None or longitud is None:
        return []

    hoy = datetime.now().date()
    inicio = hoy - timedelta(days=6)

    response = requests.get(
        ARCHIVE_URL,
        params={
            "latitude": latitud,
            "longitude": longitud,
            "hourly": "temperature_2m,precipitation,wind_speed_10m",
            "timezone": "auto",
            "start_date": inicio.strftime("%Y-%m-%d"),
            "end_date": hoy.strftime("%Y-%m-%d"),
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    hourly = data.get("hourly") or {}
    fechas = hourly.get("time") or []
    temperaturas = hourly.get("temperature_2m") or []
    precipitaciones = hourly.get("precipitation") or []
    vientos = hourly.get("wind_speed_10m") or []

    if not fechas:
        return []

    acumulado = defaultdict(
        lambda: {
            "fecha": "",
            "temperaturas": [],
            "precipitaciones": [],
            "vientos": [],
        }
    )

    for fecha_hora, temperatura, precipitacion, viento in zip(
        fechas,
        temperaturas,
        precipitaciones,
        vientos,
    ):
        fecha = fecha_hora.split("T", 1)[0]
        item = acumulado[fecha]
        item["fecha"] = fecha

        if temperatura is not None:
            item["temperaturas"].append(float(temperatura))
        if precipitacion is not None:
            item["precipitaciones"].append(float(precipitacion))
        if viento is not None:
            item["vientos"].append(float(viento))

    detalle = []
    for fecha in sorted(acumulado.keys(), reverse=True):
        item = acumulado[fecha]
        temperaturas_dia = item["temperaturas"]
        precipitaciones_dia = item["precipitaciones"]
        vientos_dia = item["vientos"]

        detalle.append(
            {
                "fecha": fecha,
                "temperatura_min": min(temperaturas_dia) if temperaturas_dia else None,
                "temperatura_max": max(temperaturas_dia) if temperaturas_dia else None,
                "viento": max(vientos_dia) if vientos_dia else None,
                "precipitacion": sum(precipitaciones_dia) if precipitaciones_dia else 0.0,
                "temperatura_texto": (
                    f"{_formatear_numero(min(temperaturas_dia), ' °C')} / "
                    f"{_formatear_numero(max(temperaturas_dia), ' °C')}"
                    if temperaturas_dia
                    else "-"
                ),
                "viento_texto": _formatear_numero(
                    max(vientos_dia) if vientos_dia else None,
                    " km/h",
                ),
                "precipitacion_texto": _formatear_numero(
                    sum(precipitaciones_dia) if precipitaciones_dia else 0.0,
                    " mm",
                ),
            }
        )

    return detalle


def construir_resumen(detalle):
    if not detalle:
        return "No se pudo obtener climatología para esta ubicación."

    temperaturas_max = [
        item["temperatura_max"] for item in detalle if item["temperatura_max"] is not None
    ]
    temperaturas_min = [
        item["temperatura_min"] for item in detalle if item["temperatura_min"] is not None
    ]
    precipitacion_total = sum(item["precipitacion"] or 0 for item in detalle)
    viento_max = max((item["viento"] or 0 for item in detalle), default=0)

    return (
        "Última semana registrada: "
        f"temperaturas entre {_formatear_numero(min(temperaturas_min), ' °C')} "
        f"y {_formatear_numero(max(temperaturas_max), ' °C')}, "
        f"viento hasta {_formatear_numero(viento_max, ' km/h')} "
        f"y precipitación acumulada de {_formatear_numero(precipitacion_total, ' mm')}."
    )


def obtener_climatologia(direccion=None, lat=None, lon=None, ubicacion_label=""):
    latitud = _parse_float(lat)
    longitud = _parse_float(lon)
    ubicacion = _normalizar_texto(ubicacion_label) or _normalizar_texto(direccion)

    if latitud is None or longitud is None:
        latitud, longitud = obtener_coordenadas(direccion)

    if latitud is None or longitud is None:
        return {
            "resumen": "No se pudo obtener climatología para esta ubicación.",
            "detalle": [],
            "detalle_json": "[]",
            "ubicacion": ubicacion,
            "latitud": None,
            "longitud": None,
        }

    detalle = obtener_clima_semana(latitud, longitud)
    resumen = construir_resumen(detalle)

    return {
        "resumen": resumen,
        "detalle": detalle,
        "detalle_json": json.dumps(detalle, ensure_ascii=False),
        "ubicacion": ubicacion,
        "latitud": latitud,
        "longitud": longitud,
    }


def generar_resumen(direccion):
    return obtener_climatologia(direccion=direccion)["resumen"]
