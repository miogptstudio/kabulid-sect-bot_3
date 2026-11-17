from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from services.ranking import get_rank_index
from services.i18n import tr

router = Router()


@router.message(Command("ranking", "top", "leaderboard", "لیدربورد", "رتبه", "رتبهبندی", "جدولرتبه"))
async def cmd_ranking(message: Message):
    await message.answer("🏆 <b>رتبه‌بندی</b>")
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.is_active == True, User.is_banned == False)
        )
        users = result.scalars().all()

    if not users:
        await message.answer(tr(message.from_user.id, "هنوز کسی ثبتنام نکرده."))
        return

    # مرتبسازی بر اساس رتبه و XP و برد
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



@router.message(Command(
    "richest", "wealth", "پولدار", "پولدارترین", "ثروتمند", "لیدربوردپول", "toprich"
))
async def cmd_richest(message: Message):
    """لیست پولدارترین بازیکنان بر اساس معادل سکه همه ارزها"""
    from html import escape
    from services.economy import currency_to_coins, get_or_create_wallet

    try:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.is_active == True, User.is_banned == False).limit(500)
            )
            users = list(result.scalars().all())
            scored = []
            for u in users:
                try:
                    w = await get_or_create_wallet(session, u.id)
                    total = int(currency_to_coins(w) or 0)
                    scored.append((total, u, w))
                except Exception:
                    continue
            scored.sort(key=lambda x: -x[0])

        if not scored:
            await message.answer("هنوز کیف پولی ثبت نشده.")
            return

        medals = ["🥇", "🥈", "🥉"]
        lines = ["💰 <b>پولدارترین‌ها</b> (معادل همه ارزها به سکه)", ""]
        for i, (total, u, w) in enumerate(scored[:15]):
            medal = medals[i] if i < 3 else f"{i+1}."
            name = escape(str(u.full_name or u.username or u.telegram_id or "?"))
            lines.append(
                f"{medal} <b>{name}</b>" + chr(10)
                + f"   💎 مجموع ≈ {total:,} سکه" + chr(10)
                + f"   🪙{int(w.coins or 0):,} | روحی {int(w.spirit_stones or 0):,}"
            )
        me_tg = message.from_user.id
        for i, (total, u, w) in enumerate(scored):
            if getattr(u, "telegram_id", None) == me_tg:
                lines.append("")
                lines.append(f"📍 رتبه تو: <b>#{i+1}</b> از {len(scored)} | ≈ {total:,} سکه")
                break
        await message.answer(chr(10).join(lines))
    except Exception as e:
        await message.answer(f"⚠️ خطا در لیست پولدارها: {type(e).__name__}")



@router.message(Command("achievements", "دستاوردها", "مدالها"))
async def cmd_achievements(message: Message):
    from services.achievements import list_user
    await message.answer(list_user(message.from_user.id))
