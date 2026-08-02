
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import ADMIN_IDS

router = Router()

SECTIONS = {
    "rules": (
        "📜 قوانین بازی",
        "۱) احترام به بازیکنان — توهین و اسپم ممنوع\n"
        "۲) جنسیت با /gender فقط یک‌بار و دائمی است\n"
        "۳) دوئل و جنگ بخشی از بازی است؛ خارج از بازی دعوا نکنید\n"
        "۴) آسیب به خدمتکار = حذف اکانت\n"
        "۵) حداکثر ۳ مأموریت روزانه؛ چهارمی = حذف اکانت\n"
        "۶) سوءاستفاده از باگ را گزارش دهید\n"
        "۷) کنترل کل ربات فقط مال سازنده (ADMIN) است\n"
        "۸) شرط دوئل با رضایت دو طرف است\n"
        "۹) خودارضایی باکرگی را از بین نمی‌برد\n"
        "۱۰) پرورش ممنوعه غیرقابل برگشت است\n"
        "۱۱) شمشیر کوروش یکتاست و ضربه آن اکانت را پاک می‌کند\n"
        "۱۲) سم بعد از /kill سه ساعت وقت /heal دارد"
    ),
    "start": (
        "🚀 شروع",
        "/start — ثبت‌نام\n"
        "/profile — پروفایل کامل\n"
        "/gender — انتخاب جنسیت (اجباری قبل از تذهیب)\n"
        "/help — همین منو\n"
        "/ping — تست آنلاین بودن ربات\n\n"
        "اول /gender بزن، بعد تذهیب را شروع کن."
    ),
    "cult": (
        "🧘 تذهیب",
        "با نوشتن «تذهیب کردن» یا «جمع آوری چی» انرژی می‌گیری.\n"
        "/cultivation — وضعیت قلمرو، مرحله، ریشه، بدن\n"
        "/learntech — تکنیک پایه\n"
        "/learnforbidden — ⚠️ پرورش ممنوعه (قفل ابدی، بار اول +سطح، هر بار +۱ چی)\n"
        "/techniques — لیست و فعال‌سازی\n"
        "/afk و /afkclaim — تذهیب خودکار ۳۰ دقیقه\n"
        "/body — نوع بدن (ضریب تذهیب)\n"
        "/solo — تمرین انفرادی\n"
        "/dual — تذهیب دوگانه (زن و مرد)\n\n"
        "قلمروها از بیداری تا مطلق؛ هرچه بالاتر سخت‌تر.\n"
        "چای تذهیب از مغازه: +۸۰۰۰ انرژی هر ۱۰ دقیقه (۵۰۰ سکه)."
    ),
    "duel": (
        "⚔️ جنگ و دوئل",
        "/duel — دوئل قدرتی (سلاح مجهز + تکنیک)؛ خون کم می‌شود\n"
        "/deathduel — تا مرگ\n"
        "/kill — زخم + سم (۳ ساعت /heal)\n"
        "/equip و /unequip — سلاح\n"
        "/blood — خون و سم\n"
        "/heal — قرص سلامتی\n"
        "/guardian — سوال نگهبان\n"
        "/arena · /arenafight · /arenatop\n"
        "/lootarena — آرنای غنیمت\n"
        "/power — قدرت رزمی"
    ),
    "sect": (
        "🏛️ فرقه و جهان",
        "/sects · /newsect · /joinsect · /mysect\n"
        "/challengeleader · /transferleader\n"
        "/cities · /travel · /explorecity (سلاح مخفی)\n"
        "/worlds · /creatures · /huntcreature\n"
        "/path — مسیر تذهیب"
    ),
    "shop": (
        "🛒 مغازه و کیف",
        "/buildings — خرید از ساختمان‌ها\n"
        "/inventory — کیف\n"
        "/use شماره — استفاده (چای، قرص، …)\n"
        "/gift شماره — هدیه به کسی (ریپلای)\n"
        "/drop شماره — دور انداختن\n"
        "/wallet · /dailycoin · /pay\n"
        "/market · /marketbuy — بازار آزاد\n"
        "/garden · /plant · /harvest"
    ),
    "family": (
        "💍 خانواده",
        "/marry — خواستگاری (مرد یا زن)\n"
        "/divorce · /wives\n"
        "/master · /takedisciple · /askmaster · /leavemaster\n"
        "/servants — خدمتکار"
    ),
    "games": (
        "🎮 بازی‌ها",
        "/games — منوی ربات\n"
        "وب‌اپ: شطرنج واقعی، تخته‌نرد ایرانی، حکم، سنگ‌کاغذ، کازینو\n"
        "/hukum · /rpsduel · /guess · /coinflip\n"
        "سرباز در شطرنج می‌تواند به وزیر/رخ/فیل/اسب تبدیل شود."
    ),
    "extra": (
        "✨ بخش ویژه",
        "/codex — دانشنامه کوتاه جهان فرقه\n"
        "/daily — مأموریت/پاداش روزانه\n"
        "/leaders · /solotop · /ranking\n"
        "/possess — تسخیر (فقط روح، یک‌بار)\n"
        "وب‌اپ ورود روزانه: +۵ سنگ بهشتی"
    ),
}


@router.message(Command("help", "راهنما", "منو"))
async def cmd_help_menu(message: Message):
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.adjust(1)
    await message.answer(
        "📖 <b>راهنمای دنیای فرقه</b>\n"
        "یک بخش را انتخاب کن.\n"
        "پیشنهاد: اول <b>قوانین</b> و <b>شروع</b> را بخوان.",
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
        "📖 <b>راهنمای دنیای فرقه</b>\nیک بخش را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(Command("helpforadmin", "راهنما‌ادمین"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ فقط سازنده ربات.")
        return
    await message.answer(
        "🛠 <b>ادمین</b>\n"
        "/iamadmin · /admin\n"
        "/setrole · /setcult · /givemoney · /takemoney\n"
        "/adshop · /adget نام‌آیتم — فروشگاه رایگان\n"
        "/setdimension\n"
    )


@router.message(Command("codex", "دانشنامه"))
async def cmd_codex(message: Message):
    await message.answer(
        "📚 <b>دانشنامه کوتاه</b>\n\n"
        "• <b>تذهیب</b>: جمع انرژی و بالا رفتن قلمرو\n"
        "• <b>ریشه</b>: نوع استعداد؛ کمیاب‌ها قوی‌تر و گاهی سخت‌تر\n"
        "• <b>فرقه</b>: گروه بازیکنان با رهبری و قلمرو\n"
        "• <b>آرنا</b>: رقابت رتبه‌ای با هزینه ورود\n"
        "• <b>سم</b>: بعد از حمله؛ ۳ ساعت وقت درمان\n"
        "• <b>پرورش ممنوعه</b>: قدرت سریع با قفل دائمی\n"
        "• <b>شمشیر کوروش</b>: یکتا؛ ضربه = پاک شدن اکانت\n\n"
        "برای جزئیات: /help"
    )
