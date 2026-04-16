import requests
import time
import json
from datetime import datetime
from .db import load_targets, delete_target, export_targets, import_targets
import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_USER_ID = os.getenv('TG_USER_ID')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

last_offset = 0

# ====================== 统一状态管理 ======================
user_state = {
    "pending_action": None,          # "renew" 或 "delete"
    "pending_renew_target": None,    # 正在续费的目标名称
    "pending_import": False
}

# =========================
# 辅助函数
# =========================
def is_valid_push_time(time_str):
    try:
        if ':' not in time_str:
            return False
        h, m = map(int, time_str.split(':'))
        return 0 <= h < 24 and 0 <= m < 60
    except:
        return False

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except:
        return False

# =========================
# 发送消息
# =========================
def send_msg(text, reply_markup=None):
    url = f"{BASE_URL}sendMessage"
    payload = {
        "chat_id": TG_USER_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ 发送失败: {response.text}")
        else:
            print("✅ 消息发送成功")
    except Exception as e:
        print(f"❌ 发送异常: {e}")

# =========================
# 通用操作按钮
# =========================
def generate_inline_buttons():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ 续费目标", "callback_data": "action_renew"},
                {"text": "🗑️ 删除目标", "callback_data": "action_delete"},
            ],
            [
                {"text": "🔄 刷新目标", "callback_data": "show_subscriptions"},
                {"text": "➕ 添加目标", "callback_data": "add_target"},
            ],
            [
                {"text": "📤 导出备份", "callback_data": "export_data"},
                {"text": "📥 导入备份", "callback_data": "import_data"},
            ],
            [
                {"text": "⏰ 设置推送时间", "callback_data": "set_time"},
            ]
        ]
    }
    return keyboard

# =========================
# 极简序号列表（按日期计算天数）
# =========================
def format_numbered_targets(targets):
    if not targets:
        return "📅 当前没有任何目标\n\n<b>共 0 个目标</b>"
    
    message = "📅 <b>当前倒计时目标</b>\n\n"
    sorted_targets = sorted(targets.items(), key=lambda x: x[1])
    
    now_date = datetime.now().date()
    
    for i, (name, target_time) in enumerate(sorted_targets, 1):
        target_date = target_time.date()
        days = (target_date - now_date).days
        
        if days < 0:
            message += f"{i}. {name}: 已结束\n"
        elif days == 0:
            message += f"{i}. {name}: <b>今天</b>\n"
        elif days <= 3:
            message += f"{i}. {name}: <b>{days}天 (紧急)</b>\n"
        else:
            message += f"{i}. {name}: {days}天\n"
    return message

def show_targets():
    global user_state
    user_state = {k: None if k != "pending_import" else False for k in user_state}
    
    targets = load_targets()
    formatted = format_numbered_targets(targets)
    keyboard = generate_inline_buttons()
    send_msg(formatted, keyboard)

# =========================
# 定时推送日报（带按钮）
# =========================
def send_daily_report():
    targets = load_targets()
    if not targets:
        send_msg("📅 <b>Daily Subscription Report</b>\n\n当前没有任何目标", generate_inline_buttons())
        return
    
    body = format_numbered_targets(targets).replace("📅 <b>当前倒计时目标</b>\n\n", "")
    msg = f"📅 <b>Daily Subscription Report</b>\n\n{body}"
    send_msg(msg, generate_inline_buttons())
    print("✅ 定时日报已发送")

# =========================
# 处理按钮点击
# =========================
def handle_callback_query(update):
    global user_state
    callback_data = update["callback_query"]["data"]
    requests.post(f"{BASE_URL}answerCallbackQuery", data={
        "callback_query_id": update["callback_query"]["id"]
    })
    
    if callback_data == "action_renew":
        user_state["pending_action"] = "renew"
        send_msg("✅ 请输入要<b>续费</b>的目标序号（例如：1、2、...）", generate_inline_buttons())
    
    elif callback_data == "action_delete":
        user_state["pending_action"] = "delete"
        send_msg("🗑️ 请输入要<b>删除</b>的目标序号（例如：1、2、...）", generate_inline_buttons())
    
    elif callback_data == "show_subscriptions":
        show_targets()
    elif callback_data == "add_target":
        send_msg("请输入：/addsub &lt;名称&gt; &lt;日期&gt;")
    elif callback_data == "set_time":
        send_msg("请输入新的推送时间，格式：HH:MM")
    elif callback_data == "export_data":
        data = export_targets()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>导出成功！</b>\n\n<code>{json_str}</code>\n\n复制保存即可备份。", generate_inline_buttons())
    elif callback_data == "import_data":
        user_state["pending_import"] = True
        send_msg("📥 请直接粘贴你要导入的 JSON 数据", generate_inline_buttons())

