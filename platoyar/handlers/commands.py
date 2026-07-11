"""دستورهای اسلش برای منوی کنار چت — هر دستور بخش مربوطه را باز می‌کند."""
from telegram import Update
from telegram.ext import ContextTypes

from ..config import *
from .menu import show_main_menu, support_menu, referral_menu
from .ads import show_agahi_menu
from .wallet import wallet_menu
from .myads import my_ads_menu
from .shop import shop_open


# ---- شیم: صدا زدن هندلرهای callback از داخل یک دستور (پیام متنی) ----
class _EditableMessage:
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


class _CbUpdate:
    def __init__(self, update):
        self.callback_query = _FakeQuery(update.message, update.effective_user)
        self.effective_user = update.effective_user
        self.effective_chat = update.effective_chat
        self.message = None


async def cmd_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await shop_open(_CbUpdate(update), context)


async def cmd_agahi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_agahi_menu(_CbUpdate(update), context)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await wallet_menu(_CbUpdate(update), context)


async def cmd_myads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await my_ads_menu(_CbUpdate(update), context)


async def cmd_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await referral_menu(_CbUpdate(update), context)


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await support_menu(_CbUpdate(update), context)
