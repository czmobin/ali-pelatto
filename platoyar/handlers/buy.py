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


async def voice_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    user_id = int(parts[2])
    
    current_time = datetime.now()
    last_call = voice_call_cooldown.get(str(user_id))
    
    if last_call:
        time_diff = (current_time - last_call).total_seconds()
        if time_diff < VOICE_CALL_COOLDOWN:
            remaining = int(VOICE_CALL_COOLDOWN - time_diff)
            await query.message.edit_text(
                f"⏳ لطفاً {remaining} ثانیه دیگر صبر کنید!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_operation", style="danger")]
                ])
            )
            return
    
    profile = load_profiles().get(str(user_id), {})
    phone = profile.get('phone')
    
    if not phone:
        await query.message.edit_text("❌ شماره موبایل یافت نشد!")
        return
    
    otp = otp_cache.get(str(user_id))
    if not otp:
        otp = generate_otp()
        otp_cache[str(user_id)] = otp
    
    voice_call_cooldown[str(user_id)] = current_time
    
    try:
        url = f"https://api.kavenegar.com/v1/{KAVENEGAR_API_KEY}/verify/lookup.json"
        payload = {
            'receptor': phone,
            'token': otp,
            'template': KAVENEGAR_TEMPLATE_VERIFY,
            'type': 'call'
        }
        response = requests.get(url, params=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('return', {}).get('status') == 200:
                await query.message.edit_text(
                    f"✅ کد تایید با تماس صوتی به شماره {phone} ارسال شد.\n\n🔐 کد 4 رقمی را وارد کنید:",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📞 درخواست مجدد (1 دقیقه)", callback_data=f"voice_call_{user_id}", style="primary")]
                    ])
                )
                return
        
        await query.message.edit_text(
            "❌ ارسال تماس صوتی ناموفق بود!\n\nلطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 درخواست مجدد (1 دقیقه)", callback_data=f"voice_call_{user_id}", style="primary")]
            ])
        )
    except:
        await query.message.edit_text(
            "❌ خطا در ارسال تماس صوتی!\n\nلطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 درخواست مجدد (1 دقیقه)", callback_data=f"voice_call_{user_id}", style="primary")]
            ])
        )


async def process_buy_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id):
    user_id = update.effective_user.id
    
    if not is_profile_complete(user_id):
        # نام خودکار از تلگرام؛ مستقیم شماره موبایل را می‌گیریم
        profiles = load_profiles()
        if str(user_id) not in profiles:
            profiles[str(user_id)] = {}
        profiles[str(user_id)]['name'] = update.effective_user.first_name or 'کاربر'
        save_profiles(profiles)
        context.user_data['return_to_buy'] = ad_id
        await update.message.reply_text("👤 برای خرید ابتدا پروفایل خود را تکمیل کنید.\n📞 شماره موبایل خود را وارد کنید:")
        context.user_data['profile_step'] = 'waiting_phone'
        context.user_data['profile_for_buy'] = True
        return
    
    all_agahi = load_agahi()
    ad = None
    seller_id = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id and a.get('published') and a.get('status') == 'published':
                ad = a
                seller_id = int(uid)
                break
        if ad:
            break
    
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد یا فروش رفته است!")
        return
    
    global temp_purchase_data
    temp_purchase_data[user_id] = {'ad_id': ad_id, 'seller_id': seller_id, 'ad_data': ad}
    
    final_price = ad.get('price')
    if final_price is None:
        final_price = 0
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                final_price = disc['new_price']
                break
    
    # کاربر عکس/فیلم/مشخصات را در کانال دیده؛ اینجا مستقیم می‌رویم سراغ پرداخت.
    price_text = f"<b>{final_price:,}</b> تومان"

    payment_text = f"""💰 <b>تکمیل خرید اکانت</b>

🆔 شناسه آگهی: {ad_id}
💵 مبلغ قابل پرداخت: {price_text}

🏦 <b>شماره کارت برای واریز:</b>
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 مبلغ بالا را به کارت فوق واریز کنید، سپس دکمه «پرداخت انجام شد» را بزنید و تصویر رسید را ارسال کنید.
{SIGNATURE}"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data=f"receipt_buy_{ad_id}", style="success")],
        [InlineKeyboardButton("❌ انصراف", callback_data="back_to_main", style="danger")]
    ])
    await context.bot.send_message(chat_id=user_id, text=payment_text, reply_markup=keyboard, parse_mode="HTML")


async def confirm_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[2])
    buyer_id = query.from_user.id
    global temp_purchase_data
    purchase = temp_purchase_data.get(buyer_id)
    if not purchase or purchase['ad_id'] != ad_id:
        await query.message.edit_text("❌ خطا! دوباره تلاش کنید.")
        return
    ad = purchase['ad_data']
    
    final_price = ad.get('price')
    if final_price is None:
        final_price = 0
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                final_price = disc['new_price']
                break
    
    price_text = f"{final_price:,} تومان"
    payment_text = f"""💰 <b>تکمیل خرید</b>

