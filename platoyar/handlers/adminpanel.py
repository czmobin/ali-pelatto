from datetime import datetime, timedelta
import json
import os
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..config import *
from ..state import *
from ..storage import *
from ..services import *

logger = logging.getLogger(__name__)


async def on_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هر وقت وضعیت عضویت خود ربات تغییر کند (مثلاً به گروهی اضافه شود)،
    chat id و عنوان گروه را لاگ و در فایل ثبت می‌کند تا برای تنظیم گروه‌ها استفاده شود."""
    cm = update.my_chat_member
    if not cm:
        return
    chat = cm.chat
    status = cm.new_chat_member.status if cm.new_chat_member else "?"
    line = f"[GROUP-ID] chat_id={chat.id} type={chat.type} status={status} title={chat.title!r}"
    logger.info(line)
    try:
        with open(os.path.join(DATA_FOLDER, "group_ids.txt"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    # اطلاع به ادمین‌ها
    if chat.type in ("group", "supergroup") and status in ("member", "administrator"):
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=aid,
                    text=f"🆔 ربات به گروه اضافه شد:\n<b>{chat.title}</b>\nchat id: <code>{chat.id}</code>",
                    parse_mode="HTML",
                )
            except Exception:
                pass


# ---- ابزارها ----
def _is_admin(update):
    u = update.effective_user
    return bool(u and u.id in ADMIN_IDS)


async def _show(update, text, keyboard=None, parse_mode="HTML"):
    markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=markup, parse_mode=parse_mode)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode=parse_mode)


def _panel_keyboard(update=None):
    rows = [
        [InlineKeyboardButton("📊 آمار", callback_data="ap_stats"),
         InlineKeyboardButton("👥 کاربران اخیر", callback_data="ap_users")],
        [InlineKeyboardButton("🔎 اطلاعات کاربر", callback_data="ap_userinfo"),
         InlineKeyboardButton("🔎 سرچ آگهی", callback_data="ap_adsearch")],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="ap_broadcast"),
         InlineKeyboardButton("✉️ پیام به یک کاربر", callback_data="ap_sendone")],
    ]
    # فقط سوپرادمین دکمه‌های مدیریت ادمین و دیتابیس را می‌بیند
    if update is not None and update.effective_user and update.effective_user.id == SUPER_ADMIN_ID:
        rows.append([InlineKeyboardButton("👮 مدیریت ادمین‌ها", callback_data="ap_admins"),
                     InlineKeyboardButton("🗄 دیتابیس", callback_data="ap_db")])
        rows.append([InlineKeyboardButton("⚙️ تنظیمات (هزینه/کارت/متن)", callback_data="ap_settings")])
    rows.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")])
    return rows


def _back_kb():
    return [[InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")]]


def _clear_ap_flags(context):
    for k in ("ap_waiting_user_id", "ap_waiting_broadcast",
              "ap_waiting_sendone_id", "ap_waiting_sendone_text", "ap_waiting_adsearch",
              "ap_waiting_admin_id", "ap_waiting_setting"):
        context.user_data.pop(k, None)


# ---- منوی پنل ----
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    _clear_ap_flags(context)
    users = load_users()
    text = (
        "🛠 <b>پنل مدیریت پلاتویار</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 کاربران کل: <b>{len(users)}</b>\n"
        "یک بخش را انتخاب کنید:"
    )
    await _show(update, text, _panel_keyboard(update))


# ---- آمار ----
def _count_new_since(users, days):
    """شمارش کاربران جدید در بازه‌ی اخیر بر اساس timestamp عددی (ts)."""
    cutoff = datetime.now().timestamp() - days * 86400
    return sum(1 for rec in users.values() if float(rec.get("ts", 0)) >= cutoff)


async def ap_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    users = load_users()
    profiles = load_profiles()
    agahi = load_agahi()
    pending = load_pending_ads()
    blacklist = load_blacklist()
    text = (
        "📊 <b>آمار ربات</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 کل کاربران: <b>{len(users)}</b>\n"
        f"📝 پروفایل تکمیل‌شده: <b>{len(profiles)}</b>\n"
        f"📢 آگهی منتشرشده: <b>{len(agahi)}</b>\n"
        f"⏳ آگهی در انتظار: <b>{len(pending)}</b>\n"
        f"⛔ لیست سیاه: <b>{len(blacklist)}</b>\n"
        f"🆕 جدید (۷ روز اخیر): <b>{_count_new_since(users, 7)}</b>\n"
        f"🆕 جدید (۲۴ ساعت اخیر): <b>{_count_new_since(users, 1)}</b>"
    )
    await _show(update, text, _back_kb())


# ---- کاربران اخیر ----
async def ap_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    users = load_users()
    # جدیدترین‌ها بر اساس ترتیب درج (آخرین کلیدها) — دیکشنری پایتون ترتیب درج را حفظ می‌کند
    items = list(users.values())[-25:][::-1]
    lines = ["👥 <b>۲۵ کاربر اخیر</b>", "━━━━━━━━━━━━━━━━━━━━",
             "روی نام کاربر بزنید تا پیویش باز شود 👇", ""]
    for rec in items:
        uid = rec.get('id')
        uname = f"@{rec['username']}" if rec.get("username") else "—"
        lines.append(
            f"👤 {user_mention(uid, rec.get('first_name'))} | {uname}\n"
            f"   🆔 <code>{uid}</code> | 📅 {rec.get('first_seen','-')}"
        )
    if len(items) == 0:
        lines.append("هنوز کاربری ثبت نشده.")
    await _show(update, "\n".join(lines), _back_kb())


# ---- اطلاعات کامل یک کاربر ----
async def ap_user_info_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_user_id"] = True
    await _show(update, "🔎 آیدی عددی کاربر را ارسال کنید:", _back_kb())


def _user_info_text(uid):
    uid = str(uid)
    users = load_users()
    profiles = load_profiles()
    agahi = load_agahi()
    rec = users.get(uid, {})
    prof = profiles.get(uid, {})
    bal = get_wallet_balance(uid)
    ref_count = get_referral_count(uid)
    ref_by = get_referred_by(uid)
    blk = "بله ⛔" if int(uid) in load_blacklist() else "خیر ✅"
    my_ads = [aid for aid, ad in agahi.items() if str(ad.get("user_id")) == uid]

    lines = [
        f"👤 <b>اطلاعات کاربر</b> <code>{uid}</code>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"باز کردن پیوی: {user_mention(uid, rec.get('first_name') or 'کاربر')} 👈",
        f"نام تلگرام: {escape_html(rec.get('first_name','-'))}",
        f"یوزرنیم: @{rec['username']}" if rec.get("username") else "یوزرنیم: —",
        f"اولین بازدید: {rec.get('first_seen','-')}",
        f"آخرین بازدید: {rec.get('last_seen','-')}",
        "━━━━━━━━━━━━━━━━━━━━",
        "📝 <b>پروفایل:</b>",
    ]
    if prof:
        lines += [
            f"نام: {escape_html(prof.get('name','-'))}",
            f"موبایل: {escape_html(prof.get('phone','-'))} ({'تایید' if prof.get('phone_verified') else 'تایید نشده'})",
            f"شماره کارت: {escape_html(prof.get('card_number','-'))}",
        ]
        if prof.get("platoid"):
            lines.append(f"آیدی پلاتو: {escape_html(prof.get('platoid'))}")
    else:
        lines.append("پروفایل تکمیل نشده.")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        f"💰 موجودی کیف پول: {bal:,} تومان",
        f"👥 تعداد زیرمجموعه: {ref_count}",
        f"🔗 دعوت‌شده توسط: {ref_by if ref_by else '—'}",
        f"⛔ در لیست سیاه: {blk}",
        f"📢 آگهی‌ها ({len(my_ads)}): {', '.join(map(str, my_ads)) if my_ads else '—'}",
    ]
    return "\n".join(lines)


async def ap_process_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("ap_waiting_user_id", None)
    txt = (update.message.text or "").strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ آیدی نامعتبر. یک عدد بفرست.", reply_markup=InlineKeyboardMarkup(_back_kb()))
        return
    await update.message.reply_text(_user_info_text(txt), parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup(_back_kb()))


# ---- سرچ آگهی با اطلاعات مالک ----
async def ap_adsearch_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_adsearch"] = True
    await _show(update, "🔎 شناسه‌ی آگهی را ارسال کنید:", _back_kb())


async def ap_process_adsearch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("ap_waiting_adsearch", None)
    aid = (update.message.text or "").strip()
    agahi = load_agahi()
    pending = load_pending_ads()
    ad = agahi.get(aid) or pending.get(aid)
    where = "منتشرشده" if aid in agahi else ("در انتظار" if aid in pending else None)
    if not ad:
        await update.message.reply_text("❌ آگهی با این شناسه پیدا نشد.",
                                        reply_markup=InlineKeyboardMarkup(_back_kb()))
        return
    owner = ad.get("user_id")
    lines = [
        f"📢 <b>آگهی {aid}</b> ({where})",
        "━━━━━━━━━━━━━━━━━━━━",
        f"⭐ ویپ: {ad.get('vip_count','-')} | 📊 آیتم: {ad.get('item_count','-')}",
        f"🪙 سکه: {ad.get('coin_count','-')} | 💰 پیپ: {ad.get('pip_count','-')}",
        f"🏆 وین: {ad.get('win_count','-')} | 📅 سن: {ad.get('account_age','-')}",
        f"💵 قیمت: {ad.get('price','-')}",
        f"📝 توضیحات: {escape_html(ad.get('seller_note',''))}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"👤 مالک: <code>{owner}</code>",
    ]
    kb = [[InlineKeyboardButton("👤 اطلاعات کامل مالک", callback_data=f"ap_owner_{owner}")]] + _back_kb()
    await update.message.reply_text("\n".join(lines), parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup(kb))


async def ap_owner_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    uid = update.callback_query.data.split("_")[-1]
    await _show(update, _user_info_text(uid), _back_kb())


# ---- پیام همگانی ----
async def ap_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_broadcast"] = True
    await _show(update, "📢 متن پیام همگانی را ارسال کنید (به همه‌ی کاربران ربات فرستاده می‌شود):", _back_kb())


async def ap_process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("ap_waiting_broadcast", None)
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ فقط متن پشتیبانی می‌شود.", reply_markup=InlineKeyboardMarkup(_back_kb()))
        return
    users = load_users()
    ok = fail = 0
    await update.message.reply_text(f"⏳ در حال ارسال به {len(users)} کاربر...")
    for uid in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            ok += 1
        except Exception:
            fail += 1
    await update.message.reply_text(
        f"✅ پیام همگانی ارسال شد.\nموفق: {ok} | ناموفق: {fail}",
        reply_markup=InlineKeyboardMarkup(_back_kb()),
    )


# ---- پیام به یک کاربر ----
async def ap_sendone_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_sendone_id"] = True
    await _show(update, "✉️ آیدی عددی کاربر مقصد را ارسال کنید:", _back_kb())


async def ap_process_sendone_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ آیدی نامعتبر. یک عدد بفرست.", reply_markup=InlineKeyboardMarkup(_back_kb()))
        return
    context.user_data.pop("ap_waiting_sendone_id", None)
    context.user_data["ap_waiting_sendone_text"] = int(txt)
    await update.message.reply_text(f"✍️ متن پیام برای کاربر <code>{txt}</code> را بفرست:", parse_mode="HTML")


async def ap_process_sendone_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.pop("ap_waiting_sendone_text", None)
    text = update.message.text
    if not target or not text:
        await update.message.reply_text("❌ لغو شد.", reply_markup=InlineKeyboardMarkup(_back_kb()))
        return
    try:
        await context.bot.send_message(chat_id=int(target), text=text)
        await update.message.reply_text(f"✅ پیام به <code>{target}</code> ارسال شد.", parse_mode="HTML",
                                        reply_markup=InlineKeyboardMarkup(_back_kb()))
    except Exception as e:
        await update.message.reply_text(f"❌ ارسال ناموفق: {e}", reply_markup=InlineKeyboardMarkup(_back_kb()))


# ---- مدیریت ادمین‌ها (فقط سوپرادمین) ----
def _is_super(update):
    u = update.effective_user
    return bool(u and u.id == SUPER_ADMIN_ID)


async def ap_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        return
    _clear_ap_flags(context)
    users = load_users()
    lines = ["👮 <b>مدیریت ادمین‌ها</b>", "━━━━━━━━━━━━━━━━━━━━"]
    rows = []
    for aid in ADMIN_IDS:
        rec = users.get(str(aid), {})
        uname = f"@{rec['username']}" if rec.get("username") else ""
        tag = " (سوپرادمین)" if aid == SUPER_ADMIN_ID else ""
        lines.append(f"🆔 <code>{aid}</code> {escape_html(rec.get('first_name',''))} {uname}{tag}")
        if aid != SUPER_ADMIN_ID:
            rows.append([InlineKeyboardButton(f"❌ حذف {aid}", callback_data=f"ap_admindel_{aid}")])
    rows.append([InlineKeyboardButton("➕ افزودن ادمین", callback_data="ap_adminadd")])
    rows.append([InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")])
    await _show(update, "\n".join(lines), rows)


async def ap_admin_add_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_admin_id"] = True
    await _show(update, "➕ آیدی عددی ادمین جدید را ارسال کنید:",
                [[InlineKeyboardButton("🔙 مدیریت ادمین‌ها", callback_data="ap_admins")]])


async def ap_process_admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("ap_waiting_admin_id", None)
    if update.effective_user.id != SUPER_ADMIN_ID:
        return
    txt = (update.message.text or "").strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ آیدی نامعتبر. یک عدد بفرست.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 مدیریت ادمین‌ها", callback_data="ap_admins")]]))
        return
    added = add_admin(int(txt))
    msg = f"✅ ادمین <code>{txt}</code> اضافه شد." if added else f"ℹ️ <code>{txt}</code> از قبل ادمین بود."
    await update.message.reply_text(msg, parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 مدیریت ادمین‌ها", callback_data="ap_admins")]]))
    try:
        await context.bot.send_message(chat_id=int(txt), text="✅ شما به‌عنوان ادمین ربات پلاتویار اضافه شدید.")
    except Exception:
        pass


async def ap_admin_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        await update.callback_query.answer()
        return
    uid = int(update.callback_query.data.split("_")[-1])
    remove_admin(uid)
    await update.callback_query.answer("حذف شد")
    await ap_admins(update, context)


# ---- دسترسی کامل به دیتابیس (فقط سوپرادمین) ----
async def ap_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        return
    from ..db import kv_keys, kv_get
    keys = kv_keys()
    lines = ["🗄 <b>دیتابیس (SQLite)</b>", "━━━━━━━━━━━━━━━━━━━━"]
    rows = []
    for k in keys:
        raw = kv_get(k)
        try:
            obj = json.loads(raw) if raw else None
            cnt = len(obj) if hasattr(obj, "__len__") else "-"
        except Exception:
            cnt = "?"
        lines.append(f"• <code>{k}</code> : {cnt}")
        rows.append([InlineKeyboardButton(f"👁 {k}", callback_data=f"ap_dbview_{k}")])
    if not keys:
        lines.append("خالی است.")
    rows.append([InlineKeyboardButton("📥 دانلود فایل کامل دیتابیس", callback_data="ap_dbdownload")])
    rows.append([InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")])
    await _show(update, "\n".join(lines), rows)


async def ap_db_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        await update.callback_query.answer()
        return
    from ..db import kv_get
    await update.callback_query.answer()
    key = update.callback_query.data[len("ap_dbview_"):]
    raw = kv_get(key)
    if raw is None:
        await update.callback_query.message.reply_text("خالی است.")
        return
    try:
        raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
    except Exception:
        pass
    if len(raw) <= 3500:
        await update.callback_query.message.reply_text(
            f"🗄 <b>{key}</b>\n<pre>{escape_html(raw)}</pre>", parse_mode="HTML")
    else:
        import io
        bio = io.BytesIO(raw.encode("utf-8"))
        bio.name = key
        await context.bot.send_document(chat_id=update.effective_user.id, document=bio,
                                        filename=key, caption=f"🗄 {key}")


async def ap_db_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        await update.callback_query.answer()
        return
    from ..db import DB_PATH, get_conn
    await update.callback_query.answer("در حال ارسال فایل دیتابیس...")
    try:
        get_conn().commit()
        with open(DB_PATH, "rb") as f:
            await context.bot.send_document(chat_id=update.effective_user.id, document=f,
                                            filename="platoyar.sqlite",
                                            caption="🗄 فایل کامل دیتابیس (SQLite)")
    except Exception as e:
        await update.callback_query.message.reply_text(f"❌ خطا در ارسال فایل: {e}")


# ---- تنظیمات قابل‌ویرایش (فقط سوپرادمین) ----
# (key, label, type, default)  type: int | text | longtext
_SETTINGS_DEFS = [
    ("fee_admin", "💰 هزینه تعیین قیمت توسط ادمین", "int", PRICE_ADMIN_PRICE),
    ("fee_game", "💰 هزینه انتشار در کانال بازی", "int", PRICE_CHANNEL_GAME),
    ("fee_both", "💰 هزینه انتشار در هر دو کانال", "int", PRICE_CHANNEL_BOTH),
    ("min_withdraw", "💸 حداقل مبلغ برداشت", "int", MIN_WITHDRAW_AMOUNT),
    ("card_number", "🏦 شماره کارت", "text", CARD_NUMBER),
    ("card_name", "👤 نام صاحب کارت", "text", CARD_NAME),
    ("welcome_text", "📝 متن خوش‌آمد منوی اصلی", "longtext", None),
]
_SETTINGS_BY_KEY = {d[0]: d for d in _SETTINGS_DEFS}


async def ap_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        return
    _clear_ap_flags(context)
    lines = ["⚙️ <b>تنظیمات</b>", "━━━━━━━━━━━━━━━━━━━━", "روی هر مورد بزنید تا تغییرش دهید:", ""]
    rows = []
    for key, label, typ, default in _SETTINGS_DEFS:
        cur = get_setting(key, default)
        if typ == "int":
            disp = f"{int(cur):,} تومان" if cur is not None else "-"
        elif typ == "longtext":
            disp = "✅ سفارشی" if get_setting(key) else "پیش‌فرض"
        else:
            disp = escape_html(str(cur)) if cur is not None else "-"
        lines.append(f"{label}: <b>{disp}</b>")
        rows.append([InlineKeyboardButton(f"✏️ {label}", callback_data=f"ap_setedit_{key}")])
    rows.append([InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")])
    await _show(update, "\n".join(lines), rows)


async def ap_setting_edit_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_super(update):
        await update.callback_query.answer()
        return
    key = update.callback_query.data[len("ap_setedit_"):]
    d = _SETTINGS_BY_KEY.get(key)
    if not d:
        await update.callback_query.answer()
        return
    _clear_ap_flags(context)
    context.user_data["ap_waiting_setting"] = key
    label, typ, default = d[1], d[2], d[3]
    cur = get_setting(key, default)
    if typ == "int":
        hint = "مقدار جدید را به تومان (فقط عدد) بفرستید:"
        curline = f"مقدار فعلی: {int(cur):,} تومان" if cur is not None else ""
    elif typ == "longtext":
        hint = ("متن جدید را بفرستید. می‌توانید از <code>{name}</code> (نام کاربر) و "
                "<code>{SIGNATURE}</code> (امضا) استفاده کنید.\nبرای بازگشت به پیش‌فرض، «-» بفرستید.")
        curline = ""
    else:
        hint = "مقدار جدید را بفرستید. برای بازگشت به پیش‌فرض «-» بفرستید:"
        curline = f"مقدار فعلی: {escape_html(str(cur))}" if cur is not None else ""
    await _show(update, f"✏️ <b>{label}</b>\n{curline}\n\n{hint}",
                [[InlineKeyboardButton("🔙 تنظیمات", callback_data="ap_settings")]])


async def ap_process_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = context.user_data.pop("ap_waiting_setting", None)
    if not key:
        return
    d = _SETTINGS_BY_KEY.get(key)
    if not d:
        return
    typ = d[2]
    text = (update.message.text or "").strip()
    prices = load_settings()
    if typ == "int":
        raw = text.replace(",", "").replace("،", "")
        if not raw.isdigit():
            await update.message.reply_text("❌ مقدار نامعتبر. فقط عدد بفرست.")
            context.user_data["ap_waiting_setting"] = key
            return
        set_setting(key, int(raw))
        await update.message.reply_text(f"✅ «{d[1]}» روی {int(raw):,} تومان تنظیم شد.",
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="ap_settings")]]))
    else:
        if text == "-":
            s = load_settings()
            s.pop(key, None)
            save_settings(s)
            await update.message.reply_text(f"✅ «{d[1]}» به حالت پیش‌فرض برگشت.",
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="ap_settings")]]))
        else:
            set_setting(key, text)
            await update.message.reply_text(f"✅ «{d[1]}» ذخیره شد.",
                                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 تنظیمات", callback_data="ap_settings")]]))
