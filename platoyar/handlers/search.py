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


async def search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['search_mode'] = True
    await query.message.edit_text("🔍 لطفاً شماره آگهی مورد نظر را وارد کنید:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="primary")]]))


async def search_ad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('search_mode'):
        return
    try:
        ad_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ شماره نامعتبر!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="primary")]]))
        context.user_data['search_mode'] = False
        return
    
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
        await update.message.reply_text(f"❌ آگهی {ad_id} یافت نشد!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="primary")]]))
        context.user_data['search_mode'] = False
        return
    
    current_price = ad.get('price')
    if current_price is None:
        current_price = 0
    price_display = f"<b>{current_price:,}</b> تومان"
    
    search_result = f"""🔍 <b>نتیجه جستجو</b>

🆔 شماره: {ad_id}
🎮 بازی: پلاتو
💵 قیمت: {price_display}
{SIGNATURE}"""
    
    await update.message.reply_text(search_result, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="agahi_menu", style="primary")]]))
    
    context.user_data['search_mode'] = False
