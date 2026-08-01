from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import ADMIN_IDS

router = Router()

SECTIONS = {
    "rules": (
        "📜 قوانین",
        "۱) احترام به بازیکنان — توهین ممنوع\n"
        "۲) جنسیت با /gender فقط یک‌بار و دائمی است\n"
        "۳) دوئل و کشتار بخشی از بازی است؛ خارج از بازی دعوا نکنید\n"
        "۴) آسیب به خدمتکار = حذف اکانت\n"
        "۵) حداکثر ۳ مأموریت در روز؛ چهارمی = حذف اکانت\n"
        "۶) سوءاستفاده از باگ را گزارش دهید\n"
        "۷) کنترل کل ربات فقط مال سازنده است\n"
        "۸) شرط‌بندی دوئل با رضایت دو طرف است\n"
        "۹) خودارضایی باکرگی را از بین نمی‌برد\n"
        "۱۰) ادمین می‌تواند تذهیب/پول را تنظیم کند"
    ),
    "start": (
        "🚀 شروع و پروفایل",
        "/start — ثبت‌نام\n"
        "/profile — پروفایل (رتبه، عمر، کیف پول، تذهیب…)\n"
        "/gender — جنسیت دائمی (قبل از تذهیب اجباری)\n"
        "/iamadmin — چک ادمین بودن"
    ),
    "duel": (
        "⚔️ دوئل و جنگ",
        "/duel [مبلغ] — دوئل بر اساس قدرت و سلاح مجهز (خون کم می‌شود)\n/deathduel — دوئل تا مرگ\n/equip · /unequip — سلاح\n/kill — زخم+سم (۳ ساعت /heal)\n/blood — وضعیت خون\n/heal — قرص سلامتی\n"
        "  رد دوئل حداکثر ۵ بار در روز\n"
        "  ۲٪ شانس آسیب به قلمرو بازنده\n"
        "/guardian — نگهبان (هر ۵ دقیقه)\n"
        "/gduel — نگهبان دو نفره\n"
        "/kill — حمله مرگبار\n"
        "/power — قدرت\n"
        "/ranking · /leaders — لیدربورد"
    ),
    "cult": (
        "🧘 تذهیب",
        "/cultivation — وضعیت\n/afk · /afkclaim — تذهیب خودکار\n/body — نوع بدن\n"
        "«تذهیب کردن» / «جمع آوری چی» → +۵۰۰۰ انرژی\n"
        "هر سطح ۵۰۰۰۰ انرژی | هر قلمرو ۱۰ مرحله\n"
        "قلمروها تا ای‌تری، جاودان، خلقت…\n"
        "/techniques · /learntech\n"
        "/solo — خودارضایی (+انرژی، −عمر، بدون از دست دادن باکرگی)\n"
        "/dual — تذهیب دوگانه\n"
        "/path — مسیر (شیطانی، ارتدوکس…)\n"
        "/afterdeath · /releasespirit"
    ),
    "sect": (
        "🏛️ فرقه",
        "/sects · /newsect · /joinsect · /mysect\n"
        "/challengeleader · /transferleader · /betray\n"
        "/territories · /conquer · /sectsettings"
    ),
    "family": (
        "💍 خانواده",
        "/marry — خواستگاری (مرد یا زن)\n"
        "/divorce · /wives · /invitewedding\n"
        "/dual — جفت‌گیری / شانس بچه\n"
        "/servants — خدمتکار (آسیب=حذف اکانت)"
    ),
    "shop": (
        "🛒 مغازه و منابع",
        "/buildings — مغازه با سکه\n"
        "/inventory · /use · /drop\n"
        "/craft · /pets · /hunt\n"
        "/wallet · /dailycoin · /daily\n"
        "/pay — ارسال پول به دیگران\n"
        "/market · /marketbuy — بازار آزاد\n"
        "/exchangeup heavenly|celestial|god\n"
        "/garden · /plant · /harvest"
    ),
    "world": (
        "🏙️ جهان",
        "/cities · /mycity · /travel\n"
        "/worlds · /goworld · /worldlist\n"
        "/creatures · /huntcreature\n"
        "/attackdim — حمله به بُعد\n"
        "/dimension · /setdimension"
    ),
    "mission": (
        "🎯 مأموریت",
        "/missions — روزانه (هر کدام یک‌بار در روز)\n"
        "حداکثر ۳؛ چهارمی = حذف اکانت\n"
        "/completemission\n"
        "/auction · /bid\n"
        "/master · /takedisciple · /leavemaster"
    ),
    "games": (
        "🎮 بازی‌ها",
        "/games — منوی بازی\n"
        "/rps — سنگ‌کاغذ‌قیچی با ربات\n"
        "/rpsduel — سنگ‌کاغذ با دیگران\n"
        "/dice · /chess · /casino مبلغ\n"
        "/guess — حدس عدد\n"
        "/coinflip شیر|خط\n"
        "/hukum — بازی حکم (کارت)\n"
        "وب‌اپ: Menu Button → /webapp/games.html"
    ),
}


@router.message(Command("help", "راهنما", "منو"))
async def cmd_help_menu(message: Message):
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.adjust(1)
    await message.answer(
        "📖 <b>راهنمای ربات فرقه</b>\n"
        "یک بخش را انتخاب کن:\n\n"
        "📜 اول قوانین را بخوان.",
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
        "📖 <b>راهنمای ربات فرقه</b>\nیک بخش را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(Command("helpforadmin", "راهنما‌ادمین"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ فقط سازنده ربات.")
        return
    text = (
        "🛠 <b>یادآوری اختیارات ادمین</b>\n\n"
        "<b>هویت</b>\n"
        "/iamadmin — تأیید ادمین بودن\n"
        "/admin — پنل خلاصه\n\n"
        "<b>نقش‌ها</b>\n"
        "/setrole &lt;telegram_id&gt; &lt;نقش&gt;\n"
        "نقش: رهبر | معاون رهبر | ارجمند | ارشد | عضو\n\n"
        "<b>تذهیب</b>\n"
        "/setcult — ریپلای یا آیدی\n"
        "مثال: ریپلای + /setcult ای‌تری 5 1000\n"
        "یا /setcult 6227792513 پایه 3 0\n\n"
        "<b>پول</b>\n"
        "/givemoney — دادن (ریپلای یا آیدی)\n"
        "مثال: /givemoney coins 500\n"
        "نوع: coins | spirit | heavenly | celestial | god\n"
        "/takemoney — گرفتن همین فرمت\n\n"
        "<b>بُعد گروه</b>\n"
        "/setdimension فانی|بهشتی|زیرین\n\n"
        "<b>نکات</b>\n"
        "• فقط ADMIN_IDS به این دستورات دسترسی دارد\n"
        "• رهبری فرقه ≠ ادمین کل ربات\n"
        "• DATABASE_URL را برای حفظ دیتا تنظیم کن\n"
    )
    await message.answer(text)
