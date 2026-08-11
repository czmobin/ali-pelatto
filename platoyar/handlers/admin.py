from datetime import datetime, timedelta
import json
import os
import random
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes

from ..config import *
from ..state import *
from ..storage import *
from ..services import *

logger = logging.getLogger(__name__)


async def approve_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    ad_id = int(parts[2])
    new_price = int(parts[3])
    discount = int(parts[4])
    
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
    
    discount_amount = int(discount)
    discount_text = f"{discount_amount:,} تومان"
    
    if 'discount_history' not in ad:
        ad['discount_history'] = []
    
    for disc in ad['discount_history']:
        disc['is_active'] = False
    
    ad['discount_history'].append({
        'date': now_jalali(),
        'discount_amount': discount_amount,
        'new_price': new_price,
        'discount_text': discount_text,
        'is_active': True
    })
    
    bot_username = (await context.bot.get_me()).username
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 اطلاعات بیشتر و خرید", url=f"https://t.me/{bot_username}?start=buy_{ad_id}", style="success")
    ]])
    
    if len(ad['discount_history']) > 1:
        price_line = f"💵 قیمت اصلی: <s>{ad.get('price'):,}</s> تومان\n💰 قیمت نهایی: <b>{new_price:,}</b> تومان 🔥"
    else:
        price_line = f"💵 <s>{ad.get('price'):,}</s> <b>{new_price:,}</b> تومان 🔥"
    
    seller_note = escape_html(ad.get('seller_note', '-'))
    
    post_text = f"""🎮 <b>آگهی فروش اکانت پلاتو</b>

🆔 شناسه: {ad_id}

⭐ ویپ: {ad.get('vip_count', '-')}
📊 آیتم: {ad.get('item_count', '-')}
🪙 سکه: {ad.get('coin_count', '-')}
💰 پیپ: {ad.get('pip_count', '-')}
🏆 وین: {ad.get('win_count', '-')}
📅 سن اکانت: {ad.get('account_age', '-')}
{price_line}

📝 توضیحات:
{seller_note}
{SIGNATURE}"""
    
    channel_post_id = ad.get('channel_post_id')
    game_channel_post_id = ad.get('game_channel_post_id')
    
    try:
        discount_notice = f"🎉 تخفیف ویژه!\n\nاین آگهی با تخفیف {discount_text} به قیمت {new_price:,} تومان تغییر کرد.\n{SIGNATURE}"
        
        if channel_post_id:
            try:
                if ad.get('profile_photo') and ad.get('games_photo'):
                    await context.bot.edit_message_caption(chat_id=MAIN_CHANNEL_ID, message_id=channel_post_id, caption=post_text, parse_mode="HTML")
                elif ad.get('profile_photo'):
                    await context.bot.edit_message_caption(chat_id=MAIN_CHANNEL_ID, message_id=channel_post_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
                elif ad.get('games_photo'):
                    await context.bot.edit_message_caption(chat_id=MAIN_CHANNEL_ID, message_id=channel_post_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await context.bot.edit_message_text(chat_id=MAIN_CHANNEL_ID, message_id=channel_post_id, text=post_text, reply_markup=keyboard, parse_mode="HTML")
                await context.bot.send_message(chat_id=MAIN_CHANNEL_ID, text=discount_notice, reply_to_message_id=channel_post_id, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        if game_channel_post_id:
            try:
                if ad.get('profile_photo') and ad.get('games_photo'):
                    await context.bot.edit_message_caption(chat_id=GAME_CHANNEL_ID, message_id=game_channel_post_id, caption=post_text, parse_mode="HTML")
                elif ad.get('profile_photo'):
                    await context.bot.edit_message_caption(chat_id=GAME_CHANNEL_ID, message_id=game_channel_post_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
                elif ad.get('games_photo'):
                    await context.bot.edit_message_caption(chat_id=GAME_CHANNEL_ID, message_id=game_channel_post_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await context.bot.edit_message_text(chat_id=GAME_CHANNEL_ID, message_id=game_channel_post_id, text=post_text, reply_markup=keyboard, parse_mode="HTML")
                await context.bot.send_message(chat_id=GAME_CHANNEL_ID, text=discount_notice, reply_to_message_id=game_channel_post_id, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        save_agahi(all_agahi)
        
        await query.message.edit_text(f"✅ تخفیف آگهی {ad_id} تایید و اعمال شد.")
        
        user_id = ad['user_id']
        await context.bot.send_message(chat_id=user_id, text=f"🎉 درخواست تخفیف شما تایید شد!\n\n🆔 آگهی: {ad_id}\n💰 قیمت جدید: {new_price:,} تومان\n{SIGNATURE}")
        
    except Exception as e:
        await query.message.edit_text(f"❌ خطا در اعمال تخفیف: {e}")


async def reject_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ad_id = int(query.data.split("_")[2])
    
    await query.message.edit_text(f"❌ درخواست تخفیف برای آگهی {ad_id} رد شد.")
    
    all_agahi = load_agahi()
    ad = None
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                break
        if ad:
            break
    
    if ad:
        user_id = ad['user_id']
        await context.bot.send_message(chat_id=user_id, text=f"❌ درخواست تخفیف شما برای آگهی {ad_id} رد شد.")


async def search_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ این دستور فقط برای ادمین است!")
        return
    
    try:
        ad_id = int(context.args[0]) if context.args else None
        if not ad_id:
            await update.message.reply_text("❗ استفاده: /searchadmin [شماره آگهی]")
            return
    except:
        await update.message.reply_text("❗ شماره آگهی نامعتبر!")
        return
    
    all_agahi = load_agahi()
    pending_ads = load_pending_ads()
    price_requests = load_price_requests()
    rejected_ads = load_rejected_ads()
    
    ad = None
    seller_id = None
    ad_type = "آگهی منتشر شده"
    
    for uid, ads in all_agahi.items():
        for a in ads:
            if a['id'] == ad_id:
                ad = a
                seller_id = int(uid)
                break
        if ad:
            break
    
    if not ad:
        pending = pending_ads.get(str(ad_id))
        if pending:
            ad = pending
            seller_id = pending.get('user_id')
            ad_type = "آگهی در انتظار تایید"
    
    if not ad:
        price_req = price_requests.get(str(ad_id))
        if price_req:
            ad = price_req
            seller_id = price_req.get('user_id')
            ad_type = "درخواست قیمت‌گذاری"
    
    if not ad:
        rejected = rejected_ads.get(str(ad_id))
        if rejected:
            ad = rejected
            seller_id = rejected.get('user_id')
            ad_type = "آگهی رد شده"
    
    if not ad:
        await update.message.reply_text(f"❌ آگهی با شماره {ad_id} در هیچ بخشی یافت نشد!")
        return
    
    profile = load_profiles().get(str(seller_id), {}) if seller_id else {}
    
    current_price = ad.get('price')
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                current_price = disc['new_price']
                break
    
    if current_price is None:
        current_price = 0
    
    username_display = ad.get('username')
    if not username_display or username_display == 'None':
        username_display = 'ندارد'
    else:
        username_display = f"@{username_display}"
    
    info_text = f"""🔍 <b>اطلاعات کامل آگهی</b>

📋 نوع: {ad_type}
🆔 شماره: {ad_id}

👤 فروشنده:
نام: {profile.get('name', 'ثبت نشده')}
یوزرنیم: {username_display}
شماره تماس: {profile.get('phone', 'ثبت نشده')}

🎮 اطلاعات اکانت:
آیدی پلاتو: {ad.get('platoid', '-')}
ویپ: {ad.get('vip_count', '-')}
آیتم: {ad.get('item_count', '-')}
سکه: {ad.get('coin_count', '-')}
پیپ: {ad.get('pip_count', '-')}
وین: {ad.get('win_count', '-')}
سن: {ad.get('account_age', '-')}

💰 قیمت: {current_price:,} تومان
{SIGNATURE}"""
    
    await update.message.reply_text(info_text, parse_mode="HTML")


async def price_set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 3:
        await query.message.reply_text("❌ خطا در شناسه!")
        return
    
    try:
        request_id = int(parts[2])
    except ValueError:
        await query.message.reply_text("❌ شناسه نامعتبر!")
        return
    
    context.user_data['set_price_only_id'] = request_id
    
    admin_msg_id = context.user_data.get(f'price_only_admin_msg_{request_id}')
    if admin_msg_id:
        try:
            await delete_admin_messages(context, admin_msg_id)
        except:
            pass
    
    await query.message.reply_text(
        f"💰 لطفاً قیمت این اکانت را وارد کنید:\n"
        f"🆔 کد درخواست: {request_id}\n\n"
        f"مثال: 250000",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="agahi_menu", style="danger")]
        ])
    )


async def select_button_color(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id):
    query = update.callback_query
    await query.answer()
    context.user_data['color_ad_id'] = ad_id
    
    keyboard = [
        [InlineKeyboardButton("🟢 سبز (اکانت زیر ۱۰ میلیون)", callback_data=f"color_green_{ad_id}", style="success")],
        [InlineKeyboardButton("🔴 قرمز (اکانت فول)", callback_data=f"color_red_{ad_id}", style="danger")],
        [InlineKeyboardButton("🔵 آبی (بالای ۱۰ میلیون)", callback_data=f"color_blue_{ad_id}", style="primary")]
    ]
    
    await query.message.reply_text("🎨 انتخاب رنگ دکمه:", reply_markup=InlineKeyboardMarkup(keyboard))


async def set_button_color(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id, color):
    query = update.callback_query
    await query.answer()
    
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد!")
        return
    
    admin_msg_id = context.user_data.get(f'admin_msg_{ad_id}')
    if admin_msg_id:
        try:
            await delete_admin_messages(context, admin_msg_id)
        except:
            pass

    # اگر قیمت را ادمین تعیین کرده، اول از کاربر تایید می‌گیریم؛ بعد منتشر می‌کنیم
    if ad.get('price_method') == 'admin':
        ad['button_color'] = color
        ad['status'] = 'awaiting_user_confirm'
        save_pending_ads(pending_ads)
        price = ad.get('price')
        price_disp = f"{price:,} تومان" if isinstance(price, int) else str(price)
        try:
            await context.bot.send_message(
                chat_id=ad['user_id'],
                text=(f"💰 قیمت آگهی شما توسط تیم پشتیبانی تعیین شد: <b>{price_disp}</b>\n\n"
                      f"در صورت تایید شما و انتشار آگهی در چنل‌های ذکرشده، دکمه‌ی زیر را بزنید:\n{SIGNATURE}"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("تایید درخواست ✅", callback_data=f"confirm_publish_{ad_id}", style="success")],
                    [InlineKeyboardButton("❌ رد و پیشنهاد قیمت", callback_data=f"propose_price_{ad_id}", style="danger")],
                ]),
                parse_mode="HTML")
        except Exception as e:
            logger.error(f"ارسال تایید قیمت به کاربر ناموفق: {e}")
        await query.message.edit_text(
            f"✅ قیمت {price_disp} ثبت شد و برای تایید نهایی به کاربر ارسال شد.\nپس از تایید کاربر، آگهی در چنل منتشر می‌شود.")
        return

    await publish_ad(update, context, ad_id, color)


