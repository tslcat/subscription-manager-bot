import time
from datetime import datetime
from .db import load_targets, get_push_time
from .utils import format_msg
from .telegram import send_msg

last_sent_day = None


def push_loop():
    global last_sent_day
    while True:
        try:
            now = datetime.now()
            t = get_push_time()
            hour, minute = map(int, t.split(":"))
            today = now.strftime("%Y-%m-%d")

            if (now.hour == hour and
                now.minute == minute and
                last_sent_day != today):

                targets = load_targets()
                msg = "📅 <b>Daily Subscription Report</b>\n\n" + format_msg(targets)
                send_msg(msg)

                last_sent_day = today
                print(f"✅ 已发送每日报告 ({t})")
        except Exception as e:
            print("scheduler error:", e)

        time.sleep(30)