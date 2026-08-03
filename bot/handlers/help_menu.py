from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.config import ADMIN_IDS

router = Router()

SECTIONS = {
    "rules": (
        "📜 قوانین بازی",
        "۱) احترام — توهین، اسپم و تبلیغ ممنوع\n"
        "۲) قبل از تذهیب: /gender (غیرقابل تغییر)\n"
        "۳) نژاد با /race فقط یک‌بار انتخاب می‌شود\n"
        "۴) دوئل و جنگ بخشی از بازی است؛ خارج از بازی دعوا نکنید\n"
        "۵) آسیب به خدمتکار = حذف اکانت\n"
        "۶) حداکثر ۳ مأموریت روزانه؛ چهارمی = حذف اکانت\n"
        "۷) سوءاستفاده از باگ را گزارش دهید\n"
        "۸) کنترل کل ربات فقط برای سازنده (ADMIN) است\n"
        "۹) شرط دوئل با رضایت دو طرف\n"
        "۱۰) خودارضایی باکرگی را از بین نمی‌برد\n"
        "۱۱) پرورش ممنوعه غیرقابل برگشت است\n"
        "۱۲) شمشیر کوروش یکتاست؛ ضربه‌اش اکانت را پاک می‌کند\n"
        "۱۳) بعد از /kill طرف مسموم است؛ ۳ ساعت وقت /heal دارد\n"
        "۱۴) ازدواج: مرد-زن، مرد-مرد، زن-زن مجاز\n"
        "۱۵) بعد از مرگ: /afterdeath — روح، انتقام، یا پوچی (ریست کامل)\n"
        "۱۶) بازی‌ها: هر ۵ دقیقه یک‌بار\n"
        "۱۷) کشاورزی: هر ۵ ساعت یک گیاه؛ ظرفیت ۱۰ زمین (قابل خرید)\n"
        "۱۸) خرید فروشگاه با همه ارزها (سکه تا سنگ خدا) ممکن است"
    ),
    "start": (
        "🚀 شروع و پایه",
        "/start — ثبت‌نام و خوش‌آمدگویی\n"
        "/help یا /راهنما یا /منو — همین راهنما با دکمه‌ها\n"
        "/rules یا /قانون — فقط قوانین\n"
        "/codex یا /دانشنامه — مفاهیم کوتاه بازی\n"
        "/ping یا /تست — چک آنلاین بودن ربات\n"
        "/removekb یا /حذف‌کیبورد — پاک کردن دکمه‌های پایین صفحه\n"
        "/profile یا /me یا /پروفایل — پروفایل کامل (رتبه، تذهیب، کیف، …)\n"
        "/gender یا /جنسیت — انتخاب مرد | زن (اجباری قبل از تذهیب، دائمی)\n"
        "/race یا /نژاد — انتخاب نژاد (یک‌بار؛ هر نژاد ضریب و سبک تذهیب خودش)\n"
        "/iamadmin یا /مقام‌من — چک ادمین بودن + نقش رهبر برای سازنده\n\n"
        "ترتیب پیشنهادی شروع:\n"
        "۱ /start → ۲ /gender → ۳ /race → ۴ /gather → ۵ /learntech"
    ),
    "cult": (
        "🧘 تذهیب و تکنیک",
        "جمع انرژی:\n"
        "• بنویس: تذهیب کردن | جمع آوری چی\n"
        "• /gather یا /qi یا /جمع یا /meditate — همان کار با دستور\n\n"
        "/cultivation یا /تذهیب یا /cult — وضعیت قلمرو، مرحله، ریشه، انرژی، تکنیک\n"
        "/learntech — یادگیری تکنیک پایه (تنفس پایه)\n"
        "/learnforbidden یا /پرورش‌ممنوعه — ⚠️ قفل ابدی؛ بار اول +سطح؛ هر بار +۱ چی\n"
        "/techniques یا /تکنیک‌ها — لیست تکنیک‌ها و فعال‌سازی با دکمه\n"
        "/givetech یا /انتقال‌تکنیک — ریپلای روی کسی + انتقال تکنیک فعال\n"
        "/afk یا /تذهیب‌خودکار — شروع تذهیب خودکار\n"
        "/afkclaim یا /دریافت‌افک — دریافت نتیجه AFK\n"
        "/body یا /بدن — نوع بدن (ضریب تذهیب)\n"
        "/solo یا /خودارضایی یا /انفرادی — تمرین انفرادی (+انرژی؛ محدودیت یانگ/یین)\n"
        "/virgin یا /باکرگی — وضعیت بدن/باکرگی\n"
        "/dual یا /تذهیب‌دوگانه — ریپلای + تذهیب دوگانه\n\n"
        "قلمروها از بیداری تا وحدت/نیستی‌مطلق بالا می‌روند.\n"
        "نژاد و ریشه روی سرعت تذهیب اثر دارند."
    ),
    "duel": (
        "⚔️ دوئل، جنگ، آرنا",
        "/duel یا /دوئل — ریپلای روی حریف؛ دوئل بر اساس قدرت+سلاح (خون کم می‌شود)\n"
        "/duel مبلغ — دوئل با شرط سکه\n"
        "/deathduel — دوئل تا مرگ یکی\n"
        "/kill — حمله: زخم + سم (۳ ساعت وقت درمان با /heal)\n"
        "/equip یا /تجهیز — لیست سلاح‌های کیف؛ /equip شماره برای مسلح کردن\n"
        "/unequip یا /خلع‌سلاح — برداشتن سلاح و برگشت به کیف\n"
        "/blood — وضعیت خون و سم\n"
        "/heal یا /درمان — مصرف قرص/پادزهر برای سم و خون\n"
        "/power — قدرت رزمی تقریبی\n"
        "/guardian — سوال نگهبان (محدودیت زمانی و کول‌داون)\n"
        "/arena — منوی آرنا و درجه‌ها\n"
        "/arenafight — چالش آرنا (ریپلای)\n"
        "/arenatop — لیدربورد آرنا\n"
        "/arenaopen | /arenajoin | /arenastart | /arenarooms — آرنای چندنفره\n"
        "/lootarena — آرنای غنیمت (مرگ قانونی؛ وسایل به ادمین)"
    ),
    "sect": (
        "🏛 فرقه، دنیا، مأموریت",
        "/sects یا /فرقه — لیست و وضعیت فرقه‌ها\n"
        "/createsect — ساخت فرقه (نیاز سطح تذهیب بالا)\n"
        "/joinsect | /leavesect — عضویت / ترک\n"
        "/sectinfo — جزئیات فرقه خودت\n"
        "/missions یا /مأموریت — لیست مأموریت‌ها\n"
        "  انواع: روزانه | شهری | جهانی | فرعی | چندنفره | فرقه‌ای\n"
        "/completemission یا /تموم‌ماموریت — تکمیل مأموریت فعال\n"
        "/travel — سفر بین شهرها\n"
        "/explorecity — کاوش شهر (شانس سلاح مخفی برای اولین بازدید)\n"
        "/world — دنیاهای فانی | بهشتی | زیرین\n"
        "/hunt یا /شکار — شکار (ریسک زخم/مرگ)\n"
        "/ranking — جدول رتبه‌ها"
    ),
    "shop": (
        "🛒 فروشگاه، کیف، کشاورزی",
        "/buildings یا /فروشگاه یا /مغازه — ساختمان‌ها و خرید\n"
        "  خرید با همه ارزها: سکه ← روحی ← بهشتی ← آسمانی ← خدا\n"
        "  اگر سکه کم باشد از ارز بالاتر کسر می‌شود\n"
        "/inventory یا /کیف — لیست آیتم‌های تو\n"
        "/use شماره یا /استفاده — مصرف آیتم (قرص، چای، …)\n"
        "/drop یا /دورریختن — حذف آیتم از کیف\n"
        "/gift یا /هدیه — ریپلای + هدیه آیتم\n"
        "/itemlist یا /لیست‌آیتم یا /دانشنامه‌آیتم — همه آیتم‌ها و روش تهیه\n"
        "/buildingscodex — راهنمای ساختمان دانشنامه\n"
        "/craft — ساخت معجون/طلسم\n"
        "/wallet — موجودی همه ارزها\n"
        "/dailycoin — سکه روزانه\n"
        "/exchangestone — تبدیل سکه↔روحی\n"
        "/exchangeup heavenly | celestial | god — ارتقای ارز\n\n"
        "🌱 کشاورزی:\n"
        "/garden یا /باغ — وضعیت زمین و کول‌داون\n"
        "/plant بذر — کاشت (هر ۵ ساعت فقط ۱ گیاه)\n"
        "  بذرها: معمولی | معنوی | روحی\n"
        "/harvest یا /برداشت — برداشت گیاهان رسیده\n"
        "/buyland یا /خریدزمین — +۵ ظرفیت زمین (۵۰۰۰ سکه یا معادل؛ سقف ۵۰)"
    ),
    "social": (
        "💍 اجتماعی و حیوان",
        "/marry یا /ازدواج یا /نامزدی — ریپلای + خواستگاری (مرد-زن | مرد-مرد | زن-زن)\n"
        "/divorce یا /طلاق — ریپلای روی همسر\n"
        "/wives — لیست همسران\n"
        "/master — استاد و شاگرد (دکمه قبول | رد)\n"
        "\n"
        "🐾 حیوانات:\n"
        "/pets یا /پت — لیست حیوانات با شماره\n"
        "/petinfo شماره — جزئیات\n"
        "/hunt یا /شکار — شکار وحشی (خطر زخم | مرگ) سپس رام یا رها\n"
        "/buypet — خرید خونگی (۱۰۰ سکه یا معادل)\n"
        "/feedpet شماره — غذا (+وفاداری)\n"
        "/trainpet شماره — آموزش (+حمله | دفاع)\n"
        "/renamepet شماره نام‌جدید — تغییر نام\n"
        "/sellpet شماره — فروش\n"
        "/giftpet شماره — ریپلای + هدیه\n"
        "/releasepet شماره — آزاد کردن\n"
        "\n"
        "/accounts — چندحسابه (آیدی + رمز)\n"
        "بازار خدمتکار: آسیب = حذف اکانت مهاجم"
    ),
    "death": (
        "💀 مرگ و روح",
        "وقتی is_dead باشی:\n"
        "/afterdeath یا /بعدازمرگ — منوی سرنوشت\n"
        "  👻 پرورش‌دهنده روح — تذهیب روحی از نو\n"
        "  😈 روح انتقام‌جو — دنیای زیرین\n"
        "  🌑 پوچی — ریست کامل اکانت از صفر\n"
        "/possess یا /تسخیر — تسخیر بدن دیگران (روح؛ یک‌بار)\n"
        "/releasespirit یا /رها‌روح — ترک حالت انتقام"
    ),
    "games": (
        "🎮 بازی‌ها و وب‌اپ",
        "محدودیت: هر بازیکن هر ۵ دقیقه یک‌بار می‌تواند بازی کند.\n\n"
        "/games یا /بازی‌ها — منوی بازی در چت\n"
        "/rps یا /سنگ‌کاغذ‌قیچی — با ربات یا دیگران\n"
        "/dice یا /تاس یا /تخته‌نرد — تاس\n"
        "/chess یا /شطرنج — نمایشی در چت؛ واقعی در وب‌اپ\n"
        "/casino یا /کازینو مبلغ — شرط سکه\n"
        "/guess یا /حدس‌عدد\n"
        "/coinflip یا /شیرخط\n"
        "/hukum یا /حکم | /hukumduel — حکم\n\n"
        "🌐 وب‌اپ: آدرس Render + /webapp/\n"
        "تب‌ها: ورود روزانه | پروفایل | لیدربورد | فرقه | آرنا | بازی‌ها\n"
        "بازی‌های وب‌اپ: شطرنج قانونی | تخته‌نرد | سنگ‌کاغذ | کازینو | حکم"
    ),
    "admin": (
        "🛠 ادمین (فقط سازنده)",
        "فقط برای ADMIN_IDS (سازنده ربات):\n\n"
        "/admin — پنل مدیریت\n"
        "/helpforadmin — همین لیست\n"
        "/setrole [آیدی] [نقش]\n"
        "  نقش‌ها: رهبر | معاون رهبر | ارجمند | ارشد | عضو\n"
        "/restrict [آیدی] [دقیقه] [دلیل] — محدود کردن موقت\n"
        "/unrestrict [آیدی]\n"
        "/promote [آیدی] | /demote [آیدی] — رتبه دوئل\n"
        "/ban [آیدی] | /unban [آیدی]\n"
        "/setcult یا /تنظیم‌تذهیب — ریپلای یا آیدی + قلمرو مرحله [انرژی]\n"
        "/givemoney یا /بده‌پول — دادن ارز\n"
        "/takemoney یا /بگیر‌پول — گرفتن ارز\n"
        "/adshop یا /فروشگاه‌ادمین — لیست آیتم‌ها برای ادمین\n"
        "/adget یا /ادمین‌بگیر نام‌آیتم — گرفتن رایگان آیتم\n"
        "/setdimension یا /تنظیم‌بعد فانی | بهشتی | زیرین — بُعد گروه"
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
        "یک بخش را انتخاب کن تا دستورها را یکی‌یکی ببینی.\n\n"
        "پیشنهاد: اول <b>قوانین</b> و <b>شروع</b>.\n"
        "سریع: /rules | /gender | /race | /gather | /missions | /buildings | /garden | /itemlist",
        reply_markup=builder.as_markup(),
    )



@router.callback_query(F.data.startswith("helpsec:"))
async def help_section(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    try:
        owner = int(parts[1])
    except ValueError:
        await callback.answer()
        return
    key = parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ بازگشت", callback_data=f"helpback:{owner}")

    if key == "admin" and callback.from_user.id not in ADMIN_IDS:
        txt = (
            "🛠 <b>ادمین (فقط سازنده)</b>" + chr(10) + chr(10)
            + "این بخش فقط برای سازنده ربات است." + chr(10)
            + "اگر سازنده‌ای بزن: /helpforadmin یا /admin"
        )
        try:
            await callback.message.edit_text(txt, reply_markup=builder.as_markup())
        except Exception:
            await callback.message.answer(txt, reply_markup=builder.as_markup())
        await callback.answer()
        return

    title, body = SECTIONS.get(key, ("؟", "نامشخص"))
    # جلوگیری از TelegramBadRequest به‌خاطر < > داخل متن
    safe_body = (
        body.replace("&", "&amp;")
        .replace("<آیدی>", "[آیدی]")
        .replace("<دقیقه>", "[دقیقه]")
        .replace("<نقش>", "[نقش]")
    )
    # فقط اگر تگ HTML مجاز نباشد، بقیه < > را هم امن کن؛ <b> در title جداست
    import re as _re
    safe_body = _re.sub(r"<(?!/?b>)", "&lt;", safe_body)
    safe_body = safe_body.replace(">", "&gt;")  # might break nothing important in body
    # restore bold if any
    safe_body = safe_body.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    full = f"<b>{title}</b>" + chr(10) + chr(10) + safe_body
    if len(full) > 3900:
        full = full[:3900] + chr(10) + chr(10) + "… ادامه: /helpforadmin"

    try:
        await callback.message.edit_text(full, reply_markup=builder.as_markup())
    except Exception:
        try:
            # بدون HTML
            plain = f"{title}" + chr(10) + chr(10) + body
            await callback.message.answer(plain[:4000], reply_markup=builder.as_markup())
        except Exception as e:
            await callback.answer(str(type(e).__name__)[:50], show_alert=True)
            return
    await callback.answer()


@router.callback_query(F.data.startswith("helpback:"))
async def help_back(callback: CallbackQuery):
    try:
        owner = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    if callback.from_user.id != owner:
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        short = title if len(title) <= 40 else title[:38] + "…"
        builder.button(text=short, callback_data=f"helpsec:{owner}:{key}")
    builder.adjust(1)
    text = "📖 <b>راهنمای دنیای فرقه</b>" + chr(10) + "یک بخش را انتخاب کن:"
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.message(Command("helpforadmin", "راهنما‌ادمین"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ فقط سازنده ربات.")
        return
    title, body = SECTIONS["admin"]
    body = body.replace("<", "[").replace(">", "]")
    await message.answer(f"<b>{title}</b>" + chr(10) + chr(10) + body)


@router.message(Command("codex", "دانشنامه"))
async def cmd_codex(message: Message):
    await message.answer(
        "📚 <b>دانشنامه کوتاه</b>\n\n"
        "• <b>تذهیب</b>: جمع انرژی و بالا رفتن قلمرو\n"
        "• <b>ریشه</b>: استعداد معنوی\n"
        "• <b>نژاد</b>: سبک و ضریب تذهیب (/race)\n"
        "• <b>فرقه</b>: گروه با رهبری و قلمرو\n"
        "• <b>آرنا</b>: رقابت با هزینه ورود\n"
        "• <b>سم</b>: بعد از /kill؛ ۳ ساعت /heal\n"
        "• <b>پرورش ممنوعه</b>: قدرت سریع + قفل دائمی\n"
        "• <b>شمشیر کوروش</b>: یکتا؛ ضربه = پاک شدن اکانت\n"
        "• <b>چای‌خانه</b>: ده‌ها چای با اثر جدا\n"
        "• <b>کشاورزی</b>: هر ۵س یک گیاه؛ ۱۰ زمین؛ /buyland\n"
        "• <b>خرید</b>: با همه ارزها\n\n"
        "/itemlist — آیتم‌ها\n/help — راهنمای کامل"
    )


@router.message(Command("rules", "قانون", "قوانین"))
async def cmd_rules(message: Message):
    title, body = SECTIONS["rules"]
    await message.answer(f"<b>{title}</b>\n\n{body}")


@router.message(Command("commands", "دستورات", "کامندها"))
async def cmd_all_commands(message: Message):
    """لیست فشرده همه دستورات"""
    text = (
        "📋 <b>فهرست دستورات</b>\n\n"
        "<b>پایه:</b> /start /help /rules /profile /gender /race /ping /removekb\n\n"
        "<b>تذهیب:</b> /gather /cultivation /learntech /learnforbidden /techniques "
        "/givetech /afk /afkclaim /body /solo /dual /virgin\n\n"
        "<b>جنگ:</b> /duel /deathduel /kill /equip /unequip /blood /heal /power "
        "/guardian /arena /arenafight /arenatop /lootarena\n\n"
        "<b>فرقه و دنیا:</b> /sects /createsect /joinsect /missions /travel "
        "/explorecity /world /hunt /ranking\n\n"
        "<b>فروشگاه:</b> /buildings /inventory /use /itemlist /craft /wallet "
        "/dailycoin /gift /drop\n\n"
        "<b>باغ:</b> /garden /plant /harvest /buyland\n\n"
        "<b>اجتماعی:</b> /marry /divorce /master /pets /accounts\n\n"
        "<b>مرگ:</b> /afterdeath /possess /releasespirit\n\n"
        "<b>بازی:</b> /games /rps /dice /chess /casino /hukum\n\n"
        "جزئیات هر کدام: /help"
    )
    await message.answer(text)
