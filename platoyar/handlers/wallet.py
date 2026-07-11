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


async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = get_wallet_balance(user_id)
    profile = load_profiles().get(str(user_id), {})
    card_number = profile.get('card_number', 'ثبت نشده')
    
    text = f"""💼 <b>کیف پول شما</b>

━━━━━━━━━━━━━━━━━━━━
💰 <b>موجودی فعلی:</b> {balance:,} تومان
🏦 <b>شماره کارت ثبت شده:</b> {card_number}
━━━━━━━━━━━━━━━━━━━━

📋 <b>راهنما:</b>
• موجودی فقط برای ثبت آگهی قابل استفاده است
• حداقل مبلغ برداشت: {MIN_WITHDRAW_AMOUNT:,} تومان

{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("💰 شارژ کیف پول", callback_data="charge_wallet", style="success")],
        [InlineKeyboardButton("💸 برداشت از کیف پول", callback_data="withdraw_wallet", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت به منوی آگهی", callback_data="agahi_menu", style="primary")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def charge_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    charge_text = f"""💰 <b>شارژ کیف پول</b>

━━━━━━━━━━━━━━━━━━━━
🏦 <b>شماره کارت برای واریز:</b>
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 مبلغ مورد نظر خود را به کارت فوق واریز کنید.
پس از واریز، تصویر رسید را ارسال کنید.

⚠️ حداقل مبلغ شارژ: ۱۰,۰۰۰ تومان
{SIGNATURE}"""

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data="wallet_menu", style="primary")]]
    await query.message.edit_text(charge_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    context.user_data['waiting_charge_receipt'] = True


async def handle_charge_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_charge_receipt'):
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر رسید ارسال کنید.")
        return
    
    photo = update.message.photo[-1].file_id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    admin_text = f"""💰 درخواست شارژ کیف پول

👤 کاربر: {user_name}
🆔 آیدی: {user_id}

لطفاً مبلغ واریزی را مشخص کنید:"""

    keyboard = [
        [InlineKeyboardButton("✅ تایید و شارژ", callback_data=f"confirm_charge_{user_id}", style="success")],
        [InlineKeyboardButton("❌ رد", callback_data=f"reject_charge_{user_id}", style="danger")]
    ]
    
    await send_to_target(context, GROUP_WALLET, photo=photo, caption=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text("✅ رسید شما به ادمین ارسال شد.\nپس از تایید، کیف پول شما شارژ می‌شود.")
    context.user_data['waiting_charge_receipt'] = False


async def confirm_charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    
    context.user_data['charge_user_id'] = user_id
    await query.message.reply_text("💰 لطفاً مبلغ واریزی را به تومان وارد کنید:")


async def process_charge_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('charge_user_id')
    if not user_id:
        return
    
    try:
        amount = int(update.message.text.replace(',', '').strip())
        if amount < 10000:
            await update.message.reply_text("❌ حداقل مبلغ شارژ ۱۰,۰۰۰ تومان است!")
            return
    except:
        await update.message.reply_text("❌ مبلغ نامعتبر!")
        return
    
    new_balance = add_to_wallet(user_id, amount)
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ کیف پول شما به مبلغ {amount:,} تومان شارژ شد.\n💰 موجودی جدید: {new_balance:,} تومان"
    )
    await update.message.reply_text(f"✅ کیف پول کاربر به مبلغ {amount:,} تومان شارژ شد.")
    context.user_data['charge_user_id'] = None


async def reject_charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    
    await query.message.reply_text("❌ لطفاً دلیل رد شارژ را وارد کنید:")
    context.user_data['reject_charge_user_id'] = user_id


async def process_reject_charge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('reject_charge_user_id')
    if not user_id:
        return
    
    reason = update.message.text
    await context.bot.send_message(
        chat_id=user_id,
        text=f"❌ درخواست شارژ کیف پول شما رد شد.\n📝 دلیل: {reason}"
    )
    await update.message.reply_text(f"✅ درخواست شارژ کاربر رد شد.")
    context.user_data['reject_charge_user_id'] = None


async def withdraw_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = get_wallet_balance(user_id)
    profile = load_profiles().get(str(user_id), {})
    card_number = profile.get('card_number', 'ثبت نشده')
    
    if balance <= 0:
        await query.message.edit_text("❌ موجودی کیف پول شما صفر است! امکان برداشت وجود ندارد.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet_menu", style="primary")]]))
        return
    
    if balance < MIN_WITHDRAW_AMOUNT:
        await query.message.edit_text(
            f"❌ حداقل مبلغ برداشت {MIN_WITHDRAW_AMOUNT:,} تومان است!\n"
            f"💰 موجودی شما: {balance:,} تومان",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet_menu", style="primary")]])
        )
        return
    
    text = f"""💸 <b>برداشت از کیف پول</b>

━━━━━━━━━━━━━━━━━━━━
💰 <b>موجودی قابل برداشت:</b> {balance:,} تومان
🏦 <b>شماره کارت ثبت شده:</b> {card_number}
⚠️ <b>حداقل مبلغ برداشت:</b> {MIN_WITHDRAW_AMOUNT:,} تومان

