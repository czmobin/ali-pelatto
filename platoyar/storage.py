# ============================================================
# لایه‌ی ذخیره‌سازی (SQLite)
# همه‌ی خواندن/نوشتن‌ها از دو تابع عمومی _read_json / _write_json می‌گذرند که حالا
# داده را به‌جای فایل، داخل SQLite (جدول kv، با کلیدِ نام فایل) ذخیره می‌کنند.
# ============================================================
import json
import os

from .config import (
    WALLET_FILE, PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE,
    BLACKLIST_FILE, REJECT_COUNTER_FILE, PRICE_REQUEST_FILE, REJECTED_ADS_FILE,
    REFERRAL_FILE, USERS_FILE, SHOP_PRICES_FILE, SHOP_UNAVAILABLE_FILE,
    ADMINS_FILE, ADMIN_IDS, SUPER_ADMIN_ID, SHOP_ORDERS_FILE, SETTINGS_FILE,
    ADMIN_PERMS_FILE, ADMIN_PERM_LABELS,
)
from .db import kv_get, kv_set


def _key(path):
    # کلید دیتابیس = نام فایل (مثل wallet.json) تا مستقل از مسیر داده باشد
    return os.path.basename(path)


def _read_json(path, default):
    """خواندن امن از دیتابیس؛ در صورت نبود یا خطا، مقدار پیش‌فرض برمی‌گردد."""
    raw = kv_get(_key(path))
    if raw is None:
        return default() if callable(default) else default
    try:
        return json.loads(raw)
    except Exception:
        return default() if callable(default) else default


def _write_json(path, data):
    """نوشتن امن در دیتابیس."""
    try:
        kv_set(_key(path), json.dumps(data, ensure_ascii=False))
    except Exception:
        pass


# ---- کیف پول ----
def load_wallet():
    return _read_json(WALLET_FILE, dict)


def save_wallet(data):
    _write_json(WALLET_FILE, data)


def get_wallet_balance(user_id):
    wallet = load_wallet()
    return wallet.get(str(user_id), 0)


def add_to_wallet(user_id, amount):
    wallet = load_wallet()
    user_id_str = str(user_id)
    wallet[user_id_str] = wallet.get(user_id_str, 0) + amount
    save_wallet(wallet)
    return wallet[user_id_str]


def deduct_from_wallet(user_id, amount):
    wallet = load_wallet()
    user_id_str = str(user_id)
    current = wallet.get(user_id_str, 0)
    if current >= amount:
        wallet[user_id_str] = current - amount
        save_wallet(wallet)
        return True, wallet[user_id_str]
    return False, current


# ---- شمارنده‌ی شناسه‌ی آگهی ----
def get_next_ad_id():
    try:
        data = _read_json(COUNTER_FILE, dict)
        last_id = data.get("last_id", -1) + 1
        data["last_id"] = last_id
        _write_json(COUNTER_FILE, data)
        return last_id
    except Exception:
        return 0


# ---- پروفایل‌ها ----
def load_profiles():
    return _read_json(PROFILE_FILE, dict)


def save_profiles(data):
    _write_json(PROFILE_FILE, data)


# ---- آگهی‌های منتشرشده ----
def load_agahi():
    return _read_json(AGAHI_FILE, dict)


def save_agahi(data):
    _write_json(AGAHI_FILE, data)


# ---- آگهی‌های در انتظار تایید ----
def load_pending_ads():
    return _read_json(PENDING_ADS_FILE, dict)


def save_pending_ads(data):
    _write_json(PENDING_ADS_FILE, data)


# ---- لیست سیاه ----
def load_blacklist():
    return _read_json(BLACKLIST_FILE, list)


def save_blacklist(data):
    _write_json(BLACKLIST_FILE, data)


# ---- درخواست‌های قیمت ----
def load_price_requests():
    return _read_json(PRICE_REQUEST_FILE, dict)


def save_price_requests(data):
    _write_json(PRICE_REQUEST_FILE, data)


# ---- آگهی‌های ردشده ----
def load_rejected_ads():
    return _read_json(REJECTED_ADS_FILE, dict)


def save_rejected_ads(data):
    _write_json(REJECTED_ADS_FILE, data)


# ---- شمارنده‌ی رد کردن + لیست سیاه خودکار ----
def get_reject_count(user_id):
    data = _read_json(REJECT_COUNTER_FILE, dict)
    return data.get(str(user_id), 0)


def increment_reject_count(user_id):
    data = _read_json(REJECT_COUNTER_FILE, dict)
    count = data.get(str(user_id), 0) + 1
    data[str(user_id)] = count
    _write_json(REJECT_COUNTER_FILE, data)

    if count >= 3:
        blacklist = load_blacklist()
        if user_id not in blacklist:
            blacklist.append(user_id)
            save_blacklist(blacklist)
        return count, True
    return count, False


# ---- زیرمجموعه‌گیری (referral) ----
def load_referrals():
    return _read_json(REFERRAL_FILE, dict)


def save_referrals(data):
    _write_json(REFERRAL_FILE, data)


