# ============================================================
# نقطه‌ی راه‌اندازی ربات: ساخت Application و ثبت هندلرها
# ============================================================
import json
import os
import logging

from telegram import (
    Update, BotCommand, BotCommandScopeDefault, BotCommandScopeChat,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ChatMemberHandler, filters,
)

from .config import (
    TOKEN, ADMIN_IDS, PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE,
    BLACKLIST_FILE, WALLET_FILE, REJECT_COUNTER_FILE, PRICE_REQUEST_FILE,
    REJECTED_ADS_FILE, DISCOUNT_REQUEST_FILE, REFERRAL_FILE, USERS_FILE,
    SHOP_PRICES_FILE, SHOP_UNAVAILABLE_FILE, ADMINS_FILE,
)
from .db import migrate_json_files
from .handlers.router import handle_callbacks, handle_message
from .handlers.menu import start, chat_id_command
from .handlers.admin import search_admin_command, cash_command, ads_db_command
from .handlers.adminpanel import show_admin_panel, on_my_chat_member
from .handlers.commands import (
    cmd_shop, cmd_agahi, cmd_wallet, cmd_myads, cmd_referral, cmd_support,
)

# دستورهای منوی کنار چت
USER_COMMANDS = [
    BotCommand("start", "🏠 منوی اصلی"),
    BotCommand("shop", "🛒 فروشگاه"),
    BotCommand("agahi", "📢 ثبت آگهی"),
    BotCommand("wallet", "💼 کیف پول"),
    BotCommand("myads", "📋 آگهی‌های من"),
    BotCommand("referral", "🎁 دعوت دوستان و جایزه"),
    BotCommand("support", "🆘 پشتیبانی"),
]
ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand("panel", "🛠 پنل مدیریت"),
    BotCommand("searchadmin", "🔎 سرچ آگهی"),
    BotCommand("id", "🆔 آیدی چت"),
]


async def _post_init(app):
    """ثبت منوی دستورها؛ دستورهای مدیریتی فقط برای ادمین‌ها."""
    await app.bot.set_my_commands(USER_COMMANDS, scope=BotCommandScopeDefault())
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logger.error(f"set_my_commands برای ادمین {admin_id} ناموفق: {e}")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


_DATA_FILES = [PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE,
               BLACKLIST_FILE, WALLET_FILE, REJECT_COUNTER_FILE,
               PRICE_REQUEST_FILE, REJECTED_ADS_FILE, DISCOUNT_REQUEST_FILE,
               REFERRAL_FILE, USERS_FILE, SHOP_PRICES_FILE,
               SHOP_UNAVAILABLE_FILE]
# نکته: ADMINS_FILE عمداً منتقل نمی‌شود و به‌صورت فایل می‌ماند (بوت‌استرپ config)


def main():
    # داده‌ی JSON قبلی (اگر باشد) یک‌بار به SQLite منتقل می‌شود
    migrate_json_files(_DATA_FILES)

    app = Application.builder().token(TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("searchadmin", search_admin_command))
    app.add_handler(CommandHandler("id", chat_id_command))
    app.add_handler(CommandHandler("panel", show_admin_panel))
    app.add_handler(CommandHandler("cash", cash_command))
    app.add_handler(CommandHandler("ad", ads_db_command))
    app.add_handler(CommandHandler("ads", ads_db_command))
    app.add_handler(CommandHandler("shop", cmd_shop))
    app.add_handler(CommandHandler("agahi", cmd_agahi))
    app.add_handler(CommandHandler("wallet", cmd_wallet))
    app.add_handler(CommandHandler("myads", cmd_myads))
    app.add_handler(CommandHandler("referral", cmd_referral))
    app.add_handler(CommandHandler("support", cmd_support))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO, handle_message))
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    print("🚀 ربات پلاتویار روشن شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
