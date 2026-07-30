from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.arena import get_or_create_arena_profile

router = Router()


@router.message(Command("arena", "آرنا"))
async def cmd_arena(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        profile = await get_or_create_arena_profile(session, user.id)
    
    text = (
        f"⚔️ <b>وضعیت آرنا</b>\n\n"
        f"درجه: <b>{profile.tier}</b>\n"
        f"امتیاز: {profile.points}\n"
        f"برد: {profile.wins} | باخت: {profile.losses}\n"
        f"امتیاز فصل: {profile.season_points}\n\n"
        f"درجه‌ها: برنز ← نقره ← طلا\n"
        f"(سیستم مسابقه آرنا به زودی کامل می‌شود)"
    )
    await message.answer(text)
