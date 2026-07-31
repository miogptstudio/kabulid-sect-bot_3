from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

SECTIONS = {
    "start": (
        "🚀 شروع و پروفایل",
        "/start — ثبت‌نام و خوش‌آمد\n"
        "/profile — پروفایل کامل (رتبه، نقش، شهر، قدرت، عمر…)\n"
        "/iamadmin — وضعیت ادمین بودن\n"
        "/gender — انتخاب جنسیت (فقط یک‌بار، دائمی)\n"
        "قبل از تذهیب حتماً جنسیت بزن."
    ),
    "duel": (
        "⚔️ دوئل و نگهبان و جنگ",
        "/duel — ریپلای روی حریف؛ دکمه قبول/رد\n"
        "  نتیجه بر اساس قدرت است؛ رد دوئل حداکثر ۵ بار در روز\n"
        "/guardian — سوال نگهبان (هر ۵ دقیقه، چند ثانیه وقت)\n"
        "/gduel — دوئل نگهبان دو نفره (ریپلای)\n"
        "/kill — حمله مرگبار (ریپلای)؛ ممکن است بکشی یا کشته شوی\n"
        "/power — قدرت رزمی\n"
        "/ranking — لیدربورد"
    ),
    "cult": (
        "🧘 تذهیب و ریشه",
        "/cultivation — وضعیت تذهیب و انرژی\n"
        "بگو: «تذهیب کردن» یا «جمع آوری چی» → +۴۰۰ انرژی\n"
        "نیاز سطح بعد: ۲۰۰۰۰۰ + هر سطح ۲۵۰۰۰۰\n"
        "بدون ریشه باید انرژی جمع کنی تا ریشه شانسی بیدار شود\n"
        "/techniques · /learntech — تکنیک‌ها\n"
        "/solo — خودارضایی (+انرژی، −عمر)\n"
        "/dual — تذهیب دوگانه (ریپلای، مرد+زن)\n"
        "/afterdeath — بعد از مرگ (روح / انتقام / پوچی)\n"
        "/releasespirit — ترک روح انتقام"
    ),
    "sect": (
        "🏛️ فرقه و قلمرو",
        "/sects — لیست فرقه‌ها\n"
        "/newsect نام — ساخت فرقه + انتخاب نوع با دکمه\n"
        "/joinsect نام — عضو شدن\n"
        "/mysect — فرقه و مشارکت تو\n"
        "/transferleader — واگذاری رهبری (ریپلای)\n"
        "/challengeleader — چالش رهبری (هر ۱ ساعت)\n"
        "  بازنده ممکن است بمیرد مگر رهبر ببخشد\n"
        "/betray — خیانت و ترک\n"
        "/territories · /conquer — قلمرو\n"
        "/sectsettings — تنظیمات (فقط رهبر)"
    ),
    "family": (
        "💍 خانواده",
        "/gender — جنسیت دائمی\n"
        "/marry — نامزدی (ریپلای؛ فقط مرد درخواست)\n"
        "/divorce — طلاق (ریپلای)\n"
        "/wives — خانواده\n"
        "/invitewedding — دعوت مهمان\n"
        "/mate — راهنمای جفت‌گیری"
    ),
    "shop": (
        "🛒 مغازه، ساخت، حیوان",
        "/buildings — مغازه (خرید با سکه)\n"
        "/inventory — کیف\n"
        "/craft — ساخت معجون و طلسم\n"
        "/pets — حیوانات من\n"
        "/hunt — شکار (خطر زخم/مرگ)\n"
        "/sellpet شماره — فروش\n"
        "/giftpet شماره — هدیه (ریپلای)\n"
        "/wallet — سکه و سنگ روحی\n"
        "/dailycoin · /daily — سکه روزانه و استریک\n"
        "/exchangestone · /exchangecoin — تبدیل"
    ),
    "world": (
        "🏙️ جهان و سفر",
        "/cities — کشورها و شهرها (هر شهر مرحله خاص دارد)\n"
        "/mycity — جزئیات شهر فعلی\n"
        "/travel نام‌شهر — سفر\n"
        "مثال: /travel بندرعباس | /travel کابل | /travel دبی\n"
        "/worlds · /goworld — دنیای فانی/بهشتی/زیرین\n"
        "/dimension — بُعد این گروه\n"
        "/setdimension — تنظیم بُعد (ادمین)"
    ),
    "mission": (
        "🎯 مأموریت و پیشرفت",
        "/missions — مأموریت روزانه (حداکثر ۳)\n"
        "اگر بعد از ۳ تا چهارمی بگیری اکانت پاک می‌شود\n"
        "/completemission — تکمیل مأموریت فعال\n"
        "/daily — استریک ورود روزانه\n"
        "/auction · /bid — مزایده\n"
        "/master · /takedisciple · /leavemaster — استاد و شاگرد"
    ),
    "games": (
        "🎮 مینی‌اپ و بازی",
        "Menu Button در BotFather → آدرس /webapp/\n"
        "بازی‌ها: /webapp/games.html\n"
        "شطرنج، تخته‌نرد، سنگ‌کاغذ‌قیچی، کازینو"
    ),
    "admin": (
        "🛠 مدیریت",
        "/admin — فقط سازنده ربات (ADMIN_IDS)\n"
        "ارتقا/تنزل، نقش، مسدود و…\n"
        "کنترل کل ربات فقط مال سازنده است."
    ),
}


@router.message(Command("help", "راهنما", "منو"))
async def cmd_help_menu(message: Message):
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.adjust(1)
    await message.answer(
        "📖 <b>راهنمای کامل ربات</b>\n"
        "یک بخش را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("helpsec:"))
async def help_section(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, key = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    title, body = SECTIONS.get(key, ("؟", "نامشخص"))
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ بازگشت", callback_data=f"helpback:{owner}")
    await callback.message.edit_text(
        f"<b>{title}</b>\n\n{body}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("helpback:"))
async def help_back(callback: CallbackQuery):
    owner = int(callback.data.split(":")[1])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{owner}:{key}")
    builder.adjust(1)
    await callback.message.edit_text(
        "📖 <b>راهنمای کامل ربات</b>\nیک بخش را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
