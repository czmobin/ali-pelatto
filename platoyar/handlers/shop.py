"""فروشگاه پلاتویار — منوی داده‌محور، قیمت قابل‌ویرایش ادمین، و گرفتن اطلاعات لازم هر سفارش."""
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
#   kind: order (پیش‌فرض) | digital | soon
#   ask : اطلاعاتی که از مشتری گرفته می‌شود:
#         friendlink | gmail | platoid | photo_friendlink | None
# ============================================================
def _leaf(label, kind="order", ask=None):
    return {"label": label, "kind": kind, "ask": ask}


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
    _cat("🛍 آیتم‌های شاپ پلاتو", [_leaf(f"آیتم {x} سکه‌ای", ask="photo_friendlink") for x in _COIN_ITEMS]),
    _cat("💎 آیتم‌های کمیاب پلاتو", [_leaf(f"آیتم کمیاب {x} سکه‌ای", ask="photo_friendlink") for x in _COIN_ITEMS]),
    _cat("🔋 شارژ پیپ و سکه", [
        _cat("💠 شارژ پیپ", [_leaf(f"شارژ {x} پیپ", ask="gmail") for x in _PIP]),
        _cat("🪙 شارژ سکه", [_leaf(f"شارژ {x} کا سکه", ask="friendlink") for x in _COIN_CHARGE]),
    ]),
    _cat("🎁 گیفت آیتم پیپی", [_leaf(f"گیفت آیتم {x} پیپی", ask="photo_friendlink") for x in _GIFT]),
    _cat("🏆 وین (برد) فیک", [_leaf(f"وین فیک {x}", ask="friendlink") for x in _WIN]),
    _leaf("🎉 آفر استارتر پک", ask="gmail"),
    _leaf("⭐ سفارش گلد کردن رنک", ask="gmail"),
    _cat("🔥 هاله (آتیش)", [_leaf(f"هاله {x}", ask="platoid") for x in _HALE]),
    _cat("🚀 هایپ", [_leaf(f"هایپ {x} تایی", ask="platoid") for x in _HYPE]),
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
    NODES[nid] = {"label": spec["label"], "parent": parent_id, "children": [],
                  "kind": spec.get("kind"), "ask": spec.get("ask")}
    for child in spec.get("children") or []:
        cid = _flatten(child, nid)
        NODES[nid]["children"].append(cid)
    return nid


ROOT = _flatten(_ROOT_SPEC, None)

# متن راهنمای هر نوع ورودی
_ASK_PROMPT = {
    "friendlink": "🔗 لطفاً <b>لینک دوستی</b> خود را ارسال کنید:",
    "gmail": "📧 لطفاً <b>جیمیل</b> خود را ارسال کنید:",
    "platoid": "🆔 لطفاً <b>آیدی اکانت پلاتو</b> خود را ارسال کنید:",
}
_ASK_LABEL = {
    "friendlink": "🔗 لینک دوستی",
    "gmail": "📧 جیمیل",
    "platoid": "🆔 آیدی پلاتو",
}


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


def _own_unavailable(nid):
    return nid in load_shop_unavailable()


def _is_unavailable(nid):
    """ناموجود اگر خودش یا یکی از والدینش ناموجود باشد."""
    ua = set(load_shop_unavailable())
    cur = nid
    while cur:
        if cur in ua:
            return True
        cur = NODES[cur]["parent"]
    return False


def _avail_button(nid):
    if _own_unavailable(nid):
        return InlineKeyboardButton("🟢 موجود کردن", callback_data=f"shopavail:{nid}", style="success")
    return InlineKeyboardButton("🔴 ناموجود کردن", callback_data=f"shopavail:{nid}", style="danger")


def _cat_kb(node_id, is_admin=False):
    node = NODES[node_id]
    rows = []
    kids = node["children"]
    for i in range(0, len(kids), 2):
        row = []
        for c in kids[i:i + 2]:
            label = NODES[c]["label"]
            if _own_unavailable(c):
                label = "🚫 " + label
            row.append(InlineKeyboardButton(label, callback_data=f"shop:{c}"))
        rows.append(row)
    if is_admin:
        if kids:
            rows.append([InlineKeyboardButton("📈 افزایش گروهی قیمت", callback_data=f"shopbulk:{node_id}")])
        if node_id != ROOT:
            rows.append([_avail_button(node_id)])
    rows.append(_back_row(node))
    return InlineKeyboardMarkup(rows)