async def confirm_publish_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کاربر قیمت تعیین‌شده توسط ادمین را تایید می‌کند → انتشار در چنل."""
    query = update.callback_query
    await query.answer()
    ad_id = int(query.data.split("_")[2])
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        await query.message.edit_text("❌ این آگهی یافت نشد یا قبلاً منتشر شده است.")
        return
    if query.from_user.id != ad.get('user_id'):
        return
    color = ad.get('button_color', 'green')
    await query.message.edit_text("✅ آگهی شما تایید شد و در حال انتشار در چنل است...")
    await publish_ad(update, context, ad_id, color)


async def _send_price_confirmation(context, ad_id, ad):
    """پیام تعیین قیمت را با دو دکمه (تایید / رد و پیشنهاد قیمت) دوباره برای کاربر می‌فرستد."""
    price = ad.get('price')
    price_disp = f"{price:,} تومان" if isinstance(price, int) else str(price)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید درخواست ✅", callback_data=f"confirm_publish_{ad_id}", style="success")],
        [InlineKeyboardButton("❌ رد و پیشنهاد قیمت", callback_data=f"propose_price_{ad_id}", style="danger")],
    ])
    try:
        await context.bot.send_message(
            chat_id=ad['user_id'],
            text=(f"💰 قیمت آگهی شما توسط تیم پشتیبانی: <b>{price_disp}</b>\n\n"
                  f"✅ برای انتشار «تایید درخواست» — ❌ برای پیشنهاد قیمت دیگر «رد و پیشنهاد قیمت».\n{SIGNATURE}"),
            reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"ارسال مجدد تایید قیمت ناموفق: {e}")


async def propose_price_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کاربر قیمت ادمین را رد کرد و می‌خواهد قیمت خودش را پیشنهاد دهد."""
    query = update.callback_query
    await query.answer()
    ad_id = int(query.data.split("_")[2])
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad or query.from_user.id != ad.get('user_id'):
        return
    context.user_data['propose_price_ad_id'] = ad_id
    await query.message.edit_text(
        "با توجه به قیمت اعلامیِ ما، لطفاً <b>قیمت پیشنهادی خود</b> برای ثبت آگهی را به تومان وارد کنید (فقط عدد):",
        parse_mode="HTML")


