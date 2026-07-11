"""فروشگاه پلاتویار — منوی داده‌محور با قیمت قابل‌ویرایش توسط ادمین."""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..config import *
from ..state import *
from ..storage import *
from ..services import *

logger = logging.getLogger(__name__)


# ============================================================
# درخت منو
# ============================================================
def _leaf(label, kind="order"):
    return {"label": label, "kind": kind}


def _cat(label, children):
    return {"label": label, "children": children}


_COIN_ITEMS = ["500", "750", "1k", "1.5k", "2k", "3k", "4k", "5k", "6k", "7k",
               "8k", "9k", "10k", "15k", "20k", "30k", "40k", "100k"]
_PIP = ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "120",
        "150", "200", "250", "300", "500", "700", "1000", "2000"]
_COIN_CHARGE = ["1", "2", "3", "5", "6", "10", "15", "20", "50", "100", "200"]
_GIFT = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "15", "20", "22",
         "25", "30", "50", "60", "100", "200"]
_WIN = ["1k", "2k", "3k", "4k", "5k", "6k", "7k", "8k", "9k", "10k", "15k"]
_HALE = ["1k", "2k", "3k", "4k", "5k", "6k", "7k", "8k", "9k", "10k", "15k",
         "20k", "50k", "100k"]
_HYPE = ["100", "1000", "7500", "20000", "100000", "250000", "1000000", "2000000"]
_STARS = ["50", "100", "150", "200", "300", "500", "700", "1000000"]
_PREM = ["۱ ماهه", "۳ ماهه", "۶ ماهه", "۱ ساله"]

_PLATO = _cat("🎮 پلاتو", [
    _cat("🛍 آیتم‌های شاپ پلاتو", [_leaf(f"آیتم {x} سکه‌ای") for x in _COIN_ITEMS]),
    _cat("💎 آیتم‌های کمیاب پلاتو", [_leaf(f"آیتم کمیاب {x} سکه‌ای") for x in _COIN_ITEMS]),
    _cat("🔋 شارژ پیپ و سکه", [
        _cat("💠 شارژ پیپ", [_leaf(f"شارژ {x} پیپ") for x in _PIP]),
        _cat("🪙 شارژ سکه", [_leaf(f"شارژ {x} کا سکه") for x in _COIN_CHARGE]),
    ]),
    _cat("🎁 گیفت آیتم پیپی", [_leaf(f"گیفت آیتم {x} پیپی", kind="gift") for x in _GIFT]),
    _cat("🏆 وین (برد) فیک", [_leaf(f"وین فیک {x}") for x in _WIN]),
    _leaf("🎉 آفر استارتر پک (۵۰k سکه + ۱k هایپ + استیکر)"),
    _leaf("⭐ سفارش گلد کردن رنک", kind="rank"),
    _cat("🔥 هاله (آتیش)", [_leaf(f"هاله {x}") for x in _HALE]),
    _cat("🚀 هایپ", [_leaf(f"هایپ {x} تایی") for x in _HYPE]),
])

_PREMIUM = _cat("⭐ پرمیوم تلگرام", [
    _cat("🔗 پرمیوم لینکی", [_leaf(f"پرمیوم لینکی {d}", kind="digital") for d in _PREM]),
    _cat("🎁 پرمیوم گیفتی", [_leaf(f"پرمیوم گیفتی {d}", kind="digital") for d in _PREM]),
])

_ROOT_SPEC = _cat("🛒 فروشگاه پلاتویار", [
    _PLATO,
    _leaf("🔫 کالاف دیوتی", kind="soon"),
    _PREMIUM,
    _cat("✨ استارز تلگرام", [_leaf(f"{x} استارز", kind="digital") for x in _STARS]),
    _leaf("📱 شماره مجازی آمریکا و کانادا (جفت)", kind="digital"),
])

NODES = {}


def _flatten(spec, parent_id):
    nid = f"n{len(NODES)}"
    NODES[nid] = {"label": spec["label"], "parent": parent_id,
                  "children": [], "kind": spec.get("kind")}
    for child in spec.get("children") or []:
        cid = _flatten(child, nid)
        NODES[nid]["children"].append(cid)
    return nid


ROOT = _flatten(_ROOT_SPEC, None)


