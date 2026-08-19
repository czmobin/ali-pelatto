from datetime import datetime, timedelta
import json
import os
import random
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from ..config import *
from ..state import *
from ..storage import *
from ..services import *

logger = logging.getLogger(__name__)


async def my_ads_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    help_text = """
🎨 <b>راهنمای رنگ دکمه های وضعیت آگهی:</b>

🟢 <b>سبز</b> - آگهی منتشر شده و در انتظار خرید
🔴 <b>قرمز</b> - آگهی فروخته شده یا رد شده
🔵 <b>آبی</b> - آگهی در انتظار تایید ادمین

⚠️ <b>توجه:</b> 
• فقط آگهی های سبز قابلیت انصراف یا درخواست تخفیف دارند
• آگهی های فروخته شده یا رد شده قابل تغییر نیستند
"""
    
    keyboard = [
        [InlineKeyboardButton("📋 مشاهده همه آگهی های من", callback_data="view_my_ads", style="primary")],
        [InlineKeyboardButton("❌ انصراف از آگهی", callback_data="cancel_my_ad", style="danger")],
        [InlineKeyboardButton("💱 تغییر قیمت اکانت", callback_data="request_discount_on_ad", style="success")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="primary")]
    ]
    await query.message.edit_text(f"📋 <b>مدیریت آگهی های من</b>\n\n{help_text}\n{SIGNATURE}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def view_my_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    all_agahi = load_agahi()
    user_agahi = all_agahi.get(str(user_id), [])
    
    if not user_agahi:
        await query.message.edit_text("📭 شما هیچ آگهی ثبت نکرده اید.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")]]))
        return
    
    text = "📋 <b>لیست همه آگهی های شما:</b>\n\n"
    buttons = []
    
    for ag in user_agahi[-20:][::-1]:
        is_published = ag.get('published', False)
        is_sold = ag.get('status') == 'sold'
        is_rejected = ag.get('status') == 'rejected'
        
        if is_sold:
            status_text = "❌ فروخته شده"
            btn_style = "danger"
        elif is_rejected:
            status_text = "⛔ رد شده"
            btn_style = "danger"
        elif not is_published:
            status_text = "⏳ در انتظار تایید"
            btn_style = "primary"
        else:
            status_text = "✅ منتشر شده - در انتظار خرید"
            btn_style = "success"
        
        current_price = ag.get('price')
        if ag.get('discount_history'):
            for disc in reversed(ag['discount_history']):
                if disc.get('is_active', True):
                    current_price = disc['new_price']
                    break
        
        if current_price is None:
            current_price = 0
        
        price_text = f"{current_price:,} تومان" if isinstance(current_price, int) else str(current_price)
        
        text += f"🆔 شناسه: {ag['id']} | {status_text} | 💰 {price_text}\n"
        buttons.append([InlineKeyboardButton(f"🔍 مشاهده آگهی {ag['id']}", callback_data=f"view_single_ad_{ag['id']}", style=btn_style)])
    
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


async def view_single_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[3])
    
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="view_my_ads", style="primary")]]))
        return
    
    original_price = ad.get('price')
    current_price = original_price
    
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                current_price = disc['new_price']
                break
    
    if current_price is None:
        current_price = 0
    
    if current_price < original_price:
        price_display = f"<s>{original_price:,}</s> <b>{current_price:,}</b> تومان 🔥"
    else:
        price_display = f"<b>{original_price:,}</b> تومان"
    
    is_published = ad.get('published', False)
    is_sold = ad.get('status') == 'sold'
    is_rejected = ad.get('status') == 'rejected'
    
    if is_sold:
        status_text = "❌ فروخته شده"
        status_emoji = "🔴"
    elif is_rejected:
        status_text = "⛔ رد شده توسط ادمین"
        status_emoji = "🔴"
    elif not is_published:
        status_text = "⏳ در انتظار تایید ادمین"
        status_emoji = "🔵"
    else:
        status_text = "✅ منتشر شده - در انتظار خرید"
        status_emoji = "🟢"
    
    seller_note = escape_html(ad.get('seller_note', '-'))
    
    ad_text = f"""🔍 <b>مشاهده آگهی</b>

🆔 شماره: {ad_id}
🎮 بازی: پلاتو
📊 وضعیت: {status_emoji} {status_text}

⭐ ویپ: {ad.get('vip_count', '-')}
📊 آیتم: {ad.get('item_count', '-')}
🪙 سکه: {ad.get('coin_count', '-')}
💰 پیپ: {ad.get('pip_count', '-')}
🏆 وین: {ad.get('win_count', '-')}
📅 سن اکانت: {ad.get('account_age', '-')}
💵 قیمت: {price_display}

📝 توضیحات:
{seller_note}
{SIGNATURE}"""
    
    back_style = "danger" if (is_sold or is_rejected) else ("primary" if not is_published else "success")
    
    await query.message.edit_text(ad_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="view_my_ads", style=back_style)]]))


