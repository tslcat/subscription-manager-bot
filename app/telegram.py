import requests
from datetime import datetime
from .db import load_targets, add_target, delete_target, clear_all_targets, set_push_time
from .utils import get_formatted_targets
from .config import BASE_URL, TG_USER_ID
import time

last_update_id = 0


def send_msg(text: str, reply_markup=None):
    url = f"{BASE_URL}sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("❌ 发送消息失败:", e)


def generate_main_buttons():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🔄 刷新", "callback_data": "show_subscriptions"},
                {"text": "➕ 添加目标", "callback_data": "add_target"},
            ],
            [
                {"text": "🗑 删除目标", "callback_data": "delete_target"},
                {"text": "🧹 清空所有", "callback_data": "clear_all"},
            ],
            [
                {"text": "⏰ 设置推送时间", "callback_data": "set_time"},
            ]
        ]
    }
    return keyboard


def generate_delete_keyboard(targets):
    keyboard = {"inline_keyboard": []}
    for name in targets.keys():
        keyboard["inline_keyboard"].append([
            {"text": f"📌 {name}", "callback_data": f"view:{name}"},
            {"text": "🗑 删除", "callback_data": f"del:{name}"}
        ])
    keyboard["inline_keyboard"].append([
        {"text": "🔙 返回主菜单", "callback_data": "show_subscriptions"}
    ])
    return keyboard


def generate_clear_confirm_keyboard():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ 确认清空", "callback_data": "clear_confirm"},
                {"text": "❌ 取消", "callback_data": "show_subscriptions"},
            ]
        ]
    }
    return keyboard


def show_targets(delete_mode=False):
    targets = load_targets()
    if not targets:
        send_msg("📅 当前没有任何目标", generate_main_buttons())
        return

    if delete_mode:
        msg = "🗑 <b>请选择要删除的目标</b>：\n\n" + get_formatted_targets(targets)
        send_msg(msg, generate_delete_keyboard(targets))
    else:
        msg = get_formatted_targets(targets)
        send_msg(msg, generate_main_buttons())


def handle_callback_query(update):
    query = update["callback_query"]
    data = query["data"]

    if data == "show_subscriptions":
        show_targets()
    elif data == "add_target":
        send_msg("请发送：/addsub 目标名称 日期\n例如：/addsub 考试 2026-06-15")
    elif data == "delete_target":
        show_targets(delete_mode=True)
    elif data.startswith("del:"):
        name = data[4:]
        if delete_target(name):
            send_msg(f"✅ 已删除目标：{name}", generate_main_buttons())
        else:
            send_msg(f"❌ 删除失败：未找到目标 {name}")
    elif data == "clear_all":
        send_msg("⚠️ <b>确定要清空所有目标吗？</b>\n此操作不可恢复！", generate_clear_confirm_keyboard())
    elif data == "clear_confirm":
        if clear_all_targets():
            send_msg("✅ 已清空所有目标", generate_main_buttons())
        else:
            send_msg("❌ 清空失败")
    elif data == "set_time":
        send_msg("请发送新的推送时间（24小时制）\n例如：/settime 08:30")


def handle_message(update):
    text = update["message"]["text"].strip()

    if text.startswith("/addsub"):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            send_msg("❌ 格式错误！正确示例：/addsub 考试 2026-06-15")
            return
        name = parts[1]
        date_str = parts[2]
        if add_target(name, date_str):
            send_msg(f"✅ 已添加目标：{name} → {date_str}", generate_main_buttons())
        else:
            send_msg("❌ 日期格式无效，请使用 YYYY-MM-DD 等格式")

    elif text.startswith(("/delsub", "/del")):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_msg("❌ 格式错误！正确示例：/delsub 考试")
            return
        name = parts[1].strip()
        if delete_target(name):
            send_msg(f"✅ 已删除目标：{name}", generate_main_buttons())
        else:
            send_msg(f"❌ 未找到目标：{name}")

    elif text.startswith("/subs"):
        show_targets()

    elif text.startswith("/settime"):
        try:
            time_str = text.split()[1]
            datetime.strptime(time_str, "%H:%M")
            set_push_time(time_str)
            send_msg(f"✅ 推送时间已设置为 {time_str}", generate_main_buttons())
        except:
            send_msg("❌ 格式错误！请使用 HH:MM（如 09:00）")


def poll_updates():
    global last_update_id
    url = f"{BASE_URL}getUpdates"

    while True:
        try:
            params = {"timeout": 60, "offset": last_update_id + 1}
            resp = requests.get(url, params=params, timeout=70)
            if resp.status_code != 200:
                time.sleep(5)
                continue

            data = resp.json()
            for update in data.get("result", []):
                last_update_id = update["update_id"]

                if "callback_query" in update:
                    handle_callback_query(update)
                elif "message" in update:
                    handle_message(update)
        except Exception as e:
            print("polling error:", e)
            time.sleep(5)


def start_bot():
    print("🤖 Telegram Bot 轮询已启动（支持删除单个目标）")
    poll_updates()