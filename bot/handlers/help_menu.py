"""راهنما و فهرست دستورات — نسخه 3.10.6"""
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
        " /codex | /دانشنامه — مفاهیم دنیا\n"
        " /profile | /me | /پروفایل — پروفایل کامل\n"
        " /gender | /جنسیت — مرد یا زن (دائمی، قبل از تذهیب)\n"
        " /race | /نژاد — نژاد پایه (نامیرا: قوی، بدون بچه؛ قادر مطلق/خدایان: ادمین)\n"
        " /lang | /زبان — تغییر زبان ربات\n"
        " /version | /نسخه — نسخه ربات و وب‌اپ\n"
        " /ping | /تست — آنلاین بودن\n"
        " /removekb | /حذف‌کیبورد — پاک کردن دکمه‌های پایین\n"
        " /iamadmin | /مقام‌من — وضعیت ادمین/رهبر\n"
        " /notice | /پیام‌سازنده — اعلامیه سازنده\n"
        " /season | /فصل — وضعیت فصل\n"
        " /statuscard | /کارت — کارت وضعیت\n"
        " /luckdice | /تاس‌شانس — شانس روزانه\n"
        " /events | /رویدادها — رویدادهای فعال\n\n"
        "ترتیب پیشنهادی: /start → /gender → /race → /gather → /learntech\n"
        "ساختمان تزکیه: /cultbuilding | /upgradecultbuilding"
    ),
    "cult": (
        "🧘 تذهیب و بدن",
        "جمع انرژی: بنویس «تذهیب کردن» یا «جمع آوری چی»\n"
        " /gather | /qi | /جمع | /meditate — جمع چی\n"
        " /cultivation | /تذهیب | /cult — وضعیت قلمرو/ریشه/انرژی\n"
        " /learntech — تکنیک پایه (هر تکنیک قلمرو/مرحله خاص می‌خواهد؛ فاصله سطح‌ها بیشتر شده)\n"
        " /learnforbidden | چای ممنوعه — قفل ابدی مصرف آیتم‌ها\n/learnforbidden | /پرورش‌ممنوعه — قفل ابدی (+سطح اول، +چی هر بار)\n"
        " /techniques | /تکنیک‌ها — لیست و فعال‌سازی\n"
        " /givetech | /انتقال‌تکنیک — ریپلای + انتقال تکنیک\n"
        " /afk | /تذهیب‌خودکار — AFK ۳۰ دقیقه\n"
        " /afkclaim | /دریافت‌افک — دریافت پاداش AFK\n"
        " /body | /بدن — نوع بدن\n"
        " /bodytechs | /تکنیک‌بدن — لیست پرورش بدن\n"
        " /bodycult | /پرورش‌بدن — پرورش (یا بنویس: پرورش بدن)\n"
        " /mybody | /بدن‌من — وضعیت پرورش بدن\n"
        " /vein | /رگ — رگ‌های معنوی\n"
        " /unlockvein نام — باز کردن رگ\n"
        " /solo | /خودارضایی — ۳ بار اول بدون کاهش عمر؛ بعدش عمر کم می‌شود\n"
        " /virgin | /باکرگی — وضعیت باکرگی\n"
        " /dual | /تذهیب‌دوگانه — ریپلای (مرد/زن، زن/زن، مرد/مرد)\n"
        " /train | /تمرین — زمین تمرین ۱۰–۶۰د (پاداش مثل AFK × دقیقه)\n"
        " /trainstatus | /trainclaim | /trainstop (انصراف + پاداش رفته) — وضعیت و دریافت پاداش تمرین"
    ),
    "duel": (
        "⚔️ دوئل و آرنا",
        " /duel | /دوئل — ریپلای؛ قدرت + سلاح (خون کم می‌شود)\n"
        " /duel مبلغ — دوئل با شرط سکه\n"
        " /deathduel — دوئل تا مرگ\n"
        " /kill — زخم + سم (۳ ساعت وقت /heal)\n"
        " /equip | /تجهیز — مسلح کردن از کیف\n"
        " /unequip | /خلع‌سلاح — برداشتن سلاح\n"
        " /blood — خون و سم\n"
        " /heal | /درمان — درمان\n"
        " /power — قدرت رزمی\n"
        " /guardian | /نگهبان — سوال نگهبان\n"
        " /gduel | /guardian2 | /نگهبان2 — نگهبان دو نفره\n"
        " /arena — منوی آرنا\n"
        " /arenafight — چالش آرنا (ریپلای، بر اساس قدرت)\n"
        " /openarena — آرنای چندنفره ۳–۱۰ نفر"
    ),
    "money": (
        "💰 اقتصاد و انتقال",
        " /wallet | /کیف — موجودی همه ارزها\n"
        " /dailycoin | /سکهروزانه — سکه روزانه (روزی یک‌بار)\n"
        " /pay | /ارسال‌پول | /انتقال‌ارز — انتقال یک ارز\n"
        "   انواع: coins/سکه · spirit/روحی · heavenly/بهشتی · celestial/آسمانی · god/خدا\n"
        "   مثال: ریپلای + /pay بهشتی 5\n"
        " /payall | /انتقال‌چندارز — چند ارز با هم\n"
        "   مثال: /payall coins 100 spirit 10 heavenly 1\n"
        " /exchangestone — تبدیل سکه ↔ سنگ روحی\n"
        " /exchangeup heavenly|celestial|god — ارتقای ارز\n"
        " /buymine | /خرید‌معدن — معدن سنگ روح\n"
        " /mine | /claimmine | /upgrademine — وضعیت/برداشت/ارتقا معدن\n"
        " /market | /بازار — بازار آزاد\n"
        " /marketbuy شماره — خرید از بازار\n"
        " /blackmarket | /buyblack — بازار سیاه"
    ),
    "chars": (
        "🎭 کاراکتر و هسته",
        " /pullchar | /کاراکتر | /شانسی — کاراکتر شانسی (۱۰۰ سکه)\n"
        "   رتبه‌ها: معمولی تا ازلی + قادر مطلق (شانس بسیار نادر)\n"
        " /mychars | /کاراکترها — لیست\n"
        " /bestchar — قوی‌ترین\n"
        " /charrates — شانس رتبه‌ها\n"
        " /cores | /هسته — هسته‌های نژادی\n"
        " /findcore | /mycore | /usecore نام — پیدا/استفاده هسته\n"
        " /awaken | /بیدار‌روح — روح رزمی\n"
        " /spirit | /trainspirit | /spiritmode — وضعیت روح رزمی"
    ),
    "social": (
        "💒 اجتماعی و فرقه",
        " /marry | /ازدواج — درخواست ازدواج (ریپلای)\n"
        " /divorce | /طلاق\n"
        " /propose | /نامزدی\n"
        " /servants | /خدمتکار — لیست خدمتکار\n"
        " /calamitystatus | /protectsect — مصیبت فرقه هر ۱۰ ساعت\n"
        " /sect | /فرقه — منوی فرقه\n"
        " /createsect | /joinsect | /leavesect\n"
        " /transferleader | /واگذاری‌رهبری\n"
        " /createtribe | /tribes | /jointribe | /setchief — قبیله\n"
        " /declarewar — جنگ قبایل\n"
        " /tradeguild | /tradelist | /tradedeposit — بازرگانی\n"
        " /master | /شاگرد — استاد و شاگرد\n"
        " /jobs | /job — شغل"
    ),
    "world": (
        "🌍 دنیا و شهر",
        " /travel | /سفر — سفر بین شهرها\n"
        " /explorecity | /کاوش — کاوش شهر (سلاح مخفی)\n"
        " /cities | /mycity | /worlds | /enter8 | /region8 | /goregion — هشت جهان: اعداد ۱…۷ سپس اسلات ای‌تری سپس ۸ | نام: نیک، مین، والا مقام، بلند مرتبه | بقیه بی‌نام | /region8 | /goregion — هشت جهان اولیه (نام اشتباه=پاکی اکانت)\n/goworld\n"
        " /cave | /غار — غار شهر و غنیمت\n"
        " /hunt | /شکار\n"
        " /dimension — ابعاد/دنیاها\n"
        " /garden | /plant | /harvest | /buyland — کشاورزی"
    ),
    "shop": (
        "🏪 فروشگاه و ساخت",
        " /buildings | /فروشگاه — ساختمان‌ها\n"
        " /teahouse | /چایخونه — چای (+تذهیب، کول‌داون)\n"
        " /inventory | /کیف‌آیتم | /use | /drop | /gift\n"
        " /itemlist | /craft | /codex\n"
        " /pets | /hunt | /petpalace | /feedpet | /trainpet"
    ),
    "games": (
        "🎮 بازی‌ها",
        " /games — منوی بازی‌ها (کول‌داون منو زمان نمی‌گیرد)\n"
        " /chess | /شطرنج — شطرنج واقعی + قلعه + آنلاین\n"
        " /nard | /تخته‌نرد — تخته‌نرد + خروج مهره\n"
        " /rps | /سنگ‌کاغذ — با ربات یا دو نفره\n"
        " /hukum | /حکم\n"
        " /casino | /کازینو\n"
        " /puzzle | /riddle | /mathquiz | /scramble | /guess\n"
        " /dice | /coinflip\n"
        "وب‌اپ: منوی ربات → Open WebApp → بازی‌ها\n"
        "محدودیت هر بازی: ۲ دقیقه بعد از شروع"
    ),
    "death": (
        "💀 مرگ و روح",
        " /suicide | /خودکشی — مرگ اختیاری کاراکتر (با تأیید)\n"
        " /afterdeath | /بعدازمرگ — انتخاب سرنوشت\n"
        "   👻 پرورش‌دهنده روح · 😈 روح انتقام‌جو · 🌑 پوچی (حذف)\n"
        " /possess — تسخیر (اگر روح باشی)\n"
        " /releasespirit — رها کردن روح"
    ),
    "rules": (
        "📜 قوانین",
        "۱. ربات یک بازی نقش‌آفرینی تذهیب/فرقه است.\n"
        "۲. توهین، اسپم و سوءاستفاده از باگ ممنوع.\n"
        "۳. مرگ، سم، زندان و خودکشی فقط درون‌بازی‌اند.\n"
        "۴. انتقال ارز فقط با رضایت طرفین؛ کلاهبرداری گزارش شود.\n"
        "۵. ادمین اصلی سازنده ربات است.\n"
        "۶. درخواست‌های نامربوط به گیم‌پلی نادیده گرفته می‌شود.\n"
        "۷. نسخه فعلی: 3.10.6"
    ),
    "admin": (
        "🛠 ادمین (فقط سازنده)",
        " /admin | /helpforadmin — پنل و راهنمای ادمین\n"
        " /adshop | /adget — شاپ ادمین (شمشیر کوروش و …)\n"
        " /setrole | /promote | /demote\n"
        " /restrict | /unrestrict | /ban | /unban\n"
        " /setcult — تغییر قلمرو/چی با ریپلای یا آیدی\n"
        " /givecurrency | دادن ارز (اگر فعال باشد)\n"
        "نژاد خدایان و قادر مطلق فقط برای ادمین"
    ),
}


