from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from services.ranking import get_rank_index
from services.i18n import tr

router = Router()


@router.message(Command("ranking", "top", "leaderboard", "لیدربورد"))
async def cmd_ranking(message: Message):
    from aiogram.types import FSInputFile
    from services.portraits import panel_url
    await message.answer_photo(FSInputFile(panel_url("ranking")), caption="🏆 <b>رتبه‌بندی</b>")
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.is_active == True, User.is_banned == False)
        )
        users = result.scalars().all()

    if not users:
        await message.answer(tr(message.from_user.id, "هنوز کسی ثبت‌نام نکرده."))
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



@router.message(Command(
    "richest", "wealth", "پولدار", "پولدارترین", "ثروتمند", "لیدربورد‌پول", "toprich"
))
async def cmd_richest(message: Message):
    """لیست پولدارترین بازیکنان بر اساس معادل سکه همه ارزها"""
    from database.models_v3 import UserWallet
    from services.economy import currency_to_coins, get_or_create_wallet

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_active == True, User.is_banned == False)
        )
        users = list(result.scalars().all())
        scored = []
        for u in users:
            try:
                w = await get_or_create_wallet(session, u.id)
                total = currency_to_coins(w)
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
        name = u.full_name or u.username or str(u.telegram_id)
        lines.append(
            f"{medal} <b>{name}</b>" + chr(10)
            + f"   💎 مجموع ≈ {total:,} سکه" + chr(10)
            + f"   🪙{int(w.coins or 0):,} | روحی {int(w.spirit_stones or 0):,} | "
            + f"بهشتی {int(getattr(w,'heavenly_stones',0) or 0):,} | "
            + f"آسمانی {int(getattr(w,'celestial_stones',0) or 0):,} | "
            + f"خدا {int(getattr(w,'god_stones',0) or 0):,}"
        )
    # رتبه خود کاربر
    me_tg = message.from_user.id
    my_rank = None
    for i, (total, u, w) in enumerate(scored):
        if u.telegram_id == me_tg:
            my_rank = i + 1
            lines.append("")
            lines.append(f"📍 رتبه تو: <b>#{my_rank}</b> از {len(scored)} | ≈ {total:,} سکه")
            break
    await message.answer(chr(10).join(lines))



@router.message(Command("achievements", "دستاوردها", "مدال‌ها"))
async def cmd_achievements(message: Message):
    from services.achievements import list_user
    await message.answer(list_user(message.from_user.id))