async def process_proposed_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('propose_price_ad_id')
    if not ad_id:
        return
    try:
        price = int(update.message.text.replace(',', '').replace('،', '').strip())
        if price <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❌ قیمت نامعتبر. فقط عدد بفرست.")
        return
    context.user_data.pop('propose_price_ad_id', None)
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد.")
        return
    ad['proposed_price'] = price
    save_pending_ads(pending_ads)

    admin_price = ad.get('price')
    txt = (f"💬 <b>پیشنهاد قیمت جدید از فروشنده</b>\n\n"
           f"🆔 آگهی: {ad_id}\n"
           f"👤 فروشنده: {user_mention(ad['user_id'], ad.get('user_name'))}\n"
           f"🆔 آیدی عددی: <code>{ad['user_id']}</code>\n"
           f"💰 قیمت اعلامیِ ادمین: {admin_price:,} تومان\n"
           f"💵 قیمت پیشنهادیِ فروشنده: <b>{price:,}</b> تومان")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید قیمت پیشنهادی و انتشار", callback_data=f"approveprop_{ad_id}", style="success")],
        [InlineKeyboardButton("❌ رد پیشنهاد", callback_data=f"rejectprop_{ad_id}", style="danger")],
    ])
    await send_to_target(context, GROUP_ADS, text=txt, reply_markup=kb, parse_mode="HTML")
    await update.message.reply_text(
        f"✅ قیمت پیشنهادی شما ({price:,} تومان) به تیم پشتیبانی ارسال شد.\nپس از بررسی به شما اطلاع داده می‌شود.\n{SIGNATURE}",
        parse_mode="HTML")


async def approve_proposed_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id not in ADMIN_IDS:
        return
    ad_id = int(query.data.split("_")[1])
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد یا قبلاً منتشر شده است.")
        return
    ad['price'] = ad.get('proposed_price', ad.get('price'))
    save_pending_ads(pending_ads)
    color = ad.get('button_color', 'green')
    await query.message.edit_text("✅ قیمت پیشنهادی فروشنده تایید شد. در حال انتشار در چنل...")
    await publish_ad(update, context, ad_id, color)


async def reject_proposed_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id not in ADMIN_IDS:
        return
    ad_id = int(query.data.split("_")[1])
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    await query.message.edit_text(f"❌ پیشنهاد قیمت فروشنده برای آگهی {ad_id} رد شد.")
    if ad:
        try:
            await context.bot.send_message(
                chat_id=ad['user_id'],
                text=f"❌ قیمت پیشنهادی شما برای آگهی {ad_id} پذیرفته نشد. قیمت اعلامیِ ما همان قبلی است:")
        except Exception:
            pass
        await _send_price_confirmation(context, ad_id, ad)


async def set_price_and_approve(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id):
    query = update.callback_query
    await query.answer()
    context.user_data['set_price_ad_id'] = ad_id
    
    admin_msg_id = context.user_data.get(f'admin_msg_{ad_id}')
    if admin_msg_id:
        try:
            await delete_admin_messages(context, admin_msg_id)
        except:
            pass
    
    await query.message.reply_text("💰 لطفاً قیمت این آگهی را وارد کنید:")


