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
    "pending_action": None,
    "pending_edit_target": None,
    "pending_import": False
}

# ====================== 多语言翻译字典 ======================
TRANSLATIONS = {
    "no_targets": {"en": "No targets currently", "zh": "当前没有任何目标"},
    "current_targets_title": {"en": "Current Targets", "zh": "当前目标"},
    "overdue": {"en": "Overdue", "zh": "逾期"},
    "expiring_soon": {"en": "Expiring Soon", "zh": "即将到期"},
    "medium_term": {"en": "Medium-term", "zh": "中期"},
    "long_term": {"en": "Long-term", "zh": "长期"},
    "overdue_str": {"en": "Overdue", "zh": "逾期"},
    "expiring_soon_str": {"en": "⏳ {days} days", "zh": "⏳ {days}天"},
    "normal_days_str": {"en": "{days} days", "zh": "{days}天"},

    "edit_button": {"en": "✏️ Edit Target", "zh": "✏️ 修改目标"},
    "archive_button": {"en": "📦 Archive Target", "zh": "📦 归档目标"},
    "refresh_button": {"en": "🔄 Refresh Targets", "zh": "🔄 刷新目标"},
    "add_button": {"en": "➕ Add Target", "zh": "➕ 添加目标"},
    "export_button": {"en": "📤 Export All", "zh": "📤 导出全部"},
    "import_button": {"en": "📥 Import All", "zh": "📥 导入全部"},
    "set_time_button": {"en": "⏰ Set Push Time", "zh": "⏰ 设置推送时间"},

    "edit_prompt": {"en": "✏️ Please enter the <b>number</b> of the target to edit (e.g. 1 or 2...)", "zh": "✏️ 请输入要<b>修改</b>的目标序号（例如：1或2...）"},
    "archive_prompt": {"en": "📦 Please enter the <b>number</b> of the target to archive (enter <b>0</b> to view all archived; enter <b>1 or 2...</b> to archive)", "zh": "📦 请输入要<b>归档</b>的目标序号（输入 <b>0</b> 查看所有历史归档;输入<b>1或2...</b> 归档目标）"},
    "add_target_prompt": {"en": "➕ Please enter: /addsub &lt;name&gt; &lt;date&gt;\nExample: /addsub XChat Registration 2026-04-25", "zh": "➕ 请输入：/addsub &lt;名称&gt; &lt;日期&gt;\n示例：/addsub XChat注册 2026-04-25"},
    "set_time_prompt": {"en": "Please enter the new push time in HH:MM format", "zh": "请输入新的推送时间，格式：HH:MM"},
    "export_success": {"en": "📤 <b>Full backup generated</b>\n\n<code>{json_str}</code>", "zh": "📤 <b>完整备份已生成</b>\n\n<code>{json_str}</code>"},
    "import_prompt": {"en": "📥 Please paste the complete JSON you want to import", "zh": "📥 请直接粘贴你要导入的完整 JSON"},
    "start_welcome": {"en": "👋 <b>Telegram Target Bot</b>\n\nUse the buttons below to add/edit targets", "zh": "👋 <b>Telegram 目标机器人</b>\n\n添加/修改目标请使用下方按钮"},
    "edit_current": {"en": "✏️ Current: <b>{name}</b> ({date})\n\nPlease enter: new name (optional) new date (YYYY-MM-DD)\nExample: Netflix Family 2026-12-20\nOr just the date: 2026-12-20", "zh": "✏️ 当前：<b>{name}</b>（{date}）\n\n请输入：新名称（可选） 新日期（YYYY-MM-DD）\n示例：Netflix家庭 2026-12-20\n或只输日期：2026-12-20"},
    "edit_success": {"en": "✅ Edit successful!", "zh": "✅ 修改成功！"},
    "edit_failed": {"en": "❌ Edit failed", "zh": "❌ 修改失败"},
    "archive_success": {"en": "✅ Target archived: 「{name}」", "zh": "✅ 已归档 「{name}」"},
    "archive_failed": {"en": "❌ Archive failed", "zh": "❌ 归档失败"},
    "no_archived": {"en": "📦 No archived targets yet", "zh": "📦 暂无任何已归档目标"},
    "archived_history": {"en": "📦 <b>Archived History</b>\n\n", "zh": "📦 <b>历史已归档目标</b>\n\n"},
    "add_success": {"en": "✅ Added successfully!", "zh": "✅ 添加成功！"},
    "add_failed": {"en": "❌ Add failed, please check date format (YYYY-MM-DD)", "zh": "❌ 添加失败，请检查日期格式（YYYY-MM-DD）"},
    "format_error": {"en": "❌ Format error\nCorrect example: /addsub XChat Registration 2026-04-25", "zh": "❌ 格式错误\n正确示例：/addsub XChat注册 2026-04-25"},
    "push_time_set": {"en": "✅ Push time has been set to <b>{time}</b>", "zh": "✅ 推送时间已设置为 <b>{time}</b>"},
    "import_success": {"en": "✅ Successfully imported {count} targets!", "zh": "✅ 成功导入 {count} 个目标！"},
    "json_error": {"en": "❌ JSON format error: {error}", "zh": "❌ JSON 格式错误：{error}"},
    "daily_report_title": {"en": "Daily Report", "zh": "每日报告"},
    "daily_report_no_targets": {"en": "No targets currently", "zh": "当前没有任何目标"},
}

