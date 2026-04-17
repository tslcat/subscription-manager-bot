import requests
import time
import json
from datetime import datetime
from .db import load_targets, update_target, archive_target, load_archives, export_all, import_all
import os

BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_USER_ID = os.getenv('TG_USER_ID')
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

last_offset = 0

user_state = {
    "pending_action": None,          # "edit" 或 "archive"
    "pending_edit_target": None,     # 正在修改的目标原始名称
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

def send_msg(text, reply_markup=None):
    url = f"{BASE_URL}sendMessage"
    payload = {"chat_id": TG_USER_ID, "text": text, "parse_mode": "HTML"}
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

def generate_inline_buttons():
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✏️ 修改目标", "callback_data": "action_edit"},
                {"text": "📦 归档目标", "callback_data": "action_archive"},
            ],
            [
                {"text": "🔄 刷新目标", "callback_data": "show_subscriptions"},
                {"text": "➕ 添加目标", "callback_data": "add_target"},
            ],
            [
                {"text": "📤 导出全部", "callback_data": "export_data"},
                {"text": "📥 导入全部", "callback_data": "import_data"},
            ],
            [
                {"text": "⏰ 设置推送时间", "callback_data": "set_time"},
            ]
        ]
    }
    return keyboard

def format_numbered_targets(targets):
    """新的分类展示格式（完全匹配你截图样式）"""
    if not targets:
        return "📅 当前没有任何目标\n\n<b>共 0 个目标</b>"
    
    message = "📅 <b>当前目标</b>\n\n"
    now_date = datetime.now().date()
    
    # 分类
    categorized = {
        "即将到期": {"emoji": "🚨", "items": []},
        "进行中": {"emoji": "📊", "items": []},
        "长期资源": {"emoji": "📦", "items": []}
    }
    
    items = []
    for name, target_time in targets.items():
        target_date = target_time.date()
        days = (target_date - now_date).days
        
        if days < 0:
            continue  # 已过期的目标不显示在当前列表
        
        if days <= 30:
            category = "即将到期"
        elif days <= 365:
            category = "进行中"
        else:
            category = "长期资源"
            
        items.append({
            "name": name,
            "days": days,
            "category": category
        })
    
    # 按剩余天数排序（最早到期的排最前）
    items.sort(key=lambda x: x["days"])
    
    # 组装消息
    idx = 1
    for cat_name, cat_data in categorized.items():
        cat_items = [item for item in items if item["category"] == cat_name]
        if not cat_items:
            continue
            
        message += f"{cat_data['emoji']} <b>{cat_name}</b>\n\n"
        
        for item in cat_items:
            days = item["days"]
            # 紧急图标（和截图一致）
            if days <= 7:
                extra = " ⏳"
            elif days <= 30:
                extra = " ⚠️"
            else:
                extra = ""
                
            message += f"{idx}. {item['name']}: <b>{days}天{extra}</b>\n"
            idx += 1
        
        message += "\n"
    
    total = len(items)
    message += f"<b>共 {total} 个目标</b>"
    return message


# =========================
# 定时推送日报
# =========================
def send_daily_report():
    targets = load_targets()
    if not targets:
        send_msg("📅 <b>Daily Subscription Report</b>\n\n当前没有任何目标", generate_inline_buttons())
        return
    body = format_numbered_targets(targets).replace("📅 <b>当前目标</b>\n\n", "")
    send_msg(f"📅 <b>Daily Subscription Report</b>\n\n{body}", generate_inline_buttons())


# =========================
# 处理按钮点击
# =========================
def handle_callback_query(update):
    global user_state
    callback_data = update["callback_query"]["data"]
    requests.post(f"{BASE_URL}answerCallbackQuery", data={"callback_query_id": update["callback_query"]["id"]})
    
    if callback_data == "action_edit":
        user_state["pending_action"] = "edit"
        send_msg("✏️ 请输入要<b>修改</b>的目标序号（例如：1或2...）", generate_inline_buttons())
    
    elif callback_data == "action_archive":
        user_state["pending_action"] = "archive"
        send_msg("📦 请输入要<b>归档</b>的目标序号（输入 <b>0</b> 查看所有历史归档;输入<b>1或2...</b> 归档目标）", generate_inline_buttons())
    
    elif callback_data == "show_subscriptions":
        show_targets()
    elif callback_data == "add_target":
        send_msg("请输入：/addsub <名称> <日期>")
    elif callback_data == "set_time":
        send_msg("请输入新的推送时间，格式：HH:MM")
    elif callback_data == "export_data":
        data = export_all()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>完整备份已生成</b>\n\n<code>{json_str}</code>", generate_inline_buttons())
    elif callback_data == "import_data":
        user_state["pending_import"] = True
        send_msg("📥 请直接粘贴你要导入的完整 JSON", generate_inline_buttons())

