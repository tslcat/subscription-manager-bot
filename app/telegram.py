import requests
import time
from datetime import datetime
from .db import load_targets
from .utils import format_msg
import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_USER_ID = os.getenv('TG_USER_ID')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

def send_msg(text, reply_markup=None):
    url = f"{BASE_URL}sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print("❌ 发送失败:", response.text)
    except Exception as e:
        print("❌ 发送异常:", e)

def generate_inline_buttons():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🔄 刷新目标", "callback_data": "show_subscriptions"},
                {"text": "➕ 添加目标", "callback_data": "add_target"},
            ],
            [
                {"text": "⏰ 设置推送时间", "callback_data": "set_time"},
                {"text": "✏️ 修改目标", "callback_data": "edit_target"},
            ]
        ]
    }
    return keyboard

def format_target_message(targets):
    formatted_message = "📅 <b>当前倒计时目标列表</b>:\n\n"
    for name, target_time in targets.items():
        remaining = calculate_time_remaining(target_time)
        if remaining == "已结束":
            formatted_message += f"<i>{name}: 已结束</i>\n"
        elif "紧急" in remaining:
            formatted_message += f"<b>{name}: {remaining}</b>\n"
        elif "今天" in remaining:
            formatted_message += f"<b>{name}: {remaining}</b>\n"
        else:
            formatted_message += f"{name}: {remaining}\n"
    return formatted_message

def calculate_time_remaining(target_time):
    now = datetime.now()
    now_date = datetime(now.year, now.month, now.day)
    target_date = datetime(target_time.year, target_time.month, target_time.day)
    days = (target_date - now_date).days
    if days < 0:
        return "已结束"
    elif days == 0:
        return "<b>今天</b>"
    elif 1 <= days <= 9:
        return f"<b>{days}天 (紧急)</b>"
    else:
        return f"{days}天"

def show_targets():
    targets = load_targets()
    if not targets:
        send_msg("📅 当前没有任何目标", generate_inline_buttons())
        return
    formatted_message = format_target_message(targets)
    send_msg(formatted_message, generate_inline_buttons())

def show_all_functions():
    help_text = """📋 <b>机器人所有功能</b>

🔄 刷新目标 → 显示当前所有倒计时
➕ 添加目标 → /addsub <名称> <日期>
✏️ 修改目标 → /editsub <名称> <新日期>
⏰ 设置推送时间 → 默认每天 08:00

输入 <b>/列出所有</b> 查看此菜单"""
    send_msg(help_text, generate_inline_buttons())

def handle_callback_query(update):
    callback_data = update["callback_query"]["data"]
    if callback_data == "add_target":
        send_msg("请输入：/addsub <目标名称> <目标日期>")
    elif callback_data == "show_subscriptions":
        show_targets()
    elif callback_data == "set_time":
        send_msg("请输入新的推送时间，格式：HH:MM (例如 08:30)")
    elif callback_data == "edit_target":
        send_msg("✏️ 请输入：/editsub <目标名称> <新日期>")

def handle_message(update):
    text = update["message"]["text"].strip()
    if text.startswith("/addsub"):
        parts = text.split()
        if len(parts) != 3:
            send_msg("❌ 格式错误！正确格式：/addsub <名称> <日期>")
        else:
            from .db import add_target
            response = add_target(parts[1], parts[2])
            send_msg("✅ 添加/更新成功" if response else "❌ 添加失败")
    elif text.startswith("/editsub"):
        parts = text.split()
        if len(parts) != 3:
            send_msg("❌ 格式错误！正确格式：/editsub <名称> <新日期>")
        else:
            from .db import add_target
            response = add_target(parts[1], parts[2])
            send_msg(f"✅ 已修改「{parts[1]}」" if response else "❌ 修改失败")
    elif text.startswith("/subs") or text == "/列出所有":
        show_all_functions() if text == "/列出所有" else show_targets()

def poll_updates():
    url = f"{BASE_URL}getUpdates"
    params = {"timeout": 100, "offset": -1}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            for update in response.json().get("result", []):
                if "callback_query" in update:
                    handle_callback_query(update)
                elif "message" in update:
                    handle_message(update)
    except Exception as e:
        print("❌ 拉取更新失败:", e)

def start_bot():
    print("🤖 Telegram Bot 开始运行...")
    while True:
        try:
            poll_updates()
            time.sleep(0.5)
        except Exception as e:
            print(f"Bot 异常: {e}")
            time.sleep(5)