def _clear_shop_flags(context):
    for k in ("shop_collect", "shop_dig", "shop_pending", "shop_setprice", "shop_bulk"):
        context.user_data.pop(k, None)


def _pay_kb(nid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏦 کارت‌به‌کارت", callback_data=f"shoppaycard:{nid}", style="success")],
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data=f"shoppayonline:{nid}", style="primary")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="back_to_main")],
    ])


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
    await _render_node(query, context, nid, _is_admin(update))


async def _render_node(query, context, nid, adm):
    node = NODES.get(nid)
    if not node:
        return

    # کاربر عادی نمی‌تواند وارد بخش ناموجود شود
    if _is_unavailable(nid) and not adm:
        await query.message.edit_text("🚫 این بخش در حال حاضر ناموجود است.",
                                      reply_markup=InlineKeyboardMarkup([_back_row(node)]))
        return

    if node["children"]:
        await query.message.edit_text(f"<b>{node['label']}</b>\n\nیک گزینه را انتخاب کنید:",
                                      reply_markup=_cat_kb(nid, adm), parse_mode="HTML")
        return

    if node.get("kind") == "soon":
        await query.message.edit_text("🚧 این بخش به‌زودی اضافه می‌شود.",
                                      reply_markup=InlineKeyboardMarkup([_back_row(node)]))
        return

    price = _price(nid)
    price_line = f"💵 قیمت: <b>{price:,}</b> تومان" if price else "💵 قیمت: با ادمین هماهنگ می‌شود"
    text = f"📦 <b>{node['label']}</b>\n\n{price_line}"
    if adm and _own_unavailable(nid):
        text += "\n\n🚫 وضعیت: <b>ناموجود</b>"

    rows = []
    if node.get("kind") == "digital":
        rows.append([InlineKeyboardButton("🛒 خرید", callback_data=f"shopbuy:{nid}", style="success")])
    else:
        rows.append([InlineKeyboardButton("🛒 ثبت سفارش", callback_data=f"shopstart:{nid}", style="success")])
    if adm:
        rows.append([InlineKeyboardButton("✏️ تغییر قیمت", callback_data=f"shopprice:{nid}", style="primary")])
        rows.append([_avail_button(nid)])
    rows.append(_back_row(node))
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")


async def shop_toggle_avail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _is_admin(update):
        await query.answer()
        return
    nid = query.data.split(":", 1)[1]
    if nid not in NODES:
        await query.answer()
        return
    ua = load_shop_unavailable()
    if nid in ua:
        ua.remove(nid)
        note = "🟢 موجود شد"
    else:
        ua.append(nid)
        note = "🔴 ناموجود شد"
    save_shop_unavailable(ua)
    await query.answer(note)
    await _render_node(query, context, nid, True)


# ============================================================
# ثبت سفارش عادی (با گرفتن اطلاعات لازم)
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
        await send_to_target(context, GROUP_SHOP, photo=photo, caption=caption, parse_mode="HTML")
    else:
        await send_to_target(context, GROUP_SHOP, text=caption, parse_mode="HTML")


async def _after_info(update, context, nid, info_lines, item_photo):
    """بعد از گرفتن اطلاعات لازم: اگر قیمت ست است → مرحله‌ی پرداخت، وگرنه سفارش برای هماهنگی به ادمین."""
    node = NODES[nid]
    price = _price(nid)
    if not price:
        await _send_order(context, update.effective_user, node["label"],
                          extra="\n".join(info_lines), photo=item_photo)
        await update.message.reply_text(
            f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n\n"
            f"قیمت این مورد هنوز ثبت نشده؛ ادمین به‌زودی مبلغ و مراحل بعدی را اعلام می‌کند.\n{SHOP_SIGNATURE}")
        return
    context.user_data["shop_pending"] = {
        "nid": nid, "label": node["label"], "info": "\n".join(info_lines),
        "item_photo": item_photo, "price": price,
    }
    await update.message.reply_text(
        f"📦 <b>{node['label']}</b>\n💵 مبلغ قابل پرداخت: <b>{price:,}</b> تومان\n\n"
        "روش پرداخت را انتخاب کنید:",
        reply_markup=_pay_kb(nid), parse_mode="HTML")


