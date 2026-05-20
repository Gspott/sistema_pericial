# Despliegue

## `.env`

Copia `.env.example` a `.env` en la raíz del proyecto y ajusta, como mínimo:

```env
APP_HOST=0.0.0.0
APP_PORT=8000
BASE_URL=https://sistema-pericial.duckdns.org
DUCKDNS_DOMAIN=sistema-pericial
DUCKDNS_TOKEN=tu_token_duckdns
```

Rutas opcionales que también admite el proyecto:

```env
DB_PATH=data/pericial.db
UPLOAD_DIR=uploads
INFORMES_DIR=informes
FOTOS_DIR=fotos
LOGS_DIR=logs
```

## Correo corporativo

Para enviar propuestas por email, configura el SMTP corporativo en `.env`:

```env
SMTP_HOST=mail.carlosblancoperito.es
SMTP_PORT=465
SMTP_USER=contacto@carlosblancoperito.es
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=contacto@carlosblancoperito.es
SMTP_FROM_NAME=Carlos Blanco
```

Reglas operativas:

- `.env` nunca debe commitearse.
- Usa las credenciales reales del buzon corporativo.
- Reinicia FastAPI despues de cambiar variables SMTP.
- El puerto `465` usa `SMTP_SSL`.
- Otros puertos mantienen `SMTP` + `STARTTLS`.
- La misma configuracion se usa para propuestas y para emails corporativos manuales desde `/emails/nuevo`.
- Si aparece `WRONG_VERSION_NUMBER`, revisa que no se este usando STARTTLS contra el puerto 465.

Prueba manual recomendada ante incidencias:

```python
import smtplib

with smtplib.SMTP_SSL("mail.carlosblancoperito.es", 465, timeout=20) as smtp:
    smtp.login("contacto@carlosblancoperito.es", "PASSWORD")
```

## Arranque local

Desde la raíz del proyecto:

```bash
./start_server.sh
```

El servidor escucha en `0.0.0.0` y expone FastAPI en `APP_PORT`.

Acceso esperado:

- Local Mac: `http://127.0.0.1:8000`
- Red local / iPhone: `http://IP_LOCAL_DEL_MAC:8000`

## DuckDNS

El script disponible es:

```bash
./scripts/update_duckdns.sh
```

`start_server.sh` lo lanza en segundo plano si `DUCKDNS_DOMAIN` y `DUCKDNS_TOKEN` existen. Si DuckDNS falla, FastAPI sigue arrancando.

## Reverse Proxy con Caddy

Hay un ejemplo en `deploy/Caddyfile`.

Flujo recomendado:

1. FastAPI escucha en `127.0.0.1:8000` o `0.0.0.0:8000`.
2. Caddy publica `https://sistema-pericial.duckdns.org`.
3. Caddy hace `reverse_proxy` hacia `127.0.0.1:8000`.

Si Caddy corre como servicio del sistema, asegúrate de exportar `DUCKDNS_DOMAIN=sistema-pericial` para que `{$DUCKDNS_DOMAIN}.duckdns.org` se resuelva en el `Caddyfile`.

## Puertos del router

Si quieres acceso externo directo desde Internet:

- Abre y reenvía `80/tcp` hacia la máquina que ejecuta Caddy.
- Abre y reenvía `443/tcp` hacia la misma máquina.
- Si expones FastAPI sin proxy, tendrías que reenviar `8000/tcp`, pero no es la opción recomendada.

## Acceso desde iPhone

En la misma Wi‑Fi:

1. Arranca el servidor con `./start_server.sh`.
2. Averigua la IP local del Mac.
3. Abre en Safari `http://IP_LOCAL_DEL_MAC:8000`.
4. Para modo app, usa "Añadir a pantalla de inicio".

La PWA usa:

- `/manifest.json`
- `/sw.js`
- `/favicon.ico`
- `/apple-touch-icon.png`
- `/static/icon-192.png`
- `/static/icon-512.png`

## CG-NAT

Si tu operadora usa CG-NAT, el reenvío de puertos del router no será suficiente para acceso externo directo, aunque DuckDNS esté bien configurado.

En ese caso tienes tres opciones:

1. Pedir IP pública a la operadora.
2. Usar un túnel como Cloudflare Tunnel.
3. Publicarlo detrás de una VPS o proxy externo.
