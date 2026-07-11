"""فروشگاه پلاتویار — منوی داده‌محور با قیمت‌گذاری دستی توسط ادمین."""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..config import *
from ..state import *
from ..storage import *
from ..services import *

logger = logging.getLogger(__name__)


# ============================================================
# ساخت درخت منو
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
    _cat("🔗 پرمیوم لینکی", [_leaf(f"پرمیوم لینکی {d}") for d in _PREM]),
    _cat("🎁 پرمیوم گیفتی", [_leaf(f"پرمیوم گیفتی {d}") for d in _PREM]),
])

_ROOT_SPEC = _cat("🛒 فروشگاه پلاتویار", [
    _PLATO,
    _leaf("🔫 کالاف دیوتی", kind="soon"),
    _PREMIUM,
    _cat("✨ استارز تلگرام", [_leaf(f"{x} استارز") for x in _STARS]),
    _leaf("📱 شماره مجازی آمریکا و کانادا (جفت)"),
])

# مسطح‌سازی درخت به دیکشنری {id: node}
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
# نمایش
# ============================================================
def _kb(node_id):
    node = NODES[node_id]
    rows = []
    kids = node["children"]
    for i in range(0, len(kids), 2):
        row = [InlineKeyboardButton(NODES[cid]["label"], callback_data=f"shop:{cid}")
               for cid in kids[i:i + 2]]
        rows.append(row)
    parent = node["parent"]
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"shop:{parent}" if parent else "back_to_main")])
    return InlineKeyboardMarkup(rows)


async def shop_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "🛒 <b>فروشگاه پلاتویار</b>\n\nیک بخش را انتخاب کنید:"
    await query.message.edit_text(text, reply_markup=_kb(ROOT), parse_mode="HTML")


async def shop_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return

    if node["children"]:
        await query.message.edit_text(f"<b>{node['label']}</b>\n\nیک گزینه را انتخاب کنید:",
                                      reply_markup=_kb(nid), parse_mode="HTML")
        return

    kind = node.get("kind")
    parent = node["parent"]
    back = [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"shop:{parent}" if parent else "back_to_main")]]

    if kind == "soon":
        await query.message.edit_text("🚧 این بخش به‌زودی اضافه می‌شود.",
                                      reply_markup=InlineKeyboardMarkup(back))
    elif kind == "gift":
        context.user_data['shop_gift'] = node['label']
        await query.message.edit_text(
            f"📦 <b>{node['label']}</b>\n\n📸 لطفاً عکس آیتم موردنظر را ارسال کنید تا سفارش ثبت شود.",
            reply_markup=InlineKeyboardMarkup(back), parse_mode="HTML")
    elif kind == "rank":
        context.user_data['shop_rank'] = node['label']
        await query.message.edit_text(
            f"📦 <b>{node['label']}</b>\n\nلطفاً «لینک دوستی، آیدی و جیمیل» خود را در یک پیام ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(back), parse_mode="HTML")
    else:  # order
        kb = [[InlineKeyboardButton("✅ ثبت سفارش", callback_data=f"shopok:{nid}", style="success")]] + back
        await query.message.edit_text(
            f"📦 <b>{node['label']}</b>\n\nبرای ثبت این سفارش دکمه‌ی زیر را بزنید.\n"
            f"قیمت و مراحل بعدی توسط ادمین به شما اعلام می‌شود.",
            reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")


async def shop_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    await _send_order(context, query.from_user, node['label'])
    await query.message.edit_text(
        f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n\n"
        f"ادمین به‌زودی قیمت و مراحل بعدی را به شما اعلام می‌کند.\n{SIGNATURE}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]]))


# ============================================================
# ثبت سفارش (ارسال به ادمین‌ها)
# ============================================================
async def _send_order(context, user, item_label, extra=None, photo=None):
    uname = f"@{user.username}" if user.username else "—"
    caption = (f"🛒 <b>سفارش جدید فروشگاه</b>\n\n"
               f"📦 {escape_html(item_label)}\n"
               f"👤 {escape_html(user.first_name or '')} ({uname})\n"
               f"🆔 <code>{user.id}</code>")
    if extra:
        caption += f"\n\n📝 اطلاعات مشتری:\n{escape_html(extra)}"
    if photo:
        await broadcast_to_admins(context, photo=photo, caption=caption, parse_mode="HTML")
    else:
        await broadcast_to_admins(context, text=caption, parse_mode="HTML")


async def shop_receive_gift_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = context.user_data.get('shop_gift')
    if not label:
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک عکس از آیتم ارسال کنید.")
        return
    photo = update.message.photo[-1].file_id
    context.user_data.pop('shop_gift', None)
    await _send_order(context, update.effective_user, label, photo=photo)
    await update.message.reply_text(
        f"✅ سفارش گیفت شما با عکس ثبت شد:\n📦 {label}\n\nادمین به‌زودی قیمت را اعلام می‌کند.\n{SIGNATURE}")


async def shop_receive_rank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    label = context.user_data.get('shop_rank')
    if not label:
        return
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ لطفاً اطلاعات را به‌صورت متن (لینک دوستی، آیدی و جیمیل) بفرستید.")
        return
    context.user_data.pop('shop_rank', None)
    await _send_order(context, update.effective_user, label, extra=text)
    await update.message.reply_text(
        f"✅ سفارش شما ثبت شد:\n📦 {label}\n\nادمین به‌زودی قیمت و مراحل بعدی را اعلام می‌کند.\n{SIGNATURE}")