def get_user_lang(update):
    """自动获取用户 Telegram 语言设置"""
    if "message" in update and "from" in update["message"]:
        lang = update["message"]["from"].get("language_code", "en")
    elif "callback_query" in update and "from" in update["callback_query"]:
        lang = update["callback_query"]["from"].get("language_code", "en")
    else:
        lang = "en"
    return "zh" if lang.startswith("zh") else "en"

def get_text(key, lang="en", **kwargs):
    """获取对应语言的文本，支持格式化"""
    lang = "zh" if lang.startswith("zh") else "en"
    text = TRANSLATIONS.get(key, {}).get(lang, TRANSLATIONS.get(key, {}).get("en", key))
    if kwargs:
        text = text.format(**kwargs)
    return text

def generate_inline_buttons(lang="en"):
    keyboard = {
        "inline_keyboard": [
            [
                {"text": get_text("edit_button", lang), "callback_data": "action_edit"},
                {"text": get_text("archive_button", lang), "callback_data": "action_archive"},
            ],
            [
                {"text": get_text("refresh_button", lang), "callback_data": "show_subscriptions"},
                {"text": get_text("add_button", lang), "callback_data": "add_target"},
            ],
            [
                {"text": get_text("export_button", lang), "callback_data": "export_data"},
                {"text": get_text("import_button", lang), "callback_data": "import_data"},
            ],
            [
                {"text": get_text("set_time_button", lang), "callback_data": "set_time"},
            ]
        ]
    }
    return keyboard

def format_numbered_targets(targets, lang="en"):
    if not targets:
        return get_text("no_targets", lang)
    
    message = f"                  <b>{get_text('current_targets_title', lang)}</b>\n\n"
    
    now_date = datetime.now().date()
    
    categorized = {
        "Overdue":       {"emoji": "⚠️", "key": "overdue"},
        "Expiring Soon": {"emoji": "🚨", "key": "expiring_soon"},
        "Medium-term":   {"emoji": "📊", "key": "medium_term"},
        "Long-term":     {"emoji": "📦", "key": "long_term"}
    }
    
    items = []
    for name, target_time in targets.items():
        days = (target_time.date() - now_date).days
        if days < 0:
            category = "Overdue"
        elif days <= 30:
            category = "Expiring Soon"
        elif days <= 365:
            category = "Medium-term"
        else:
            category = "Long-term"
        items.append({"name": name, "days": days, "category": category})
    
    items.sort(key=lambda x: x["days"])
    
    idx = 1
    for cat_key, cat_data in categorized.items():
        cat_items = [item for item in items if item["category"] == cat_key]
        if not cat_items:
            continue
        message += f"{cat_data['emoji']} <b>{get_text(cat_data['key'], lang)}</b>\n\n"
        
        for item in cat_items:
            if item["category"] == "Overdue":
                day_str = get_text("overdue_str", lang)
            elif item["category"] == "Expiring Soon":
                day_str = get_text("expiring_soon_str", lang, days=item["days"])
            else:
                day_str = get_text("normal_days_str", lang, days=item["days"])
            message += f"{idx}. {item['name']}:  <b>{day_str}</b>\n"
            idx += 1
        message += "\n"
    return message


# =========================
# 定时推送日报（使用默认语言，可自行修改默认值）
# =========================
def send_daily_report():
    targets = load_targets()
    lang = "zh"  # 这里默认中文，你可以改成 "en"
    if not targets:
        send_msg(get_text("daily_report_title", lang) + "\n\n" + get_text("daily_report_no_targets", lang), generate_inline_buttons(lang))
        return
    body = format_numbered_targets(targets, lang).replace(f"                  <b>{get_text('current_targets_title', lang)}</b>\n\n", "")
    send_msg(f"📅 <b>{get_text('daily_report_title', lang)}</b>\n\n{body}", generate_inline_buttons(lang))


# =========================
# 按钮处理
# =========================
def handle_callback_query(update):
    global user_state
    lang = get_user_lang(update)
    callback_data = update["callback_query"]["data"]
    requests.post(f"{BASE_URL}answerCallbackQuery", data={"callback_query_id": update["callback_query"]["id"]})
    
    if callback_data == "action_edit":
        user_state["pending_action"] = "edit"
        send_msg(get_text("edit_prompt", lang), generate_inline_buttons(lang))
    elif callback_data == "action_archive":
        user_state["pending_action"] = "archive"
        send_msg(get_text("archive_prompt", lang), generate_inline_buttons(lang))
    elif callback_data == "show_subscriptions":
        show_targets(update)
    elif callback_data == "add_target":
        send_msg(get_text("add_target_prompt", lang), generate_inline_buttons(lang))
    elif callback_data == "set_time":
        send_msg(get_text("set_time_prompt", lang), generate_inline_buttons(lang))
    elif callback_data == "export_data":
        data = export_all()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(get_text("export_success", lang, json_str=json_str), generate_inline_buttons(lang))
    elif callback_data == "import_data":
        user_state["pending_import"] = True
        send_msg(get_text("import_prompt", lang), generate_inline_buttons(lang))


