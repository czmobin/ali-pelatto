# ============================================================
# تنظیمات ربات پلاتویار
# مقادیر حساس با متغیر محیطی قابل تغییرند (برای سرور).
# ============================================================
import os
import json

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
SUPER_ADMIN_ID = 7528842090           # فقط این اکانت می‌تواند ادمین اضافه/حذف کند (@PLATOYAR2)
# ادمین‌های پایه (لیستِ زنده؛ در جای خود mutate می‌شود تا همه‌ی ماژول‌ها همان شیء را ببینند)
ADMIN_IDS = [7528842090, 127679626, 1301523142]
ADMIN_USERNAME = "@PLATOYAR2"
ADMIN_PHONE = "09919173528"
SUPPORT_CHANNEL = "@PLATOYARSHOP_bot"

# ---- امضا ----
SIGNATURE = f"""
━━━━━━━━━━━━━━━━━━━━
👤 ایدی ادمین: {ADMIN_USERNAME}
📢 کانال ما: @platoyar_iD
━━━━━━━━━━━━━━━━━━━━"""

# ---- امضای مخصوص فروشگاه ----
SHOP_SIGNATURE = """
━━━━━━━━━━━━━━━━━━━━
👤 ایدی ادمین: @PLATOYAR_ADMiN1
📢 کانال ما: https://t.me/PLATO_YAR_MD
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

# همه‌چیز در یک گروه: «گروه ادمینی سفارشات ربات پلاتویار» (-1003729150291).
# آگهی، قیمت‌گذاری، شارژ، برداشت، خرید اکانت، تراکنش، تخفیف و سفارش‌های فروشگاه — همه اینجا می‌آید.
# گروه‌های ۱ و ۲ و ۳ قبلی دیگر استفاده نمی‌شوند.
_ADMIN_GROUP = "-1003729150291"
GROUP_ADS = _int_or_none(os.environ.get("GROUP_ADS", _ADMIN_GROUP)) or None
GROUP_PRICING = _int_or_none(os.environ.get("GROUP_PRICING", _ADMIN_GROUP)) or None
GROUP_WALLET = _int_or_none(os.environ.get("GROUP_WALLET", _ADMIN_GROUP)) or None
GROUP_SHOP = _int_or_none(os.environ.get("GROUP_SHOP", _ADMIN_GROUP)) or None

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
SHOP_UNAVAILABLE_FILE = os.path.join(DATA_FOLDER, "shop_unavailable.json")  # لیست بخش‌های ناموجود فروشگاه
ADMINS_FILE = os.path.join(DATA_FOLDER, "admins.json")  # ادمین‌های اضافه‌شده در زمان اجرا
SHOP_ORDERS_FILE = os.path.join(DATA_FOLDER, "shop_orders.json")  # سفارش‌های فروشگاه
SETTINGS_FILE = os.path.join(DATA_FOLDER, "settings.json")  # تنظیمات قابل‌ویرایش از پنل (هزینه‌ها، کارت، متن‌ها)

# ادمین‌های ذخیره‌شده در فایل را به لیست زنده اضافه کن (بدون ساختن شیء جدید)
try:
    with open(ADMINS_FILE, encoding="utf-8") as _af:
        for _a in json.load(_af):
            if int(_a) not in ADMIN_IDS:
                ADMIN_IDS.append(int(_a))
except Exception:
    pass

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
