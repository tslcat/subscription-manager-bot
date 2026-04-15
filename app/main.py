import os
import sys
import time
import threading

# 确保能找到 app 模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.db import init_db
from app.scheduler import push_loop
from app.telegram import poll_updates

def initialize():
    init_db()
    print("✅ 数据库已初始化")

def start_scheduler():
    thread = threading.Thread(target=push_loop)
    thread.daemon = True
    thread.start()
    print("✅ 定时推送任务已启动")

def start_telegram_polling():
    thread = threading.Thread(target=poll_loop)
    thread.daemon = True
    thread.start()
    print("✅ Telegram 消息轮询已启动")

def poll_loop():
    while True:
        poll_updates()
        time.sleep(1)

if __name__ == "__main__":
    initialize()
    start_scheduler()
    start_telegram_polling()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 机器人已停止")