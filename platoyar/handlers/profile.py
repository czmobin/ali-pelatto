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


# ---- شیم برای صدا زدن هندلرهای callback از داخل یک پیام متنی ----
# (بعد از تکمیل پروفایل، ادامه‌ی فلوی ثبت آگهی/خرید که برای دکمه نوشته شده‌اند)
class _EditableMessage:
    """پیام کاربر را می‌پیچد؛ edit_text را به reply_text (پیام جدید) تبدیل می‌کند."""
    def __init__(self, message):
        self._m = message

    async def edit_text(self, *args, **kwargs):
        return await self._m.reply_text(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._m, name)


class _FakeQuery:
    def __init__(self, message, user):
        self.message = _EditableMessage(message)
        self.from_user = user
        self.data = None

    async def answer(self, *args, **kwargs):
        pass


class _FakeCallbackUpdate:
    """آبجکتی که مثل یک Update دارای callback_query رفتار می‌کند."""
    def __init__(self, update):
        self.callback_query = _FakeQuery(update.message, update.effective_user)
        self.effective_user = update.effective_user
        self.effective_chat = update.effective_chat
        self.message = None


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    profiles = load_profiles()
    profile = profiles.get(str(user_id), {})
    
    name = profile.get('name', 'ثبت نشده')
    phone = profile.get('phone', 'ثبت نشده')
    phone_verified = profile.get('phone_verified', False)
    card_number = profile.get('card_number', 'ثبت نشده')
    balance = get_wallet_balance(user_id)
    
    verified_status = "✅ تایید شده" if phone_verified else "❌ تایید نشده"
    
    profile_text = f"""👤 <b>پروفایل کاربری</b>

━━━━━━━━━━━━━━━━━━━━
📛 <b>نام:</b> {name}
📞 <b>شماره تماس:</b> {phone}
🔐 <b>وضعیت تایید:</b> {verified_status}
🏦 <b>شماره کارت:</b> {card_number}
💰 <b>موجودی کیف پول:</b> {balance:,} تومان
{SIGNATURE}"""
    
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data="agahi_profile_complete", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت به منوی آگهی", callback_data="agahi_menu", style="primary")]
    ]
    
    await query.message.edit_text(profile_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def agahi_profile_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    profiles = load_profiles()
    if str(user_id) not in profiles:
        profiles[str(user_id)] = {}
    
    context.user_data['profile_step'] = 'waiting_name'
    context.user_data['return_to'] = 'agahi_menu'
    
    await query.message.edit_text(
        "👤 <b>تکمیل پروفایل کاربری</b>\n\n"
        "لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]
        ]),
        parse_mode="HTML"
    )


