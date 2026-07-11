# ============================================================
# لایه‌ی ذخیره‌سازی (JSON روی دیسک)
# همه‌ی خواندن/نوشتن‌ها از دو تابع عمومی _read_json / _write_json می‌گذرند.
# ============================================================
import json
import os

from .config import (
    WALLET_FILE, PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE,
    BLACKLIST_FILE, REJECT_COUNTER_FILE, PRICE_REQUEST_FILE, REJECTED_ADS_FILE,
    REFERRAL_FILE, USERS_FILE, SHOP_PRICES_FILE,
)


def _read_json(path, default):
    """خواندن امن JSON؛ در صورت نبود فایل یا خطا، مقدار پیش‌فرض برمی‌گردد."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default() if callable(default) else default


def _write_json(path, data):
    """نوشتن امن JSON."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
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
        if not os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, "w") as f:
                json.dump({"last_id": 0}, f)
            return 0
        with open(COUNTER_FILE, "r") as f:
            data = json.load(f)
            last_id = data.get("last_id", -1) + 1
            data["last_id"] = last_id
        with open(COUNTER_FILE, "w") as f:
            json.dump(data, f)
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
