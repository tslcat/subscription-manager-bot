import requests
from datetime import datetime
from app.db import load_targets
from app.utils import format_msg
import os

# Telegram 配置
BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_USER_ID = os.getenv('TG_USER_ID')

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# =========================
# 发送 Telegram 消息
# =========================
def send_msg(text, reply_markup=None):
    url = f"{BASE_URL}sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "HTML",  # 使用 HTML 格式
        "reply_markup": reply_markup  # 添加内联按钮
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print("❌ 发送失败:", response.text)
    except Exception as e:
        print("❌ 发送异常:", e)

# =========================
# 生成按钮
# =========================
def generate_inline_buttons():
    # 创建内联按钮
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "添加目标", "callback_data": "add_target"},
                {"text": "查看订阅", "callback_data": "show_subscriptions"},
            ],
            [
                {"text": "设置推送时间", "callback_data": "set_time"},
                {"text": "清空所有目标", "callback_data": "clear_all"},
            ]
        ]
    }
    return keyboard

# =========================
# 格式化并发送目标列表
# =========================
def show_targets():
    # 获取目标列表
    targets = load_targets()
    if not targets:
        send_msg("📅 当前没有任何目标", generate_inline_buttons())
        return

    # 格式化目标列表
    formatted_message = "📅 <b>当前倒计时目标列表</b>:\n\n"
    formatted_message += format_msg(targets)  # 格式化目标信息

    # 发送消息，并附带按钮
    send_msg(formatted_message, generate_inline_buttons())

# =========================
# 处理按钮点击
# =========================
def handle_callback_query(update):
    query = update["callback_query"]
    callback_data = query["data"]

    if callback_data == "add_target":
        send_msg("请输入目标名称和日期，格式：/addsub <目标名称> <目标日期>")
    elif callback_data == "show_subscriptions":
        show_targets()
    elif callback_data == "set_time":
        send_msg("请输入新的推送时间，格式：HH:MM (例如：09:00)")
    elif callback_data == "clear_all":
        send_msg("确认要清空所有目标吗？")
        # 这里可以添加清空数据库目标的逻辑

# =========================
# 处理用户消息
# =========================
def handle_message(update):
    text = update["message"]["text"]
    if text.startswith("/addsub"):
        parts = text.split()
        if len(parts) != 3:
            send_msg("❌ 请按照正确格式输入：/addsub <目标名称> <目标日期>")
        else:
            name, date_str = parts[1], parts[2]
            # 添加目标到数据库
            response = add_target(name, date_str)
            send_msg(response)
    elif text.startswith("/subs"):
        show_targets()

# =========================
# 获取并解析更新
# =========================
def poll_updates():
    url = f"{BASE_URL}getUpdates"
    params = {"timeout": 100, "offset": -1}

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for update in data["result"]:
                if "callback_query" in update:
                    handle_callback_query(update)
                elif "message" in update:
                    handle_message(update)
    except Exception as e:
        print("❌ 拉取更新失败:", e)