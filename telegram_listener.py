import time
import requests
import subprocess

TOKEN = "8699636159:AAEz3jWqiCDnactyICJdLQVwEEd_rEjkWN8"
CHAT_ID = "477674266"

URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None


def get_updates():
    global last_update_id
    params = {"timeout": 100}
    if last_update_id:
        params["offset"] = last_update_id + 1

    r = requests.get(f"{URL}/getUpdates", params=params)
    data = r.json()

    if not data["ok"]:
        return []

    return data["result"]


def send_message(text):
    requests.post(f"{URL}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": text
    })


def handle_message(text):
    if text == "/abrir":
        send_message("🔧 Creando túnel...")
        subprocess.Popen(
            ["/Users/carlosblanco/sistema_pericial/start_tunnel.sh"]
        )


print("Bot Telegram escuchando...")

while True:
    updates = get_updates()

    for update in updates:
        last_update_id = update["update_id"]

        if "message" not in update:
            continue

        message = update["message"]
        chat_id = str(message["chat"]["id"])

        if chat_id != CHAT_ID:
            continue

        text = message.get("text", "")
        handle_message(text)

    time.sleep(2)
