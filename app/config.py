import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件

# ===================== 配置 =====================
DB_PATH = os.getenv("DB_PATH", "/data/subscriptions.db")

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_USER_ID = os.getenv("TG_USER_ID")

if not BOT_TOKEN or not TG_USER_ID:
    raise ValueError("❌ 请在 .env 文件中设置 TG_BOT_TOKEN 和 TG_USER_ID！")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"