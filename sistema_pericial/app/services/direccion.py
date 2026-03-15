import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _consultar_nominatim(params: dict) -> list[dict[str, Any]]:
    url = f"https://nominatim.openstreetmap.org/search?{urlencode(params)}"
    request = Request(
        url,
        headers={"User-Agent": "sistema_pericial/1.0"},
    )

    with urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


async def autocompletar_direccion(direccion: str) -> dict[str, str]:
    try:
        resultados = _consultar_nominatim(
            {
                "q": direccion,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 1,
                "countrycodes": "es",
            }
        )

        if not resultados:
            return {
                "codigo_postal": "",
                "ciudad": "",
                "provincia": "",
            }

        address = resultados[0].get("address", {})

        ciudad = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or address.get("county")
            or ""
        )
        provincia = address.get("province") or address.get("state") or ""
        codigo_postal = address.get("postcode", "")

        return {
            "codigo_postal": codigo_postal,
            "ciudad": ciudad,
            "provincia": provincia,
        }

    except Exception:
        return {
            "codigo_postal": "",
            "ciudad": "",
            "provincia": "",
        }


async def sugerir_direcciones(texto: str) -> list[dict[str, str]]:
    try:
        if not texto or len(texto.strip()) < 3:
            return []

        resultados = _consultar_nominatim(
            {
                "q": texto.strip(),
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 5,
                "countrycodes": "es",
            }
        )

        sugerencias = []

        for item in resultados:
            address = item.get("address", {})

            ciudad = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
                or ""
            )
            provincia = address.get("province") or address.get("state") or ""
            codigo_postal = address.get("postcode", "")

            sugerencias.append(
                {
                    "direccion": item.get("display_name", ""),
                    "codigo_postal": codigo_postal,
                    "ciudad": ciudad,
                    "provincia": provincia,
                }
            )

        return sugerencias

    except Exception:
        return []