async def process_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('set_price_ad_id')
    if not ad_id:
        return
    try:
        price = int(update.message.text.replace(',', '').strip())
        if price <= 0:
            await update.message.reply_text("❌ قیمت باید بزرگتر از صفر باشد!")
            return
    except:
        await update.message.reply_text("❌ قیمت نامعتبر!")
        return
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد!")
        context.user_data['set_price_ad_id'] = None
        return
    ad['price'] = price
    save_pending_ads(pending_ads)
    
    context.user_data['color_ad_id'] = ad_id
    keyboard = [
        [InlineKeyboardButton("🟢 سبز (اکانت زیر ۱۰ میلیون)", callback_data=f"color_green_{ad_id}", style="success")],
        [InlineKeyboardButton("🔴 قرمز (اکانت فول)", callback_data=f"color_red_{ad_id}", style="danger")],
        [InlineKeyboardButton("🔵 آبی (بالای ۱۰ میلیون)", callback_data=f"color_blue_{ad_id}", style="primary")]
    ]
    await update.message.reply_text(f"✅ قیمت {price:,} تومان ثبت شد.\n🎨 رنگ دکمه را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    context.user_data['set_price_ad_id'] = None


async def process_set_price_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_id = context.user_data.get('set_price_only_id')
    if not request_id:
        return
    
    try:
        price = int(update.message.text.replace(',', '').strip())
        if price <= 0:
            await update.message.reply_text("❌ قیمت باید بزرگتر از صفر باشد!")
            return
    except:
        await update.message.reply_text("❌ قیمت نامعتبر!")
        return
    
    price_requests = load_price_requests()
    req = price_requests.get(str(request_id))
    if not req:
        await update.message.reply_text("❌ درخواست یافت نشد!")
        context.user_data['set_price_only_id'] = None
        return
    
    user_id = req['user_id']
    user_phone = req.get('phone', ADMIN_PHONE)
    
    req['price'] = price
    req['status'] = 'priced'
    save_price_requests(price_requests)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"💰 قیمت اکانت شما تعیین شد!\n\n🆔 کد: {request_id}\n💰 قیمت: {price:,} تومان\n\nبرای ثبت آگهی، از منوی اصلی اقدام کنید.\n{SIGNATURE}"
    )
    
    await update.message.reply_text(f"✅ قیمت {price:,} تومان برای درخواست {request_id} ثبت شد.")
    
    context.user_data['set_price_only_id'] = None


