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

            # 获取用户设置的推送时间（默认 09:00）
            t = get_push_time()
            hour, minute = map(int, t.split(":"))

            today = now.strftime("%Y-%m-%d")

            # 到点推送目标列表
            if (
                now.hour == hour and
                now.minute == minute and
                last_sent_day != today
            ):
                # 加载目标数据
                targets = load_targets()

                # 格式化消息
                msg = "📅 <b>Daily Subscription Report</b>\n\n"
                msg += format_msg(targets)

                # 发送消息
                send_msg(msg)

                # 更新已发送日期
                last_sent_day = today

                print(f"✅ Sent daily report at {t}")

        except Exception as e:
            print("scheduler error:", e)

        time.sleep(30)  # 每30秒检查一次