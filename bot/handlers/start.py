from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command

from database.engine import async_session
from bot.config import BOT_VERSION, CREATOR_NOTICE
from database.crud import get_or_create_user
from database.models import ROLE_LEADER
from bot.config import ADMIN_IDS
from services.i18n import t, get_lang, set_lang, LANGS, tr

router = Router()


def main_keyboard(lang: str = "fa"):
    """منوی اصلی شبیه ربات‌های تزکیه"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 پروفایل"), KeyboardButton(text="🧘 تزکیه")],
            [KeyboardButton(text="⚔️ نبرد"), KeyboardButton(text="🎒 کوله‌بار")],
            [KeyboardButton(text="⚗ کیمیاگری"), KeyboardButton(text="🏛 فرقه")],
            [KeyboardButton(text="🏪 بازار"), KeyboardButton(text="🎁 گنجینه")],
            [KeyboardButton(text="📜 مأموریت‌ها"), KeyboardButton(text="🏆 دستاوردها")],
            [KeyboardButton(text="📊 رتبه‌بندی"), KeyboardButton(text="🌍 رویدادها")],
            [KeyboardButton(text="🎁 پاداش روزانه"), KeyboardButton(text="🎲 تاس شانس")],
            [KeyboardButton(text="💼 شغل"), KeyboardButton(text="📖 راهنما")],
        ],
        resize_keyboard=True,
    )




@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        lang = getattr(user, 'language', None) or 'fa'
        set_lang(message.from_user.id, lang)
        if message.from_user.id in ADMIN_IDS:
            if user.role != ROLE_LEADER:
                user.role = ROLE_LEADER
                await session.commit()

        lang = get_lang(message.from_user.id, getattr(user, "language", None))
        text = t(
            "start",
            lang,
            name=user.full_name or "Player",
            ver=__import__("bot.config", fromlist=["BOT_VERSION"]).BOT_VERSION,
        )
        text += chr(10) + chr(10) + t("help_hint", lang)
        await message.answer(text, reply_markup=main_keyboard(lang))
        try:
            await message.answer(CREATOR_NOTICE)
        except Exception:
            pass
        # کارت وضعیت کوتاه
        try:
            from bot.handlers.jobs_events import cmd_status_card
            await cmd_status_card(message)
        except Exception:
            pass


@router.message(Command("help_old_disabled"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>راهنمای کامل ربات</b>\n\n"
        "━━━━━━━━━━━━━━\n"
        "⚔️ <b>دوئل و نگهبان</b>\n"
        "/duel — ریپلای یا تگ\n"
        "/guardian — حالت نگهبان\n\n"
        "🏛️ <b>فرقه‌ها</b>\n"
        "/sects — لیست\n"
        "/createsect &lt;نام&gt; &lt;نوع&gt;\n"
        "/joinsect &lt;نام&gt;\n"
        "/mysect — فرقه من\n"
        "/challengeleader — چالش رهبری\n"
        "/betray — خیانت\n"
        "/territories — قلمروها\n\n"
        "🧘 <b>تذهیب</b>\n"
        "/cultivation — وضعیت\n"
        "«جمع آوری چی» یا «تذهیب کردن»\n"
        "/techniques — تکنیک‌ها\n"
        "/learntech — یادگیری تکنیک پایه\n"
        "/dual — تذهیب دوگانه\n"
        "/afterdeath — بعد از مرگ\n\n"
        "💍 <b>ازدواج</b>\n"
        "/marry — نامزدی\n"
        "/divorce — طلاق\n"
        "/wives — خانواده\n"
        "/gender — جنسیت\n\n"
        "🛒 <b>فروشگاه و ساخت</b>\n"
        "/buildings — ساختمان‌ها\n"
        "/craft — ساخت\n"
        "/inventory — کیف\n"
        "/pets — حیوانات\n"
        "/wallet — سکه و سنگ روحی\n\n"
        "📊 /ranking — لیدربورد\n"
        "/profile — پروفایل\n"
        "/admin — پنل مدیریت\n\n"
        ""
    )
    await message.answer(text)


@router.message(Command("iamadmin", "مقام‌من"))
async def cmd_iamadmin(message: Message):
    """وضعیت ادمین بودن را نشان می‌دهد و در صورت بودن در ADMIN_IDS نقش رهبر می‌دهد"""
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
        in_list = message.from_user.id in ADMIN_IDS
        if in_list and user.role != ROLE_LEADER:
            user.role = ROLE_LEADER
            await session.commit()
            await session.refresh(user)

    await message.answer(
        f"شناسه تلگرام تو: <code>{message.from_user.id}</code>\n"
        f"در لیست ADMIN_IDS: {'بله ✅' if in_list else 'خیر ❌'}\n"
        f"نقش فعلی: <b>{user.role}</b>\n"
        f"تعداد ادمین‌های تنظیم‌شده: {len(ADMIN_IDS)}"
    )

@router.message(Command("ping", "تست"))
async def cmd_ping(message: Message):
    await message.answer(tr(message.from_user.id, "pong ✅ ربات آنلاین است."))


@router.message(F.text.in_(set(['تأمل', '修炼', 'تذهیب کردن', 'Kültive et', 'Cultivate', 'Культивировать', 'جمع آوری چی', 'Qi topla', 'Gather Qi', 'جمع الطاقة', '聚气', 'Собрать Ци', 'تذهیب کردن', 'جمع آوری چی', 'جمع\u200cآوری چی', 'مدیتیت'])))
async def btn_gather(message: Message):
    """جمع انرژی از دکمه کیبورد"""
    try:
        from bot.handlers.cultivation import do_gather
        await do_gather(message, amount=5000)
    except Exception as e:
        await message.answer(
            "خطا در تذهیب: " + type(e).__name__ + ": " + str(e)
            + chr(10) + "اول /gender را بزن. بعد /gather"
        )


@router.message(F.text.in_(set(['Profile', 'الملف', 'پروفایل', 'Profil', 'Профиль', '资料', 'پروفایل'])))
async def btn_profile(message: Message):
    try:
        from bot.handlers.profile import cmd_profile
        await cmd_profile(message)
    except Exception as e:
        await message.answer(f"خطا پروفایل: {e}")


@router.message(F.text.in_(set(['Yardım', 'مساعدة', '帮助', 'راهنما', 'Справка', 'Help', 'راهنما'])))
async def btn_help(message: Message):
    try:
        from bot.handlers.help_menu import cmd_help_menu
        await cmd_help_menu(message)
    except Exception as e:
        await message.answer(f"خطا راهنما: {e}")


@router.message(F.text.in_(set(['商店', 'Dükkan', 'Магазин', 'فروشگاه', 'المتجر', 'Shop', 'فروشگاه', 'مغازه'])))
async def btn_shop(message: Message):
    try:
        from bot.handlers.shop import cmd_buildings
        await cmd_buildings(message)
    except Exception as e:
        await message.answer(f"خطا فروشگاه: {e}")


@router.message(F.text.in_(set(['دوئل', '决斗', 'Duel', 'مبارزة', 'Дуэль', 'Düello', 'دوئل'])))
async def btn_duel_help(message: Message):
    await message.answer(
        "⚔️ دوئل:" + chr(10)
        + "روی پیام حریف ریپلای کن و بزن /duel" + chr(10)
        + "یا /duel مبلغ برای شرط" + chr(10)
        + "/deathduel — دوئل تا مرگ"
    )


@router.message(F.text.in_(set(['Teknikler', '功法', 'تکنیک\u200cها', 'Techniques', 'Техники', 'التقنيات', 'تکنیک\u200cها'])))
async def btn_tech(message: Message):
    try:
        from bot.handlers.cultivation import cmd_techniques
        await cmd_techniques(message)
    except Exception as e:
        await message.answer(f"خطا تکنیک: {e}")


@router.message(F.text.in_(set(['宗门', 'فرقه', 'Секта', 'Tarikat', 'الطائفة', 'Sect', 'فرقه'])))
async def btn_sect(message: Message):
    try:
        from bot.handlers.sects import cmd_sects
        await cmd_sects(message)
    except Exception as e:
        await message.answer(f"خطا فرقه: {e}")


@router.message(F.text.in_(set(['Arena', 'Арена', 'آرنا', 'الحلبة', '竞技场', 'آرنا'])))
async def btn_arena(message: Message):
    try:
        from bot.handlers.arena import cmd_arena
        await cmd_arena(message)
    except Exception as e:
        await message.answer(f"خطا آرنا: {e}")


@router.message(Command("gather", "qi", "جمع‌آوری", "جمع", "meditate"))
async def cmd_gather(message: Message):
    try:
        from bot.handlers.cultivation import do_gather
        await do_gather(message, amount=5000)
    except Exception as e:
        await message.answer(f"خطا: {type(e).__name__}: {e}")


@router.message(Command("menu", "منو"))
async def cmd_menu(message: Message):
    await message.answer("منو حذف شد. از /help استفاده کن.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("gender", "جنسیت"))
async def cmd_gender_alias(message: Message):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from database.engine import async_session
    from database.crud import get_or_create_user
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender in ("مرد", "زن"):
            await message.answer(f"جنسیت تو «<b>{user.gender}</b>» است و قابل تغییر نیست.")
            return
    builder = InlineKeyboardBuilder()
    builder.button(text="مرد 👨", callback_data=f"setgender:{message.from_user.id}:مرد")
    builder.button(text="زن 👩", callback_data=f"setgender:{message.from_user.id}:زن")
    builder.adjust(1)
    await message.answer(
        "⚧ انتخاب جنسیت (فقط یک‌بار). بعد از انتخاب قابل تغییر نیست.",
        reply_markup=builder.as_markup(),
    )


@router.message(Command("removekb", "حذف‌کیبورد", "nokb"))
async def cmd_remove_kb(message: Message):
    await message.answer("کیبورد حذف شد. از /help برای دستورات استفاده کن.", reply_markup=ReplyKeyboardRemove())


@router.message(Command("version", "نسخه"))
async def cmd_version(message: Message):
    try:
        from bot.config import BOT_VERSION, CREATOR_NOTICE, WEBAPP_VERSION
        v, w = BOT_VERSION, WEBAPP_VERSION
    except Exception:
        v = w = "3.10.6"
    await message.answer(
        f"🤖 ربات: <b>{v}</b>" + chr(10)
        + f"🌐 وب‌اپ: <b>{w}</b>" + chr(10)
        + "🗓️ /season"
    )




@router.message(F.text.in_({"👤 پروفایل", "پروفایل"}))
async def kb_profile(message: Message):
    from bot.handlers.profile import cmd_profile
    await cmd_profile(message)


@router.message(F.text.in_({"🧘 تزکیه", "تزکیه", "تذهیب کردن"}))
async def kb_cult(message: Message):
    from bot.handlers.cultivation import cmd_cultivation
    await cmd_cultivation(message)


@router.message(F.text.in_({"⚔️ نبرد", "نبرد", "دوئل"}))
async def kb_battle(message: Message):
    await message.answer(
        "⚔️ نبرد:" + chr(10)
        + "/duel /arena /kill /guardian /tribewarfight"
    )


@router.message(F.text.in_({"🎒 کوله‌بار", "کوله‌بار", "اینونتوری"}))
async def kb_inv(message: Message):
    try:
        from bot.handlers.shop import cmd_inventory
        await cmd_inventory(message)
    except Exception:
        await message.answer("/inventory")


@router.message(F.text.in_({"⚗ کیمیاگری", "کیمیاگری"}))
async def kb_craft(message: Message):
    await message.answer("⚗ /craft /buildings")


@router.message(F.text.in_({"🏛 فرقه", "فرقه"}))
async def kb_sect(message: Message):
    await message.answer("🏛 /sects /mysect /createtribe /declarewar")


@router.message(F.text.in_({"🏪 بازار", "بازار"}))
async def kb_market(message: Message):
    await message.answer("🏪 /buildings /blackmarket /market /tradeguild")


@router.message(F.text.in_({"🎁 گنجینه", "گنجینه"}))
async def kb_treasure(message: Message):
    await message.answer("🎁 /wallet /inventory /cyrussale /cave")


@router.message(F.text.in_({"📜 مأموریت‌ها", "مأموریت‌ها"}))
async def kb_missions(message: Message):
    try:
        from bot.handlers.missions import cmd_missions
        await cmd_missions(message)
    except Exception:
        await message.answer("/missions")


@router.message(F.text.in_({"🏆 دستاوردها", "دستاوردها"}))
async def kb_ach(message: Message):
    await message.answer("🏆 /ranking /achievements")


@router.message(F.text.in_({"📊 رتبه‌بندی", "رتبه‌بندی"}))
async def kb_rank(message: Message):
    try:
        from bot.handlers.ranking import cmd_ranking
        await cmd_ranking(message)
    except Exception:
        await message.answer("/ranking")


@router.message(F.text.in_({"🌍 رویدادها", "رویدادها"}))
async def kb_events(message: Message):
    from bot.handlers.jobs_events import cmd_events
    await cmd_events(message)


@router.message(F.text.in_({"🎁 پاداش روزانه", "پاداش روزانه"}))
async def kb_daily(message: Message):
    await message.answer("/dailycoin")


@router.message(F.text.in_({"🎲 تاس شانس", "تاس شانس"}))
async def kb_luck(message: Message):
    from bot.handlers.jobs_events import cmd_luck_dice
    await cmd_luck_dice(message)


@router.message(F.text.in_({"💼 شغل", "شغل"}))
async def kb_job(message: Message):
    from bot.handlers.jobs_events import cmd_jobs
    await cmd_jobs(message)


@router.message(F.text.in_({"📖 راهنما", "راهنما"}))
async def kb_help(message: Message):
    from bot.handlers.help_menu import cmd_help_menu
    await cmd_help_menu(message)



@router.message(Command("notice", "پیام‌سازنده", "اعلامیه"))
async def cmd_notice(message: Message):
    from bot.config import CREATOR_NOTICE
    await message.answer(CREATOR_NOTICE)