# =========================
# 处理用户消息
# =========================
def handle_message(update):
    global user_state
    text = update["message"]["text"].strip()

    if text == "/start":
        welcome = "👋 <b>Telegram 倒计时机器人</b>\n\n已移除 +1年按钮和删除确认\n操作更直接啦～"
        send_msg(welcome, generate_inline_buttons())
        return

    # ==================== 输入序号（续费 / 删除） ====================
    if user_state["pending_action"] and text.isdigit():
        idx = int(text)
        targets = load_targets()
        sorted_targets = sorted(targets.items(), key=lambda x: x[1])
        
        if 1 <= idx <= len(sorted_targets):
            name = sorted_targets[idx-1][0]
            
            if user_state["pending_action"] == "renew":
                current = targets[name].strftime("%Y-%m-%d")
                user_state["pending_renew_target"] = name
                user_state["pending_action"] = None
                send_msg(f"🎉 正在为「{name}」续费\n\n当前到期：<b>{current}</b>\n\n📅 请输入新的到期日期（YYYY-MM-DD）：", generate_inline_buttons())
                return
            
            elif user_state["pending_action"] == "delete":
                # 直接删除（已移除二次确认）
                if delete_target(name):
                    send_msg(f"✅ 已删除 「{name}」", generate_inline_buttons())
                    show_targets()
                else:
                    send_msg("❌ 删除失败", generate_inline_buttons())
                user_state["pending_action"] = None
                return
        else:
            send_msg(f"❌ 序号 {idx} 超出范围，请重新输入", generate_inline_buttons())
            return

    # ==================== 续费第二步：输入新日期 ====================
    if user_state["pending_renew_target"] and is_valid_date(text):
        name = user_state["pending_renew_target"]
        from .db import add_target
        if add_target(name, text):
            send_msg(f"✅ 「{name}」已续费成功！", generate_inline_buttons())
            show_targets()
        else:
            send_msg("❌ 日期格式错误，请重试", generate_inline_buttons())
        user_state["pending_renew_target"] = None
        return

    # ==================== 导入 JSON ====================
    if user_state["pending_import"]:
        try:
            import_data = json.loads(text)
            count = import_targets(import_data)
            send_msg(f"✅ 成功导入 {count} 个目标！", generate_inline_buttons())
            show_targets()
        except Exception as e:
            send_msg(f"❌ JSON 格式错误：{str(e)}", generate_inline_buttons())
        user_state["pending_import"] = False
        return

    # ==================== 常规命令 ====================
    if text.startswith("/addsub"):
        parts = text.split(maxsplit=2)
        if len(parts) == 3:
            _, name, date_str = parts
            from .db import add_target
            if add_target(name, date_str):
                send_msg("✅ 添加成功", generate_inline_buttons())
                show_targets()
            else:
                send_msg("❌ 添加失败")
        else:
            send_msg("❌ 格式：/addsub 名称 日期")

    elif text.startswith("/delsub"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            name = parts[1].strip()
            if delete_target(name):
                send_msg(f"✅ 已删除 「{name}」", generate_inline_buttons())
                show_targets()
            else:
                send_msg("❌ 未找到目标")
        else:
            send_msg("❌ 格式：/delsub 名称")

    elif text.startswith("/export"):
        data = export_targets()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>数据已导出</b>\n\n<code>{json_str}</code>", generate_inline_buttons())

    elif text.startswith("/import"):
        user_state["pending_import"] = True
        send_msg("📥 请粘贴 JSON 数据：", generate_inline_buttons())

    elif is_valid_push_time(text):
        from .db import set_push_time
        set_push_time(text)
        send_msg(f"✅ 推送时间已设置为 <b>{text}</b>", generate_inline_buttons())

    elif text.startswith("/subs") or text == "/列出所有":
        show_targets()

# =========================
# 轮询更新
# =========================
def poll_updates():
    global last_offset
    url = f"{BASE_URL}getUpdates"
    params = {"timeout": 100, "offset": last_offset, "allowed_updates": ["message", "callback_query"]}
    try:
        response = requests.get(url, params=params, timeout=110)
        if response.status_code == 200:
            data = response.json()
            for update in data.get("result", []):
                last_offset = update["update_id"] + 1
                if "callback_query" in update:
                    handle_callback_query(update)
                elif "message" in update:
                    handle_message(update)
    except Exception as e:
        print(f"❌ 拉取更新失败: {e}")

def start_bot():
    global last_offset
    print("🤖 Telegram Bot 已启动（简化版）...")
    while True:
        try:
            poll_updates()
            time.sleep(0.2)
        except Exception as e:
            print(f"Bot 异常: {e}")
            time.sleep(5)