🆔 آگهی: {ad_id}
💵 مبلغ: {price_text}

🏦 شماره کارت برای واریز:
<code>{CARD_NUMBER}</code>
👤 {CARD_NAME}

📝 پس از واریز، روی دکمه زیر کلیک کنید.
{SIGNATURE}"""

    keyboard = [
        [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data=f"receipt_buy_{ad_id}", style="success")], 
        [InlineKeyboardButton("🔙 انصراف", callback_data="back_to_main", style="danger")]
    ]
    await query.message.edit_text(payment_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def receipt_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[2])
    context.user_data['waiting_buy_receipt'] = ad_id
    await query.message.edit_text("📸 لطفاً تصویر رسید واریز را ارسال کنید:")


async def handle_buy_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('waiting_buy_receipt')
    if not ad_id:
        return
    if not update.message.photo:
        await update.message.reply_text("❌ لطفاً یک تصویر ارسال کنید.")
        return
    photo = update.message.photo[-1].file_id
    buyer_id = update.effective_user.id
    buyer_name = update.effective_user.first_name
    
    context.user_data[f'receipt_buy_{ad_id}'] = photo
    
    global temp_purchase_data
    purchase = temp_purchase_data.get(buyer_id)
    if not purchase:
        await update.message.reply_text("❌ خطا!")
        return
    ad = purchase['ad_data']
    
    final_price = ad.get('price')
    if final_price is None:
        final_price = 0
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                final_price = disc['new_price']
                break
    
    price_text = f"{final_price:,} تومان"
    admin_text = f"""🔔 درخواست خرید جدید

