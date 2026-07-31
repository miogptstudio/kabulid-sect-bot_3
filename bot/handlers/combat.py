import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power, win_chance

router = Router()


@router.message(Command("kill", "بکش", "قتل"))
async def cmd_kill(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "☠️ برای حمله مرگبار روی پیام طرف ریپلای کن و /kill بزن.\n"
            "بر اساس قدرت؛ بازنده ممکن است بمیرد."
        )
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.answer("نمی‌توانی خودت را بکشی این‌طور.")
        return

    async with async_session() as session:
        attacker = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        victim = await get_or_create_user(session, t.id, t.full_name, t.username)
        if attacker.is_dead:
            await message.answer("تو مرده‌ای.")
            return
        if victim.is_dead:
            await message.answer("طرف از قبل مرده.")
            return

        p1 = await calc_power(session, attacker)
        p2 = await calc_power(session, victim)
        chance = win_chance(p1["total"], p2["total"])
        if random.random() < chance:
            victim.is_dead = True
            if hasattr(victim, "lifespan"):
                victim.lifespan = 0
            await session.commit()
            await message.answer(
                f"☠️ {attacker.full_name} ({p1['total']}) "
                f"{victim.full_name} ({p2['total']}) را کشت!\n"
                f"{victim.full_name} مرد. /afterdeath"
            )
        else:
            # counter chance
            if random.random() < 0.3:
                attacker.is_dead = True
                await session.commit()
                await message.answer(
                    f"⚔️ حمله شکست خورد و {victim.full_name} ضدحمله کرد!\n"
                    f"{attacker.full_name} مرد. /afterdeath"
                )
            else:
                dmg = random.randint(5, 20)
                if hasattr(victim, "lifespan"):
                    victim.lifespan = max(0, (victim.lifespan or 100) - dmg)
                    if victim.lifespan <= 0:
                        victim.is_dead = True
                await session.commit()
                await message.answer(
                    f"🩸 حمله زخمی کرد (−{dmg} عمر) ولی نکشت.\n"
                    f"قدرت‌ها: {p1['total']} vs {p2['total']}"
                )
