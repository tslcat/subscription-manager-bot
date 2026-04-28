import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import send_daily_report   # 定时推送使用

last_pushed_time = None

def push_loop():
    global last_pushed_time
    while True:
        try:
            now = datetime.now()
            t = get_push_time()
            hour, minute = map(int, t.split(":"))
            today = now.date()

            # 计算今天的目标推送时间
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 最终规则：
            # 1. 如果目标时间在当前时间之前（已过去）→ 今天不推送，等待明天
            # 2. 如果目标时间在当前时间之后（未来）→ 允许今天多次推送（每次改成更晚的未来时间都推）
            # 3. 之后每天都会在设定时间推送，直到下次修改
            if target_time > now and target_time != last_pushed_time:
                send_daily_report()
                last_pushed_time = target_time
                print(f"✅ 定时日报已发送 - {t}")
        except Exception as e:
            print(f"scheduler error: {e}")

        time.sleep(15)