async def publish_ad(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id, color):
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    if not ad:
        if update.callback_query:
            await update.callback_query.message.edit_text("❌ آگهی یافت نشد!")
        else:
            await update.message.reply_text("❌ آگهی یافت نشد!")
        return

    # شماره‌ی تازه در لحظه‌ی انتشار تا ترتیب چنل با ترتیب انتشار بخواند، نه ترتیب ثبت
    old_pending_id = ad_id
    ad_id = get_next_ad_id()
    ad['id'] = ad_id

    bot_username = (await context.bot.get_me()).username

    price_value = ad.get('price')
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
    
    publish_method = ad.get('publish_method', 'game')

    buy_url = f"https://t.me/{bot_username}?start=buy_{ad_id}"
    color_emoji = {"green": "🟢", "red": "🔴", "blue": "🔵"}.get(color, "🟢")
    buy_style = {"green": "success", "red": "danger", "blue": "primary"}.get(color, "success")
    buy_label = f"{color_emoji} اطلاعات بیشتر و خرید"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(buy_label, url=buy_url, style=buy_style)]])

    async def _post_to_channel(chat_id):
        # عکس‌ها و فیلم اکانت را کنار هم جمع می‌کنیم
        raw = []
        if ad.get('profile_photo'):
            raw.append(('photo', ad['profile_photo']))
        if ad.get('games_photo'):
            raw.append(('photo', ad['games_photo']))
        if ad.get('video'):
            raw.append(('video', ad['video']))

        if len(raw) >= 2:
            # آلبوم عکس‌ها و فیلم با هم (کپشن مشخصات روی اولی).
            # تلگرام روی آلبوم دکمه نمی‌پذیرد، پس دکمه‌ی خرید را بلافاصله زیرش می‌چسبانیم.
            media = []
            for i, (kind, file_id) in enumerate(raw):
                cap = post_text if i == 0 else None
                pm = "HTML" if i == 0 else None
                if kind == 'video':
                    media.append(InputMediaVideo(media=file_id, caption=cap, parse_mode=pm))
                else:
                    media.append(InputMediaPhoto(media=file_id, caption=cap, parse_mode=pm))
            sent = await context.bot.send_media_group(chat_id=chat_id, media=media)
            btn_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="👆 برای مشاهده‌ی کامل و خرید این اکانت، دکمه‌ی زیر را بزنید:",
                reply_markup=keyboard,
                reply_to_message_id=sent[0].message_id,
            )
            # (post_id, button_id, همه‌ی پیام‌های آلبوم) — دکمه روی پیام جداست
            return sent[0].message_id, btn_msg.message_id, [m.message_id for m in sent]
        elif len(raw) == 1:
            kind, file_id = raw[0]
            if kind == 'video':
                sent = await context.bot.send_video(chat_id=chat_id, video=file_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
            else:
                sent = await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=post_text, reply_markup=keyboard, parse_mode="HTML")
            # دکمه روی خود پیام است؛ پیام دکمه‌ی جدا نداریم
            return sent.message_id, None, [sent.message_id]
        else:
            sent = await context.bot.send_message(chat_id=chat_id, text=post_text, reply_markup=keyboard, parse_mode="HTML")
            return sent.message_id, None, [sent.message_id]

    try:
        ad['game_channel_post_id'], ad['game_channel_button_id'], ad['game_channel_media_ids'] = await _post_to_channel(GAME_CHANNEL_ID)
        if publish_method == 'both':
            ad['channel_post_id'], ad['channel_button_id'], ad['channel_media_ids'] = await _post_to_channel(MAIN_CHANNEL_ID)
        
        all_agahi = load_agahi()
        if str(ad['user_id']) not in all_agahi:
            all_agahi[str(ad['user_id'])] = []
        ad['published'] = True
        ad['publish_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ad['status'] = 'published'
        ad['button_color'] = color
        all_agahi[str(ad['user_id'])].append(ad)
        save_agahi(all_agahi)
        
        pending_ads = load_pending_ads()
        if str(old_pending_id) in pending_ads:
            del pending_ads[str(old_pending_id)]
            save_pending_ads(pending_ads)
        
        # سیستم رفرال
        if not has_used_referral_bonus(ad['user_id']):
            referrals = load_referrals()
            user_ref_data = referrals.get(str(ad['user_id']), {})
            if isinstance(user_ref_data, dict):
                referred_by = user_ref_data.get('referred_by')
                if referred_by:
                    new_balance = add_to_wallet(ad['user_id'], 20000)
                    mark_referral_bonus_claimed(ad['user_id'])
                    
                    await context.bot.send_message(
                        chat_id=ad['user_id'],
                        text=f"🎉 تبریک! شما اولین آگهی خود را ثبت کردید.\n\n💰 ۲۰,۰۰۰ تومان به عنوان جایزه دعوت به کیف پول شما واریز شد.\n💰 موجودی جدید: {new_balance:,} تومان\n{SIGNATURE}"
                    )
                    
                    referral_bonus = add_to_wallet(referred_by, 10000)
                    await context.bot.send_message(
                        chat_id=referred_by,
                        text=f"🎉 کاربری که شما دعوت کردید، اولین آگهی خود را ثبت کرد!\n\n💰 ۱۰,۰۰۰ تومان به عنوان پاداش دعوت به کیف پول شما واریز شد.\n💰 موجودی جدید: {referral_bonus:,} تومان\n{SIGNATURE}"
                    )
                    
                    increment_referral_count(referred_by)
        
        channels_text = f"📢 کانال اگهی اکانت پلاتو: {GAME_CHANNEL_LINK}"
        if publish_method == 'both':
            channels_text += f"\n📢 کانال فروشگاهی: {MAIN_CHANNEL_LINK}"
        
        await context.bot.send_message(chat_id=ad['user_id'], text=f"✅ آگهی شما منتشر شد!\n\n{channels_text}\n💰 قیمت: {price_display}\n{SIGNATURE}", parse_mode="HTML")
        await send_to_target(context, GROUP_ADS, text=f"✅ آگهی {ad_id} با قیمت {price_display} منتشر شد!", parse_mode="HTML")
        
        if update.callback_query:
            await update.callback_query.message.edit_text(f"✅ آگهی {ad_id} با موفقیت منتشر شد!")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await send_to_target(context, GROUP_ADS, text=f"❌ خطا در انتشار آگهی {ad_id}: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text(f"❌ خطا در انتشار: {e}")


async def reject_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    ad_id = int(parts[2])
    
    admin_msg_id = context.user_data.get(f'admin_msg_{ad_id}')
    if admin_msg_id:
        try:
            await delete_admin_messages(context, admin_msg_id)
        except:
            pass
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ رسید فیک", callback_data=f"reject_fake_ad_{ad_id}", style="danger")],
        [InlineKeyboardButton("2️⃣ اطلاعات ناقص", callback_data=f"reject_info_ad_{ad_id}", style="primary")],
        [InlineKeyboardButton("3️⃣ تخلف", callback_data=f"reject_violation_ad_{ad_id}", style="danger")],
        [InlineKeyboardButton("4️⃣ دلیل دیگر (دستی)", callback_data=f"reject_other_ad_{ad_id}", style="primary")]
    ]
    
    await query.message.reply_text("❌ دلیل رد آگهی را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_reject_with_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    reason_type = parts[1]
    request_type = parts[2]
    item_id = int(parts[3])
    
    if reason_type == 'other':
        context.user_data['reject_other_ad_id'] = item_id
        context.user_data['reject_other_type'] = request_type
        await query.message.reply_text("✏️ لطفاً دلیل رد را وارد کنید:")
        return
    
    reasons = {
        'fake': 'رسید فیک (3 بار = بن)',
        'info': 'اطلاعات ناقص یا نامعتبر',
        'violation': 'تخلف در قوانین'
    }
    
    reason_text = reasons.get(reason_type, 'رد شده')
    
    if reason_type == 'fake':
        count, is_banned = increment_reject_count(query.from_user.id)
        if is_banned:
            await query.message.edit_text(f"⚠️ کاربر به دلیل 3 بار رسید فیک، بن شد!")
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text="⛔ شما به دلیل 3 بار ارسال رسید فیک، از ربات بن شدید!"
            )
        else:
            await query.message.edit_text(f"⚠️ رسید فیک ({count}/3) - در صورت تکرار، کاربر بن می‌شود.")
    else:
        await query.message.edit_text(f"✅ آگهی با دلیل '{reason_text}' رد شد.")
    
    if request_type == 'ad':
        await complete_ad_rejection(update, context, item_id, reason_text)
    else:
        await complete_price_rejection(update, context, item_id, reason_text)


async def process_reject_other_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('reject_other_ad_id')
    request_type = context.user_data.get('reject_other_type')
    
    if not ad_id:
        return
    
    reason = update.message.text.strip()
    if not reason:
        await update.message.reply_text("❌ لطفاً یک دلیل معتبر وارد کنید!")
        return
    
    if request_type == 'ad':
        await complete_ad_rejection(update, context, ad_id, reason)
    else:
        await complete_price_rejection(update, context, ad_id, reason)

    # پیام تأیید را خودِ complete_* می‌فرستد؛ اینجا دیگر تکرار نمی‌کنیم
    context.user_data['reject_other_ad_id'] = None
    context.user_data['reject_other_type'] = None


async def _edit_or_reply(update, text):
    """پیام تأیید را می‌فرستد؛ چه از دکمه آمده باشیم چه از پیام متنی."""
    if update.callback_query:
        await update.callback_query.message.edit_text(text)
    elif update.message:
        await update.message.reply_text(text)


async def complete_ad_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_id, reason):
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))

    if not ad:
        await _edit_or_reply(update, "❌ آگهی یافت نشد!")
        return
    
    user_id = ad['user_id']
    total_fee = ad.get('total_fee', 0)
    
    rejected_ads = load_rejected_ads()
    ad['reject_reason'] = reason
    ad['rejected_date'] = now_jalali()
    rejected_ads[str(ad_id)] = ad
    save_rejected_ads(rejected_ads)
    
    if total_fee > 0:
        new_balance = add_to_wallet(user_id, total_fee)
        wallet_msg = f"\n💰 مبلغ {total_fee:,} تومان به کیف پول برگشت. موجودی: {new_balance:,} تومان"
    else:
        wallet_msg = ""
    
    del pending_ads[str(ad_id)]
    save_pending_ads(pending_ads)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"❌ آگهی شما رد شد.\n\n📝 دلیل: {reason}{wallet_msg}\n{SIGNATURE}"
    )

    await _edit_or_reply(update, f"✅ آگهی {ad_id} با دلیل '{reason}' رد شد.")


