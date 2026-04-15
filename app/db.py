import sqlite3
from datetime import datetime
from .config import DB_PATH


def normalize_date(date_str: str) -> str | None:
    """灵活解析用户输入的日期，最终统一为 YYYY-MM-DD"""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y",
        "%m-%d", "%m/%d"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if fmt in ("%m-%d", "%m/%d"):
                dt = dt.replace(year=datetime.now().year)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


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


def add_target(name: str, date_str: str) -> bool:
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


def load_targets() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, target_date FROM targets")
    rows = cursor.fetchall()
    conn.close()

    targets = {}
    for name, date_str in rows:
        try:
            targets[name] = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            pass
    return targets


def delete_target(name: str) -> bool:
    """删除单个目标"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM targets WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def clear_all_targets() -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM targets")
    conn.commit()
    conn.close()
    return True


def set_push_time(time_str: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("push_time", time_str)
    )
    conn.commit()
    conn.close()


def get_push_time() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'push_time'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "09:00"