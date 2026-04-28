import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import send_daily_report   # 定时推送使用

last_sent_date = None

def push_loop():
    global last_sent_date
    while True:
        try:
            now = datetime.now()
            t = get_push_time()
            hour, minute = map(int, t.split(":"))
            today = now.date()

            # 严格模式：只有在精确的 HH:MM 分钟到达时才推送
            # 如果设定的时间已经过去（比如现在10:05设09:00），今天不会推送
            # 如果设定的时间是未来的（比如现在10:05设10:10），今天10:10会推送
            # 之后每天都会在设定时间推送，直到下次修改
            if now.hour == hour and now.minute == minute and last_sent_date != today:
                send_daily_report()
                last_sent_date = today
                print(f"✅ 定时日报已发送 - {t}")
        except Exception as e:
            print(f"scheduler error: {e}")

        time.sleep(15)