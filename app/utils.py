from datetime import datetime

def format_msg(targets):
    if not targets:
        return "📅 当前没有任何目标"

    message = ""

    # 按照日期排序目标
    sorted_targets = sorted(targets.items(), key=lambda x: x[1])

    for name, target_date in sorted_targets:
        days_left = (target_date - datetime.now()).days
        if days_left < 0:
            message += f"{name}: 已结束\n"
        elif days_left == 0:
            message += f"{name}: <b>今天</b>\n"
        elif days_left <= 3:
            message += f"{name}: <b>{days_left}天 (紧急)</b>\n"
        else:
            message += f"{name}: {days_left}天\n"

    return message