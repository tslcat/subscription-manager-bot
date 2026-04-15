import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import format_target_message, send_msg

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
                targets = load_targets()
                msg = "📅 <b>每日目标倒计时报告</b>\n\n"
                msg += format_target_message(targets) if targets else "当前没有任何目标"
                send_msg(msg)
                last_sent_day = today
                print(f"✅ 已发送每日报告（{t}）")
        except Exception as e:
            print("scheduler error:", e)
        time.sleep(30)