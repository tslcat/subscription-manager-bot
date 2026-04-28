import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import send_daily_report   # 定时推送使用

# 使用 (日期, 小时, 分钟) 作为 key，支持当天多次修改未来时间后继续推送
last_pushed_key = None

def push_loop():
    global last_pushed_key
    while True:
        try:
            now = datetime.now()
            t = get_push_time()
            hour, minute = map(int, t.split(":"))
            today = now.date()

            current_key = (today, hour, minute)

            # 精确到分钟匹配（最可靠的方式）
            # 完全符合你的最终规则：
            # 1. 过去时间（现在10:05设09:00）→ 今天不推送，明天开始
            # 2. 未来时间（现在10:05设10:10）→ 今天10:10会推送
            # 3. 当天改成更晚的10:20 → 10:20还会再次推送
            # 4. 之后每天都会按新时间推送，直到下次修改
            if now.hour == hour and now.minute == minute and current_key != last_pushed_key:
                send_daily_report()
                last_pushed_key = current_key
                print(f"✅ 定时日报已发送 - {t} ({now.strftime('%H:%M:%S')})")
        except Exception as e:
            print(f"scheduler error: {e}")

        time.sleep(15)  # 5秒间隔，极大提高命中精确分钟的概率