async def complete_price_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id, reason):
    price_requests = load_price_requests()
    req = price_requests.get(str(request_id))

    if not req:
        await _edit_or_reply(update, "❌ درخواست یافت نشد!")
        return
    
    user_id = req['user_id']
    
    if reason == 'رسید فیک (3 بار = بن)':
        count, is_banned = increment_reject_count(user_id)
        if is_banned:
            await context.bot.send_message(
                chat_id=user_id,
                text="⛔ شما به دلیل 3 بار ارسال رسید فیک، از ربات بن شدید!"
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ درخواست قیمت‌گذاری شما رد شد.\n\n📝 دلیل: {reason}\n{SIGNATURE}"
        )
    
    del price_requests[str(request_id)]
    save_price_requests(price_requests)
    await _edit_or_reply(update, f"✅ درخواست {request_id} با دلیل '{reason}' رد شد.")


async def reject_price_only_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    request_id = int(parts[3])
    
    admin_msg_id = context.user_data.get(f'price_only_admin_msg_{request_id}')
    if admin_msg_id:
        try:
            await delete_admin_messages(context, admin_msg_id)
        except:
            pass
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ رسید فیک", callback_data=f"reject_fake_price_{request_id}", style="danger")],
        [InlineKeyboardButton("2️⃣ اطلاعات ناقص", callback_data=f"reject_info_price_{request_id}", style="primary")],
        [InlineKeyboardButton("3️⃣ تخلف", callback_data=f"reject_violation_price_{request_id}", style="danger")],
        [InlineKeyboardButton("4️⃣ دلیل دیگر (دستی)", callback_data=f"reject_other_price_{request_id}", style="primary")]
    ]
    
    await query.message.reply_text("❌ دلیل رد درخواست را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))


async def process_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ad_id = context.user_data.get('reject_ad_id')
    if not ad_id:
        return
    
    reason = update.message.text.strip()
    if not reason:
        await update.message.reply_text("❌ لطفاً یک دلیل معتبر وارد کنید!")
        return
    
    pending_ads = load_pending_ads()
    ad = pending_ads.get(str(ad_id))
    
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد!")
        context.user_data['reject_ad_id'] = None
        return
    
    user_id = ad['user_id']
    total_fee = ad.get('total_fee', 0)
    
    rejected_ads = load_rejected_ads()
    ad['reject_reason'] = reason
    ad['rejected_date'] = now_jalali()
    rejected_ads[str(ad_id)] = ad
    save_rejected_ads(rejected_ads)
    
    if total_fee > 0:
        new_balance = add_to_wallet(user_id, total_fee)
        wallet_msg = f"\n💰 مبلغ {total_fee:,} تومان به کیف پول برگشت. موجودی: {new_balance:,} تومان"
    else:
        wallet_msg = ""
    
    del pending_ads[str(ad_id)]
    save_pending_ads(pending_ads)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"❌ آگهی شما رد شد.\n\n📝 دلیل: {reason}{wallet_msg}\n{SIGNATURE}"
    )
    
    await update.message.reply_text(f"✅ آگهی {ad_id} با دلیل '{reason}' رد شد.")
    context.user_data['reject_ad_id'] = None


# ============================================================
# دستور /cash : افزایش/کاهش موجودی کاربر توسط ادمین
#   /cash <آیدی عددی> +100000   → افزودن
#   /cash <آیدی عددی> -100000   → کسر
# ============================================================
async def cash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "فرمت درست:\n<code>/cash آیدی‌عددی +مبلغ</code>\nمثال: <code>/cash 777777777 +100000</code>",
            parse_mode="HTML")
        return
    try:
        uid = int(args[0])
        amount = int(args[1].replace(",", "").replace("،", ""))
    except ValueError:
        await update.message.reply_text("❌ آیدی یا مبلغ نامعتبر است.")
        return
    if amount == 0:
        await update.message.reply_text("❌ مبلغ نمی‌تواند صفر باشد.")
        return

    if amount > 0:
        new_bal = add_to_wallet(uid, amount)
        admin_txt = f"✅ مبلغ {amount:,} تومان به موجودی کاربر <code>{uid}</code> اضافه شد.\n💰 موجودی جدید: {new_bal:,} تومان"
        user_txt = f"کاربر گرامی مبلغ {amount:,} تومان به موجودی شما توسط پشتیبانی ربات اضافه شد.\n{SIGNATURE}"
    else:
        ok, res = deduct_from_wallet(uid, -amount)
        if not ok:
            await update.message.reply_text(f"❌ موجودی کاربر کافی نیست. موجودی فعلی: {res:,} تومان")
            return
        admin_txt = f"✅ مبلغ {-amount:,} تومان از موجودی کاربر <code>{uid}</code> کسر شد.\n💰 موجودی جدید: {res:,} تومان"
        user_txt = f"کاربر گرامی مبلغ {-amount:,} تومان از موجودی شما توسط پشتیبانی ربات کسر شد.\n{SIGNATURE}"

    try:
        await context.bot.send_message(chat_id=uid, text=user_txt)
    except Exception as e:
        admin_txt += f"\n⚠️ ارسال پیام به کاربر ناموفق بود: {e}"
    await update.message.reply_text(admin_txt, parse_mode="HTML")


