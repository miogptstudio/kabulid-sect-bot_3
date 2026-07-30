from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from services.ranking import get_rank_index

router = Router()


@router.message(Command("ranking", "top", "leaderboard", "لیدربورد"))
async def cmd_ranking(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.is_active == True, User.is_banned == False)
        )
        users = result.scalars().all()

    if not users:
        await message.answer("هنوز کسی ثبت‌نام نکرده.")
        return

    # مرتب‌سازی بر اساس رتبه و XP و برد
    users = sorted(
        users,
        key=lambda u: (-get_rank_index(u.rank), -u.xp, -u.wins)
    )

    top3 = users[:3]

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 <b>لیدربورد جهانی (۳ نفر برتر)</b>\n\n"

    for i, user in enumerate(top3):
        text += (
            f"{medals[i]} <b>{user.full_name}</b>\n"
            f"    رتبه: {user.rank} | سطح: {user.level}\n"
            f"    XP: {user.xp} | برد: {user.wins}\n\n"
        )

    if len(users) > 3:
        text += f"📊 تعداد کل بازیکنان: {len(users)}"

    await message.answer(text)
