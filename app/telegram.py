import requests
import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_USER_ID = os.getenv('TG_USER_ID')

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_msg(text):
    url = f"{BASE_URL}sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print("❌ 发送失败:", response.text)
    except Exception as e:
        print("❌ 发送异常:", e)