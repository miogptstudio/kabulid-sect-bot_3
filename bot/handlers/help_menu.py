from services.i18n import t_user, LANGS, get_lang, t as _t, tr
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
        "۱۶) بازی‌ها: هر ۲ دقیقه یک‌بار\n"
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
        "💍 اجتماعی، قبیله، بازرگانی",
        "/marry — ریپلای (چندهمسری + دختر با دختر)\n/wives | /divorce | /havechild | /mychildren\n/master — استاد و شاگرد\n\n👤 خدمتکار: /servants /buyservant /marryservant\n/dualservant | /childservant\n\n🏕 قبیله: /createtribe /tribes /tribe /jointribe /setchief\n🛒 بازرگانی: /tradeguild /tradelist /tradeinfo /tradedeposit\n\n🩸 رگ معنوی: /vein /unlockvein (تا ۵ رگ از ۳۶ نوع)\n💎 هسته: /cores /findcore /mycore /usecore\n👻 روح رزمی: /awaken /spirit /trainspirit\n🌐 زبان: /lang\n\n🐾 پت: /pets /hunt /petpalace\n/accounts — چندحسابه"
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
        "محدودیت: هر بازیکن هر ۲ دقیقه یک‌بار می‌تواند بازی کند.\n\n"
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
    lang = get_lang(message.from_user.id)
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        label = title
        sk = f"sec_{key}"
        from services.i18n import T as _T
        if sk in _T:
            label = _t(sk, lang)
        builder.button(text=str(label)[:40], callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.adjust(1)
    await message.answer(
        _t("help_title", lang) + chr(10) + _t("help_hint", lang),
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

    if key == "allcmds":
        await callback.answer()
        # reuse command list by sending via bot message simulation
        class _M:
            pass
        # call list inline
        from aiogram.types import Message as _Msg
        await callback.message.answer("در حال ارسال فهرست کامل...")
        # trigger by building same text - call function body
        await cmd_all_commands(callback.message)
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
        await message.answer(tr(message.from_user.id, "⛔️ فقط سازنده ربات."))
        return
    title, body = SECTIONS["admin"]
    body = body.replace("<", "[").replace(">", "]")
    await message.answer(f"<b>{title}</b>" + chr(10) + chr(10) + body)


@router.message(Command("codex", "دانشنامه"))
async def cmd_codex(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(
        f"<b>{_t('codex_title', lang)}</b>" + chr(10) + chr(10) + _t("codex_body", lang)
    )


@router.message(Command("rules", "قانون", "قوانین"))
async def cmd_rules(message: Message):
    title, body = SECTIONS["rules"]
    await message.answer(f"<b>{title}</b>\n\n{body}")


@router.message(Command("commands", "دستورات", "کامندها", "allcommands"))
async def cmd_all_commands(message: Message):
    """لیست کامل دستورات"""
    chunks = [
        '📋 <b>فهرست کامل دستورات</b> — نسخه <b>2.9.2</b>\n\n<b>🚀 پایه</b>\n/start — شروع\n/help | /راهنما | /منو — راهنمای بخش\u200cبخش\n/commands | /دستورات — همین لیست\n/rules | /قوانین — قوانین\n/codex | /دانشنامه — مفاهیم\n/profile | /me | /پروفایل — پروفایل\n/gender | /جنسیت — مرد یا زن (دائمی)\n/race | /نژاد — نژاد پایه\n/lang | /زبان — زبان ربات\n/jobs /job /declarewar /buycyrus /luckdice /statuscard /events\n/ping | /تست\n/removekb | /حذف\u200cکیبورد\n/version | /نسخه\n/iamadmin | /مقام\u200cمن\n/season | /فصل\n\n<b>💎 هسته و نژاد</b>\n/cores | /هسته\u200cها — لیست هسته\u200cها\n/findcore — جستجوی هسته (هر ۲س)\n/mycore — هسته\u200cهای تو\n/usecore نام\u200cهسته — تبدیل نژاد',
        '<b>🧘 تذهیب</b>\n/gather | /qi | /جمع | متن: تذهیب کردن | جمع آوری چی\n/cultivation | /تذهیب | /cult — وضعیت\n/learntech | /learnforbidden | /techniques | /givetech\n/afk | /afkclaim | /body | /solo | /dual | /virgin\n/vein | /رگ — رگ\u200cهای معنوی (۳۶ نوع، تا ۵ تا)\n/unlockvein نام\u200cرگ — باز کردن رگ\n\n<b>🏟 تمرین</b>\n/train [دقیقه] — ۱۰ تا ۶۰د (قطع خدمات)\n/trainstatus | /trainclaim\n\n<b>👻 روح رزمی</b>\n/awaken | /بیدار\u200cروح — بیدارسازی\n/spirit | /trainspirit | /spiritmode',
        '<b>⚔️ جنگ و آرنا</b>\n/duel | /deathduel | /kill | /equip | /unequip\n/blood | /heal | /power | /guardian\n/arena | /arenafight | /arenatop | /lootarena\n/arenaopen | /arenajoin | /arenastart | /arenarooms\n\n<b>🔒 زندان</b>\n/prison | /bail (۵۰ سنگ بهشتی)\n\n<b>🏛 فرقه</b>\n/sects | /createsect | /joinsect | /leavesect | /sectinfo\n/missions | /completemission\n\n<b>🏕 قبیله</b>\n/createtribe نام | /tribes | /tribe\n/jointribe نام | /setchief | /tribeinvite | /tribeleave\n\n<b>🛒 بازرگانی</b>\n/tradeguild نام | /tradelist | /tradeinfo\n/tradejoin نام | /tradedeposit | /tradewithdraw | /tradeleave',
        '<b>🌍 دنیا و شهر</b>\n/travel | /explorecity | /cities | /mycity | /worlds | /goworld\n/cave | /غار — غار شهر (غنیمت)\n/hunt | /شکار | /ranking | /dimension\n\n<b>🏪 فروشگاه</b>\n/buildings | /teahouse | /inventory | /use | /drop | /gift\n/itemlist | /craft | /wallet | /dailycoin\n/exchangestone | /blackmarket | /buyblack\n\n<b>🌱 باغ</b>\n/garden | /plant | /harvest | /buyland\n\n<b>🐾 پت</b>\n/pets | /petinfo | /buypet | /feedpet | /trainpet\n/petpalace | /upgradepetpalace',
        '<b>💍 اجتماعی</b>\n/marry | /wives | /divorce | /invitewedding | /master\n/servants | /buyservant | /myservants\n/marryservant | /dualservant | /childservant\n/havechild — بچه زوج متاهل\n/mychildren | /accounts\n\n<b>💀 مرگ</b>\n/afterdeath | /possess | /releasespirit\n\n<b>🎮 بازی</b>\n/games | /rps | /dice | /chess | /casino | /hukum | /nard\n/puzzle | /riddle | /mathquiz | /scramble | /guess | /coinflip\n(محدودیت ۲ دقیقه بعد از شروع بازی)\n\n<b>🛠 ادمین</b>\n/admin | /helpforadmin | /adshop | /adget\n/setrole | /restrict | /unrestrict | /promote | /demote\n/ban | /unban | /setcult | /givemoney | /takemoney\n\nجزئیات هر بخش: /help',
    ]
    for chunk in chunks:
        await message.answer(chunk)