async def cancel_my_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    all_agahi = load_agahi()
    user_agahi = all_agahi.get(str(user_id), [])
    active_ads = [a for a in user_agahi if is_ad_active(a)]
    
    if not active_ads:
        await query.message.edit_text("❌ شما هیچ آگهی فعالی برای انصراف ندارید!\n(فقط آگهی های سبز قابلیت انصراف دارند)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")]]))
        return
    
    keyboard = []
    for ad in active_ads:
        current_price = ad.get('price')
        if ad.get('discount_history'):
            for disc in reversed(ad['discount_history']):
                if disc.get('is_active', True):
                    current_price = disc['new_price']
                    break
        
        if current_price is None:
            current_price = 0
        
        keyboard.append([InlineKeyboardButton(f"❌ انصراف از آگهی {ad['id']} (💰 {current_price:,} تومان)", callback_data=f"cancel_ad_{ad['id']}", style="danger")])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")])
    
    await query.message.edit_text("❌ لطفاً آگهی مورد نظر برای انصراف را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


async def cancel_ad_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[2])
    
    keyboard = [
        [InlineKeyboardButton("✅ بله، انصراف می خواهم", callback_data=f"confirm_cancel_ad_{ad_id}", style="danger")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_my_ad", style="primary")]
    ]
    await query.message.edit_text(f"⚠️ آیا از انصراف از آگهی {ad_id} مطمئن هستید؟\n\nدر صورت انصراف، آگهی از کانال حذف می شود.", reply_markup=InlineKeyboardMarkup(keyboard))


async def confirm_cancel_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 4:
        await query.message.edit_text("❌ خطا در شناسه آگهی!")
        return
    
    try:
        ad_id = int(parts[3])
    except:
        await query.message.edit_text("❌ شناسه نامعتبر!")
        return
    
    user_id = query.from_user.id
    
    all_agahi = load_agahi()
    ad = None
    user_ads = all_agahi.get(str(user_id), [])
    
    for i, a in enumerate(user_ads):
        if a.get('id') == ad_id:
            ad = a
            user_ads.pop(i)
            break
    
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")]]))
        return
    
    # حذف از کانال‌ها — همه‌ی پیام‌های آلبوم (عکس‌ها + ویدیو) و دکمه‌ی خرید، نه فقط پیام اول
    def _channel_delete_ids(post_key, button_key, media_key):
        ids = []
        stored = ad.get(media_key)
        if stored:
            ids.extend(stored)
        else:
            # آگهی‌های قدیمی که media_ids ذخیره نشده: پیام‌های آلبوم پشت‌سرهم‌اند
            pid = ad.get(post_key)
            if pid:
                n = sum(1 for k in ('profile_photo', 'games_photo', 'video') if ad.get(k))
                ids.extend([pid + i for i in range(n)] if n >= 2 else [pid])
        bid = ad.get(button_key)
        if bid:
            ids.append(bid)
        return ids

    for mid in _channel_delete_ids('game_channel_post_id', 'game_channel_button_id', 'game_channel_media_ids'):
        try:
            await context.bot.delete_message(chat_id=GAME_CHANNEL_ID, message_id=mid)
        except:
            pass

    for mid in _channel_delete_ids('channel_post_id', 'channel_button_id', 'channel_media_ids'):
        try:
            await context.bot.delete_message(chat_id=MAIN_CHANNEL_ID, message_id=mid)
        except:
            pass
    
    # ذخیره در آگهی‌های رد شده
    rejected_ads = load_rejected_ads()
    ad['reject_reason'] = 'انصراف توسط کاربر'
    ad['rejected_date'] = now_jalali()
    rejected_ads[str(ad_id)] = ad
    save_rejected_ads(rejected_ads)
    
    # حذف از pending_ads اگر وجود داشت
    pending_ads = load_pending_ads()
    if str(ad_id) in pending_ads:
        del pending_ads[str(ad_id)]
        save_pending_ads(pending_ads)
    
    # ❌ مبلغ برنمی‌گرده! فقط آگهی حذف میشه
    
    # ذخیره تغییرات
    all_agahi[str(user_id)] = user_ads
    save_agahi(all_agahi)
    
    await query.message.edit_text(
        f"✅ آگهی {ad_id} با موفقیت حذف شد.\n\n"
        f"⚠️ توجه: مبلغ پرداختی به دلیل انصراف شما، قابل برگشت نمی‌باشد.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 بازگشت به آگهی‌های من", callback_data="my_ads_menu", style="primary")]
        ])
    )


