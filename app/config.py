import os

DB_PATH = "/data/subscriptions.db"

BOT_TOKEN = os.getenv("TG_BOT_TOKEN1")
TG_USER_ID = str(os.getenv("TG_USER_ID1"))

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"