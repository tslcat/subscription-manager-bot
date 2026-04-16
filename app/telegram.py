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
pending_renew_target = None   # 正在等待续费输入的目标名称
pending_import = False        # 是否正在等待导入 JSON

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
            print("❌ 发送失败:", response.text)
        else:
            print("✅ 消息发送成功")
    except Exception as e:
        print("❌ 发送异常:", e)

# =========================
# 通用按钮
# =========================
def generate_inline_buttons():
    keyboard = {
        "inline_keyboard": [
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
                {"text": "✏️ 修改目标", "callback_data": "edit_target"},
            ]
        ]
    }
    return keyboard

# =========================
# 动态目标键盘（每项目标都有「已续费」+「删除」按钮）
# =========================
def generate_targets_keyboard(targets):
    keyboard = {"inline_keyboard": []}
    sorted_targets = sorted(targets.items(), key=lambda x: x[1])
    
    for name, target_date in sorted_targets:
        keyboard["inline_keyboard"].append([
            {"text": f"✅ 已续费 {name}", "callback_data": f"renew:{name}"},
            {"text": f"🗑️ 删除 {name}", "callback_data": f"delete:{name}"}
        ])
    
    # 底部通用按钮
    keyboard["inline_keyboard"].append([
        {"text": "🔄 刷新列表", "callback_data": "show_subscriptions"},
        {"text": "➕ 添加目标", "callback_data": "add_target"},
    ])
    return keyboard

# =========================
# 格式化目标消息
# =========================
def format_target_message(targets):
    if not targets:
        return "📅 当前没有任何目标"
    
    message = "📅 <b>当前倒计时目标列表</b>:\n\n"
    sorted_targets = sorted(targets.items(), key=lambda x: x[1])
    
    for name, target_time in sorted_targets:
        target_date_str = target_time.strftime("%Y-%m-%d")
        days = (target_time - datetime.now()).days
        if days < 0:
            message += f"<i>{name}: {target_date_str}（已结束）</i>\n"
        elif days == 0:
            message += f"<b>{name}: {target_date_str}（今天）</b>\n"
        elif days <= 9:
            message += f"<b>{name}: {target_date_str}（{days}天 紧急）</b>\n"
        else:
            message += f"{name}: {target_date_str}（{days}天）\n"
    return message

def show_targets():
    global pending_renew_target, pending_import
    pending_renew_target = None
    pending_import = False
    
    targets = load_targets()
    if not targets:
        send_msg("📅 当前没有任何目标", generate_inline_buttons())
        return
    formatted_message = format_target_message(targets)
    keyboard = generate_targets_keyboard(targets)
    send_msg(formatted_message, keyboard)

# =========================
# 处理按钮点击
# =========================
def handle_callback_query(update):
    global pending_renew_target, pending_import
    callback_data = update["callback_query"]["data"]
    requests.post(f"{BASE_URL}answerCallbackQuery", data={
        "callback_query_id": update["callback_query"]["id"]
    })
    
    if callback_data.startswith("delete:"):
        name = callback_data[7:]
        if delete_target(name):
            send_msg(f"✅ 已删除 「{name}」", generate_inline_buttons())
            show_targets()
        else:
            send_msg("❌ 未找到目标", generate_inline_buttons())
    
    elif callback_data.startswith("renew:"):
        name = callback_data[6:]
        targets = load_targets()
        if name in targets:
            current = targets[name].strftime("%Y-%m-%d")
            pending_renew_target = name
            send_msg(f"🎉 **正在为「{name}」续费**\n\n当前到期日期：<b>{current}</b>\n\n📅 请输入新的到期日期（YYYY-MM-DD）：", generate_inline_buttons())
        else:
            send_msg("❌ 未找到该目标", generate_inline_buttons())
    
    elif callback_data == "show_subscriptions":
        show_targets()
    elif callback_data == "add_target":
        send_msg("请输入：/addsub &lt;名称&gt; &lt;日期&gt;")
    elif callback_data == "set_time":
        send_msg("请输入新的推送时间，格式：HH:MM")
    elif callback_data == "edit_target":
        send_msg("请输入：/editsub &lt;名称&gt; &lt;新日期&gt;")
    elif callback_data == "export_data":
        data = export_targets()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>导出成功！</b>\n\n<code>{json_str}</code>\n\n复制保存此 JSON 即可备份。", generate_inline_buttons())
    elif callback_data == "import_data":
        pending_import = True
        send_msg("📥 请直接粘贴你要导入的 JSON 数据（必须和导出的格式一致）", generate_inline_buttons())

# =========================
# 处理用户消息
# =========================
def handle_message(update):
    global pending_renew_target, pending_import
    text = update["message"]["text"].strip()

    # /start 欢迎
    if text == "/start":
        welcome = "👋 <b>欢迎使用 Telegram 倒计时机器人</b>\n\n✅ 支持一键已续费 + 数据备份\n点击下方按钮开始管理你的目标吧！"
        send_msg(welcome, generate_inline_buttons())
        return

    # 正在等待续费日期输入
    if pending_renew_target and is_valid_date(text):
        from .db import add_target
        if add_target(pending_renew_target, text):
            send_msg(f"✅ 「{pending_renew_target}」已成功续费！新日期：<b>{text}</b>", generate_inline_buttons())
            show_targets()
        else:
            send_msg("❌ 日期格式错误，请重试", generate_inline_buttons())
        pending_renew_target = None
        return

    # 正在等待导入 JSON
    if pending_import:
        try:
            import_data = json.loads(text)
            count = import_targets(import_data)
            send_msg(f"✅ 成功导入 {count} 个目标！", generate_inline_buttons())
            show_targets()
        except Exception as e:
            send_msg(f"❌ JSON 解析失败：{str(e)}\n请检查格式后重试", generate_inline_buttons())
        pending_import = False
        return

    # 常规命令
    if text.startswith("/addsub"):
        parts = text.split(maxsplit=2)
        if len(parts) == 3:
            _, name, date_str = parts
            from .db import add_target
            if add_target(name, date_str):
                send_msg("✅ 添加/更新成功", generate_inline_buttons())
                show_targets()
            else:
                send_msg("❌ 添加失败")
        else:
            send_msg("❌ 格式错误：/addsub &lt;名称&gt; &lt;日期&gt;")

    elif text.startswith("/delsub"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            name = parts[1].strip()
            if delete_target(name):
                send_msg(f"✅ 已删除 「{name}」", generate_inline_buttons())
                show_targets()
            else:
                send_msg("❌ 未找到该目标")
        else:
            send_msg("❌ 格式：/delsub &lt;名称&gt;")

    elif text.startswith("/export"):
        data = export_targets()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>数据导出</b>\n\n<code>{json_str}</code>", generate_inline_buttons())

    elif text.startswith("/import"):
        pending_import = True
        send_msg("📥 请粘贴你要导入的 JSON 数据：", generate_inline_buttons())

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
    params = {
        "timeout": 100,
        "offset": last_offset,
        "allowed_updates": ["message", "callback_query"]
    }
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
        print("❌ 拉取更新失败:", e)

# =========================
# 启动 Bot
# =========================
def start_bot():
    global last_offset
    print("🤖 Telegram Bot 已启动（长轮询模式）...")
    while True:
        try:
            poll_updates()
            time.sleep(0.3)
        except Exception as e:
            print(f"Bot 异常: {e}")
            time.sleep(5)