async def request_discount_on_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    all_agahi = load_agahi()
    user_agahi = all_agahi.get(str(user_id), [])
    active_ads = [a for a in user_agahi if is_ad_active(a)]
    
    if not active_ads:
        await query.message.edit_text("❌ شما هیچ آگهی فعالی برای تغییر قیمت ندارید!\n(فقط آگهی های سبز قابلیت تغییر قیمت دارند)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")]]))
        return
    
    keyboard = []
    for ad in active_ads:
        current_price = ad.get('price')
        if ad.get('discount_history'):
            for disc in reversed(ad['discount_history']):
                if disc.get('is_active', True):
                    current_price = disc['new_price']
                    break
        
        if current_price is None:
            current_price = 0
        
        keyboard.append([InlineKeyboardButton(f"💱 آگهی {ad['id']} (💰 {current_price:,} تومان)", callback_data=f"request_discount_{ad['id']}", style="success")])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="my_ads_menu", style="primary")])

    await query.message.edit_text("💱 آگهی مورد نظر برای <b>تغییر قیمت</b> را انتخاب کنید:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def request_discount_for_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[2])
    
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد!")
        return

    current_price = ad.get('price')
    discount_count = 0
    if ad.get('discount_history'):
        discount_count = len([d for d in ad['discount_history'] if d.get('is_active', True)])
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                current_price = disc['new_price']
                break

    if current_price is None:
        current_price = 0

    context.user_data['discount_ad_id'] = ad_id
    context.user_data['discount_current_price'] = current_price
    context.user_data['discount_count'] = discount_count

    keyboard = [
        [InlineKeyboardButton("📈 افزایش قیمت آگهی", callback_data=f"pricechg_up_{ad_id}", style="primary")],
        [InlineKeyboardButton("📉 کاهش قیمت آگهی (تخفیف)", callback_data=f"pricechg_down_{ad_id}", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="request_discount_on_ad", style="danger")]
    ]
    await query.message.edit_text(
        f"💱 <b>تغییر قیمت اکانت</b>\n\n🆔 آگهی: {ad_id}\n💰 قیمت فعلی: <b>{current_price:,}</b> تومان\n\n"
        "می‌خواهی قیمت را افزایش بدهی یا کاهش؟",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def pricechg_up_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ad_id = int(query.data.split("_")[2])
    current_price = context.user_data.get('discount_current_price', 0)
    context.user_data['discount_ad_id'] = ad_id
    context.user_data['pricechg_direction'] = 'up'
    context.user_data['waiting_pricechg_value'] = True
    await query.message.edit_text(
        f"📈 <b>افزایش قیمت آگهی {ad_id}</b>\n💰 قیمت فعلی: {current_price:,} تومان\n\n"
        "مبلغی که می‌خواهی به قیمت <b>اضافه</b> شود را به تومان بفرست (فقط عدد):",
        parse_mode="HTML")


async def pricechg_down_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ad_id = int(query.data.split("_")[2])
    # قفل تخفیف فقط برای کاهش قیمت: تا N روز پس از انتشار
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    lock_days = get_setting('discount_lock_days', 4)
    pd = ad.get('publish_date') if ad else None
    if lock_days and pd:
        try:
            unlock = datetime.strptime(pd, "%Y-%m-%d %H:%M:%S") + timedelta(days=int(lock_days))
            now = datetime.now()
            if now < unlock:
                rem = unlock - now
                d, h = rem.days, rem.seconds // 3600
                await query.message.edit_text(
                    f"⏳ <b>هنوز نمی‌توانید برای این آگهی تخفیف بگذارید.</b>\n\n"
                    f"آگهی‌ها تا <b>{int(lock_days)} روز</b> پس از انتشار قابل کاهش قیمت (تخفیف) نیستند.\n"
                    f"⌛ زمان باقی‌مانده: حدود <b>{d} روز و {h} ساعت</b>.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="request_discount_on_ad", style="primary")]]))
                return
        except Exception:
            pass
    current_price = context.user_data.get('discount_current_price', 0)
    context.user_data['discount_ad_id'] = ad_id
    context.user_data['pricechg_direction'] = 'down'
    context.user_data['waiting_pricechg_value'] = True
    await query.message.edit_text(
        f"📉 <b>کاهش قیمت آگهی {ad_id} (تخفیف)</b>\n💰 قیمت فعلی: {current_price:,} تومان\n\n"
        "مبلغ <b>تخفیف/کاهش</b> را به تومان بفرست (فقط عدد):",
        parse_mode="HTML")


async def process_pricechg_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_pricechg_value'):
        return
    raw = (update.message.text or "").replace(",", "").replace("،", "").strip()
    if not raw.isdigit():
        await update.message.reply_text("❌ مقدار نامعتبر! فقط عدد بفرست.")
        return
    value = int(raw)
    ad_id = context.user_data.get('discount_ad_id')
    direction = context.user_data.get('pricechg_direction', 'down')
    current_price = context.user_data.get('discount_current_price', 0)
    if current_price <= 0:
        await update.message.reply_text("❌ خطا در دریافت قیمت فعلی!")
        context.user_data['waiting_pricechg_value'] = False
        return
    if value <= 0:
        await update.message.reply_text("❌ مقدار باید بزرگتر از صفر باشد.")
        return

    if direction == 'up':
        new_price = current_price + value
        dir_label = "افزایش"
    else:
        if value >= current_price:
            await update.message.reply_text(f"❌ مبلغ کاهش نمی‌تواند برابر یا بیشتر از قیمت فعلی ({current_price:,} تومان) باشد!")
            return
        new_price = current_price - value
        dir_label = "کاهش (تخفیف)"

    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد!")
        context.user_data['waiting_pricechg_value'] = False
        return

    profile = load_profiles().get(str(update.effective_user.id), {})
    _u = update.effective_user
    admin_text = f"""🔔 درخواست {dir_label} قیمت از کاربر

🆔 آگهی: {ad_id}
👤 کاربر: {user_mention(_u.id, _u.first_name)}
🆔 آیدی عددی: <code>{_u.id}</code>
🆔 یوزرنیم: @{escape_html(_u.username) if _u.username else 'ندارد'}
📞 شماره تماس: {escape_html(profile.get('phone', '-'))}

💰 قیمت فعلی: {current_price:,} تومان
{'➕' if direction == 'up' else '➖'} مبلغ {dir_label}: {value:,} تومان
💵 قیمت جدید: {new_price:,} تومان

لطفاً تایید یا رد کنید:"""

    if direction == 'up':
        keyboard = [
            [InlineKeyboardButton("✅ تایید افزایش", callback_data=f"approve_priceup_{ad_id}_{new_price}", style="success")],
            [InlineKeyboardButton("❌ رد", callback_data=f"reject_priceup_{ad_id}", style="danger")],
        ]
    else:
        discount = value
        keyboard = [
            [InlineKeyboardButton("✅ تایید تخفیف", callback_data=f"approve_discount_{ad_id}_{new_price}_{discount}", style="success")],
            [InlineKeyboardButton("❌ رد تخفیف", callback_data=f"reject_discount_{ad_id}", style="danger")],
        ]

    await send_to_target(context, GROUP_ADS, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    await update.message.reply_text(f"✅ درخواست {dir_label} قیمت برای آگهی {ad_id} به ادمین ارسال شد.\nپس از تایید، اعمال می‌شود.")

    context.user_data['waiting_pricechg_value'] = False
    context.user_data['discount_ad_id'] = None
    context.user_data['pricechg_direction'] = None


async def discount_method_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['discount_method'] = 'amount'
    current_price = context.user_data.get('discount_current_price', 0)
    await query.message.edit_text(f"💰 لطفاً مبلغ تخفیف مورد نظر را به تومان وارد کنید:\n(قیمت فعلی: {current_price:,} تومان)")
    context.user_data['waiting_discount_value'] = True


async def discount_method_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['discount_method'] = 'percent'
    current_price = context.user_data.get('discount_current_price', 0)
    await query.message.edit_text(f"📊 لطفاً درصد تخفیف مورد نظر را وارد کنید (مثال: 10 برای 10 درصد):\n(قیمت فعلی: {current_price:,} تومان)")
    context.user_data['waiting_discount_value'] = True


async def process_discount_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_discount_value'):
        return
    
    try:
        value = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ مقدار نامعتبر! لطفاً یک عدد وارد کنید.")
        return
    
    ad_id = context.user_data.get('discount_ad_id')
    method = context.user_data.get('discount_method')
    current_price = context.user_data.get('discount_current_price', 0)
    
    if current_price <= 0:
        await update.message.reply_text("❌ خطا در دریافت قیمت فعلی!")
        context.user_data['waiting_discount_value'] = False
        return
    
    if method == 'amount':
        if value >= current_price:
            await update.message.reply_text(f"❌ مبلغ تخفیف نمی تواند برابر یا بیشتر از قیمت فعلی ({current_price:,} تومان) باشد!")
            return
        discount = value
        new_price = current_price - discount
        discount_text = f"{discount:,} تومان"
    else:
        if value >= 100:
            await update.message.reply_text("❌ درصد تخفیف نمی تواند 100 یا بیشتر باشد!")
            return
        discount_percent = value
        discount = int(current_price * discount_percent / 100)
        new_price = current_price - discount
        discount_text = f"{discount_percent}% ({discount:,} تومان)"
    
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد!")
        context.user_data['waiting_discount_value'] = False
        return
    
    original_price = ad.get('price')
    
    profile = load_profiles().get(str(update.effective_user.id), {})
    _u = update.effective_user
    admin_text = f"""🔔 درخواست تخفیف جدید از کاربر

🆔 آگهی: {ad_id}
👤 کاربر: {user_mention(_u.id, _u.first_name)}
🆔 آیدی عددی: <code>{_u.id}</code>
🆔 یوزرنیم: @{escape_html(_u.username) if _u.username else 'ندارد'}
📞 شماره تماس: {escape_html(profile.get('phone', '-'))}

💰 قیمت اصلی: {original_price:,} تومان
💰 قیمت فعلی: {current_price:,} تومان
🎁 تخفیف درخواستی: {discount_text}
💵 قیمت پیشنهادی: {new_price:,} تومان
📊 تعداد تخفیف های قبلی: {context.user_data.get('discount_count', 0)}

لطفاً تایید یا رد کنید:"""

    keyboard = [
        [InlineKeyboardButton("✅ تایید تخفیف", callback_data=f"approve_discount_{ad_id}_{new_price}_{discount}", style="success")],
        [InlineKeyboardButton("❌ رد تخفیف", callback_data=f"reject_discount_{ad_id}", style="danger")]
    ]

    await send_to_target(context, GROUP_ADS, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    await update.message.reply_text(f"✅ درخواست تخفیف شما برای آگهی {ad_id} به ادمین ارسال شد.\nپس از تایید، تخفیف اعمال می شود.")
    
    context.user_data['waiting_discount_value'] = False
    context.user_data['discount_ad_id'] = None
    context.user_data['discount_method'] = None