def get_referral_count(user_id):
    referrals = load_referrals()
    data = referrals.get(str(user_id), {})
    if isinstance(data, int):
        return data
    return data.get("count", 0)


def increment_referral_count(user_id):
    referrals = load_referrals()
    user_id_str = str(user_id)
    data = referrals.get(user_id_str, {})
    if isinstance(data, int):
        data = {"count": data, "bonus_claimed": False}
    data["count"] = data.get("count", 0) + 1
    referrals[user_id_str] = data
    save_referrals(referrals)
    return data["count"]


def has_used_referral_bonus(user_id):
    referrals = load_referrals()
    data = referrals.get(str(user_id), {})
    if isinstance(data, int):
        return False
    return data.get("bonus_claimed", False)


def mark_referral_bonus_claimed(user_id):
    referrals = load_referrals()
    user_id_str = str(user_id)
    data = referrals.get(user_id_str, {})
    if isinstance(data, int):
        data = {"count": data, "bonus_claimed": False}
    data["bonus_claimed"] = True
    referrals[user_id_str] = data
    save_referrals(referrals)


def get_referred_by(user_id):
    referrals = load_referrals()
    data = referrals.get(str(user_id), {})
    if isinstance(data, int):
        return None
    return data.get("referred_by")


# ---- ثبت کاربران ربات ----
def load_users():
    return _read_json(USERS_FILE, dict)


def save_users(data):
    _write_json(USERS_FILE, data)


# ---- قیمت‌های فروشگاه ----
def load_shop_prices():
    return _read_json(SHOP_PRICES_FILE, dict)


def save_shop_prices(data):
    _write_json(SHOP_PRICES_FILE, data)


# ---- سفارش‌های فروشگاه ----
def load_shop_orders():
    return _read_json(SHOP_ORDERS_FILE, dict)


def save_shop_orders(data):
    _write_json(SHOP_ORDERS_FILE, data)


# ---- تنظیمات قابل‌ویرایش (هزینه‌ها، کارت، متن‌ها) ----
def load_settings():
    return _read_json(SETTINGS_FILE, dict)


def save_settings(data):
    _write_json(SETTINGS_FILE, data)


def get_setting(key, default=None):
    v = load_settings().get(key)
    return v if v is not None else default


def set_setting(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)


# ---- بخش‌های ناموجود فروشگاه ----
def load_shop_unavailable():
    data = _read_json(SHOP_UNAVAILABLE_FILE, list)
    return data if isinstance(data, list) else []


def save_shop_unavailable(data):
    _write_json(SHOP_UNAVAILABLE_FILE, data)


# ---- مدیریت ادمین‌ها (زمان اجرا) ----
# ادمین‌ها در یک فایل JSON ساده می‌مانند (نه SQLite) چون config در زمان import
# قبل از آماده‌شدن دیتابیس، آن‌ها را می‌خواند.
def _save_admins():
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(ADMIN_IDS, f, ensure_ascii=False)
    except Exception:
        pass


def add_admin(uid):
    """ادمین جدید اضافه می‌کند (لیست زنده را در جای خود تغییر می‌دهد)."""
    uid = int(uid)
    if uid not in ADMIN_IDS:
        ADMIN_IDS.append(uid)
        _save_admins()
        return True
    return False


def remove_admin(uid):
    uid = int(uid)
    if uid == SUPER_ADMIN_ID:
        return False  # سوپرادمین قابل حذف نیست
    if uid in ADMIN_IDS:
        ADMIN_IDS.remove(uid)
        _save_admins()
        # نقش‌های ذخیره‌شده‌ی این ادمین را هم پاک کن
        perms = load_admin_perms()
        if str(uid) in perms:
            perms.pop(str(uid))
            save_admin_perms(perms)
        return True
    return False


# ---- نقش/دسترسی ادمین‌ها ----
# admin_perms.json در SQLite: {"<uid>": ["ads","shop", ...]}
def load_admin_perms():
    return _read_json(ADMIN_PERMS_FILE, dict)


def save_admin_perms(data):
    _write_json(ADMIN_PERMS_FILE, data)


def get_effective_perms(uid):
    """دسترسی‌های مؤثر یک ادمین. اگر رکوردی نداشته باشد → همه‌ی دسترسی‌ها (پیش‌فرض)."""
    uid = str(uid)
    perms = load_admin_perms()
    if uid not in perms:
        return list(ADMIN_PERM_LABELS.keys())
    return perms[uid]


def set_admin_perms(uid, perms_list):
    data = load_admin_perms()
    data[str(uid)] = list(perms_list)
    save_admin_perms(data)


def has_perm(uid, perm):
    """آیا این کاربر اجازه‌ی این بخش را دارد؟ سوپرادمین همیشه بله."""
    uid = int(uid)
    if uid == SUPER_ADMIN_ID:
        return True
    if uid not in ADMIN_IDS:
        return False
    perms = load_admin_perms()
    if str(uid) not in perms:
        return True  # هنوز نقشی تنظیم نشده → دسترسی کامل (سازگاری با ادمین‌های قبلی)
    return perm in perms[str(uid)]