# ============================================================
# دستور /ad و /ads : دسترسی به اطلاعات آگهی‌های دیتابیس
# ============================================================
def _find_ad_anywhere(aid):
    aid = str(aid)
    pending = load_pending_ads()
    if aid in pending:
        return pending[aid], "⏳ در انتظار"
    rejected = load_rejected_ads()
    if aid in rejected:
        return rejected[aid], "❌ ردشده"
    agahi = load_agahi()
    for uid, ads in agahi.items():
        if isinstance(ads, list):
            for a in ads:
                if str(a.get("id")) == aid:
                    return a, "✅ منتشرشده"
    return None, None


def _format_ad(ad, where):
    price = ad.get("price")
    price_disp = f"{price:,} تومان" if isinstance(price, int) else str(price)
    uid = ad.get("user_id")
    lines = [
        f"📋 <b>آگهی {ad.get('id')}</b> ({where})",
        "━━━━━━━━━━━━━━━━━━━━",
        f"👤 فروشنده: {user_mention(uid, ad.get('user_name'))}",
        f"🆔 آیدی عددی: <code>{uid}</code>",
        f"🆔 یوزرنیم: @{escape_html(ad.get('username')) if ad.get('username') else 'ندارد'}",
        f"🆔 آیدی پلاتو: {escape_html(ad.get('platoid', '-'))}",
        f"⭐ ویپ: {escape_html(ad.get('vip_count','-'))} | 📊 آیتم: {escape_html(ad.get('item_count','-'))}",
        f"🪙 سکه: {escape_html(ad.get('coin_count','-'))} | 💰 پیپ: {escape_html(ad.get('pip_count','-'))}",
        f"🏆 وین: {escape_html(ad.get('win_count','-'))} | 📅 سن: {escape_html(ad.get('account_age','-'))}",
        f"💵 قیمت: {price_disp}",
        f"📢 انتشار: {ad.get('publish_method','-')} | 🎨 رنگ: {ad.get('button_color','-')}",
        f"📝 توضیحات: {escape_html(ad.get('seller_note',''))}",
        f"📅 تاریخ: {ad.get('publish_date') or ad.get('date','-')}",
    ]
    if ad.get("reject_reason"):
        lines.append(f"❌ دلیل رد: {escape_html(ad.get('reject_reason'))}")
    return "\n".join(lines)


async def ads_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    args = context.args or []
    if args:
        ad, where = _find_ad_anywhere(args[0])
        if not ad:
            await update.message.reply_text("❌ آگهی با این شناسه پیدا نشد.")
            return
        await update.message.reply_text(_format_ad(ad, where), parse_mode="HTML")
        return
    agahi = load_agahi()
    pending = load_pending_ads()
    rejected = load_rejected_ads()
    total_pub = sum(len(v) for v in agahi.values() if isinstance(v, list))
    await update.message.reply_text(
        "🗂 <b>آگهی‌های دیتابیس</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ منتشرشده: <b>{total_pub}</b>\n"
        f"⏳ در انتظار: <b>{len(pending)}</b>\n"
        f"❌ ردشده: <b>{len(rejected)}</b>\n\n"
        "برای دیدن یک آگهی خاص: <code>/ad شناسه</code>",
        parse_mode="HTML")


# ============================================================
# ویرایش آگهی‌های کاربران توسط ادمین (متن/قیمت/مشخصات + آپدیت چنل)
# ============================================================
_AD_EDIT_FIELDS = [
    ("seller_note", "📝 توضیحات"),
    ("price", "💵 قیمت"),
    ("vip_count", "⭐ ویپ"),
    ("item_count", "📊 آیتم"),
    ("coin_count", "🪙 سکه"),
    ("pip_count", "💰 پیپ"),
    ("win_count", "🏆 وین"),
    ("account_age", "📅 سن اکانت"),
]


def _find_ad_editable(ad_id):
    """آگهی را در pending یا agahi پیدا می‌کند. خروجی: (ad, kind, container)"""
    pending = load_pending_ads()
    if str(ad_id) in pending:
        return pending[str(ad_id)], 'pending', pending
    agahi = load_agahi()
    for uid, ads in agahi.items():
        if isinstance(ads, list):
            for a in ads:
                if a.get('id') == ad_id:
                    return a, 'agahi', agahi
    return None, None, None


def _ad_effective_price(ad):
    price = ad.get('price')
    if ad.get('discount_history'):
        for disc in reversed(ad['discount_history']):
            if disc.get('is_active', True):
                return disc.get('new_price', price)
    return price


def _ad_post_text(ad):
    price_value = _ad_effective_price(ad)
    price_display = f"<b>{price_value:,}</b> تومان" if isinstance(price_value, int) else str(price_value)
    seller_note = escape_html(ad.get('seller_note', '-'))
    return f"""🎮 <b>آگهی فروش اکانت پلاتو</b>

🆔 شناسه: {ad.get('id')}

⭐ ویپ: {escape_html(str(ad.get('vip_count', '-')))}
📊 آیتم: {escape_html(str(ad.get('item_count', '-')))}
🪙 سکه: {escape_html(str(ad.get('coin_count', '-')))}
💰 پیپ: {escape_html(str(ad.get('pip_count', '-')))}
🏆 وین: {escape_html(str(ad.get('win_count', '-')))}
📅 سن اکانت: {escape_html(str(ad.get('account_age', '-')))}
💵 قیمت: {price_display}

📝 توضیحات:
{seller_note}
{SIGNATURE}"""


