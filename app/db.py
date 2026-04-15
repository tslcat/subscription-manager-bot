import sqlite3
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
# 获取推送时间（默认 09:00）
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
        cleaned = date_str.replace('/', '-').replace(' ', '')
        if len(cleaned) == 8 and cleaned.isdigit():
            cleaned = f"{cleaned[:4]}-{cleaned[4:6]}-{cleaned[6:]}"
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        return None