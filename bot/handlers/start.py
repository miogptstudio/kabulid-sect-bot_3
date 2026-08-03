from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command

from database.engine import async_session
from bot.config import BOT_VERSION
from database.crud import get_or_create_user
from database.models import ROLE_LEADER
from bot.config import ADMIN_IDS

router = Router()

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="تذهیب کردن"), KeyboardButton(text="پروفایل")],
            [KeyboardButton(text="فروشگاه"), KeyboardButton(text="دوئل")],
            [KeyboardButton(text="تکنیک‌ها"), KeyboardButton(text="فرقه")],
            [KeyboardButton(text="آرنا"), KeyboardButton(text="راهنما")],
            [KeyboardButton(text="جمع آوری چی"), KeyboardButton(text="/gender")],
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

        if message.from_user.id in ADMIN_IDS:
            if user.role != ROLE_LEADER:
                user.role = ROLE_LEADER
                await session.commit()

    text = (
        f"سلام <b>{user.full_name}</b> 👋\n\n"
        f"به ربات فرقه‌ای و تذهیب خوش اومدی!\n\n"
        f"🏆 رتبه: <b>{user.rank}</b>\n"
        f"⭐ نقش: <b>{user.role}</b>\n"
        f"سطح: {user.level} | XP: {user.xp}\n\n"
        f"دستورات اصلی:\n"
        f"/profile — پروفایل\n"
        f"/ranking — لیدربورد\n"
        f"/sects — فرقه‌ها\n"
        f"/cultivation — تذهیب\n"
        f"/missions — مأموریت‌ها\n"
        f"/arena — آرنا\n"
        f"/master — استاد و شاگرد\n"
        f"/accounts — چندحسابه\n"
        f"/buildings — ساختمان‌ها\n"
        f"/craft — ساخت معجون و طلسم\n"
        f"/inventory — کیف\n"
        f"/gender — جنسیت\n"
        f"/dual — تذهیب دوگانه\n"
        f"/marry — نامزدی و ازدواج\n"
        f"/divorce — طلاق\n"
        f"/wives — همسران\n"
        f"/pets — حیوانات\n"
        f"/wallet — سکه\n"
        f"/hunt — شکار\n"
        f"/afterdeath — بعد از مرگ\n"
        f"/duel — دوئل\n"
        f"/guardian — نگهبان\n"
        f"/help — راهنمای کامل"
    )
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


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
    await message.answer("pong ✅ ربات آنلاین است.")


@router.message(F.text.in_({"تذهیب کردن", "جمع آوری چی", "جمع‌آوری چی", "مدیتیت"}))
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


@router.message(F.text == "پروفایل")
async def btn_profile(message: Message):
    try:
        from bot.handlers.profile import cmd_profile
        await cmd_profile(message)
    except Exception as e:
        await message.answer(f"خطا پروفایل: {e}")


@router.message(F.text == "راهنما")
async def btn_help(message: Message):
    try:
        from bot.handlers.help_menu import cmd_help_menu
        await cmd_help_menu(message)
    except Exception as e:
        await message.answer(f"خطا راهنما: {e}")


@router.message(F.text.in_({"فروشگاه", "مغازه"}))
async def btn_shop(message: Message):
    try:
        from bot.handlers.shop import cmd_buildings
        await cmd_buildings(message)
    except Exception as e:
        await message.answer(f"خطا فروشگاه: {e}")


@router.message(F.text == "دوئل")
async def btn_duel_help(message: Message):
    await message.answer(
        "⚔️ دوئل:" + chr(10)
        + "روی پیام حریف ریپلای کن و بزن /duel" + chr(10)
        + "یا /duel مبلغ برای شرط" + chr(10)
        + "/deathduel — دوئل تا مرگ"
    )


@router.message(F.text == "تکنیک‌ها")
async def btn_tech(message: Message):
    try:
        from bot.handlers.cultivation import cmd_techniques
        await cmd_techniques(message)
    except Exception as e:
        await message.answer(f"خطا تکنیک: {e}")


@router.message(F.text == "فرقه")
async def btn_sect(message: Message):
    try:
        from bot.handlers.sects import cmd_sects
        await cmd_sects(message)
    except Exception as e:
        await message.answer(f"خطا فرقه: {e}")


@router.message(F.text == "آرنا")
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
        from bot.config import BOT_VERSION, WEBAPP_VERSION
        v, w = BOT_VERSION, WEBAPP_VERSION
    except Exception:
        v = w = "2.8.2"
    await message.answer(
        f"🤖 ربات: <b>{v}</b>" + chr(10)
        + f"🌐 وب‌اپ: <b>{w}</b>" + chr(10)
        + "🗓️ /season"
    )