# ============================================================
# ابزارها
# ============================================================
def _is_admin(update):
    u = update.effective_user
    return bool(u and u.id in ADMIN_IDS)


def _price(nid):
    p = load_shop_prices().get(nid)
    try:
        return int(p) if p is not None else None
    except (TypeError, ValueError):
        return None


def _leaf_ids(nid):
    node = NODES[nid]
    if not node["children"]:
        return [nid]
    out = []
    for c in node["children"]:
        out += _leaf_ids(c)
    return out


def _back_row(node):
    parent = node["parent"]
    return [InlineKeyboardButton("🔙 بازگشت", callback_data=f"shop:{parent}" if parent else "back_to_main")]


def _cat_kb(node_id, is_admin=False):
    node = NODES[node_id]
    rows = []
    kids = node["children"]
    for i in range(0, len(kids), 2):
        rows.append([InlineKeyboardButton(NODES[c]["label"], callback_data=f"shop:{c}")
                     for c in kids[i:i + 2]])
    if is_admin and kids:
        rows.append([InlineKeyboardButton("📈 افزایش گروهی قیمت", callback_data=f"shopbulk:{node_id}")])
    rows.append(_back_row(node))
    return InlineKeyboardMarkup(rows)


def _clear_shop_flags(context):
    for k in ("shop_gift", "shop_rank", "shop_dig", "shop_setprice", "shop_bulk"):
        context.user_data.pop(k, None)


# ============================================================
# نمایش
# ============================================================
async def shop_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _clear_shop_flags(context)
    await query.message.edit_text("🛒 <b>فروشگاه پلاتویار</b>\n\nیک بخش را انتخاب کنید:",
                                  reply_markup=_cat_kb(ROOT, _is_admin(update)), parse_mode="HTML")


async def shop_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    adm = _is_admin(update)

    if node["children"]:
        await query.message.edit_text(f"<b>{node['label']}</b>\n\nیک گزینه را انتخاب کنید:",
                                      reply_markup=_cat_kb(nid, adm), parse_mode="HTML")
        return

    kind = node.get("kind")
    if kind == "soon":
        await query.message.edit_text("🚧 این بخش به‌زودی اضافه می‌شود.",
                                      reply_markup=InlineKeyboardMarkup([_back_row(node)]))
        return

    price = _price(nid)
    price_line = f"💵 قیمت: <b>{price:,}</b> تومان" if price else "💵 قیمت: با ادمین هماهنگ می‌شود"
    text = f"📦 <b>{node['label']}</b>\n\n{price_line}"

    rows = []
    if kind == "digital":
        rows.append([InlineKeyboardButton("🛒 خرید", callback_data=f"shopbuy:{nid}", style="success")])
    elif kind == "gift":
        rows.append([InlineKeyboardButton("🛒 ثبت سفارش (ارسال عکس آیتم)", callback_data=f"shopgift:{nid}", style="success")])
    elif kind == "rank":
        rows.append([InlineKeyboardButton("🛒 ثبت سفارش", callback_data=f"shoprank:{nid}", style="success")])
    else:
        rows.append([InlineKeyboardButton("✅ ثبت سفارش", callback_data=f"shopok:{nid}", style="success")])
    if adm:
        rows.append([InlineKeyboardButton("✏️ تغییر قیمت", callback_data=f"shopprice:{nid}", style="primary")])
    rows.append(_back_row(node))
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")


# ============================================================
# سفارش ساده (قیمت‌گذاری دستی)
# ============================================================
async def _send_order(context, user, item_label, extra=None, photo=None):
    uname = f"@{user.username}" if user.username else "—"
    caption = (f"🛒 <b>سفارش جدید فروشگاه</b>\n\n"
               f"📦 {escape_html(item_label)}\n"
               f"👤 {escape_html(user.first_name or '')} ({uname})\n"
               f"🆔 <code>{user.id}</code>")
    if extra:
        caption += f"\n\n{extra}"
    if photo:
        await broadcast_to_admins(context, photo=photo, caption=caption, parse_mode="HTML")
    else:
        await broadcast_to_admins(context, text=caption, parse_mode="HTML")


