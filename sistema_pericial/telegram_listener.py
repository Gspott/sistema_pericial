import time
import subprocess
from pathlib import Path

import requests

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env")

URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
last_update_id = None

BASE_DIR = Path(__file__).resolve().parent
START_TUNNEL_SCRIPT = str(BASE_DIR / "start_tunnel.sh")
START_SERVER_SCRIPT = str(BASE_DIR / "start_server.sh")


def get_updates():
    global last_update_id
    params = {"timeout": 100}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    try:
        r = requests.get(f"{URL}/getUpdates", params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            return []
        return data.get("result", [])
    except Exception as e:
        print(f"Error consultando Telegram: {e}")
        time.sleep(5)
        return []


def send_message(text: str):
    try:
        requests.post(
            f"{URL}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=30,
        )
    except Exception as e:
        print(f"Error enviando mensaje: {e}")


def run_script(script_path: str):
    try:
        subprocess.Popen(["bash", script_path])
        return True
    except Exception as e:
        print(f"Error lanzando script {script_path}: {e}")
        return False


def handle_message(text: str):
    text = (text or "").strip()

    if text == "/abrir":
        ok = run_script(START_TUNNEL_SCRIPT)
        send_message("Creando túnel..." if ok else "No he podido lanzar el túnel.")
    elif text == "/server":
        ok = run_script(START_SERVER_SCRIPT)
        send_message(
            "Arrancando servidor..." if ok else "No he podido arrancar el servidor."
        )
    elif text == "/ping":
        send_message("Bot activo.")
    elif text == "/help":
        send_message("/ping\n/server\n/abrir\n/help")
    else:
        send_message("Comando no reconocido. Usa /help")


def main():
    global last_update_id
    print("Bot Telegram escuchando...")

    while True:
        updates = get_updates()
        for update in updates:
            last_update_id = update["update_id"]

            if "message" not in update:
                continue

            message = update["message"]
            chat_id = str(message["chat"]["id"])

            if chat_id != str(TELEGRAM_CHAT_ID):
                continue

            text = message.get("text", "")
            handle_message(text)

        time.sleep(2)


if __name__ == "__main__":
    main()
