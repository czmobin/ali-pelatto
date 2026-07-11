# ============================================================
# نقطه‌ی راه‌اندازی ربات: ساخت Application و ثبت هندلرها
# ============================================================
import json
import os
import logging

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ChatMemberHandler, filters,
)

from .config import (
    TOKEN, PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE, BLACKLIST_FILE,
    WALLET_FILE, REJECT_COUNTER_FILE, PRICE_REQUEST_FILE, REJECTED_ADS_FILE,
    DISCOUNT_REQUEST_FILE, REFERRAL_FILE, USERS_FILE,
)
from .handlers.router import handle_callbacks, handle_message
from .handlers.menu import start, chat_id_command
from .handlers.admin import search_admin_command
from .handlers.adminpanel import show_admin_panel, on_my_chat_member

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def _init_data_files():
    files = [PROFILE_FILE, AGAHI_FILE, PENDING_ADS_FILE, COUNTER_FILE,
             BLACKLIST_FILE, WALLET_FILE, REJECT_COUNTER_FILE,
             PRICE_REQUEST_FILE, REJECTED_ADS_FILE, DISCOUNT_REQUEST_FILE,
             REFERRAL_FILE, USERS_FILE]
    for file in files:
        if not os.path.exists(file):
            try:
                with open(file, "w", encoding="utf-8") as f:
                    if file == COUNTER_FILE:
                        json.dump({"last_id": 0}, f)
                    elif file == BLACKLIST_FILE:
                        json.dump([], f)
                    else:
                        json.dump({}, f)
            except Exception:
                pass


def main():
    _init_data_files()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("searchadmin", search_admin_command))
    app.add_handler(CommandHandler("id", chat_id_command))
    app.add_handler(CommandHandler("panel", show_admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(MessageHandler(filters.VIDEO, handle_message))
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    print("🚀 ربات پلاتویار روشن شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
