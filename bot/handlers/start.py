from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import ROLE_LEADER
from bot.config import ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        if message.from_user.id in ADMIN_IDS and user.role != ROLE_LEADER:
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
    await message.answer(text)


@router.message(Command("help", "راهنما"))
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
