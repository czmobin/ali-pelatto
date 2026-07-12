# ============================================================
# تنظیمات ربات پلاتویار
# مقادیر حساس با متغیر محیطی قابل تغییرند (برای سرور).
# ============================================================
import os

# ---- توکن ربات ----
TOKEN = os.environ.get("BOT_TOKEN", "8631100472:AAF-KpEbK-LifRfTETfEeKk5qhpEuYx4CYM")

# ---- کاوه‌نگار ----
KAVENEGAR_API_KEY = os.environ.get(
    "KAVENEGAR_API_KEY",
    "61395A7A4E785A387534506D4E364C7A6C712B6868505A433634694E4F727934317A5A45527559333032633D",
)
KAVENEGAR_TEMPLATE_NEWAGAHI = "telegram-newagahi"
KAVENEGAR_TEMPLATE_RESID = "telegram-resid"
KAVENEGAR_TEMPLATE_KHARID = "telegram-kharid"
KAVENEGAR_TEMPLATE_TAEED = "telegram-taeed-karid"
KAVENEGAR_TEMPLATE_VERIFY = "telegram-verify"
KAVENEGAR_TEMPLATE_GHEYMAT_ADMIN = "telegram-gheymatadmin"
KAVENEGAR_TEMPLATE_GHEYMAT_OK = "telegram-gheymatok"

# ---- ادمین‌ها ----
ADMIN_ID = 7528842090                 # ادمین اصلی (مقصد پیش‌فرض برخی سازگاری‌ها)
ADMIN_IDS = [7528842090, 127679626]   # همه‌ی ادمین‌ها؛ اولی ادمین اصلی است
ADMIN_USERNAME = "@PLATOYAR2"
ADMIN_PHONE = "09919173528"
SUPPORT_CHANNEL = "@PLATOYARSHOP_bot"

# ---- امضا ----
SIGNATURE = f"""
━━━━━━━━━━━━━━━━━━━━
👤 ایدی ادمین: {ADMIN_USERNAME}
📢 کانال ما: @platoyar_iD
━━━━━━━━━━━━━━━━━━━━"""

# ---- کارت ----
CARD_NUMBER = "6219861872243216"
CARD_NAME = "کرمشاهی"

# ---- کانال‌ها ----
MAIN_CHANNEL_ID = "@PLATO_YAR_MD"
MAIN_CHANNEL_LINK = "https://t.me/PLATO_YAR_MD"
GAME_CHANNEL_ID = "@platoyar_iD"
GAME_CHANNEL_LINK = "https://t.me/platoyar_iD"
NEW_CHANNEL_ID = "@GAMEYARS"
NEW_CHANNEL_LINK = "https://t.me/GAMEYARS"

# ---- گروه‌های سفارش ----
# chat id عددی گروه (مثل -1001234567890) را اینجا یا با متغیر محیطی بگذارید.
# اگر خالی بماند، همان رفتار قبلی (ارسال به پیوی همه‌ی ادمین‌ها) اجرا می‌شود.
def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

# گروه ۱: ثبت آگهی جدید و قیمت‌گذاری همان آگهی (+ تخفیف + انتشار)
GROUP_ADS = _int_or_none(os.environ.get("GROUP_ADS", "-1004317332470")) or None
# گروه ۲: فقط قیمت‌گذاری
GROUP_PRICING = _int_or_none(os.environ.get("GROUP_PRICING", "-1004362886632")) or None
# گروه ۳: شارژ کیف پول + خرید اکانت + رسید تراکنش + برداشت
GROUP_WALLET = _int_or_none(os.environ.get("GROUP_WALLET", "-1004483394723")) or None

# ---- مسیر داده‌ها ----
# پیش‌فرض: پوشه‌ی data کنار همین پکیج. با BOT_DATA_FOLDER قابل override است.
DATA_FOLDER = os.environ.get(
    "BOT_DATA_FOLDER",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)
os.makedirs(DATA_FOLDER, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_FOLDER, "profiles.json")
AGAHI_FILE = os.path.join(DATA_FOLDER, "agahi_data.json")
PENDING_ADS_FILE = os.path.join(DATA_FOLDER, "pending_ads.json")
COUNTER_FILE = os.path.join(DATA_FOLDER, "counter.json")
BLACKLIST_FILE = os.path.join(DATA_FOLDER, "blacklist.json")
WALLET_FILE = os.path.join(DATA_FOLDER, "wallet.json")
REJECT_COUNTER_FILE = os.path.join(DATA_FOLDER, "reject_counter.json")
PRICE_REQUEST_FILE = os.path.join(DATA_FOLDER, "price_requests.json")
REJECTED_ADS_FILE = os.path.join(DATA_FOLDER, "rejected_ads.json")
DISCOUNT_REQUEST_FILE = os.path.join(DATA_FOLDER, "discount_requests.json")
REFERRAL_FILE = os.path.join(DATA_FOLDER, "referral.json")
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")  # ثبت همه‌ی کاربرانی که ربات را استارت کرده‌اند
SHOP_PRICES_FILE = os.path.join(DATA_FOLDER, "shop_prices.json")  # قیمت آیتم‌های فروشگاه (قابل ویرایش ادمین)

# ---- درگاه پرداخت زیبال ----
# تا وقتی زیردامنه‌ی callback (pay.platoyar.com) آماده نشده، خالی می‌ماند و درگاه آنلاین غیرفعال است.
ZIBAL_MERCHANT = os.environ.get("ZIBAL_MERCHANT", "")
ZIBAL_CALLBACK_URL = os.environ.get("ZIBAL_CALLBACK_URL", "")
ZIBAL_ENABLED = bool(ZIBAL_MERCHANT and ZIBAL_CALLBACK_URL)

# ---- تعرفه‌ها ----
PRICE_ADMIN_PRICE = 20000
PRICE_CHANNEL_GAME = 50000
PRICE_CHANNEL_BOTH = 150000
MIN_WITHDRAW_AMOUNT = 50000

# ---- محدودیت تماس صوتی ----
VOICE_CALL_COOLDOWN = 60
