import sqlite3
import json
from datetime import datetime
from .config import DB_PATH

# =========================
# 初始化数据库
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            name TEXT PRIMARY KEY,
            target_date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# =========================
# 添加或更新目标
# =========================
def add_target(name, date_str):
    date_str = normalize_date(date_str)
    if not date_str:
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO targets (name, target_date) VALUES (?, ?)",
            (name, date_str)
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# =========================
# 获取所有目标
# =========================
def load_targets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, target_date FROM targets")
    rows = cursor.fetchall()
    conn.close()

    targets = {}
    for name, date_str in rows:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            targets[name] = target_date
        except:
            pass
    return targets

# =========================
# 删除目标
# =========================
def delete_target(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM targets WHERE name = ?", (name,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# =========================
# 导出所有目标（用于备份）
# =========================
def export_targets():
    """返回 dict 格式，方便 JSON 导出"""
    targets = load_targets()
    return {name: dt.strftime("%Y-%m-%d") for name, dt in targets.items()}

# =========================
# 导入目标（批量覆盖）
# =========================
def import_targets(data: dict):
    """从 dict 导入，返回成功数量"""
    if not isinstance(data, dict):
        return 0
    success = 0
    for name, date_str in data.items():
        if add_target(name, str(date_str)):
            success += 1
    return success

# =========================
# 设置推送时间
# =========================
def set_push_time(time_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("push_time", time_str)
    )
    conn.commit()
    conn.close()

# =========================
# 获取推送时间
# =========================
def get_push_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'push_time'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "09:00"

# =========================
# 日期规范化
# =========================
def normalize_date(date_str):
    try:
        cleaned = str(date_str).replace('/', '-').replace(' ', '')
        if len(cleaned) == 8 and cleaned.isdigit():
            cleaned = f"{cleaned[:4]}-{cleaned[4:6]}-{cleaned[6:]}"
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        return None