🆔 آگهی: {ad_id}
👤 خریدار: {user_mention(buyer_id, buyer_name)}
🆔 آیدی عددی خریدار: <code>{buyer_id}</code>
👤 فروشنده: {user_mention(ad.get('user_id'), ad.get('user_name'))}
🆔 آیدی عددی فروشنده: <code>{ad.get('user_id')}</code>
💵 مبلغ: {price_text}"""

    keyboard = [
        [InlineKeyboardButton("✅ تایید خرید", callback_data=f"confirm_sale_{ad_id}_{buyer_id}", style="success")],
        [InlineKeyboardButton("❌ رد خرید", callback_data=f"reject_sale_{ad_id}_{buyer_id}", style="danger")]
    ]
    await send_to_target(context, GROUP_WALLET, photo=photo, caption=admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    await update.message.reply_text(f"✅ رسید شما به ادمین ارسال شد.\n🆔 شناسه خرید: {ad_id}\n\nپس از تایید، اکانت به شما تحویل داده می شود.\n{SIGNATURE}")
    context.user_data['waiting_buy_receipt'] = None


async def confirm_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    ad_id = int(parts[2])
    buyer_id = int(parts[3])
    
    all_agahi = load_agahi()
    ad = None
    seller_id = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                seller_id = int(uid)
                break
        if ad:
            break
    
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد!")
        return
    
    global temp_group_links
    temp_group_links[ad_id] = {'seller_id': seller_id, 'buyer_id': buyer_id, 'status': 'waiting_for_link'}
    
    await query.message.reply_text(
        f"🔗 لطفاً لینک گروه انتقال اکانت را ارسال کنید:"
    )
    context.user_data['waiting_group_link'] = ad_id


async def receive_group_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('waiting_group_link')
    if not ad_id:
        return
    
    group_link = update.message.text.strip()
    if not group_link.startswith('https://t.me/'):
        await update.message.reply_text("❌ لینک نامعتبر!")
        return
    
    global temp_group_links
    buyer_id = temp_group_links[ad_id]['buyer_id']
    
    temp_group_links[ad_id]['group_link'] = group_link
    temp_group_links[ad_id]['status'] = 'link_received'
    
    all_agahi = load_agahi()
    ad = None
    seller_id = None
    channel_post_id = None
    game_channel_post_id = None
    channel_button_id = None
    game_channel_button_id = None
    ad_price = None
    publish_date = None

    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                seller_id = int(uid)
                channel_post_id = a.get('channel_post_id')
                game_channel_post_id = a.get('game_channel_post_id')
                channel_button_id = a.get('channel_button_id')
                game_channel_button_id = a.get('game_channel_button_id')
                ad_price = ad.get('price')
                if ad.get('discount_history'):
                    for disc in reversed(ad['discount_history']):
                        if disc.get('is_active', True):
                            ad_price = disc['new_price']
                            break
                publish_date = a.get('publish_date')
                break
        if ad:
            break
    
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد!")
        context.user_data['waiting_group_link'] = None
        return
    
    if ad_price is None:
        ad_price = 0
    
    # محاسبه زمان تا فروش
    days_text = "همان روز"
    if publish_date:
        try:
            pub_date = datetime.strptime(publish_date, "%Y-%m-%d %H:%M:%S")
            sold_date = datetime.now()
            diff = sold_date - pub_date
            
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            
            if days > 0:
                days_text = f"{days} روز و {hours} ساعت"
            elif hours > 0:
                days_text = f"{hours} ساعت و {minutes} دقیقه"
            else:
                days_text = f"{minutes} دقیقه"
        except:
            pass
    
    sold_time = now_jalali()
    seller_note = escape_html(ad.get('seller_note', '-'))
    
    # متن جدید با فروخته شد
    new_post_text = f"""❌ <b>فروخته شد!</b>

🎮 <b>آگهی فروش اکانت پلاتو</b>

🆔 شناسه: {ad_id}

⭐ ویپ: {ad.get('vip_count', '-')}
📊 آیتم: {ad.get('item_count', '-')}
🪙 سکه: {ad.get('coin_count', '-')}
💰 پیپ: {ad.get('pip_count', '-')}
🏆 وین: {ad.get('win_count', '-')}
📅 سن اکانت: {ad.get('account_age', '-')}
💵 قیمت: <s>{ad_price:,}</s> <b>{ad_price:,}</b> تومان ❌

📝 توضیحات:
{seller_note}

━━━━━━━━━━━━━━━━━━━━
⏱ زمان تا فروش: {days_text}
📅 تاریخ فروش: {sold_time}
{SIGNATURE}"""
    
    # متن ریپلای فروخته شد
    reply_text = f"""❌ <b>فروخته شد!</b>

