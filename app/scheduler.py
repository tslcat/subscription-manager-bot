import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import send_daily_report   # 定时推送使用

last_sent_day = None

def push_loop():
    global last_sent_day
    while True:
        try:
            now = datetime.now()
            t = get_push_time()
            hour, minute = map(int, t.split(":"))
            today = now.strftime("%Y-%m-%d")

            if now.hour == hour and now.minute == minute and last_sent_day != today:
                send_daily_report()
                last_sent_day = today
                print(f"✅ 定时日报已发送 - {t}")
        except Exception as e:
            print(f"scheduler error: {e}")

        time.sleep(30)