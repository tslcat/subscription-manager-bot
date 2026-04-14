import os
import time
import threading
from app.db import init_db
from app.scheduler import push_loop
from app.telegram import send_msg

# 初始化数据库
def initialize():
    init_db()
    print("✅ 数据库已初始化")

# 启动定时任务
def start_scheduler():
    thread = threading.Thread(target=push_loop)
    thread.daemon = True
    thread.start()
    print("✅ 定时任务已启动")

if __name__ == "__main__":
    initialize()
    start_scheduler()

    # 保持主程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 机器人已停止")