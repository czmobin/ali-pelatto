from datetime import datetime, timedelta
import random
import logging

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import *
from .state import *
from .storage import *

logger = logging.getLogger(__name__)


async def broadcast_to_admins(context, *, text=None, photo=None, video=None, caption=None, reply_markup=None, parse_mode=None):
    """ارسال یک پیام/عکس/ویدیو به همه‌ی ادمین‌ها. خروجی: دیکشنری {admin_id: message_id}."""
    msg_ids = {}
    for admin_id in ADMIN_IDS:
        try:
            if photo is not None:
                sent = await context.bot.send_photo(chat_id=admin_id, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
            elif video is not None:
                sent = await context.bot.send_video(chat_id=admin_id, video=video, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
            else:
                sent = await context.bot.send_message(chat_id=admin_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
            msg_ids[admin_id] = sent.message_id
        except Exception as e:
            logger.error(f"ارسال به ادمین {admin_id} ناموفق بود: {e}")
    return msg_ids


async def send_to_target(context, target_chat, *, text=None, photo=None, video=None, caption=None, reply_markup=None, parse_mode=None):
    """ارسال سفارش به یک گروه مقصد. اگر target_chat تنظیم نشده باشد،
    به رفتار قبلی (ارسال به پیوی همه‌ی ادمین‌ها) برمی‌گردد.
    خروجی همیشه دیکشنری {chat_id: message_id} است تا با delete_admin_messages سازگار بماند."""
    if not target_chat:
        return await broadcast_to_admins(
            context, text=text, photo=photo, video=video, caption=caption,
            reply_markup=reply_markup, parse_mode=parse_mode,
        )
    try:
        if photo is not None:
            sent = await context.bot.send_photo(chat_id=target_chat, photo=photo, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
        elif video is not None:
            sent = await context.bot.send_video(chat_id=target_chat, video=video, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            sent = await context.bot.send_message(chat_id=target_chat, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        return {target_chat: sent.message_id}
    except Exception as e:
        logger.error(f"ارسال به گروه {target_chat} ناموفق بود: {e}؛ ارسال به پیوی ادمین‌ها.")
        return await broadcast_to_admins(
            context, text=text, photo=photo, video=video, caption=caption,
            reply_markup=reply_markup, parse_mode=parse_mode,
        )


def user_mention(user_id, name):
    """لینک کلیک‌شونده به پیوی کاربر (حتی بدون یوزرنیم)."""
    return f'<a href="tg://user?id={user_id}">{escape_html(name or "کاربر")}</a>'


async def send_album_to_target(context, target_chat, media):
    """ارسال آلبوم عکس/فیلم به گروه مقصد (یا پیوی ادمین‌ها اگر مقصد تنظیم نشده)."""
    if not media:
        return
    targets = [target_chat] if target_chat else list(ADMIN_IDS)
    for t in targets:
        try:
            await context.bot.send_media_group(chat_id=t, media=media)
        except Exception as e:
            logger.error(f"ارسال آلبوم به {t} ناموفق: {e}")


async def delete_admin_messages(context, msg_ids):
    """حذف پیام‌های ارسال‌شده به ادمین‌ها. msg_ids می‌تواند دیکشنری {admin_id: message_id} یا یک message_id قدیمی باشد."""
    if not msg_ids:
        return
    if not isinstance(msg_ids, dict):
        msg_ids = {ADMIN_ID: msg_ids}
    for admin_id, message_id in msg_ids.items():
        try:
            await context.bot.delete_message(chat_id=admin_id, message_id=message_id)
        except Exception:
            pass


def now_jalali():
    try:
        from jdatetime import datetime as jdatetime
        return jdatetime.now().strftime("%Y/%m/%d - %H:%M:%S")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")


def register_user(tg_user):
    """کاربر را در users.json ثبت/به‌روزرسانی می‌کند (اولین بازدید، آخرین بازدید، یوزرنیم)."""
    if tg_user is None:
        return
    users = load_users()
    uid = str(tg_user.id)
    now = now_jalali()
    ts = datetime.now().timestamp()
    rec = users.get(uid)
    if rec is None:
        users[uid] = {
            "id": tg_user.id,
            "first_name": tg_user.first_name or "",
            "username": tg_user.username or "",
            "first_seen": now,
            "last_seen": now,
            "ts": ts,          # timestamp عددی برای محاسبه‌ی آمار (مستقل از شمسی/میلادی)
        }
    else:
        rec["first_name"] = tg_user.first_name or rec.get("first_name", "")
        rec["username"] = tg_user.username or rec.get("username", "")
        rec["last_seen"] = now
        rec.setdefault("ts", ts)
    save_users(users)


def generate_otp():
    return str(random.randint(1000, 9999))


def send_sms_via_kavenegar(phone_number, token, token2, template):
    try:
        url = f"https://api.kavenegar.com/v1/{KAVENEGAR_API_KEY}/verify/lookup.json"
        payload = {
            'receptor': phone_number,
            'token': str(token),
            'token2': str(token2) if token2 else "",
            'template': template
        }
        response = requests.get(url, params=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('return', {}).get('status') == 200:
                return True
        return False
    except:
        return False


def send_otp_via_kavenegar(phone_number, otp_code):
    try:
        url = f"https://api.kavenegar.com/v1/{KAVENEGAR_API_KEY}/verify/lookup.json"
        payload = {
            'receptor': phone_number,
            'token': otp_code,
            'template': KAVENEGAR_TEMPLATE_VERIFY
        }
        response = requests.get(url, params=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('return', {}).get('status') == 200:
                return True, "کد ارسال شد"
        return False, "خطا"
    except:
        return False, "خطا"


def is_profile_complete(user_id):
    profiles = load_profiles()
    user_profile = profiles.get(str(user_id))
    if not user_profile:
        return False
    required_fields = ['name', 'phone', 'phone_verified', 'card_number']
    for field in required_fields:
        if field not in user_profile or not user_profile[field]:
            return False
    return True


def is_blacklisted(user_id):
    blacklist = load_blacklist()
    return user_id in blacklist


def is_ad_active(ad):
    return ad.get('published', False) and ad.get('status') == 'published'


async def check_membership(user_id, context):
    channels = [
        {"id": MAIN_CHANNEL_ID, "link": MAIN_CHANNEL_LINK, "name": "اصلی"},
        {"id": GAME_CHANNEL_ID, "link": GAME_CHANNEL_LINK, "name": "بازی"},
        {"id": NEW_CHANNEL_ID, "link": NEW_CHANNEL_LINK, "name": "جدید"}
    ]
    not_member = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_member.append(ch)
        except:
            not_member.append(ch)
    return len(not_member) == 0, not_member


async def membership_buttons(user_id, context):
    channels = [
        {"id": MAIN_CHANNEL_ID, "link": MAIN_CHANNEL_LINK, "name": "چنل فروشگاهی"},
        {"id": GAME_CHANNEL_ID, "link": GAME_CHANNEL_LINK, "name": "چنل اگهی اکانت پلاتو"},
        {"id": NEW_CHANNEL_ID, "link": NEW_CHANNEL_LINK, "name": "چنل پابجی و کالاف"}
    ]
    keyboard = []
    for ch in channels:
        keyboard.append([InlineKeyboardButton(f"📢 عضویت در کانال {ch['name']}", url=ch["link"], style="primary")])
    keyboard.append([InlineKeyboardButton("✅ بررسی مجدد", callback_data="check_membership", style="success")])
    return InlineKeyboardMarkup(keyboard)
