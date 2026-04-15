import sqlite3
import os
from datetime import datetime

# 使用和 config.py 一致的路径，并确保目录存在
DB_PATH = "/data/subscriptions.db"

# =========================
# 日期格式标准化
# =========================
def normalize_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip().replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '').replace(' ', '')

    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y",
        "%Y年%m月%d日", "%Y%m%d"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except:
            pass
    return None

# =========================
# 初始化数据库（已修复路径问题）
# =========================
def init_db():
    # 确保 /data 目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
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
    print(f"✅ 数据库已初始化 → {DB_PATH}")

# =========================
# 添加或更新目标（支持修改）
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
    except sqlite3.Error as e:
        print("数据库错误:", e)
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
# 获取推送时间（默认北京时间 08:00）
# =========================
def get_push_time():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'push_time'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "08:00"