async def _update_ad_channel_posts(context, ad):
    """کپشن/متن پست آگهی را در کانال‌ها با مقادیر جدید به‌روزرسانی می‌کند."""
    post_text = _ad_post_text(ad)
    bot_username = (await context.bot.get_me()).username
    color = ad.get('button_color', 'green')
    emoji = {"green": "🟢", "red": "🔴", "blue": "🔵"}.get(color, "🟢")
    style = {"green": "success", "red": "danger", "blue": "primary"}.get(color, "success")
    buy_btn = InlineKeyboardMarkup([[InlineKeyboardButton(
        f"{emoji} اطلاعات بیشتر و خرید",
        url=f"https://t.me/{bot_username}?start=buy_{ad.get('id')}", style=style)]])
    raw = [m for m in (ad.get('profile_photo'), ad.get('games_photo'), ad.get('video')) if m]

    async def _edit(chat_id, post_id):
        if not post_id:
            return
        try:
            if len(raw) >= 2:
                # آلبوم: دکمه روی پیام جداست، فقط کپشن را عوض کن
                await context.bot.edit_message_caption(chat_id=chat_id, message_id=post_id, caption=post_text, parse_mode="HTML")
            elif len(raw) == 1:
                await context.bot.edit_message_caption(chat_id=chat_id, message_id=post_id, caption=post_text, reply_markup=buy_btn, parse_mode="HTML")
            else:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=post_id, text=post_text, reply_markup=buy_btn, parse_mode="HTML")
        except Exception as e:
            logger.error(f"آپدیت پست چنل ناموفق: {e}")

    await _edit(GAME_CHANNEL_ID, ad.get('game_channel_post_id'))
    await _edit(MAIN_CHANNEL_ID, ad.get('channel_post_id'))


async def editad_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id not in ADMIN_IDS:
        return
    context.user_data['ap_waiting_editad_id'] = True
    await query.message.edit_text("✏️ شناسه‌ی آگهی‌ای که می‌خواهید ویرایش کنید را بفرستید:",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")]]))


async def _show_ad_editor(msg, ad_id, ad, kind):
    where = "منتشرشده" if kind == 'agahi' else "در انتظار"
    price = _ad_effective_price(ad)
    price_disp = f"{price:,} تومان" if isinstance(price, int) else str(price)
    text = (f"✏️ <b>ویرایش آگهی {ad_id}</b> ({where})\n"
            f"⭐ {ad.get('vip_count','-')} | 📊 {ad.get('item_count','-')} | 🪙 {ad.get('coin_count','-')} | "
            f"💰 {ad.get('pip_count','-')} | 🏆 {ad.get('win_count','-')} | 📅 {ad.get('account_age','-')}\n"
            f"💵 {price_disp}\n📝 {escape_html(ad.get('seller_note','-'))}\n\nکدام مورد را ویرایش می‌کنید؟")
    rows = []
    for i in range(0, len(_AD_EDIT_FIELDS), 2):
        row = [InlineKeyboardButton(lbl, callback_data=f"aded_{ad_id}_{f}") for f, lbl in _AD_EDIT_FIELDS[i:i + 2]]
        rows.append(row)
    rows.append([InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")])
    await msg.reply_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")


async def editad_process_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('ap_waiting_editad_id', None)
    txt = (update.message.text or "").strip()
    if not txt.isdigit():
        await update.message.reply_text("❌ شناسه نامعتبر. یک عدد بفرست.")
        return
    ad, kind, _ = _find_ad_editable(int(txt))
    if not ad:
        await update.message.reply_text("❌ آگهی با این شناسه پیدا نشد.")
        return
    await _show_ad_editor(update.message, int(txt), ad, kind)


async def editad_field_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id not in ADMIN_IDS:
        return
    parts = query.data.split("_", 2)  # aded_<id>_<field>
    ad_id = int(parts[1])
    field = parts[2]
    context.user_data['ap_editad'] = {'ad_id': ad_id, 'field': field}
    label = dict(_AD_EDIT_FIELDS).get(field, field)
    await query.message.edit_text(f"✏️ مقدار جدیدِ «{label}» برای آگهی {ad_id} را بفرستید:",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")]]))


async def editad_field_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = context.user_data.pop('ap_editad', None)
    if not info:
        return
    ad_id, field = info['ad_id'], info['field']
    ad, kind, container = _find_ad_editable(ad_id)
    if not ad:
        await update.message.reply_text("❌ آگهی یافت نشد.")
        return
    val = (update.message.text or "").strip()
    if field == 'price':
        raw = val.replace(',', '').replace('،', '')
        if not raw.isdigit():
            await update.message.reply_text("❌ قیمت نامعتبر. فقط عدد بفرست.")
            context.user_data['ap_editad'] = info
            return
        ad['price'] = int(raw)
    else:
        ad[field] = val
    # ذخیره
    if kind == 'pending':
        save_pending_ads(container)
    else:
        save_agahi(container)
    # آپدیت پست چنل اگر منتشر شده
    if kind == 'agahi' and (ad.get('game_channel_post_id') or ad.get('channel_post_id')):
        await _update_ad_channel_posts(context, ad)
        note = "و پست چنل هم به‌روز شد."
    else:
        note = "(هنوز در چنل منتشر نشده.)"
    label = dict(_AD_EDIT_FIELDS).get(field, field)
    await update.message.reply_text(
        f"✅ «{label}» آگهی {ad_id} ویرایش شد {note}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✏️ ویرایش مورد دیگر", callback_data=f"aded_menu_{ad_id}")],
                                           [InlineKeyboardButton("🔙 پنل مدیریت", callback_data="admin_panel")]]))


async def editad_menu_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ad_id = int(query.data.split("_")[2])
    ad, kind, _ = _find_ad_editable(ad_id)
    if not ad:
        await query.message.edit_text("❌ آگهی یافت نشد.")
        return
    await _show_ad_editor(query.message, ad_id, ad, kind)
