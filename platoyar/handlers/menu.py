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


async def chat_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آیدی چت فعلی را برمی‌گرداند؛ برای گرفتن chat id گروه‌ها. فقط ادمین‌ها."""
    if update.effective_user.id not in ADMIN_IDS:
        return
    chat = update.effective_chat
    await update.message.reply_text(
        f"🆔 chat id:\n<code>{chat.id}</code>\nنوع: {chat.type}\nعنوان: {chat.title or '-'}",
        parse_mode="HTML",
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_blacklisted(user_id):
        await update.message.reply_text("⛔ شما از دسترسی به ربات محروم شده‌اید!")
        return
    
    user_name = update.effective_user.first_name or "کاربر عزیز"
    
    welcome_text = f"""🌟 <b>به پلاتویار خوش آمدید!</b> 🌟

━━━━━━━━━━━━━━━━━━━━
<b>🎯 اولین و تخصصی‌ترین 
ربات خرید و فروش اکانت بازی های موبایلی آنلاین</b>
━━━━━━━━━━━━━━━━━━━━

<b>👋 سلام {user_name}!</b>

ما اینجاییم تا خرید و فروش اکانت پلاتو رو 
برای شما آسان، امن و حرفه‌ای کنیم.

━━━━━━━━━━━━━━━━━━━━
✨ <b>چرا پلاتویار؟</b>
━━━━━━━━━━━━━━━━━━━━

✅ <b>امنیت کامل</b> با ضمانت معامله
✅ <b>قیمت‌گذاری حرفه‌ای</b> توسط کارشناسان
✅ <b>انتشار در کانال‌های پربازدید</b>
✅ <b>پشتیبانی ۲۴ ساعته</b>
✅ <b>بازار امن</b> با حذف کلاهبرداران

━━━━━━━━━━━━━━━━━━━━
📊 <b>آمار ما</b>
━━━━━━━━━━━━━━━━━━━━

🔹 بیش از ۲۰۰۰ کاربر فعال
🔹 بیش از ۱۰۰۰ معامله موفق
🔹 رضایت ۹۸٪ کاربران

━━━━━━━━━━━━━━━━━━━━
💡 <b>شروع کنید!</b>
━━━━━━━━━━━━━━━━━━━━

برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:

{SIGNATURE}"""
    
    keyboard = [
        [InlineKeyboardButton("🛒 فروشگاه", callback_data="shop_menu", style="primary")],
        [InlineKeyboardButton("📢 ثبت آگهی", callback_data="agahi_menu", style="success")],
        [InlineKeyboardButton("🆘 پشتیبانی", callback_data="support_menu", style="danger")]
    ]
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🛠 پنل مدیریت", callback_data="admin_panel", style="primary")])

    if update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        await update.callback_query.answer()
    else:
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    support_text = f"""🆘 <b>پشتیبانی پلاتویار</b>

━━━━━━━━━━━━━━━━━━━━
⏰ <b>ساعات پاسخگویی:</b>
۲۴ ساعته - ۷ روز هفته

