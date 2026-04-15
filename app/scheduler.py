import time
from datetime import datetime
from .db import load_targets, get_push_time
from .telegram import format_target_message, send_msg   # 使用和手动刷新一样的漂亮格式

last_sent_day = None

def push_loop():
    global last_sent_day

    while True:
        try:
            now = datetime.now()

            # 获取用户设置的推送时间（默认 08:00）
            t = get_push_time()
            hour, minute = map(int, t.split(":"))

            today = now.strftime("%Y-%m-%d")

            # 到点推送完整目标列表
            if (
                now.hour == hour and
                now.minute == minute and
                last_sent_day != today
            ):
                # 加载目标数据
                targets = load_targets()

                # 使用和手动“刷新目标”完全一样的漂亮格式
                msg = "📅 <b>每日目标倒计时报告</b>\n\n"
                if targets:
                    msg += format_target_message(targets)
                else:
                    msg += "当前没有任何目标"

                # 发送消息
                send_msg(msg)

                # 更新已发送日期，防止一天发多次
                last_sent_day = today

                print(f"✅ 已发送每日报告（时间：{t}）")

        except Exception as e:
            print("scheduler error:", e)

        time.sleep(30)  # 每30秒检查一次