async def shop_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    price = _price(nid)
    extra = f"💵 قیمت: {price:,} تومان" if price else None
    await _send_order(context, query.from_user, node["label"], extra=extra)
    await query.message.edit_text(
        f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n\nادمین به‌زودی قیمت و مراحل بعدی را اعلام می‌کند.\n{SIGNATURE}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]]))


async def shop_gift_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    _clear_shop_flags(context)
    context.user_data["shop_gift"] = node["label"]
    await query.message.edit_text(
        f"📦 <b>{node['label']}</b>\n\n📸 لطفاً عکس آیتم موردنظر را ارسال کنید تا سفارش ثبت شود.",
        reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_rank_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    _clear_shop_flags(context)
    context.user_data["shop_rank"] = node["label"]
    await query.message.edit_text(
        f"📦 <b>{node['label']}</b>\n\nلطفاً «لینک دوستی، آیدی و جیمیل» خود را در یک پیام ارسال کنید.",
        reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_receive_gift_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = context.user_data.get("shop_gift")
    if not label:
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک عکس از آیتم ارسال کنید.")
        return
    photo = update.message.photo[-1].file_id
    context.user_data.pop("shop_gift", None)
    await _send_order(context, update.effective_user, label, photo=photo)
    await update.message.reply_text(
        f"✅ سفارش گیفت شما با عکس ثبت شد:\n📦 {label}\n\nادمین به‌زودی قیمت را اعلام می‌کند.\n{SIGNATURE}")


async def shop_receive_rank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = context.user_data.get("shop_rank")
    if not label:
        return
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ لطفاً اطلاعات را به‌صورت متن (لینک دوستی، آیدی و جیمیل) بفرستید.")
        return
    context.user_data.pop("shop_rank", None)
    await _send_order(context, update.effective_user, label, extra=f"📝 اطلاعات مشتری:\n{escape_html(text)}")
    await update.message.reply_text(
        f"✅ سفارش شما ثبت شد:\n📦 {label}\n\nادمین به‌زودی قیمت و مراحل بعدی را اعلام می‌کند.\n{SIGNATURE}")


# ============================================================
# جریان دیجیتال (استارز/پرمیوم/شماره مجازی): آیدی مقصد → قیمت → پرداخت
# ============================================================
async def shop_buy_digital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    _clear_shop_flags(context)
    context.user_data["shop_dig"] = {"nid": nid, "stage": "target"}
    await query.message.edit_text(
        f"📦 <b>{node['label']}</b>\n\n"
        "👤 لطفاً <b>آیدی تلگرام مقصد</b> (یوزرنیم مثل <code>@name</code> یا آیدی عددی) که این سفارش برای آن است را ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_digital_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dig = context.user_data.get("shop_dig")
    if not dig:
        return
    node = NODES.get(dig["nid"])
    if not node:
        context.user_data.pop("shop_dig", None)
        return

    if dig.get("stage") == "receipt":
        if not update.message.photo:
            await update.message.reply_text("❌ لطفاً تصویر رسید پرداخت را ارسال کنید.")
            return
        photo = update.message.photo[-1].file_id
        price = _price(dig["nid"])
        target = dig.get("target", "-")
        context.user_data.pop("shop_dig", None)
        extra = f"🎯 آیدی مقصد: {escape_html(target)}"
        if price:
            extra += f"\n💵 مبلغ: {price:,} تومان"
        await _send_order(context, update.effective_user, node["label"], extra=extra, photo=photo)
        await update.message.reply_text(
            f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n🎯 مقصد: {target}\n\n"
            f"پس از بررسی رسید، سفارش شما انجام می‌شود.\n{SIGNATURE}")
        return

    # مرحله‌ی گرفتن آیدی مقصد
    target = (update.message.text or "").strip()
    if not target:
        await update.message.reply_text("❌ لطفاً آیدی مقصد را به‌صورت متن بفرستید.")
        return
    dig["target"] = target
    price = _price(dig["nid"])

    if not price:
        # قیمت تعیین نشده → سفارش برای هماهنگی به ادمین می‌رود
        context.user_data.pop("shop_dig", None)
        await _send_order(context, update.effective_user, node["label"],
                          extra=f"🎯 آیدی مقصد: {escape_html(target)}\n💵 قیمت: تعیین نشده (نیاز به اعلام ادمین)")
        await update.message.reply_text(
            f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n🎯 مقصد: {target}\n\n"
            f"قیمت این مورد هنوز ثبت نشده؛ ادمین به‌زودی مبلغ را به شما اعلام می‌کند.\n{SIGNATURE}")
        return

    dig["stage"] = "receipt"
    pay_text = (f"📦 <b>{node['label']}</b>\n"
                f"🎯 مقصد: {escape_html(target)}\n"
                f"💵 مبلغ قابل پرداخت: <b>{price:,}</b> تومان\n\n"
                f"🏦 <b>شماره کارت برای واریز:</b>\n<code>{CARD_NUMBER}</code>\n👤 {CARD_NAME}\n\n"
                f"📝 مبلغ بالا را واریز کنید و سپس تصویر رسید را همین‌جا ارسال کنید.\n{SIGNATURE}")
    await update.message.reply_text(pay_text, parse_mode="HTML")


# ============================================================
# مدیریت قیمت توسط ادمین (تکی + گروهی)
# ============================================================
async def shop_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_admin(update):
        return
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    _clear_shop_flags(context)
    context.user_data["shop_setprice"] = nid
    cur = _price(nid)
    cur_line = f"قیمت فعلی: {cur:,} تومان\n" if cur else "قیمت فعلی: تعیین نشده\n"
    await query.message.edit_text(
        f"✏️ <b>تغییر قیمت</b>\n📦 {node['label']}\n{cur_line}\n"
        "مبلغ جدید را به تومان بفرستید (فقط عدد). برای حذف قیمت، عدد <code>0</code> بفرستید.",
        reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_receive_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nid = context.user_data.get("shop_setprice")
    if not nid:
        return
    node = NODES.get(nid)
    raw = (update.message.text or "").replace(",", "").replace("،", "").strip()
    if not raw.isdigit():
        await update.message.reply_text("❌ مبلغ نامعتبر. فقط عدد بفرست.")
        return
    context.user_data.pop("shop_setprice", None)
    prices = load_shop_prices()
    val = int(raw)
    if val <= 0:
        prices.pop(nid, None)
        save_shop_prices(prices)
        await update.message.reply_text(f"✅ قیمت «{node['label']}» حذف شد.")
    else:
        prices[nid] = val
        save_shop_prices(prices)
        await update.message.reply_text(f"✅ قیمت «{node['label']}» روی {val:,} تومان تنظیم شد.")


async def shop_bulk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _is_admin(update):
        return
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    _clear_shop_flags(context)
    context.user_data["shop_bulk"] = nid
    await query.message.edit_text(
        f"📈 <b>افزایش گروهی قیمت</b>\n📂 {node['label']}\n\n"
        "میزان افزایش را بفرستید:\n"
        "• درصدی: مثل <code>10%</code> (۱۰٪ به همه‌ی قیمت‌های این بخش اضافه می‌شود)\n"
        "• مبلغی: مثل <code>5000</code> (۵۰۰۰ تومان به همه اضافه می‌شود)\n\n"
        "توجه: فقط روی آیتم‌هایی که قیمت دارند اعمال می‌شود.",
        reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_receive_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nid = context.user_data.get("shop_bulk")
    if not nid:
        return
    node = NODES.get(nid)
    raw = (update.message.text or "").replace(",", "").replace("،", "").strip()
    is_percent = raw.endswith("%")
    num = raw[:-1].strip() if is_percent else raw
    try:
        amount = float(num)
    except ValueError:
        await update.message.reply_text("❌ نامعتبر. مثل «10%» یا «5000» بفرست.")
        return
    context.user_data.pop("shop_bulk", None)

    prices = load_shop_prices()
    changed = 0
    for leaf_id in _leaf_ids(nid):
        cur = prices.get(leaf_id)
        try:
            cur = int(cur)
        except (TypeError, ValueError):
            continue
        new = round(cur * (1 + amount / 100)) if is_percent else round(cur + amount)
        new = max(0, int(new))
        prices[leaf_id] = new
        changed += 1
    save_shop_prices(prices)
    how = f"{amount}٪" if is_percent else f"{int(amount):,} تومان"
    await update.message.reply_text(
        f"✅ افزایش {how} روی {changed} آیتمِ دارای قیمت در «{node['label']}» اعمال شد.")