━━━━━━━━━━━━━━━━━━━━
📌 <b>موضوعات پشتیبانی:</b>
• مشکلات ثبت آگهی
• مشکلات پرداخت
• راهنمایی و آموزش
• گزارش تخلفات
• پیشنهادات و انتقادات"""

    keyboard = [
        [InlineKeyboardButton("📞 تماس با ادمین", url=f"https://t.me/{ADMIN_USERNAME[1:]}", style="primary")],
        [InlineKeyboardButton("📢 کانال ربات", url="https://t.me/platoyar_iD", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main", style="primary")]
    ]
    
    await query.message.edit_text(support_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("⚠️ ربات فروشگاهی در حال توسعه است!\nبه زودی...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main", style="primary")]]), parse_mode="HTML")


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    is_member, _ = await check_membership(query.from_user.id, context)
    if not is_member:
        await query.message.edit_text("🚫 لطفاً در کانال ها عضو شوید:", reply_markup=await membership_buttons(query.from_user.id, context))
        return
    await show_main_menu(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_with_ref(update, context)


async def start_with_ref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .buy import process_buy_from_channel  # import محلی برای پرهیز از چرخه
    user_id = update.effective_user.id
    text = update.message.text

    register_user(update.effective_user)

    if is_blacklisted(user_id):
        await update.message.reply_text("⛔ شما از دسترسی به ربات محروم شده اید!")
        return
    
    # رفرال
    if text.startswith('/start ref_'):
        try:
            ref_user_id = int(text.replace('/start ref_', ''))
            if ref_user_id != user_id:
                referrals = load_referrals()
                ref_data = referrals.get(str(user_id), {})
                if isinstance(ref_data, int):
                    ref_data = {'count': ref_data, 'bonus_claimed': False}
                ref_data['referred_by'] = ref_user_id
                referrals[str(user_id)] = ref_data
                save_referrals(referrals)
                
                await update.message.reply_text(
                    f"🎉 شما با لینک دعوت وارد شدید!\n\n"
                    f"پس از ثبت اولین آگهی، ۲۰,۰۰۰ تومان به کیف پول شما واریز می‌شود.\n"
                    f"و همچنین به دعوت‌کننده شما هم جایزه تعلق می‌گیرد.\n{SIGNATURE}"
                )
        except:
            pass
    
    is_member, _ = await check_membership(user_id, context)
    if not is_member:
        await update.message.reply_text("🚫 دسترسی محدود!\n\nلطفاً در کانال ها عضو شوید:", reply_markup=await membership_buttons(user_id, context))
        return
    
    if text.startswith('/start buy_'):
        try:
            ad_id = int(text.replace('/start buy_', ''))
            await process_buy_from_channel(update, context, ad_id)
        except:
            await show_main_menu(update, context)
    else:
        await show_main_menu(update, context)


async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    is_member, not_member = await check_membership(user_id, context)
    if not is_member:
        await query.message.edit_text("❌ لطفاً در کانال های زیر عضو شوید:", reply_markup=await membership_buttons(user_id, context))
        await query.answer()
        return
    await query.message.edit_text("✅ عضویت شما تایید شد! به پلاتویار خوش آمدید.")
    await show_main_menu(update, context)


async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    referral_count = get_referral_count(user_id)
    
    text = f"""🎁 <b>سیستم دعوت پلاتویار</b>

━━━━━━━━━━━━━━━━━━━━
📊 <b>تعداد دعوت‌های شما:</b> {referral_count} نفر

━━━━━━━━━━━━━━━━━━━━
🎯 <b>جوایز:</b>
• هر کاربر جدید با لینک شما ثبت نام کند
• بعد از ثبت اولین آگهی:
  🔹 به شما: ۱۰,۰۰۰ تومان
  🔹 به کاربر جدید: ۲۰,۰۰۰ تومان

━━━━━━━━━━━━━━━━━━━━
📋 <b>لینک دعوت شما:</b>
<code>{referral_link}</code>

📤 لینک را برای دوستان خود ارسال کنید
و از جوایز نقدی بهره‌مند شوید!

{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("📤 اشتراک‌گذاری لینک", url=f"https://t.me/share/url?url={referral_link}&text=🎁 به ربات پلاتویار بپیوندید و از جوایز نقدی بهره‌مند شوید!", style="primary")],
        [InlineKeyboardButton("📋 کپی لینک", callback_data=f"copy_link_{user_id}", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت به منوی آگهی", callback_data="agahi_menu", style="primary")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def copy_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    await query.message.reply_text(
        f"📋 لینک دعوت شما:\n<code>{referral_link}</code>\n\n"
        f"لینک را کپی کرده و برای دوستان خود ارسال کنید.",
        parse_mode="HTML"
    )


async def cancel_current_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keys_to_clear = [
        'temp_agahi', 'agahi_step', 'price_only_mode', 
        'last_question_msg_id', 'waiting_custom_price',
        'price_method', 'admin_price_fee', 'publish_fee',
        'publish_method', 'profile_step', 'search_mode',
        'waiting_discount_value', 'discount_ad_id', 'discount_method',
        'discount_current_price', 'discount_count', 'offer_mode',
        'offer_ad_id', 'offer_ad_data', 'offer_current_price',
        'offer_method', 'waiting_offer_value'
    ]
    for key in keys_to_clear:
        context.user_data.pop(key, None)
    
    await query.message.edit_text(
        "✅ عملیات فعلی لغو شد.\nاز منوی اصلی استفاده کنید.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_to_main", style="primary")]
        ]),
        parse_mode="HTML"
    )


async def game_inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("⚠️ این بخش به زودی فعال می شود.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_submit_start", style="primary")]]))
