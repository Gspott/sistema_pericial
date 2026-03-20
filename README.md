# Sistema Pericial

Aplicación web para la gestión de expedientes periciales, visitas, estancias, patologías, fotografías e informes.

## Funcionalidades actuales

- Alta, edición y consulta de expedientes
- Registro de visitas
- Definición y edición de estancias
- Registro y edición de patologías
- Subida y visualización de fotos
- Generación y almacenamiento de informes
- Consulta de climatología
- Arranque del servidor y del túnel mediante scripts
- Control básico por Telegram
- Control manual local de FastAPI + Caddy + DuckDNS mediante app Tkinter

## Estructura del proyecto

```text
sistema_pericial/
├── app/
│   ├── routers/
│   ├── services/
│   ├── utils/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── static/
├── templates/
├── data/
├── uploads/
├── informes/
├── fotos/
├── logs/
├── .env.example
├── .gitignore
├── control_app.py
├── start_all.sh
├── stop_all.sh
├── status.sh
├── run_app.sh
├── disable_autostart.sh
├── main.py
├── start_server.sh
├── start_tunnel.sh
└── telegram_listener.py

## Control manual del servidor

- `./disable_autostart.sh` desactiva los `LaunchAgents` antiguos del proyecto para evitar autoarranque al encender el Mac o abrir herramientas como VS Code.
- `./start_all.sh` arranca FastAPI, actualiza DuckDNS, levanta Caddy y mantiene el Mac despierto con `caffeinate`.
- `./stop_all.sh` detiene FastAPI, Caddy y `caffeinate`.
- `./status.sh` devuelve `RUNNING` o `STOPPED`.
- `./run_app.sh` abre la app local `control_app.py`, que también se puede lanzar desde la app de Dock `Servidor Pericial.app`.
- En Apple Silicon, `Servidor Pericial.app` y `run_app.sh` deben ejecutarse en `arm64` nativo; no abras la app con Rosetta si quieres reutilizar la `.venv` arm64 de Python 3.12.