# =========================
# 处理用户消息
# =========================
def handle_message(update):
    global user_state
    text = update["message"]["text"].strip()

    if text == "/start":
        welcome = "👋 <b>Telegram 目标机器人</b>\n\n已修复启动问题！\n「修改目标」支持改名称+日期"
        send_msg(welcome, generate_inline_buttons())
        return

    # 输入序号
    if user_state["pending_action"] and text.isdigit():
        idx = int(text)
        targets = load_targets()
        sorted_targets = sorted(targets.items(), key=lambda x: x[1])
        
        if idx == 0 and user_state["pending_action"] == "archive":
            archives = load_archives()
            if not archives:
                send_msg("📦 暂无任何已归档目标", generate_inline_buttons())
            else:
                msg = "📦 <b>历史已归档目标</b>\n\n"
                for name, target_date in sorted(archives.items(), key=lambda x: x[1], reverse=True):
                    msg += f"• {name}：{target_date.strftime('%Y-%m-%d')}\n"
                send_msg(msg, generate_inline_buttons())
            user_state["pending_action"] = None
            return

        if 1 <= idx <= len(sorted_targets):
            old_name = sorted_targets[idx-1][0]
            current_date = targets[old_name].strftime("%Y-%m-%d")
            
            if user_state["pending_action"] == "edit":
                user_state["pending_edit_target"] = old_name
                user_state["pending_action"] = None
                send_msg(f"✏️ 当前：<b>{old_name}</b>（{current_date}）\n\n请输入：新名称（可选） 新日期（YYYY-MM-DD）\n示例：Netflix家庭 2026-12-20\n或只输日期：2026-12-20", generate_inline_buttons())
                return
            elif user_state["pending_action"] == "archive":
                if archive_target(old_name):
                    send_msg(f"✅ 已归档 「{old_name}」", generate_inline_buttons())
                    show_targets()
                else:
                    send_msg("❌ 归档失败", generate_inline_buttons())
                user_state["pending_action"] = None
                return

    # 修改目标第二步
    if user_state["pending_edit_target"] and text:
        old_name = user_state["pending_edit_target"]
        parts = text.strip().split(maxsplit=1)
        new_name = None
        new_date = None
        if len(parts) == 1:
            if is_valid_date(parts[0]):
                new_date = parts[0]
            else:
                new_name = parts[0]
        else:
            new_name = parts[0]
            if len(parts) > 1 and is_valid_date(parts[1]):
                new_date = parts[1]
        from .db import update_target
        if update_target(old_name, new_name, new_date):
            send_msg(f"✅ 修改成功！", generate_inline_buttons())
            show_targets()
        else:
            send_msg("❌ 修改失败", generate_inline_buttons())
        user_state["pending_edit_target"] = None
        return

    # 导入
    if user_state["pending_import"]:
        try:
            import_data = json.loads(text)
            count = import_all(import_data)
            send_msg(f"✅ 成功导入 {count} 个目标！", generate_inline_buttons())
            show_targets()
        except Exception as e:
            send_msg(f"❌ JSON 格式错误：{str(e)}", generate_inline_buttons())
        user_state["pending_import"] = False
        return

    # 常规命令
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

    elif text.startswith("/export"):
        data = export_all()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(f"📤 <b>完整备份</b>\n\n<code>{json_str}</code>", generate_inline_buttons())

    elif text.startswith("/import"):
        user_state["pending_import"] = True
        send_msg("📥 请粘贴完整 JSON：", generate_inline_buttons())

    elif is_valid_push_time(text):
        from .db import set_push_time
        set_push_time(text)
        send_msg(f"✅ 推送时间已设置为 <b>{text}</b>", generate_inline_buttons())

    elif text.startswith("/subs") or text == "/列出所有":
        show_targets()

# =========================
# 显示当前目标（使用新格式）
# =========================
def show_targets():
    global user_state
    user_state = {k: None if k != "pending_import" else False for k in user_state}
    targets = load_targets()
    formatted = format_numbered_targets(targets)
    keyboard = generate_inline_buttons()
    send_msg(formatted, keyboard)

# =========================
# 轮询
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
    print("🤖 Telegram Bot 已启动（最新稳定版）...")
    while True:
        try:
            poll_updates()
            time.sleep(0.2)
        except Exception as e:
            print(f"Bot 异常: {e}")
            time.sleep(5)