async def start_profile_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, 'callback_query') and update.callback_query:
        query = update.callback_query
        await query.answer()
        sent_msg = await query.message.edit_text("👤 <b>تکمیل پروفایل کاربری</b>\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]]), parse_mode="HTML")
    else:
        sent_msg = await update.message.reply_text("👤 <b>تکمیل پروفایل کاربری</b>\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]]), parse_mode="HTML")
    context.user_data['profile_step'] = 'waiting_name'
    context.user_data['last_question_msg_id'] = sent_msg.message_id


async def handle_profile_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .ads import agahi_submit_start, price_only_start  # import محلی برای پرهیز از چرخه
    from .buy import process_buy_from_channel
    step = context.user_data.get('profile_step')
    if not step:
        return
    user_id = update.effective_user.id
    text = update.message.text
    profiles = load_profiles()
    if str(user_id) not in profiles:
        profiles[str(user_id)] = {}
    
    try:
        await update.message.delete()
    except:
        pass
    
    if context.user_data.get('last_question_msg_id'):
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_question_msg_id']
            )
        except:
            pass
    
    if step == 'waiting_name':
        profiles[str(user_id)]['name'] = text
        save_profiles(profiles)
        context.user_data['profile_step'] = 'waiting_phone'
        sent_msg = await update.message.reply_text(
            f"✅ نام شما: {text}\n\n📞 شماره موبایل خود را وارد کنید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]])
        )
        context.user_data['last_question_msg_id'] = sent_msg.message_id
        
    elif step == 'waiting_phone':
        if text.startswith('09') and len(text) == 11 and text.isdigit():
            profiles[str(user_id)]['phone'] = text
            save_profiles(profiles)
            otp = generate_otp()
            otp_cache[str(user_id)] = otp
            
            success, msg = send_otp_via_kavenegar(text, otp)
            
            voice_btn = [[InlineKeyboardButton("📞 پیامک دریافت نکردم | تماس صوتی", callback_data=f"voice_call_{user_id}", style="primary")]]
            
            if success:
                context.user_data['profile_step'] = 'waiting_otp'
                sent_msg = await update.message.reply_text(
                    f"✅ کد تایید به شماره {text} ارسال شد.\n\n🔐 کد 4 رقمی را وارد کنید:",
                    reply_markup=InlineKeyboardMarkup(voice_btn)
                )
                context.user_data['last_question_msg_id'] = sent_msg.message_id
            else:
                await update.message.reply_text(
                    f"❌ ارسال پیامک به شماره {text} ناموفق بود!\n\n📞 برای دریافت کد، روی دکمه تماس صوتی کلیک کنید:",
                    reply_markup=InlineKeyboardMarkup(voice_btn)
                )
        else:
            await update.message.reply_text("❌ شماره موبایل نامعتبر! لطفاً شماره 11 رقمی با فرمت 09xxxxxxxxx وارد کنید.")
            
    elif step == 'waiting_otp':
        if otp_cache.get(str(user_id)) == text:
            profiles[str(user_id)]['phone_verified'] = True
            save_profiles(profiles)
            context.user_data['profile_step'] = 'waiting_card'
            sent_msg = await update.message.reply_text(
                "✅ شماره موبایل تایید شد!\n\n💳 شماره کارت بانکی خود را وارد کنید:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]])
            )
            context.user_data['last_question_msg_id'] = sent_msg.message_id
            del otp_cache[str(user_id)]
        else:
            await update.message.reply_text("❌ کد تایید اشتباه است!")
            
    elif step == 'waiting_card':
        if len(text) == 16 and text.isdigit():
            profiles[str(user_id)]['card_number'] = text
            save_profiles(profiles)
            context.user_data['profile_step'] = None
            context.user_data['last_question_msg_id'] = None
            
            user_name = update.effective_user.first_name or "کاربر عزیز"
            welcome_msg = f"""🎉 <b>ثبت نام با موفقیت انجام شد!</b>

👤 <b>کاربر گرامی {user_name}</b>

✅ پروفایل شما با موفقیت تکمیل شد.
💰 کیف پول شما آماده شارژ است.
📢 می‌توانید آگهی خود را ثبت کنید.

{SIGNATURE}"""
            
            if context.user_data.get('profile_for_buy'):
                context.user_data['profile_for_buy'] = False
                ad_id = context.user_data.get('return_to_buy')
                if ad_id:
                    await update.message.reply_text(welcome_msg, parse_mode="HTML")
                    await process_buy_from_channel(update, context, ad_id)
                    
            elif context.user_data.get('return_to') == 'price_only_start':
                context.user_data['return_to'] = None
                await update.message.reply_text(welcome_msg, parse_mode="HTML")
                await price_only_start(_FakeCallbackUpdate(update), context)
                
            elif context.user_data.get('return_to') == 'agahi_submit_start':
                context.user_data['return_to'] = None
                await update.message.reply_text(welcome_msg, parse_mode="HTML")
                await agahi_submit_start(_FakeCallbackUpdate(update), context)
                
            else:
                await update.message.reply_text(
                    welcome_msg,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت آگهی", callback_data="agahi_submit_start", style="success")],
                        [InlineKeyboardButton("💼 کیف پول", callback_data="wallet_menu", style="primary")],
                        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_to_main", style="primary")]
                    ]),
                    parse_mode="HTML"
                )
        else:
            await update.message.reply_text("❌ شماره کارت نامعتبر! لطفاً 16 رقم را وارد کنید.")
