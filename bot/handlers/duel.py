import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id, create_duel, update_user_stats
from database.models import User
from services.ranking import process_duel_result
from services.xp import process_xp_for_duel
from services.power import calc_power, win_chance
from services.economy import get_or_create_wallet
from services.sects import add_contribution

router = Router()
_reject_counts: dict[tuple, int] = {}  # (user_id, date) -> count

def _reject_key(uid: int):
    from datetime import date
    return (uid, date.today().isoformat())

def _can_reject(uid: int) -> bool:
    from bot.config import DUEL_REJECT_LIMIT_PER_DAY
    return _reject_counts.get(_reject_key(uid), 0) < DUEL_REJECT_LIMIT_PER_DAY

def _inc_reject(uid: int):
    k = _reject_key(uid)
    _reject_counts[k] = _reject_counts.get(k, 0) + 1



class DuelStates(StatesGroup):
    waiting_accept = State()


async def _resolve_duel(session, challenger: User, opponent: User) -> str:
    p1 = await calc_power(session, challenger)
    p2 = await calc_power(session, opponent)
    chance = win_chance(p1["total"], p2["total"])
    winner = challenger if random.random() < chance else opponent
    loser = opponent if winner.id == challenger.id else challenger
    await update_user_stats(session, winner, won=True)
    await update_user_stats(session, loser, won=False)
    rank_result = process_duel_result(winner, loser, is_guardian=False)
    xp_messages = process_xp_for_duel(winner, loser, is_guardian=False)
    await add_contribution(session, winner.id, 10)
    try:
        w = await get_or_create_wallet(session, winner.id)
        w.coins += 15
    except Exception:
        pass
    await session.commit()
    text = (
        f"🏁 <b>نتیجه دوئل</b>\n"
        f"{challenger.full_name} ({p1['total']}) vs {opponent.full_name} ({p2['total']})\n"
        f"برنده: <b>{winner.full_name}</b> 🏆\n"
        f"بازنده: {loser.full_name}\n🪙 برنده +۱۵ سکه"
    )
    if rank_result.get("messages"):
        text += "\n" + "\n".join(rank_result["messages"])
    if xp_messages:
        text += "\n" + "\n".join(xp_messages)
    return text


@router.message(Command("duel", "دوئل"))
async def cmd_duel(message: Message, state: FSMContext):
    async with async_session() as session:
        challenger = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        opponent = None
        if message.reply_to_message and message.reply_to_message.from_user:
            ou = message.reply_to_message.from_user
            if ou.id == message.from_user.id:
                await message.answer("❌ با خودت نه!")
                return
            opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
        elif message.entities:
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    ou = entity.user
                    opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
                    break
            if not opponent:
                await message.answer("روی پیام حریف ریپلای کن و /duel بزن.")
                return
        else:
            await message.answer("⚔️ روی پیام حریف ریپلای کن و /duel بزن.")
            return

        if opponent.is_banned or not opponent.is_active:
            await message.answer("کاربر در دسترس نیست.")
            return

        p1 = await calc_power(session, challenger)
        p2 = await calc_power(session, opponent)
        await create_duel(session, challenger.id, opponent.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="قبول ✅", callback_data=f"duelacc:{challenger.id}:{opponent.id}")
        builder.button(text="رد ❌", callback_data=f"duelrej:{challenger.id}:{opponent.id}")
        builder.adjust(2)

        chance = win_chance(p1["total"], p2["total"]) * 100
        await message.answer(
            f"⚔️ <b>درخواست دوئل</b>\n\n"
            f"از: {challenger.full_name} — قدرت {p1['total']}\n"
            f"به: {opponent.full_name} — قدرت {p2['total']}\n"
            f"شانس چالش‌گر: ~{chance:.0f}%\n\n"
            f"فقط <b>{opponent.full_name}</b> دکمه بزند.",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(challenger_id=challenger.id, opponent_id=opponent.id)
        await state.set_state(DuelStates.waiting_accept)


@router.callback_query(F.data.startswith("duelacc:"))
async def cb_duel_accept(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    challenger_id, opponent_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, callback.from_user.id)
        if not me or me.id != opponent_id:
            await callback.answer()
            return
        challenger = await session.get(User, challenger_id)
        opponent = me
        text = await _resolve_duel(session, challenger, opponent)
        await callback.message.edit_text(text)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("duelrej:"))
async def cb_duel_reject(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    opponent_id = int(parts[2])
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, callback.from_user.id)
        if not me or me.id != opponent_id:
            await callback.answer()
            return
        if not _can_reject(callback.from_user.id):
            await callback.answer("امروز ۵ بار رد کردی. فردا دوباره.", show_alert=True)
            return
        _inc_reject(callback.from_user.id)
    await callback.message.edit_text("❌ دوئل رد شد.")
    await state.clear()
    await callback.answer()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["قبول", "accept", "آره"]))
async def accept_text(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, message.from_user.id)
        if not me or me.id != data.get("opponent_id"):
            await message.answer("فقط طرف مقابل!")
            return
        challenger = await session.get(User, data["challenger_id"])
        text = await _resolve_duel(session, challenger, me)
        await message.answer(text)
    await state.clear()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["رد", "reject", "نه"]))
async def reject_text(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, message.from_user.id)
        if not me or me.id not in (data.get("opponent_id"), data.get("challenger_id")):
            await message.answer("این دوئل مال تو نیست.")
            return
    await message.answer("❌ دوئل رد شد.")
    await state.clear()
