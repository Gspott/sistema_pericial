from datetime import datetime, timedelta

import requests


def obtener_coordenadas(direccion):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": direccion,
        "count": 1,
        "language": "es",
        "format": "json",
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    if "results" not in data or not data["results"]:
        return None, None

    lugar = data["results"][0]
    return lugar["latitude"], lugar["longitude"]


def obtener_clima_semana(lat, lon):
    hoy = datetime.today()
    inicio = hoy - timedelta(days=7)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "start_date": inicio.strftime("%Y-%m-%d"),
        "end_date": hoy.strftime("%Y-%m-%d"),
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    if "daily" not in data:
        return None

    return data["daily"]


def generar_resumen(direccion):
    lat, lon = obtener_coordenadas(direccion)

    if lat is None or lon is None:
        return "No se pudo obtener climatología para esta dirección."

    datos = obtener_clima_semana(lat, lon)

    if not datos:
        return "No se pudo obtener climatología para esta dirección."

    tmax = max(datos["temperature_2m_max"])
    tmin = min(datos["temperature_2m_min"])
    lluvia = sum(datos["precipitation_sum"])

    resumen = (
        f"Durante la última semana se han registrado temperaturas máximas "
        f"aproximadas de {tmax} °C y mínimas de {tmin} °C. "
        f"La precipitación acumulada ha sido de aproximadamente "
        f"{round(lluvia, 1)} mm."
    )

    return resumen