async def shop_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ثبت سفارش یک آیتم (غیر دیجیتال)."""
    query = update.callback_query
    await query.answer()
    nid = query.data.split(":", 1)[1]
    node = NODES.get(nid)
    if not node:
        return
    if _is_unavailable(nid):
        await query.message.edit_text("🚫 این بخش در حال حاضر ناموجود است.",
                                      reply_markup=InlineKeyboardMarkup([_back_row(node)]))
        return
    _clear_shop_flags(context)
    ask = node.get("ask")

    if not ask:
        price = _price(nid)
        extra = f"💵 قیمت: {price:,} تومان" if price else None
        await _send_order(context, query.from_user, node["label"], extra=extra)
        await query.message.edit_text(
            f"✅ سفارش شما ثبت شد:\n📦 {node['label']}\n\nادمین به‌زودی قیمت و مراحل بعدی را اعلام می‌کند.\n{SHOP_SIGNATURE}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_main")]]))
        return

    if ask == "photo_friendlink":
        context.user_data["shop_collect"] = {"nid": nid, "ask": ask, "stage": "photo"}
        await query.message.edit_text(
            f"📦 <b>{node['label']}</b>\n\n📸 لطفاً <b>عکس آیتم موردنظر</b> را ارسال کنید:",
            reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")
    else:
        context.user_data["shop_collect"] = {"nid": nid, "ask": ask, "stage": "text"}
        await query.message.edit_text(
            f"📦 <b>{node['label']}</b>\n\n{_ASK_PROMPT[ask]}",
            reply_markup=InlineKeyboardMarkup([_back_row(node)]), parse_mode="HTML")


async def shop_collect_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    col = context.user_data.get("shop_collect")
    if not col:
        return
    node = NODES.get(col["nid"])
    if not node:
        context.user_data.pop("shop_collect", None)
        return
    ask = col["ask"]

    # مرحله‌ی عکس (فقط برای گیفت آیتم پیپی)
    if col["stage"] == "photo":
        if not update.message.photo:
            await update.message.reply_text("❌ لطفاً یک عکس از آیتم ارسال کنید.")
            return
        col["photo"] = update.message.photo[-1].file_id
        col["stage"] = "text"
        await update.message.reply_text("🔗 حالا لطفاً <b>لینک دوستی</b> خود را ارسال کنید:", parse_mode="HTML")
        return

    # مرحله‌ی متن (لینک دوستی / جیمیل / آیدی پلاتو)
    text = update.message.text
    if not text:
        await update.message.reply_text("❌ لطفاً اطلاعات را به‌صورت متن ارسال کنید.")
        return
    context.user_data.pop("shop_collect", None)
    label_key = "friendlink" if ask == "photo_friendlink" else ask
    info_lines = [f"{_ASK_LABEL[label_key]}: {escape_html(text)}"]
    await _after_info(update, context, col["nid"], info_lines, col.get("photo"))


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
    if _is_unavailable(nid):
        await query.message.edit_text("🚫 این بخش در حال حاضر ناموجود است.",
                                      reply_markup=InlineKeyboardMarkup([_back_row(node)]))
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
    target = (update.message.text or "").strip()
    if not target:
        await update.message.reply_text("❌ لطفاً آیدی مقصد را به‌صورت متن بفرستید.")
        return
    context.user_data.pop("shop_dig", None)
    await _after_info(update, context, dig["nid"], [f"🎯 آیدی مقصد: {escape_html(target)}"], None)


# ============================================================
# مرحله‌ی پرداخت (کارت‌به‌کارت / درگاه آنلاین) — برای همه‌ی سفارش‌ها
# ============================================================
async def shop_pay_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pend = context.user_data.get("shop_pending")
    if not pend:
        await query.message.edit_text("❌ سفارش منقضی شده؛ دوباره از فروشگاه ثبت کنید.")
        return
    pend["method"] = "کارت‌به‌کارت"
    pend["await_receipt"] = True
    await query.message.edit_text(
        f"🏦 <b>پرداخت کارت‌به‌کارت</b>\n📦 {pend['label']}\n"
        f"💵 مبلغ: <b>{pend['price']:,}</b> تومان\n\n"
        f"🏦 شماره کارت:\n<code>{CARD_NUMBER}</code>\n👤 {CARD_NAME}\n\n"
        f"📝 مبلغ بالا را واریز کنید و سپس <b>تصویر رسید</b> را همین‌جا ارسال کنید.",
        parse_mode="HTML")


async def shop_pay_online(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pend = context.user_data.get("shop_pending")
    if not pend:
        await query.message.edit_text("❌ سفارش منقضی شده؛ دوباره از فروشگاه ثبت کنید.")
        return
    if not ZIBAL_ENABLED:
        await query.message.edit_text(
            f"📦 {pend['label']}\n💵 مبلغ: {pend['price']:,} تومان\n\n"
            "💳 پرداخت آنلاین به‌زودی فعال می‌شود. فعلاً لطفاً «کارت‌به‌کارت» را انتخاب کنید:",
            reply_markup=_pay_kb(pend["nid"]))
        return
    # درگاه آنلاین وقتی زیردامنه/زیبال آماده شود اینجا پیاده می‌شود.
    await query.message.edit_text("💳 در حال آماده‌سازی درگاه آنلاین...")


async def shop_receive_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pend = context.user_data.get("shop_pending")
    if not pend or not pend.get("await_receipt"):
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً تصویر رسید پرداخت را ارسال کنید.")
        return
    receipt = update.message.photo[-1].file_id
    context.user_data.pop("shop_pending", None)
    await _finalize_paid_order(context, update.effective_user, pend, receipt)
    await update.message.reply_text(
        f"✅ سفارش و رسید شما ثبت شد:\n📦 {pend['label']}\n💵 مبلغ: {pend['price']:,} تومان\n\n"
        f"پس از بررسی رسید، سفارش شما انجام می‌شود.\n{SHOP_SIGNATURE}")


async def _finalize_paid_order(context, user, pend, receipt_photo):
    uname = f"@{user.username}" if user.username else "—"
    text = (f"🛒 <b>سفارش فروشگاه (پرداخت‌شده)</b>\n\n"
            f"📦 {escape_html(pend['label'])}\n"
            f"{pend['info']}\n"
            f"💵 مبلغ: {pend['price']:,} تومان\n"
            f"💳 روش پرداخت: {pend.get('method', '-')}\n"
            f"👤 {escape_html(user.first_name or '')} ({uname})\n🆔 <code>{user.id}</code>")
    if pend.get("item_photo"):
        await send_to_target(context, GROUP_SHOP, photo=pend["item_photo"], caption=text, parse_mode="HTML")
    else:
        await send_to_target(context, GROUP_SHOP, text=text, parse_mode="HTML")
    await send_to_target(
        context, GROUP_SHOP, photo=receipt_photo,
        caption=f"🧾 رسید پرداخت سفارش «{escape_html(pend['label'])}» — کاربر <code>{user.id}</code>",
        parse_mode="HTML")


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
        "• درصدی: مثل <code>10%</code>\n"
        "• مبلغی: مثل <code>5000</code>\n\n"
        "فقط روی آیتم‌هایی که قیمت دارند اعمال می‌شود.",
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
        prices[leaf_id] = max(0, int(new))
        changed += 1
    save_shop_prices(prices)
    how = f"{amount}٪" if is_percent else f"{int(amount):,} تومان"
    await update.message.reply_text(
        f"✅ افزایش {how} روی {changed} آیتمِ دارای قیمت در «{node['label']}» اعمال شد.")