# =========================
# 用户消息处理
# =========================
def handle_message(update):
    global user_state
    lang = get_user_lang(update)
    text = update["message"]["text"].strip()

    if text == "/start":
        send_msg(get_text("start_welcome", lang), generate_inline_buttons(lang))
        return

    if user_state["pending_action"] and text.isdigit():
        # ...（序号处理逻辑保持不变，仅提示文字使用 get_text）
        idx = int(text)
        targets = load_targets()
        sorted_targets = sorted(targets.items(), key=lambda x: x[1])
        
        if idx == 0 and user_state["pending_action"] == "archive":
            archives = load_archives()
            if not archives:
                send_msg(get_text("no_archived", lang), generate_inline_buttons(lang))
            else:
                msg = get_text("archived_history", lang)
                for name, target_date in sorted(archives.items(), key=lambda x: x[1], reverse=True):
                    msg += f"• {name}: {target_date.strftime('%Y-%m-%d')}\n"
                send_msg(msg, generate_inline_buttons(lang))
            user_state["pending_action"] = None
            return

        if 1 <= idx <= len(sorted_targets):
            old_name = sorted_targets[idx-1][0]
            current_date = targets[old_name].strftime("%Y-%m-%d")
            
            if user_state["pending_action"] == "edit":
                user_state["pending_edit_target"] = old_name
                user_state["pending_action"] = None
                send_msg(get_text("edit_current", lang, name=old_name, date=current_date), generate_inline_buttons(lang))
                return
            elif user_state["pending_action"] == "archive":
                if archive_target(old_name):
                    send_msg(get_text("archive_success", lang, name=old_name), generate_inline_buttons(lang))
                    show_targets(update)
                else:
                    send_msg(get_text("archive_failed", lang), generate_inline_buttons(lang))
                user_state["pending_action"] = None
                return

    # 修改目标第二步
    if user_state["pending_edit_target"] and text:
        # ...（逻辑不变）
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
        if update_target(old_name, new_name, new_date):
            send_msg(get_text("edit_success", lang), generate_inline_buttons(lang))
            show_targets(update)
        else:
            send_msg(get_text("edit_failed", lang), generate_inline_buttons(lang))
        user_state["pending_edit_target"] = None
        return

    # 导入
    if user_state["pending_import"]:
        try:
            import_data = json.loads(text)
            count = import_all(import_data)
            send_msg(get_text("import_success", lang, count=count), generate_inline_buttons(lang))
            show_targets(update)
        except Exception as e:
            send_msg(get_text("json_error", lang, error=str(e)), generate_inline_buttons(lang))
        user_state["pending_import"] = False
        return

    # 添加目标
    if text.startswith("/addsub"):
        parts = text.split(maxsplit=2)
        if len(parts) == 3:
            _, name, date_str = parts
            from .db import add_target
            if add_target(name, date_str):
                send_msg(get_text("add_success", lang), generate_inline_buttons(lang))
                show_targets(update)
            else:
                send_msg(get_text("add_failed", lang), generate_inline_buttons(lang))
        else:
            send_msg(get_text("format_error", lang), generate_inline_buttons(lang))
        return

    # 其他命令（保持不变）
    elif text.startswith("/export"):
        data = export_all()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        send_msg(get_text("export_success", lang, json_str=json_str), generate_inline_buttons(lang))

    elif text.startswith("/import"):
        user_state["pending_import"] = True
        send_msg(get_text("import_prompt", lang), generate_inline_buttons(lang))

    elif is_valid_push_time(text):
        from .db import set_push_time
        set_push_time(text)
        send_msg(get_text("push_time_set", lang, time=text), generate_inline_buttons(lang))

    elif text.startswith("/subs") or text.lower() == "/list all":
        show_targets(update)

def show_targets(update):
    global user_state
    lang = get_user_lang(update)
    user_state = {k: None if k != "pending_import" else False for k in user_state}
    targets = load_targets()
    formatted = format_numbered_targets(targets, lang)
    keyboard = generate_inline_buttons(lang)
    send_msg(formatted, keyboard)

# =========================
# 轮询 & 启动
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
        print(f"❌ Failed to fetch updates: {e}")

def start_bot():
    global last_offset
    print("🤖 Telegram Bot started (Auto Chinese/English switching enabled)...")
    while True:
        try:
            poll_updates()
            time.sleep(0.2)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(5)