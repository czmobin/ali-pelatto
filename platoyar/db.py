"""لایه‌ی دیتابیس SQLite.

برای حفظ کامل رابط فعلی، هر «مجموعه» (wallet, profiles, agahi, ...) به‌صورت یک ردیف
key/value در جدول kv ذخیره می‌شود که value همان JSON قبلی است. این‌طوری همه‌ی توابع
load_X/save_X بدون تغییر کار می‌کنند، فقط داده به‌جای فایل، داخل SQLite می‌نشیند.
"""
import os
import sqlite3

from .config import DATA_FOLDER

DB_PATH = os.path.join(DATA_FOLDER, "platoyar.sqlite")

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
        _conn.commit()
    return _conn


def kv_get(key):
    row = get_conn().execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return row[0] if row else None


def kv_set(key, value):
    c = get_conn()
    c.execute("INSERT OR REPLACE INTO kv(k, v) VALUES(?, ?)", (key, value))
    c.commit()


def kv_keys():
    return [r[0] for r in get_conn().execute("SELECT k FROM kv ORDER BY k").fetchall()]


def migrate_json_files(paths):
    """داده‌ی فایل‌های JSON قدیمی را (اگر هنوز در دیتابیس نیست) یک‌بار وارد SQLite می‌کند."""
    for path in paths:
        key = os.path.basename(path)
        try:
            if kv_get(key) is not None:
                continue  # قبلاً منتقل شده
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    kv_set(key, f.read())
        except Exception:
            pass
