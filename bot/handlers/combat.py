import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power, win_chance
from services.combat_blood import apply_damage, apply_poison, check_poison_death, has_cyrus

router = Router()


@router.message(Command("kill", "بکش", "قتل"))
async def cmd_kill(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "☠️ حمله: ریپلای + /kill\n"
            "با یک ضربه نمی‌میرد — زخمی و مسموم می‌شود.\n"
            "۳ ساعت فرصت /heal با قرص سلامتی."
        )
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.answer("خودت را نه.")
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
            await message.answer("طرف مرده است.")
            return
        msg_p = await check_poison_death(session, attacker)
        if msg_p:
            await message.answer(msg_p)
            return

        p1 = await calc_power(session, attacker)
        p2 = await calc_power(session, victim)
        # قدرت تعیین می‌کند چقدر آسیب
        dmg = 12 + max(0, (p1["total"] - p2["total"]) // 15)
        cyrus = has_cyrus(attacker)
        if cyrus:
            res = await apply_damage(
                session, attacker, victim, dmg,
                is_cyrus_strike=True, is_death_duel=True
            )
            await message.answer(
                f"⚔️ {attacker.full_name} با شمشیر کوروش به {victim.full_name} زد!\n"
                + "\n".join(res["messages"])
            )
            return

        res = await apply_damage(session, attacker, victim, dmg)
        poison_msg = await apply_poison(session, victim)
        text = (
            f"⚔️ حمله {attacker.full_name} به {victim.full_name}\n"
            f"قدرت {p1['total']} vs {p2['total']}\n"
            + "\n".join(res["messages"]) + "\n" + poison_msg
        )
        await message.answer(text)