⚠️ مبلغ به همین شماره کارت واریز خواهد شد.
{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("✅ تایید و ادامه", callback_data="withdraw_confirm_same", style="success")],
        [InlineKeyboardButton("🔄 تغییر شماره کارت", callback_data="withdraw_new_card", style="primary")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="wallet_menu", style="danger")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def withdraw_confirm_same(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    balance = get_wallet_balance(user_id)
    
    context.user_data['withdraw_amount'] = balance
    await query.message.edit_text(f"💰 مبلغ {balance:,} تومان از کیف پول شما برداشت خواهد شد.\n\n✅ برای تایید نهایی، دکمه زیر را لمس کنید:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید نهایی برداشت", callback_data="withdraw_final", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="wallet_menu", style="danger")]
    ]))


async def withdraw_new_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['waiting_new_card'] = True
    await query.message.edit_text("💳 لطفاً شماره کارت بانکی جدید خود را وارد کنید (16 رقم):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 انصراف", callback_data="wallet_menu", style="danger")]]))


async def process_new_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_new_card'):
        return
    
    card_number = update.message.text.strip()
    if len(card_number) != 16 or not card_number.isdigit():
        await update.message.reply_text("❌ شماره کارت نامعتبر! لطفاً 16 رقم را وارد کنید.")
        return
    
    user_id = update.effective_user.id
    profiles = load_profiles()
    if str(user_id) not in profiles:
        profiles[str(user_id)] = {}
    profiles[str(user_id)]['card_number'] = card_number
    save_profiles(profiles)
    
    balance = get_wallet_balance(user_id)
    context.user_data['withdraw_amount'] = balance
    context.user_data['waiting_new_card'] = False
    
    await update.message.reply_text(f"✅ شماره کارت جدید با موفقیت ثبت شد.\n\n💰 مبلغ {balance:,} تومان از کیف پول شما برداشت خواهد شد.\n\n✅ برای تایید نهایی، دکمه زیر را لمس کنید:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید نهایی برداشت", callback_data="withdraw_final", style="success")],
        [InlineKeyboardButton("🔙 انصراف", callback_data="wallet_menu", style="danger")]
    ]), parse_mode="HTML")


async def withdraw_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    amount = context.user_data.get('withdraw_amount', 0)
    
    if amount <= 0:
        await query.message.edit_text("❌ خطا! مبلغ نامعتبر.")
        return
    
    if amount < MIN_WITHDRAW_AMOUNT:
        await query.message.edit_text(f"❌ حداقل مبلغ برداشت {MIN_WITHDRAW_AMOUNT:,} تومان است!")
        return
    
    profile = load_profiles().get(str(user_id), {})
    admin_text = f"""💰 درخواست برداشت از کیف پول

👤 کاربر: {profile.get('name', '-')}
🆔 آیدی: {user_id}
📞 شماره تماس: {profile.get('phone', '-')}
🏦 شماره کارت: {profile.get('card_number', '-')}
💰 مبلغ درخواستی: {amount:,} تومان

لطفاً اقدام به واریز کنید:"""
    
    keyboard = [
        [InlineKeyboardButton("✅ تایید و پرداخت", callback_data=f"withdraw_approve_{user_id}_{amount}", style="success")],
        [InlineKeyboardButton("❌ رد", callback_data=f"withdraw_reject_{user_id}_{amount}", style="danger")]
    ]
    
    await send_to_target(context, GROUP_WALLET, text=admin_text, reply_markup=InlineKeyboardMarkup(keyboard))
    await query.message.edit_text("✅ درخواست برداشت شما به ادمین ارسال شد.\n📌 پس از تایید، مبلغ به حساب شما واریز می شود.")
    context.user_data['withdraw_amount'] = None


async def withdraw_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])
    
    context.user_data['withdraw_approve_user_id'] = user_id
    context.user_data['withdraw_approve_amount'] = amount
    await query.message.reply_text(f"💰 لطفاً تصویر رسید واریز {amount:,} تومانی به حساب کاربر را ارسال کنید:")


async def withdraw_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    amount = int(parts[3])
    
    await query.message.reply_text("❌ لطفاً دلیل رد درخواست برداشت را وارد کنید:")
    context.user_data['withdraw_reject_user_id'] = user_id


async def process_withdraw_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('withdraw_reject_user_id')
    if not user_id:
        return
    reason = update.message.text
    await context.bot.send_message(chat_id=user_id, text=f"❌ درخواست برداشت شما رد شد.\n📝 دلیل: {reason}")
    await update.message.reply_text(f"✅ درخواست برداشت کاربر رد شد.")
    context.user_data['withdraw_reject_user_id'] = None


async def handle_withdraw_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('withdraw_approve_user_id')
    amount = context.user_data.get('withdraw_approve_amount')
    
    if not user_id or not amount:
        return
    
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return
    
    success, new_balance = deduct_from_wallet(user_id, amount)
    if success:
        await context.bot.send_message(chat_id=user_id, text=f"✅ مبلغ {amount:,} تومان از کیف پول شما کسر و به حساب شما واریز شد.\n💰 موجودی جدید: {new_balance:,} تومان")
        await update.message.reply_text(f"✅ رسید برای کاربر ارسال شد و {amount:,} تومان از کیف پول کسر گردید.")
    else:
        await update.message.reply_text("❌ خطا در کسر از کیف پول!")
    
    context.user_data['withdraw_approve_user_id'] = None
    context.user_data['withdraw_approve_amount'] = None
