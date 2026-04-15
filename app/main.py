import time
import threading

from .db import init_db
from .scheduler import push_loop
from .telegram import start_bot

def initialize():
    init_db()
    print("✅ 数据库已初始化")

def start_scheduler():
    thread = threading.Thread(target=push_loop, daemon=True)
    thread.start()
    print("✅ 定时推送任务已启动")

def start_telegram_bot():
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    print("✅ Telegram Bot 已启动（长轮询模式）")

if __name__ == "__main__":
    initialize()
    start_scheduler()
    start_telegram_bot()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 机器人已停止")