@router.message(Command("help", "راهنما", "منو"))
async def cmd_help_menu(message: Message):
    lang = get_lang(message.from_user.id)
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        if key == "admin" and message.from_user.id not in ADMIN_IDS:
            continue
        label = title
        builder.button(text=str(label)[:40], callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.button(text="📋 همه دستورات", callback_data=f"helpsec:{message.from_user.id}:allcmds")
    builder.adjust(2)
    await message.answer(
        f"📖 <b>راهنما — نسخه {BOT_VERSION}</b>" + chr(10)
        + "یک بخش را انتخاب کن:" + chr(10)
        + "/commands — فهرست کامل یک‌جا",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("helpsec:"))
async def help_section(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    owner, key = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ بازگشت", callback_data=f"helpback:{owner}")
    builder.adjust(1)
    if key == "allcmds":
        await callback.message.edit_text("در حال ارسال فهرست…")
        await cmd_all_commands(callback.message)
        await callback.answer()
        return
    if key == "admin" and callback.from_user.id not in ADMIN_IDS:
        await callback.answer("فقط سازنده", show_alert=True)
        return
    title, body = SECTIONS.get(key, ("؟", "نامشخص"))
    text = f"<b>{title}</b>" + chr(10) + chr(10) + body
    if len(text) > 4000:
        text = text[:3900] + "\n… /commands"
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("helpback:"))
async def help_back(callback: CallbackQuery):
    owner = int(callback.data.split(":")[1])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        if key == "admin" and callback.from_user.id not in ADMIN_IDS:
            continue
        builder.button(text=str(title)[:40], callback_data=f"helpsec:{owner}:{key}")
    builder.button(text="📋 همه دستورات", callback_data=f"helpsec:{owner}:allcmds")
    builder.adjust(2)
    await callback.message.edit_text(
        f"📖 <b>راهنما — نسخه {BOT_VERSION}</b>" + chr(10) + "یک بخش را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(Command("helpforadmin", "راهنما‌ادمین"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط سازنده.")
        return
    title, body = SECTIONS["admin"]
    await message.answer(f"<b>{title}</b>" + chr(10) + chr(10) + body)


@router.message(Command("rules", "قوانین"))
async def cmd_rules(message: Message):
    title, body = SECTIONS["rules"]
    await message.answer(f"<b>{title}</b>" + chr(10) + chr(10) + body)


@router.message(Command("commands", "دستورات", "cmdlist"))
async def cmd_all_commands(message: Message):
    chunks = []
    header = f"📋 <b>فهرست کامل دستورات — نسخه {BOT_VERSION}</b>" + chr(10)
    chunks.append(header)
    for key, (title, body) in SECTIONS.items():
        if key == "admin":
            continue
        chunks.append(f"<b>{title}</b>" + chr(10) + body)
    chunks.append("<b>" + SECTIONS["admin"][0] + "</b>" + chr(10) + "(جزئیات: /helpforadmin)")
    text = (chr(10) + chr(10)).join(chunks)
    # Telegram limit ~4096
    while text:
        part = text[:4000]
        # break on newline if possible
        if len(text) > 4000:
            cut = part.rfind("\n")
            if cut > 3000:
                part = part[:cut]
        await message.answer(part)
        text = text[len(part):].lstrip()


@router.message(Command("version", "نسخه"))
async def cmd_version(message: Message):
    try:
        from bot.config import WEBAPP_VERSION
        w = WEBAPP_VERSION
    except Exception:
        w = BOT_VERSION
    await message.answer(f"🤖 ربات: <b>{BOT_VERSION}</b>" + chr(10) + f"🌐 وب‌اپ: <b>{w}</b>")
