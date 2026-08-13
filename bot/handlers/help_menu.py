"""راهنما و فهرست دستورات — نسخه 4.4.0"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS, BOT_VERSION
from services.i18n import tr, t as _t, get_lang, set_lang

router = Router()

SECTIONS = {
    "start": (
        "🚀 شروع و پایه",
        " /start — شروع ربات و کیبورد اصلی\n"
        " /help | /راهنما | /منو — راهنمای بخش‌بخش\n"
        " /commands | /دستورات — فهرست کامل دستورات\n"
        " /rules | /قوانین — قوانین بازی\n"
        " /codex | /دانشنامه — دانشنامه آیتم‌ها و مفاهیم\n"
        " /profile | /me | /پروفایل — پروفایل کامل\n"
        " /gender | /جنسیت — مرد یا زن (دائمی؛ یا بنویس: مرد / زن)\n"
        " /race | /نژاد — نژاد (نامیرا قوی؛ خدایان/قادر مطلق: ادمین)\n"
        " /lang | /زبان — زبان ربات\n"
        " /version | /نسخه — نسخه ربات و وب‌اپ\n"
        " /ping — تست آنلاین\n"
        " /notice | /پیام‌سازنده — پیام جهانی\n"
        " /season | /فصل — فصل جاری\n"
        " /events | /رویدادها — رویدادها\n"
        " /statuscard | /کارت — کارت وضعیت\n\n"
        "ترتیب پیشنهادی:\n"
        "/start → مرد یا زن → /race → /gather → /learntech
 تکنیک ساخت جهان — قلمرو خدا مرحله ۹+ | /learntech ساخت جهان → /buildings"
    ),
    "cult": (
        "🧘 تذهیب و قلمرو",
        "بنویس «تذهیب کردن» یا «جمع آوری چی» برای جمع انرژی\n"
        " /gather | /qi | /meditate — جمع چی\n"
        " /cultivation | /تذهیب | /cult | تزکیه — وضعیت\n"
        " /realms | /قلمروها — لیست همه قلمروهای تذهیب\n"
        " /learntech — یادگیری تکنیک (هر تکنیک قلمرو/مرحله دارد)\n"
        " /techniques | /تکنیک‌ها — لیست و فعال‌سازی\n"
        " /givetech — انتقال تکنیک (ریپلای)\n"
        " /afk — تذهیب خودکار ۳۰ دقیقه | /afkclaim — دریافت\n"
        " /trainstop — قطع تمرین با پاداش نسبی\n"
        " /learnforbidden | /پرورش‌ممنوعه — قوی ولی قفل مصرف\n"
        " /voidtech | /buyvoidtech | /showvoidtech | /learnvoidtech — تکنیک پوچی\n"
        " /cultpath
 /daopath ارتدوکس|شیطانی|بی‌طرف — مسیر معنوی (محدودیت تکنیک) — مسیر قدرت/سرعت/دفاع\n/worldblade — شمشیر نابودکننده جهان\n/cultbuilding | /upgradecultbuilding — ساختمان تذهیب\n"
        " /vein | /رگ — رگ‌های معنوی\n\n"
        "فاصله قلمروها بیشتر شده (۱۵ مرحله / انرژی پایه ۵۰۰هزار)"
    ),
    "body": (
        "💪 بدن و روح",
        "پرورش بدن باید متعادل باشد (اختلاف سطح ≤ ۲)\n"
        "بنویس: پرورش پوست | پرورش عضله | …\n"
        " /trainyang | /تمرین — بازیابی یانگ از‌دست‌رفته (یا تعادل یین)\n/bodycult | /bodytechs | /mybody — پرورش بدن\n"
        " /bodyrealms | /قلمروبدن — ۱۵ قلمرو بدن\n"
        " /spiritrealms | /قلمروروح — ۱۵ قلمرو روح\n"
        " /trainspirit — تمرین روح\n"
        " /knowledge | /readbook | /wanderworld | /talkmaster — دانش\n"
        " /trainbody — لول بدن جدا\n"
        "قدرت مؤثر بدن سقف دارد؛ اسپم یک تکنیک بی‌فایده است"
    ),
    "combat": (
        "⚔️ دوئل و آرنا",
        " /duel
 /randomduel | /دوئل‌رندوم — صف/حریف تصادفی
 /randomduelfight — دوئل رندوم فوری
 /cancelrandom — خروج از صف — ریپلای + درخواست دوئل (قدرت، نه شانس)\n"
        " /deathduel — دوئل مرگ\n"
        " /accept | /reject — قبول/رد دوئل\n"
        " /arena — آرناهای برنزی تا خدایان\n"
        " /openarena — آرنای گروهی ۳–۱۰ نفر\n"
        " /challengeleader — چالش رهبری فرقه (فقط قدرت)\n"
        " /guardian — نگهبان سوالی | محدودیت زمانی\n"
        " /kill — حمله (زخم/سم؛ نه یک‌ضرب مگر کوروش)\n"
        "رد دوئل: حداکثر ۵ بار در روز"
    ),
    "social": (
        "👥 اجتماعی و فرقه",
        " /sect | /فرقه — وضعیت فرقه\n"
        " /createsect | /joinsect | /leavesect\n"
        " /transferleader | /challengeleader\n"
        " /master | /disciple — استاد/شاگرد (با دکمه تأیید)\n"
        " /dual | /تذهیب‌دوگانه — ریپلای | /canceldual — لغو\n"
        " /marry | /divorce | /wedding — ازدواج\n"
        " /children | /namechild — فرزندان\n"
        " /servants | /buy servant — خدمتکار\n"
        " /knights — شوالیه محافظ\n"
        " /tribe | /declarewar — قبیله و جنگ"
    ),
    "eco": (
        "💰 اقتصاد و خانه",
        " /wallet | /کیف — همه ارزها\n"
        " /pay نوع مقدار — انتقال (ریپلای یا آیدی)\n"
        " /payall coins 10 spirit 2 — چند ارز\n"
        " انواع: coins spirit heavenly celestial god chaos void origin karma\n"
        " /exchangestone | /exchangecoin — سکه ↔ روحی\n"
        " /exchangeup heavenly|celestial|god|chaos|void|origin\n"
        " /exchangedown spirit|heavenly|celestial|god|chaos|void|origin\n"
        " /dailycoin

📅 <b>رویداد و نگهداشت</b>
 /guide — راهنمای سه‌مرحله‌ای تازه‌کار
 /daily — ورود روزانه و استریک (۷روز بهشتی، ۳۰روز آسمانی)
 /event — وضعیت رویداد هفتگی
 /eventjoin /eventscore /eventtop
 /warstatus — پنجره جنگ قلمرو (هر ۳ روز، ۲ ساعت)
 /marketoffer شماره قیمت — پیشنهاد روی آگهی
 /offers شماره — دیدن پیشنهادها
 /repair — تعمیر (غرق سکه)
 — سکه روزانه (یک‌بار در روز)\n"
        " /myhome | /upgradehome | /buyfurniture — خانه\n"
        " /buymine | /claimmine | /upgrademine — معدن روح\n"
        " /market — بازار آزاد"
    ),
    "shop": (
        "🏪 فروشگاه و ساخت",
        "بنویس نام ساختمان: داروخانه | آهنگری | چای‌خانه | کیمیاگری | …\n"
        "بنویس: خرید نام‌آیتم\n"
        " /buildings — همه ساختمان‌ها\n"
        " /teahouse — چای‌خانه\n"
        " /inventory
 /use شماره تعداد — مصرف دسته‌ای (مثلاً ۴ قرص)
 /buyitem نام|شماره تعداد — خرید دسته‌ای | /use — کیف و مصرف\n"
        " /equip | /unequip — سلاح\n"
        " /craft — ساخت معجون/طلسم\n"
        " /codex | /itemlist — دانشنامه آیتم‌ها\n"
        " /garden | /plant — باغ"
    ),
    "chars": (
        "🎭 کاراکتر و پت",
        " /pullchar | /کاراکتر — گacha\n"
        " /mychars | /bestchar | /charrates\n"
        " /tradechar | /accepttrade — معاوضه\n"
        " /charduel | /acceptcharduel — دوئل کاراکتر\n"
        "رتبه‌های بالا (اسطوره‌ای+): قدرت خیلی بیشتر\n"
        " /pets | /huntpet | /tame — حیوانات\n"
        " /feedpet | /trainpet"
    ),
    "world": (
        "🌍 دنیا و مأموریت",
        " /travel | /city | /explorecity — سفر و شهر\n"
        " /cave — غار\n"
        " /missions | /daily — مأموریت\n"
        "جهان فانی / بهشتی / زیرین + هشت جهان اولیه\n"
        " /jobs | /work — شغل\n"
        " /luckdice — تاس شانس"
    ),
    "games": (
        "🎮 بازی‌ها و وب‌اپ",
        " /games | /game — منوی بازی\n"
        "شطرنج | تخته‌نرد | حکم | سنگ‌کاغذ | کازینو\n"
        "وب‌اپ: پروفایل، لیدربورد
 /richest | /پولدارترین — لیست پولدارها، فرقه، ورود روزانه\n"
        "محدودیت بازی حدود ۲ دقیقه\n"
        "دکمه 🔄 برای رفرش بازی آنلاین"
    ),
    "admin": (
        "🛡 ادمین (سازنده)",
        "فقط ADMIN_IDS در .env\n"
        " /admin | /helpforadmin — پنل ادمین\n"
        " /unlockconsume [آیدی] — باز کردن قفل مصرف\n"
        "ارتقا/تنزل رتبه، پول دادن/گرفتن، تغییر قلمرو چی\n"
        "محافظت فرقه از مصیبت، ادمین‌شاپ"
    ),
}



def help_keyboard(user_id: int = 0):
    b = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        if key == "admin" and user_id not in ADMIN_IDS:
            continue
        b.button(text=title, callback_data=f"helpsec:{key}")
    b.button(text="📋 همه دستورات", callback_data="helpsec:allcmds")
    b.adjust(2)
    return b.as_markup()


@router.message(Command("help", "راهنما", "منو", "helpmenu"))
async def cmd_help(message: Message):
    await message.answer(
        f"📖 <b>راهنما — نسخه {BOT_VERSION}</b>\n"
        "بخش مورد نظر را انتخاب کن:",
        reply_markup=help_keyboard(message.from_user.id),
    )


@router.callback_query(F.data.startswith("helpsec:"))
async def help_section(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    if key == "allcmds":
        await callback.message.answer(full_commands_text())
        await callback.answer()
        return
    if key == "admin" and callback.from_user.id not in ADMIN_IDS:
        await callback.answer("فقط سازنده", show_alert=True)
        return
    title, body = SECTIONS.get(key, ("", "بخش نامعتبر"))
    await callback.message.answer(f"<b>{title}</b>\n\n{body}")
    await callback.answer()


def full_commands_text() -> str:
    lines = [f"📋 <b>فهرست دستورات — {BOT_VERSION}</b>", ""]
    for key, (title, body) in SECTIONS.items():
        lines.append(f"<b>{title}</b>")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


@router.message(Command("commands", "دستورات", "cmds", "لیست‌دستورات"))
async def cmd_commands(message: Message):
    text = full_commands_text()
    # split
    while text:
        await message.answer(text[:4000])
        text = text[4000:]


@router.message(Command("rules", "قوانین"))
async def cmd_rules(message: Message):
    await message.answer(
        f"📜 <b>قوانین — {BOT_VERSION}</b>\n\n"
        "۱) چندحسابه مجاز است ولی سوءاستفاده ممنوع\n"
        "۲) دوئل و چالش رهبری بر اساس قدرت است نه شانس\n"
        "۳) پرورش بدن باید متعادل باشد\n"
        "۴) تکنیک/چای ممنوعه مصرف را قفل می‌کند\n"
        "۵) داده‌های پیشرفت روی دیتابیس/دیسک ذخیره می‌شوند\n"
        "۶) تصمیم ادمین سازنده نهایی است\n"
        "۷) درخواست‌های عجیب خارج از دنیای بازی نکنید"
    )


@router.message(Command("version", "نسخه"))
async def cmd_version(message: Message):
    from bot.config import WEBAPP_VERSION
    await message.answer(
        f"🤖 ربات: <b>{BOT_VERSION}</b>\n"
        f"🌐 وب‌اپ: <b>{WEBAPP_VERSION}</b>\n"
        "ذخیره پایدار: persist + persist_kv"
    )


@router.message(Command("helpforadmin", "راهنماادمین"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط سازنده.")
        return
    title, body = SECTIONS["admin"]
    await message.answer(f"<b>{title}</b>\n\n{body}\n\n/admin برای پنل")
