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
        CREATE TABLE IF NOT EXISTS archives (
            name TEXT PRIMARY KEY,
            target_date TEXT NOT NULL,
            archived_date TEXT NOT NULL
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
# 添加或更新当前目标
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
# 【新增】修改目标（支持改名 + 改日期）
# =========================
def update_target(old_name: str, new_name: str = None, new_date: str = None):
    """修改名称和/或日期。如果只改其中一项，另一项保持不变"""
    if new_name is None:
        new_name = old_name
    if new_date is None:
        # 只改名称时也要读取当前日期
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_date FROM targets WHERE name = ?", (old_name,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        new_date = row[0]
    else:
        new_date = normalize_date(new_date)
        if not new_date:
            return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 如果名称发生变化，需要先删除旧记录
        if new_name != old_name:
            cursor.execute("DELETE FROM targets WHERE name = ?", (old_name,))
        
        cursor.execute(
            "INSERT OR REPLACE INTO targets (name, target_date) VALUES (?, ?)",
            (new_name, new_date)
        )
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# =========================
# 获取所有当前目标
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
# 归档目标
# =========================
def archive_target(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT target_date FROM targets WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return False
        
        date_str = row[0]
        archived_date = datetime.now().strftime("%Y-%m-%d %H:%M")

        cursor.execute(
            "INSERT OR REPLACE INTO archives (name, target_date, archived_date) VALUES (?, ?, ?)",
            (name, date_str, archived_date)
        )
        cursor.execute("DELETE FROM targets WHERE name = ?", (name,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

# =========================
# 获取所有已归档目标
# =========================
def load_archives():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, target_date FROM archives ORDER BY archived_date DESC")
    rows = cursor.fetchall()
    conn.close()

    archives = {}
    for name, date_str in rows:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            archives[name] = target_date
        except:
            pass
    return archives

# =========================
# 导出/导入全部数据
# =========================
def export_all():
    return {
        "targets": {name: dt.strftime("%Y-%m-%d") for name, dt in load_targets().items()},
        "archives": {name: dt.strftime("%Y-%m-%d") for name, dt in load_archives().items()}
    }

def import_all(data: dict):
    if not isinstance(data, dict):
        return 0
    success = 0
    
    if "targets" in data and isinstance(data["targets"], dict):
        for name, date_str in data["targets"].items():
            if add_target(name, str(date_str)):
                success += 1
    
    if "archives" in data and isinstance(data["archives"], dict):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            for name, date_str in data["archives"].items():
                date_str = normalize_date(date_str)
                if date_str:
                    archived_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    cursor.execute(
                        "INSERT OR REPLACE INTO archives (name, target_date, archived_date) VALUES (?, ?, ?)",
                        (name, date_str, archived_date)
                    )
                    success += 1
            conn.commit()
        finally:
            conn.close()
    
    # 兼容旧版
    elif not any(k in data for k in ["targets", "archives"]):
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