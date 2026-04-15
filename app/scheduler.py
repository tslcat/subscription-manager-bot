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

            # 获取最新设置的推送时间
            t = get_push_time()
            hour, minute = map(int, t.split(":"))

            today = now.strftime("%Y-%m-%d")

            # 到点推送
            if (
                now.hour == hour and
                now.minute == minute and
                last_sent_day != today
            ):
                targets = load_targets()

                # === 关键修改：和「🔄 刷新目标」显示完全一致 ===
                current_time = get_push_time()
                header = f"📅 <b>当前倒计时目标列表</b>\n⏰ 当前推送时间：<b>{current_time}</b>\n\n"
                
                if targets:
                    msg = header + format_target_message(targets)
                else:
                    msg = header + "当前没有任何目标"

                # 发送消息
                send_msg(msg)

                last_sent_day = today
                print(f"✅ 已发送每日报告（时间：{t}）")

        except Exception as e:
            print("scheduler error:", e)

        time.sleep(30)