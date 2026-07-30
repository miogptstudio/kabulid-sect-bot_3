from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user

router = Router()


@router.message(Command("profile", "me"))
async def cmd_profile(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

    win_rate = user.win_rate
    virgin = "باکره" if user.is_virgin else "غیر باکره"
    status = "💀 مرده — /afterdeath" if user.is_dead else ("👻 پرورش‌دهنده روح" if getattr(user, "is_spirit_raiser", False) else "زنده")

    text = (
        f"👤 <b>پروفایل {user.full_name}</b>\n\n"
        f"🏆 رتبه: <b>{user.rank}</b>\n"
        f"⭐ نقش: <b>{user.role}</b>\n"
        f"⚧ جنسیت: {user.gender}\n"
        f"🧬 باکرگی: {virgin}\n"
        f"وضعیت: {status}\n"
    )
    if user.gender == "مرد":
        text += f"☯️ یانگ: {user.yang}%\n"
    elif user.gender == "زن":
        text += f"☯️ یین: {user.yin}%\n"
    
    text += (
        f"\nسطح: {user.level} | XP: {user.xp}\n\n"
        f"📊 آمار:\n"
        f"├ برد: {user.wins}\n"
        f"├ باخت: {user.losses}\n"
        f"├ کل دوئل‌ها: {user.total_duels}\n"
        f"├ درصد برد: {win_rate}%\n"
        f"├ برد متوالی: {user.win_streak}\n"
        f"└ باخت متوالی: {user.loss_streak}\n\n"
        f"📅 عضویت: {user.joined_at.strftime('%Y-%m-%d')}\n"
        f"🕐 آخرین فعالیت: {user.last_active.strftime('%Y-%m-%d %H:%M')}"
    )
    await message.answer(text)
