from datetime import datetime


def format_msg(targets: dict) -> str:
    """定时推送使用的简洁消息"""
    if not targets:
        return "📅 当前没有任何目标"

    message = ""
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


def get_formatted_targets(targets: dict) -> str:
    """手动查看时使用的美观格式"""
    if not targets:
        return "📅 当前没有任何目标"

    message = "📅 <b>当前倒计时目标列表</b>:\n\n"
    sorted_targets = sorted(targets.items(), key=lambda x: x[1])

    for name, target_date in sorted_targets:
        days_left = (target_date - datetime.now()).days
        if days_left < 0:
            message += f"<i>{name}: 已结束</i>\n"
        elif days_left == 0:
            message += f"<b>{name}: 今天</b>\n"
        elif days_left <= 9:
            message += f"<b>{name}: {days_left}天 (紧急)</b>\n"
        else:
            message += f"{name}: {days_left}天\n"
    return message