🆔 شناسه: {ad_id}
💰 قیمت نهایی: {ad_price:,} تومان
⏱ زمان تا فروش: {days_text}
📅 تاریخ فروش: {sold_time}
{SIGNATURE}"""
    
    # ویرایش پیام کانال بازی و حذف دکمه
    if game_channel_post_id:
        try:
            if ad.get('profile_photo') or ad.get('games_photo'):
                await context.bot.edit_message_caption(
                    chat_id=GAME_CHANNEL_ID,
                    message_id=game_channel_post_id,
                    caption=new_post_text,
                    parse_mode="HTML",
                    reply_markup=None
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=GAME_CHANNEL_ID,
                    message_id=game_channel_post_id,
                    text=new_post_text,
                    parse_mode="HTML",
                    reply_markup=None
                )
            # حذف پیام دکمه‌ی «اطلاعات بیشتر و خرید» چون اکانت فروخته شد
            if game_channel_button_id:
                try:
                    await context.bot.delete_message(chat_id=GAME_CHANNEL_ID, message_id=game_channel_button_id)
                except Exception:
                    pass
            # ارسال ریپلای
            _sr = await context.bot.send_message(
                chat_id=GAME_CHANNEL_ID,
                text=reply_text,
                reply_to_message_id=game_channel_post_id,
                parse_mode="HTML"
            )
            ad['game_sold_reply_id'] = _sr.message_id
        except Exception as e:
            logger.error(f"خطا در کانال بازی: {e}")
    
    # ویرایش پیام کانال اصلی و حذف دکمه
    if channel_post_id:
        try:
            if ad.get('profile_photo') or ad.get('games_photo'):
                await context.bot.edit_message_caption(
                    chat_id=MAIN_CHANNEL_ID,
                    message_id=channel_post_id,
                    caption=new_post_text,
                    parse_mode="HTML",
                    reply_markup=None
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=MAIN_CHANNEL_ID,
                    message_id=channel_post_id,
                    text=new_post_text,
                    parse_mode="HTML",
                    reply_markup=None
                )
            # حذف پیام دکمه‌ی «اطلاعات بیشتر و خرید» چون اکانت فروخته شد
            if channel_button_id:
                try:
                    await context.bot.delete_message(chat_id=MAIN_CHANNEL_ID, message_id=channel_button_id)
                except Exception:
                    pass
            # ارسال ریپلای
            _sr = await context.bot.send_message(
                chat_id=MAIN_CHANNEL_ID,
                text=reply_text,
                reply_to_message_id=channel_post_id,
                parse_mode="HTML"
            )
            ad['channel_sold_reply_id'] = _sr.message_id
        except Exception as e:
            logger.error(f"خطا در کانال اصلی: {e}")
    
    # ذخیره در دیتابیس
    ad['status'] = 'sold'
    ad['sold_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ad['buyer_id'] = buyer_id
    ad['days_to_sell'] = days_text
    save_agahi(all_agahi)
    
    seller_profile = load_profiles().get(str(seller_id), {})
    buyer_profile = load_profiles().get(str(buyer_id), {})
    
    transfer_text = f"✅ <b>انتقال اکانت</b>\n\n🆔 آگهی: {ad_id}\n💰 مبلغ: {ad_price:,} تومان\n\n🔗 لینک گروه:\n{group_link}\n{SIGNATURE}"
    
    await context.bot.send_message(chat_id=seller_id, text=transfer_text, parse_mode="HTML")
    await context.bot.send_message(chat_id=buyer_id, text=transfer_text, parse_mode="HTML")
    
    # ارسال رسید به خریدار
    receipt_photo = context.user_data.get(f'receipt_buy_{ad_id}')
    if receipt_photo:
        await context.bot.send_photo(
            chat_id=buyer_id,
            photo=receipt_photo,
            caption=f"✅ رسید پرداخت شما برای آگهی {ad_id} تایید شد.\n{SIGNATURE}"
        )
        context.user_data[f'receipt_buy_{ad_id}'] = None
    
    # پیام نهایی
    await update.message.reply_text(f"✅ خرید آگهی {ad_id} تایید شد.\n🔗 لینک گروه برای فروشنده و خریدار ارسال شد.\n{SIGNATURE}")
    revert_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 کنسل معامله و برگرداندن آگهی", callback_data=f"revert_sale_{ad_id}", style="danger")]])
    await send_to_target(context, GROUP_WALLET, text=f"✅ خرید آگهی {ad_id} تکمیل شد.\nلینک گروه: {group_link}\n\nاگر معامله کنسل شد، دکمه‌ی زیر آگهی را به حالت اول برمی‌گرداند:", reply_markup=revert_kb)

    context.user_data['waiting_group_link'] = None


async def revert_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کنسل معامله: آگهیِ فروخته‌شده را به حالت منتشرشده برمی‌گرداند."""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id not in ADMIN_IDS:
        return
    ad_id = int(query.data.split("_")[2])
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a.get('id') == ad_id:
                ad = a
                break
        if ad:
            break
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد.")
        return
    if ad.get('status') != 'sold':
        await query.message.edit_text("این آگهی در حالت فروخته‌شده نیست.")
        return

    bot_username = (await context.bot.get_me()).username
    price_value = ad.get('price')
    # قیمت با تخفیف فعال (اگر باشد)
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                price_value = disc.get('new_price', price_value)
                break
    price_display = f"<b>{price_value:,}</b> تومان" if isinstance(price_value, int) else str(price_value)
    seller_note = escape_html(ad.get('seller_note', '-'))
    post_text = f"""🎮 <b>آگهی فروش اکانت پلاتو</b>

🆔 شناسه: {ad_id}

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

    color = ad.get('button_color', 'green')
    emoji = {"green": "🟢", "red": "🔴", "blue": "🔵"}.get(color, "🟢")
    style = {"green": "success", "red": "danger", "blue": "primary"}.get(color, "success")
    buy_url = f"https://t.me/{bot_username}?start=buy_{ad_id}"
    buy_btn = InlineKeyboardMarkup([[InlineKeyboardButton(f"{emoji} اطلاعات بیشتر و خرید", url=buy_url, style=style)]])

    raw = [m for m in (ad.get('profile_photo'), ad.get('games_photo'), ad.get('video')) if m]

    async def _restore(chat_id, post_id, button_key, sold_reply_key):
        if not post_id:
            return
        try:
            if len(raw) >= 2:
                # آلبوم: کپشن را برگردان، دکمه‌ی خرید را دوباره به‌صورت ریپلای بفرست
                await context.bot.edit_message_caption(chat_id=chat_id, message_id=post_id, caption=post_text, parse_mode="HTML")
                btn = await context.bot.send_message(
                    chat_id=chat_id, text="👆 برای مشاهده‌ی کامل و خرید این اکانت، دکمه‌ی زیر را بزنید:",
                    reply_markup=buy_btn, reply_to_message_id=post_id)
                ad[button_key] = btn.message_id
            elif len(raw) == 1:
                await context.bot.edit_message_caption(chat_id=chat_id, message_id=post_id, caption=post_text, reply_markup=buy_btn, parse_mode="HTML")
            else:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=post_id, text=post_text, reply_markup=buy_btn, parse_mode="HTML")
        except Exception as e:
            logger.error(f"بازگردانی پست ناموفق: {e}")
        # حذف ریپلای «فروخته شد»
        if ad.get(sold_reply_key):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=ad[sold_reply_key])
            except Exception:
                pass
            ad[sold_reply_key] = None

    await _restore(GAME_CHANNEL_ID, ad.get('game_channel_post_id'), 'game_channel_button_id', 'game_sold_reply_id')
    if ad.get('channel_post_id'):
        await _restore(MAIN_CHANNEL_ID, ad.get('channel_post_id'), 'channel_button_id', 'channel_sold_reply_id')

    ad['status'] = 'published'
    ad['published'] = True
    for k in ('sold_date', 'buyer_id', 'days_to_sell'):
        ad.pop(k, None)
    save_agahi(all_agahi)

    await query.message.edit_text(f"🔄 معامله‌ی آگهی {ad_id} کنسل شد و آگهی به حالت منتشرشده برگشت.")
    try:
        await context.bot.send_message(chat_id=ad['user_id'], text=f"🔄 معامله‌ی آگهی {ad_id} کنسل شد و آگهی شما دوباره در چنل فعال شد.\n{SIGNATURE}")
    except Exception:
        pass


async def reject_sale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    ad_id = int(parts[2])
    buyer_id = int(parts[3])
    
    context.user_data['reject_sale_id'] = ad_id
    context.user_data['reject_buyer_id'] = buyer_id
    await query.message.reply_text("❌ لطفاً دلیل رد خرید را وارد کنید:")


async def process_reject_sale_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('reject_sale_id')
    buyer_id = context.user_data.get('reject_buyer_id')
    if not ad_id:
        return
    reason = update.message.text
    await context.bot.send_message(chat_id=buyer_id, text=f"❌ درخواست خرید شما رد شد.\n🆔 آگهی: {ad_id}\nدلیل: {reason}\n{SIGNATURE}")
    await update.message.reply_text(f"✅ خرید آگهی {ad_id} رد شد.")
    context.user_data['reject_sale_id'] = None
    context.user_data['reject_buyer_id'] = None
