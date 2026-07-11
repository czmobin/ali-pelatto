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


async def show_agahi_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet_balance = get_wallet_balance(user_id)
    
    bot_username = (await context.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    text = f"""📢 <b>سیستم ثبت آگهی پلاتویار</b>

━━━━━━━━━━━━━━━━━━━━
💰 <b>موجودی کیف پول:</b> {wallet_balance:,} تومان
━━━━━━━━━━━━━━━━━━━━

📌 <b>راهنما:</b>
• ثبت آگهی با کمترین هزینه
• انتشار در کانال های پربازدید
• قیمت گذاری حرفه ای توسط کارشناسان

━━━━━━━━━━━━━━━━━━━━
🎁 <b>سیستم دعوت:</b>
هر کاربری که با لینک دعوت شما ثبت نام کند
و اولین آگهی خود را ثبت کند:
💰 ۲۰,۰۰۰ تومان به او
💰 ۱۰,۰۰۰ تومان به شما
هدیه تعلق می‌گیرد!

{SIGNATURE}"""
    
    keyboard = [
        [InlineKeyboardButton("➕ ثبت آگهی جدید", callback_data="agahi_submit_start", style="success")],
        [InlineKeyboardButton("👤 پروفایل من", callback_data="agahi_profile", style="primary")],
        [InlineKeyboardButton("📋 آگهی های من", callback_data="my_ads_menu", style="primary")],
        [InlineKeyboardButton("💰 فقط قیمت گذاری میخواهم", callback_data="price_only_start", style="danger")],
        [InlineKeyboardButton("🔍 جستجوی آگهی", callback_data="search_menu", style="primary")],
        [InlineKeyboardButton("💼 کیف پول", callback_data="wallet_menu", style="success")],
        [InlineKeyboardButton("🎁 دعوت از دوستان", callback_data="referral_menu", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main", style="primary")]
    ]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    await update.callback_query.answer()


async def show_terms_before_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    terms_text = f"""📋 <b>قوانین و شرایط ثبت آگهی در پلاتویار</b>

━━━━━━━━━━━━━━━━━━━━
📌 <b>مدارک مورد نیاز:</b>
━━━━━━━━━━━━━━━━━━━━

1️⃣ <b>عکس پروفایل اکانت</b>
   ⚠️ آیدی کامل پوشانده شده باشد!
   📸 کیفیت بالا و واضح

2️⃣ <b>عکس از بخش بازی‌ها و لول‌آپ</b>
   ⚠️ آیدی کامل پوشانده شده باشد!
   🎮 نمایش کامل پیشرفت بازی

3️⃣ <b>فیلم کامل از تمام آیتم‌های اکانت</b>
   🎥 با کیفیت HD
   ⚠️ نمایش تمام آیتم‌های موجود

━━━━━━━━━━━━━━━━━━━━
💰 <b>هزینه‌ها و تعرفه‌ها</b>
━━━━━━━━━━━━━━━━━━━━

🔹 حق واسطه: <b>15%</b> از مبلغ فروش
🔹 هزینه انتشار در کانال بازی: <b>۵۰,۰۰۰</b> تومان
🔹 هزینه انتشار در هر دو کانال: <b>۱۵۰,۰۰۰</b> تومان
🔹 هزینه قیمت‌گذاری توسط ادمین: <b>۲۰,۰۰۰</b> تومان

━━━━━━━━━━━━━━━━━━━━
⏱ <b>زمان‌بندی</b>
━━━━━━━━━━━━━━━━━━━━

📆 مدت زمان چنج: <b>حدود 1 هفته</b>
⏰ زمان پاسخگویی: <b>24 ساعته</b>
⚡ تایید نهایی: پس از چنج شماره و جیمیل

━━━━━━━━━━━━━━━━━━━━
⚠️ <b>توجه مهم</b>
━━━━━━━━━━━━━━━━━━━━

• بعد از پرداخت و تحویل اکانت، امکان انصراف وجود ندارد
• در صورت رد شدن آگهی توسط ادمین، مبلغ به کیف پول برگشت داده می‌شود
• در صورت انصراف کاربر، مبلغ <b>قابل برگشت نمی‌باشد</b>
• 3 بار رسید فیک = بن دائمی
• اطلاعات ناقص = رد آگهی

━━━━━━━━━━━━━━━━━━━━
📢 <b>کانال‌های ما:</b>
• کانال فروشگاه: {MAIN_CHANNEL_LINK}
• کانال اگهی اکانت پلاتو: {GAME_CHANNEL_LINK}
• کانال پابجی و کالاف: {NEW_CHANNEL_LINK}

{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("✅ تایید و ادامه", callback_data="terms_accepted_start_form", style="success")],
        [InlineKeyboardButton("❌ لغو", callback_data="agahi_menu", style="danger")]
    ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(terms_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(terms_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def terms_accepted_start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['price_only_mode'] = False
    context.user_data['temp_agahi'] = {}
    context.user_data['agahi_step'] = 'waiting_vip_count_normal'
    context.user_data['last_question_msg_id'] = None
    
    sent_msg = await query.message.edit_text("✅ قوانین تایید شد.\n\n🎯 ثبت آگهی جدید - پلاتو\n\n⭐ تعداد ویپ را وارد کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]]), parse_mode="HTML")
    context.user_data['last_question_msg_id'] = sent_msg.message_id


async def agahi_submit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .profile import start_profile_completion  # import محلی برای پرهیز از چرخه
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if is_blacklisted(user_id):
        await query.message.edit_text("⛔ شما از دسترسی به ربات محروم شده اید!")
        return
    
    if not is_profile_complete(user_id):
        context.user_data['return_to'] = 'agahi_submit_start'
        await start_profile_completion(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("🎮 پلاتو", callback_data="game_platoyar", style="success")],
        [InlineKeyboardButton("🔫 کالاف و پابجی (به زودی)", callback_data="game_inactive", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="danger")]
    ]
    await query.message.edit_text("🎯 انتخاب بازی مورد نظر:", reply_markup=InlineKeyboardMarkup(keyboard))


async def game_platoyar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_terms_before_form(update, context)


async def handle_normal_agahi_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('price_only_mode'):
        return
    
    step = context.user_data.get('agahi_step')
    if not step:
        return
    
    temp = context.user_data.setdefault('temp_agahi', {})
    
    cancel_btn = [[InlineKeyboardButton("❌ لغو ثبت آگهی", callback_data="cancel_operation", style="danger")]]
    
    if context.user_data.get('last_question_msg_id'):
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_question_msg_id']
            )
        except:
            pass
    
    steps = {
        'waiting_vip_count_normal': ('vip_count', 'waiting_item_count_normal', '❓ تعداد آیتم را وارد کنید:'),
        'waiting_item_count_normal': ('item_count', 'waiting_coin_count_normal', '❓ تعداد سکه اکانت را وارد کنید:'),
        'waiting_coin_count_normal': ('coin_count', 'waiting_pip_count_normal', '❓ تعداد پیپ اکانت را وارد کنید:'),
        'waiting_pip_count_normal': ('pip_count', 'waiting_win_count_normal', '❓ تعداد وین را وارد کنید:'),
        'waiting_win_count_normal': ('win_count', 'waiting_account_age_normal', '❓ سن اکانت را وارد کنید:'),
        'waiting_account_age_normal': ('account_age', 'waiting_seller_note_normal', '❓ توضیحات فروشنده را وارد کنید:'),
        'waiting_seller_note_normal': ('seller_note', 'waiting_platoid_normal', '❓ آیدی پلاتو خود را وارد کنید:'),
        'waiting_platoid_normal': ('platoid', 'waiting_profile_photo_normal', '✅ آیدی پلاتو ثبت شد.\n\n📸 عکس پروفایل اکانت را ارسال کنید:'),
    }
    
    if step == 'waiting_profile_photo_normal':
        if update.message.photo:
            temp['profile_photo'] = update.message.photo[-1].file_id
            context.user_data['agahi_step'] = 'waiting_games_photo_normal'
            
            sent_msg = await update.message.reply_text(
                "✅ عکس پروفایل دریافت شد.\n\n📸 عکس از بخش بازی ها و لول آپ اکانت را ارسال کنید:",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            context.user_data['last_question_msg_id'] = sent_msg.message_id
            await update.message.delete()
            return
        else:
            await update.message.reply_text(
                "❌ لطفاً یک عکس معتبر ارسال کنید!",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            await update.message.delete()
            return
    
    if step == 'waiting_games_photo_normal':
        if update.message.photo:
            temp['games_photo'] = update.message.photo[-1].file_id
            context.user_data['agahi_step'] = 'waiting_video_normal'
            
            sent_msg = await update.message.reply_text(
                "✅ عکس بازی ها دریافت شد.\n\n🎥 فیلم واضح از تمامی آیتم های اکانت را ارسال کنید (اجباری):",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            context.user_data['last_question_msg_id'] = sent_msg.message_id
            await update.message.delete()
            return
        else:
            await update.message.reply_text(
                "❌ لطفاً یک عکس معتبر ارسال کنید!",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            await update.message.delete()
            return
    
    # فیلم (اجباری برای ثبت آگهی عادی)
    if step == 'waiting_video_normal':
        if update.message.video:
            temp['video'] = update.message.video.file_id
            context.user_data['agahi_step'] = None
            context.user_data['last_question_msg_id'] = None
            
            await update.message.reply_text("✅ فیلم با موفقیت دریافت شد!\n\n✅ اطلاعات آگهی تکمیل شد!\n\nدر حال رفتن به مرحله قیمت گذاری...")
            await ask_price_method(update, context)
            await update.message.delete()
            return
        else:
            await update.message.reply_text(
                "❌ لطفاً یک فیلم معتبر ارسال کنید! (فیلم اجباری است)",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            await update.message.delete()
            return
    
    if step in steps and update.message.text:
        key, next_step, msg = steps[step]
        temp[key] = update.message.text
        context.user_data['agahi_step'] = next_step
        
        try:
            await update.message.delete()
        except:
            pass
        
        sent_msg = await update.message.reply_text(
            f"✅ ثبت شد: {update.message.text}\n\n{msg}",
            reply_markup=InlineKeyboardMarkup(cancel_btn)
        )
        context.user_data['last_question_msg_id'] = sent_msg.message_id
    
    elif not update.message.photo and not update.message.video:
        try:
            await update.message.delete()
        except:
            pass
        await update.message.reply_text(
            "❌ ورودی نامعتبر! لطفاً اطلاعات خواسته شده را وارد کنید.",
            reply_markup=InlineKeyboardMarkup(cancel_btn)
        )


async def handle_price_only_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('price_only_mode'):
        return
    
    step = context.user_data.get('agahi_step')
    if not step:
        return
    
    temp = context.user_data.setdefault('temp_agahi', {})
    
    cancel_btn = [[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]]
    
    try:
        await update.message.delete()
    except:
        pass
    
    steps = {
        'waiting_vip_count_priceonly': ('vip_count', 'waiting_item_count_priceonly', '❓ تعداد آیتم را وارد کنید:'),
        'waiting_item_count_priceonly': ('item_count', 'waiting_coin_count_priceonly', '❓ تعداد سکه اکانت را وارد کنید:'),
        'waiting_coin_count_priceonly': ('coin_count', 'waiting_pip_count_priceonly', '❓ تعداد پیپ اکانت را وارد کنید:'),
        'waiting_pip_count_priceonly': ('pip_count', 'waiting_win_count_priceonly', '❓ تعداد وین را وارد کنید:'),
        'waiting_win_count_priceonly': ('win_count', 'waiting_account_age_priceonly', '❓ سن اکانت را وارد کنید:'),
        'waiting_account_age_priceonly': ('account_age', 'waiting_seller_note_priceonly', '❓ توضیحات فروشنده را وارد کنید:'),
        'waiting_seller_note_priceonly': ('seller_note', 'waiting_platoid_priceonly', '❓ آیدی پلاتو خود را وارد کنید:'),
        'waiting_platoid_priceonly': ('platoid', 'waiting_profile_photo_priceonly', '✅ آیدی پلاتو ثبت شد.\n\n📸 عکس پروفایل اکانت ارسال کنید:'),
        'waiting_profile_photo_priceonly': ('profile_photo', 'waiting_games_photo_priceonly', '✅ عکس پروفایل دریافت شد.\n\n📸 عکس از بخش بازی ها و لول آپ ارسال کنید:'),
        'waiting_games_photo_priceonly': ('games_photo', 'done_priceonly', '✅ عکس بازی ها دریافت شد.\n\n✅ اطلاعات آگهی تکمیل شد!\n\nدر حال رفتن به مرحله پرداخت...'),
    }
    
    if context.user_data.get('last_question_msg_id'):
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_question_msg_id']
            )
        except:
            pass
    
    if step == 'waiting_profile_photo_priceonly':
        if update.message.photo:
            temp['profile_photo'] = update.message.photo[-1].file_id
            context.user_data['agahi_step'] = 'waiting_games_photo_priceonly'
            
            sent_msg = await update.message.reply_text(
                "✅ عکس پروفایل دریافت شد.\n\n📸 عکس از بخش بازی ها و لول آپ ارسال کنید:",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            context.user_data['last_question_msg_id'] = sent_msg.message_id
            await update.message.delete()
            return
        else:
            await update.message.reply_text(
                "❌ لطفاً یک عکس معتبر ارسال کنید!",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            await update.message.delete()
            return
    
    if step == 'waiting_games_photo_priceonly':
        if update.message.photo:
            temp['games_photo'] = update.message.photo[-1].file_id
            context.user_data['agahi_step'] = None
            context.user_data['last_question_msg_id'] = None
            
            await update.message.reply_text("✅ عکس بازی ها دریافت شد.\n\n✅ اطلاعات آگهی تکمیل شد!\n\nدر حال رفتن به مرحله پرداخت...")
            await show_invoice_price_only(update, context)
            await update.message.delete()
            return
        else:
            await update.message.reply_text(
                "❌ لطفاً یک عکس معتبر ارسال کنید!",
                reply_markup=InlineKeyboardMarkup(cancel_btn),
                parse_mode="HTML"
            )
            await update.message.delete()
            return
    
    if step == 'done_priceonly':
        # این مرحله نباید اجرا بشه چون مستقیم میریم به show_invoice_price_only
        pass
    
    if step in steps and step not in ['waiting_profile_photo_priceonly', 'waiting_games_photo_priceonly', 'done_priceonly'] and update.message.text:
        key, next_step, msg = steps[step]
        temp[key] = update.message.text
        context.user_data['agahi_step'] = next_step
        
        sent_msg = await update.message.reply_text(
            f"✅ ثبت شد: {update.message.text}\n\n{msg}",
            reply_markup=InlineKeyboardMarkup(cancel_btn)
        )
        context.user_data['last_question_msg_id'] = sent_msg.message_id
    
    elif not update.message.photo and not update.message.video:
        try:
            await update.message.delete()
        except:
            pass
        await update.message.reply_text(
            "❌ ورودی نامعتبر! لطفاً اطلاعات خواسته شده را وارد کنید.",
            reply_markup=InlineKeyboardMarkup(cancel_btn)
        )


async def show_invoice_price_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp = context.user_data.get('temp_agahi', {})
    total_fee = PRICE_ADMIN_PRICE
    user_id = update.effective_user.id
    wallet_balance = get_wallet_balance(user_id)
    
    invoice_text = f"""🧾 <b>فاکتور قیمت گذاری</b>

🆔 آیدی پلاتو: {temp.get('platoid', '-')}
⭐ ویپ: {temp.get('vip_count', '-')}
📊 آیتم: {temp.get('item_count', '-')}
🪙 سکه: {temp.get('coin_count', '-')}
💰 پیپ: {temp.get('pip_count', '-')}
🏆 وین: {temp.get('win_count', '-')}
📅 سن: {temp.get('account_age', '-')}
━━━━━━━━━━━━━━━━━━━━
💰 هزینه: {total_fee:,} تومان
💰 موجودی کیف پول: {wallet_balance:,} تومان"""
    
    if wallet_balance >= total_fee:
        invoice_text += f"\n\n✅ موجودی کیف پول کافی است."
        keyboard = [
            [InlineKeyboardButton("✅ پرداخت از کیف پول", callback_data="pay_price_only_wallet", style="success")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ]
    else:
        invoice_text += f"\n\n⚠️ موجودی کیف پول ناکافی است."
        keyboard = [
            [InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data="pay_price_only_card", style="primary")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ]
    
    await update.message.reply_text(invoice_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def pay_price_only_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    total_fee = PRICE_ADMIN_PRICE
    wallet_balance = get_wallet_balance(user_id)
    
    if wallet_balance >= total_fee:
        success, new_balance = deduct_from_wallet(user_id, total_fee)
        if success:
            await query.message.edit_text(f"✅ مبلغ {total_fee:,} تومان از کیف پول کسر شد.\n💰 موجودی جدید: {new_balance:,} تومان\n\nدر حال ارسال به ادمین...")
            await process_price_only_request(update, context, payment_method="کیف پول")
        else:
            await query.message.edit_text("❌ خطا در کسر از کیف پول!")
    else:
        await query.message.edit_text("❌ موجودی کیف پول کافی نیست!")


async def pay_price_only_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['waiting_price_only_receipt'] = True
    await query.message.edit_text(f"""💳 <b>پرداخت کارت به کارت</b>

💰 مبلغ: {PRICE_ADMIN_PRICE:,} تومان

🏦 شماره کارت:
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 پس از واریز، تصویر رسید را ارسال کنید.
{SIGNATURE}""", parse_mode="HTML")


async def handle_price_only_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_price_only_receipt'):
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر رسید ارسال کنید.")
        return
    
    photo = update.message.photo[-1].file_id
    await process_price_only_request(update, context, receipt_photo=photo, payment_method="کارت به کارت")
    context.user_data['waiting_price_only_receipt'] = False


async def ask_price_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 خودم قیمت میگذارم", callback_data="price_method_self", style="success")],
        [InlineKeyboardButton("👑 قیمت گذاری توسط ادمین", callback_data="price_method_admin", style="primary")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
    ]
    if update.callback_query:
        await update.callback_query.message.edit_text("📊 انتخاب روش قیمت گذاری:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("📊 انتخاب روش قیمت گذاری:", reply_markup=InlineKeyboardMarkup(keyboard))


async def price_method_self(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['price_method'] = 'self'
    context.user_data['admin_price_fee'] = 0
    await query.message.edit_text("💰 لطفاً قیمت اکانت خود را به تومان وارد کنید:")
    context.user_data['waiting_custom_price'] = True


async def price_method_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['price_method'] = 'admin'
    context.user_data['admin_price_fee'] = PRICE_ADMIN_PRICE
    context.user_data['temp_agahi']['price'] = "تعیین توسط ادمین"
    await query.message.edit_text(f"✅ روش قیمت گذاری توسط ادمین انتخاب شد.\n💰 هزینه: {PRICE_ADMIN_PRICE:,} تومان")
    await ask_publish_method(update, context, from_callback=True)


async def get_custom_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_custom_price'):
        return
    try:
        price = int(update.message.text.replace(',', '').strip())
        if price <= 0:
            await update.message.reply_text("❌ قیمت باید بزرگتر از صفر باشد!")
            return
        context.user_data['temp_agahi']['price'] = price
        context.user_data['waiting_custom_price'] = False
        await update.message.reply_text(f"✅ قیمت: {price:,} تومان ثبت شد.")
        await ask_publish_method(update, context)
    except:
        await update.message.reply_text("❌ قیمت نامعتبر!")


async def ask_publish_method(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    keyboard = [
        [InlineKeyboardButton("📢 کانال آگهی پلاتو (50,000 تومان)", callback_data="publish_game", style="primary")],
        [InlineKeyboardButton("🌟 کانال فروشگاه + کانال آگهی پلاتو (150,000 تومان)", callback_data="publish_both", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
    ]
    if from_callback and update.callback_query:
        await update.callback_query.message.edit_text("📢 انتخاب روش انتشار:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("📢 انتخاب روش انتشار:", reply_markup=InlineKeyboardMarkup(keyboard))


async def publish_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['publish_method'] = 'game'
    context.user_data['publish_fee'] = PRICE_CHANNEL_GAME
    await show_invoice(update, context)


async def publish_both(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['publish_method'] = 'both'
    context.user_data['publish_fee'] = PRICE_CHANNEL_BOTH
    await show_invoice(update, context)


async def show_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    temp = context.user_data.get('temp_agahi', {})
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    user_id = update.effective_user.id
    wallet_balance = get_wallet_balance(user_id)
    
    price_value = temp.get('price')
    if price_value is None:
        price_value = 0
    price_text = f"{price_value:,} تومان" if isinstance(price_value, int) else temp.get('price', 'نامشخص')
    
    invoice_text = f"""🧾 <b>فاکتور ثبت آگهی</b>

🆔 آیدی پلاتو: {temp.get('platoid', '-')}
⭐ ویپ: {temp.get('vip_count', '-')}
📊 آیتم: {temp.get('item_count', '-')}
🪙 سکه: {temp.get('coin_count', '-')}
💰 پیپ: {temp.get('pip_count', '-')}
🏆 وین: {temp.get('win_count', '-')}
📅 سن: {temp.get('account_age', '-')}
💵 قیمت: {price_text}
━━━━━━━━━━━━━━━━━━━━
💰 هزینه ها:"""
    
    if admin_fee > 0:
        invoice_text += f"\n👑 قیمت گذاری توسط ادمین: {admin_fee:,} تومان"
    invoice_text += f"\n📢 انتشار: {publish_fee:,} تومان"
    invoice_text += f"\n💵 مجموع: {total_fee:,} تومان"
    invoice_text += f"\n\n💰 موجودی کیف پول: {wallet_balance:,} تومان"
    
    if wallet_balance >= total_fee:
        invoice_text += f"\n\n✅ موجودی کیف پول کافی است."
        keyboard = [
            [InlineKeyboardButton("✅ پرداخت از کیف پول", callback_data="pay_from_wallet", style="success")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ]
    elif wallet_balance > 0:
        remaining = total_fee - wallet_balance
        invoice_text += f"\n\n⚠️ موجودی کیف پول ناکافی است.\n💰 قابل پرداخت: {wallet_balance:,} تومان\n💎 باقیمانده: {remaining:,} تومان"
        keyboard = [
            [InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data="card_payment_after_wallet", style="primary")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ]
    else:
        invoice_text += f"\n\n⚠️ موجودی کیف پول صفر است."
        keyboard = [
            [InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data="card_payment_only", style="primary")],
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ]
    
    if update.callback_query:
        await update.callback_query.message.edit_text(invoice_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    else:
        await update.message.reply_text(invoice_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def pay_from_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    wallet_balance = get_wallet_balance(user_id)
    
    if wallet_balance >= total_fee:
        success, new_balance = deduct_from_wallet(user_id, total_fee)
        if success:
            await query.message.edit_text(f"✅ مبلغ {total_fee:,} تومان از کیف پول کسر شد.\n💰 موجودی جدید: {new_balance:,} تومان\n\nدر حال ارسال آگهی به ادمین...")
            await process_payment_complete(update, context, payment_method="کیف پول")
        else:
            await query.message.edit_text("❌ خطا در کسر از کیف پول!")
    else:
        await query.message.edit_text("❌ موجودی کیف پول کافی نیست!")


async def card_payment_after_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    user_id = query.from_user.id
    wallet_balance = get_wallet_balance(user_id)
    remaining = total_fee - wallet_balance
    
    payment_text = f"""💳 <b>پرداخت باقیمانده</b>

💰 مبلغ قابل پرداخت: {remaining:,} تومان
💎 کسر شده از کیف پول: {wallet_balance:,} تومان

🏦 شماره کارت برای واریز:
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 پس از واریز، روی دکمه زیر کلیک کنید.
{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data="payment_done_after_wallet", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
    ]
    await query.message.edit_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def card_payment_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    
    payment_text = f"""💳 <b>پرداخت کارت به کارت</b>

💰 مبلغ قابل پرداخت: {total_fee:,} تومان

🏦 شماره کارت برای واریز:
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 پس از واریز، روی دکمه زیر کلیک کنید.
{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data="payment_done", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
    ]
    await query.message.edit_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['waiting_payment_receipt'] = True
    await query.message.edit_text("📸 لطفاً تصویر رسید واریز را ارسال کنید:")


async def payment_done_after_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['waiting_payment_receipt_after_wallet'] = True
    await query.message.edit_text("📸 لطفاً تصویر رسید واریز را ارسال کنید:")


async def handle_payment_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_payment_receipt'):
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return
    photo = update.message.photo[-1].file_id
    await process_payment_complete_with_receipt(update, context, photo)
    context.user_data['waiting_payment_receipt'] = False


async def handle_payment_receipt_after_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_payment_receipt_after_wallet'):
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return
    
    photo = update.message.photo[-1].file_id
    user_id = update.effective_user.id
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    wallet_balance = get_wallet_balance(user_id)
    
    deduct_from_wallet(user_id, wallet_balance)
    await process_payment_complete_with_receipt(update, context, photo, wallet_balance, "کیف پول + کارت به کارت")
    context.user_data['waiting_payment_receipt_after_wallet'] = False


async def process_payment_complete(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_method="کارت به کارت"):
    agahi_id = get_next_ad_id()
    temp = context.user_data.get('temp_agahi', {})
    
    if not temp:
        await update.message.reply_text("❌ خطا! اطلاعات آگهی یافت نشد.")
        return
    
    price_method = context.user_data.get('price_method', 'self')
    publish_method = context.user_data.get('publish_method', 'game')
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    new_agahi = {
        'id': agahi_id,
        'user_id': user_id,
        'user_name': update.effective_user.first_name or 'کاربر',
        'username': username,
        'game': 'platoyar',
        'platoid': temp.get('platoid', ''),
        'vip_count': temp.get('vip_count', '0'),
        'item_count': temp.get('item_count', '0'),
        'coin_count': temp.get('coin_count', '0'),
        'pip_count': temp.get('pip_count', '0'),
        'win_count': temp.get('win_count', '0'),
        'account_age': temp.get('account_age', '0'),
        'seller_note': temp.get('seller_note', ''),
        'price': temp.get('price', ''),
        'profile_photo': temp.get('profile_photo'),
        'games_photo': temp.get('games_photo'),
        'video': temp.get('video'),
        'price_method': price_method,
        'publish_method': publish_method,
        'total_fee': total_fee,
        'status': 'pending',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'channel_post_id': None,
        'game_channel_post_id': None,
        'payment_method': payment_method,
        'published': False,
        'discount_history': []
    }
    
    pending_ads = load_pending_ads()
    pending_ads[str(agahi_id)] = new_agahi
    save_pending_ads(pending_ads)
    
    profile = load_profiles().get(str(user_id), {})
    admin_text = f"""🔔 آگهی جدید - نیاز به تایید

🆔 شناسه: {agahi_id}
👤 فروشنده: {update.effective_user.first_name}
🆔 یوزرنیم: @{username if username else 'ندارد'}
📞 شماره تماس: {profile.get('phone', '-')}
🆔 آیدی پلاتو: {temp.get('platoid', '')}
💰 مبلغ پرداختی: {total_fee:,} تومان
💳 روش پرداخت: {payment_method}

⭐ ویپ: {temp.get('vip_count', '0')}
📊 آیتم: {temp.get('item_count', '0')}
🪙 سکه: {temp.get('coin_count', '0')}
💰 پیپ: {temp.get('pip_count', '0')}
🏆 وین: {temp.get('win_count', '0')}
📅 سن: {temp.get('account_age', '0')}
📝 توضیحات: {temp.get('seller_note', '')}
💵 قیمت: {temp.get('price') if price_method == 'self' else 'تعیین توسط ادمین'}
📢 انتشار: {'کانال بازی' if publish_method == 'game' else 'هر دو کانال'}"""
    
    if price_method == 'admin':
        keyboard = [
            [InlineKeyboardButton("💰 تعیین قیمت و تایید", callback_data=f"set_price_{agahi_id}", style="success")],
            [InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_ad_{agahi_id}", style="danger")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎨 انتخاب رنگ دکمه", callback_data=f"select_color_{agahi_id}", style="primary")],
            [InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_ad_{agahi_id}", style="danger")]
        ]
    
    # تعیین قیمت → گروه ۲ ، انتشار (قیمت مشخص) → گروه ۳
    target = GROUP_ADS
    # اول عکس‌ها و فیلم، بعد مشخصات و دکمه‌ها
    if new_agahi.get('profile_photo'):
        await send_to_target(context, target, photo=new_agahi['profile_photo'], caption="📸 عکس پروفایل اکانت")
    if new_agahi.get('games_photo'):
        await send_to_target(context, target, photo=new_agahi['games_photo'], caption="📸 عکس بازی ها و لول آپ")
    if new_agahi.get('video'):
        await send_to_target(context, target, video=new_agahi['video'], caption="🎥 فیلم آیتم های اکانت")

    admin_msgs = await send_to_target(context, target, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data[f'admin_msg_{agahi_id}'] = admin_msgs

    if update.callback_query:
        await update.callback_query.message.edit_text(f"✅ آگهی شما برای تایید به ادمین ارسال شد!\n🆔 شناسه: {agahi_id}\n💳 روش پرداخت: {payment_method}\n{SIGNATURE}")
    else:
        await update.message.reply_text(f"✅ آگهی شما برای تایید به ادمین ارسال شد!\n🆔 شناسه: {agahi_id}\n💳 روش پرداخت: {payment_method}\n{SIGNATURE}")
    
    context.user_data['temp_agahi'] = None
    context.user_data['price_method'] = None
    context.user_data['admin_price_fee'] = 0
    context.user_data['publish_fee'] = None


async def process_payment_complete_with_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE, receipt_photo, wallet_deducted=0, payment_method="کارت به کارت"):
    agahi_id = get_next_ad_id()
    temp = context.user_data.get('temp_agahi', {})
    
    if not temp:
        await update.message.reply_text("❌ خطا! اطلاعات آگهی یافت نشد.")
        return
    
    price_method = context.user_data.get('price_method', 'self')
    publish_method = context.user_data.get('publish_method', 'game')
    admin_fee = context.user_data.get('admin_price_fee', 0)
    publish_fee = context.user_data.get('publish_fee', 0)
    total_fee = admin_fee + publish_fee
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    if wallet_deducted > 0:
        payment_method = f"کیف پول ({wallet_deducted:,} تومان) + کارت به کارت ({total_fee - wallet_deducted:,} تومان)"
    
    new_agahi = {
        'id': agahi_id,
        'user_id': user_id,
        'user_name': update.effective_user.first_name or 'کاربر',
        'username': username,
        'game': 'platoyar',
        'platoid': temp.get('platoid', ''),
        'vip_count': temp.get('vip_count', '0'),
        'item_count': temp.get('item_count', '0'),
        'coin_count': temp.get('coin_count', '0'),
        'pip_count': temp.get('pip_count', '0'),
        'win_count': temp.get('win_count', '0'),
        'account_age': temp.get('account_age', '0'),
        'seller_note': temp.get('seller_note', ''),
        'price': temp.get('price', ''),
        'profile_photo': temp.get('profile_photo'),
        'games_photo': temp.get('games_photo'),
        'video': temp.get('video'),
        'price_method': price_method,
        'publish_method': publish_method,
        'total_fee': total_fee,
        'status': 'pending',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'channel_post_id': None,
        'game_channel_post_id': None,
        'payment_method': payment_method,
        'published': False,
        'discount_history': []
    }
    
    pending_ads = load_pending_ads()
    pending_ads[str(agahi_id)] = new_agahi
    save_pending_ads(pending_ads)
    
    profile = load_profiles().get(str(user_id), {})
    admin_text = f"""🔔 آگهی جدید - نیاز به تایید

🆔 شناسه: {agahi_id}
👤 فروشنده: {update.effective_user.first_name}
🆔 یوزرنیم: @{username if username else 'ندارد'}
📞 شماره تماس: {profile.get('phone', '-')}
🆔 آیدی پلاتو: {temp.get('platoid', '')}
💰 مبلغ پرداختی: {total_fee:,} تومان
💳 روش پرداخت: {payment_method}

⭐ ویپ: {temp.get('vip_count', '0')}
📊 آیتم: {temp.get('item_count', '0')}
🪙 سکه: {temp.get('coin_count', '0')}
💰 پیپ: {temp.get('pip_count', '0')}
🏆 وین: {temp.get('win_count', '0')}
📅 سن: {temp.get('account_age', '0')}
📝 توضیحات: {temp.get('seller_note', '')}
💵 قیمت: {temp.get('price') if price_method == 'self' else 'تعیین توسط ادمین'}
📢 انتشار: {'کانال بازی' if publish_method == 'game' else 'هر دو کانال'}"""
    
    if price_method == 'admin':
        keyboard = [
            [InlineKeyboardButton("💰 تعیین قیمت و تایید", callback_data=f"set_price_{agahi_id}", style="success")],
            [InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_ad_{agahi_id}", style="danger")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎨 انتخاب رنگ دکمه", callback_data=f"select_color_{agahi_id}", style="primary")],
            [InlineKeyboardButton("❌ رد آگهی", callback_data=f"reject_ad_{agahi_id}", style="danger")]
        ]
    
    # تعیین قیمت → گروه ۲ ، انتشار (قیمت مشخص) → گروه ۳
    target = GROUP_ADS
    # اول عکس‌ها و فیلم اکانت، بعد مشخصات و رسید و دکمه‌ها
    if new_agahi.get('profile_photo'):
        await send_to_target(context, target, photo=new_agahi['profile_photo'], caption="📸 عکس پروفایل اکانت")
    if new_agahi.get('games_photo'):
        await send_to_target(context, target, photo=new_agahi['games_photo'], caption="📸 عکس بازی ها و لول آپ")
    if new_agahi.get('video'):
        await send_to_target(context, target, video=new_agahi['video'], caption="🎥 فیلم آیتم های اکانت")

    admin_msgs = await send_to_target(context, target, photo=receipt_photo, caption=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))

    context.user_data[f'admin_msg_{agahi_id}'] = admin_msgs
    
    await update.message.reply_text(f"✅ آگهی شما برای تایید به ادمین ارسال شد!\n🆔 شناسه: {agahi_id}\n💳 روش پرداخت: {payment_method}\n{SIGNATURE}")
    
    context.user_data['temp_agahi'] = None
    context.user_data['price_method'] = None
    context.user_data['admin_price_fee'] = 0
    context.user_data['publish_fee'] = None


async def price_only_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .profile import start_profile_completion  # import محلی برای پرهیز از چرخه
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if is_blacklisted(user_id):
        await query.message.edit_text("⛔ شما از دسترسی به ربات محروم شده اید!")
        return
    
    if not is_profile_complete(user_id):
        context.user_data['return_to'] = 'price_only_start'
        await start_profile_completion(update, context)
        return
    
    context.user_data['price_only_mode'] = True
    context.user_data['temp_agahi'] = {}
    context.user_data['agahi_step'] = 'waiting_vip_count_priceonly'
    context.user_data['last_question_msg_id'] = None
    
    sent_msg = await query.message.edit_text(
        "💰 <b>قیمت گذاری فقط توسط ادمین</b>\n\n"
        "📌 هزینه: 20,000 تومان\n"
        "📌 پس از تعیین قیمت، به شما اطلاع داده می‌شود.\n\n"
        "لطفاً اطلاعات اکانت خود را وارد کنید:\n\n"
        "⭐ تعداد ویپ را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]
        ]),
        parse_mode="HTML"
    )
    context.user_data['last_question_msg_id'] = sent_msg.message_id


async def process_price_only_request(update: Update, context: ContextTypes.DEFAULT_TYPE, receipt_photo=None, payment_method="کارت به کارت"):
    temp = context.user_data.get('temp_agahi', {})
    
    if not temp:
        await update.message.reply_text("❌ خطا! اطلاعات آگهی یافت نشد.")
        return
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    username = update.effective_user.username
    profile = load_profiles().get(str(user_id), {})
    
    request_id = get_next_ad_id()
    
    price_request = {
        'id': request_id,
        'user_id': user_id,
        'user_name': user_name,
        'username': username,
        'phone': profile.get('phone', '-'),
        'card_number': profile.get('card_number', '-'),
        'platoid': temp.get('platoid', ''),
        'vip_count': temp.get('vip_count', '0'),
        'item_count': temp.get('item_count', '0'),
        'coin_count': temp.get('coin_count', '0'),
        'pip_count': temp.get('pip_count', '0'),
        'win_count': temp.get('win_count', '0'),
        'account_age': temp.get('account_age', '0'),
        'seller_note': temp.get('seller_note', ''),
        'profile_photo': temp.get('profile_photo'),
        'games_photo': temp.get('games_photo'),
        'status': 'pending',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'payment_method': payment_method
    }
    
    price_requests = load_price_requests()
    price_requests[str(request_id)] = price_request
    save_price_requests(price_requests)
    
    admin_text = f"""🔔 درخواست قیمت گذاری

🆔 کد: {request_id}
👤 فروشنده: {user_name}
🆔 یوزرنیم: @{username if username else 'ندارد'}
📞 شماره تماس: {profile.get('phone', '-')}
🆔 آیدی پلاتو: {temp.get('platoid', '')}
💳 روش پرداخت: {payment_method}

⭐ ویپ: {temp.get('vip_count', '0')}
📊 آیتم: {temp.get('item_count', '0')}
🪙 سکه: {temp.get('coin_count', '0')}
💰 پیپ: {temp.get('pip_count', '0')}
🏆 وین: {temp.get('win_count', '0')}
📅 سن: {temp.get('account_age', '0')}

📝 توضیحات:
{temp.get('seller_note', '')}"""

    keyboard = [
        [InlineKeyboardButton("💰 ثبت قیمت", callback_data=f"price_set_{request_id}", style="success")],
        [InlineKeyboardButton("❌ رد درخواست", callback_data=f"reject_price_only_{request_id}", style="danger")]
    ]
    
    try:
        # سفارش تعیین قیمت اکانت → گروه ۲ ؛ اول عکس‌ها بعد مشخصات و دکمه‌ها
        if temp.get('profile_photo'):
            await send_to_target(context, GROUP_PRICING, photo=temp['profile_photo'], caption="📸 عکس پروفایل")
        if temp.get('games_photo'):
            await send_to_target(context, GROUP_PRICING, photo=temp['games_photo'], caption="📸 عکس بازی ها")

        if receipt_photo:
            admin_msgs = await send_to_target(context, GROUP_PRICING, photo=receipt_photo, caption=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            admin_msgs = await send_to_target(context, GROUP_PRICING, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))

        context.user_data[f'price_only_admin_msg_{request_id}'] = admin_msgs
        
        await update.message.reply_text(f"✅ درخواست شما با کد {request_id} به ادمین ارسال شد.\nپس از تعیین قیمت، به شما اطلاع داده می شود.\n{SIGNATURE}")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ خطا در ارسال درخواست! لطفاً دوباره تلاش کنید.")
    
    context.user_data['price_only_mode'] = False
    context.user_data['temp_agahi'] = None
    context.user_data['agahi_step'] = None
