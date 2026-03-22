from collections import defaultdict
from datetime import date, timedelta

import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _round_or_none(value, digits: int):
    if value is None:
        return None
    return round(float(value), digits)


async def geocodificar(municipio: str) -> tuple[float, float]:
    municipio_limpio = str(municipio or "").strip()
    if not municipio_limpio:
        raise ValueError("No se indicó un municipio o dirección para geocodificar")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            GEOCODING_URL,
            params={
                "name": municipio_limpio,
                "count": 1,
                "language": "es",
            },
        )
        response.raise_for_status()

    data = response.json()
    resultados = data.get("results") or []
    if not resultados:
        raise ValueError(f"No se encontró el municipio: {municipio_limpio}")

    primer_resultado = resultados[0]
    return float(primer_resultado["latitude"]), float(primer_resultado["longitude"])


def _agrupar_por_dia(hourly: dict) -> list[dict]:
    horas = hourly.get("time") or []
    temperaturas = hourly.get("temperature_2m") or []
    humedades = hourly.get("relative_humidity_2m") or []
    vientos = hourly.get("wind_speed_10m") or []
    precipitaciones = hourly.get("precipitation") or []

    if not (
        horas
        and len(horas) == len(temperaturas) == len(humedades) == len(vientos) == len(precipitaciones)
    ):
        raise ValueError("Respuesta incompleta de Open-Meteo")

    acumulado = defaultdict(
        lambda: {
            "temperaturas": [],
            "humedades": [],
            "vientos": [],
            "precipitaciones": [],
        }
    )

    for timestamp, temperatura, humedad, viento, precipitacion in zip(
        horas,
        temperaturas,
        humedades,
        vientos,
        precipitaciones,
    ):
        fecha = str(timestamp)[:10]
        item = acumulado[fecha]
        item["temperaturas"].append(float(temperatura))
        item["humedades"].append(float(humedad))
        item["vientos"].append(float(viento))
        item["precipitaciones"].append(float(precipitacion))

    resumen = []
    for fecha in sorted(acumulado.keys()):
        item = acumulado[fecha]
        temperaturas_dia = item["temperaturas"]
        humedades_dia = item["humedades"]
        vientos_dia = item["vientos"]
        precipitaciones_dia = item["precipitaciones"]

        resumen.append(
            {
                "fecha": fecha,
                "temperatura": {
                    "min": _round_or_none(min(temperaturas_dia), 1),
                    "max": _round_or_none(max(temperaturas_dia), 1),
                    "media": _round_or_none(
                        sum(temperaturas_dia) / len(temperaturas_dia),
                        1,
                    ),
                },
                "humedad_media": _round_or_none(
                    sum(humedades_dia) / len(humedades_dia),
                    1,
                ),
                "viento_max_kmh": _round_or_none(max(vientos_dia), 1),
                "precipitacion_total_mm": _round_or_none(sum(precipitaciones_dia), 2),
            }
        )

    return resumen


async def obtener_climatologia(lat: float, lon: float) -> dict:
    fecha_hasta = date.today()
    fecha_desde = fecha_hasta - timedelta(days=7)

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                "start_date": fecha_desde.strftime("%Y-%m-%d"),
                "end_date": fecha_hasta.strftime("%Y-%m-%d"),
                "timezone": "Europe/Madrid",
                "wind_speed_unit": "kmh",
            },
        )
        response.raise_for_status()

    data = response.json()
    hourly = data.get("hourly")
    if not isinstance(hourly, dict) or not (hourly.get("time") or []):
        raise ValueError("Respuesta incompleta de Open-Meteo")

    resumen_diario = _agrupar_por_dia(hourly)

    return {
        "coordenadas": {"lat": float(lat), "lon": float(lon)},
        "periodo": {
            "desde": fecha_desde.strftime("%Y-%m-%d"),
            "hasta": fecha_hasta.strftime("%Y-%m-%d"),
        },
        "resumen_diario": resumen_diario,
        "datos_horarios": hourly,
    }
