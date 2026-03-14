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
├── main.py
├── start_server.sh
├── start_tunnel.sh
└── telegram_listener.py
