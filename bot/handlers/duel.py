from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id, create_duel, update_user_stats, finish_duel
from database.models import User
from services.ranking import process_duel_result
from services.xp import process_xp_for_duel

router = Router()


class DuelStates(StatesGroup):
    waiting_accept = State()


@router.message(Command("duel"))
async def cmd_duel(message: Message, state: FSMContext):
    async with async_session() as session:
        challenger = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        # روش ۱: ریپلای
        if message.reply_to_message:
            opponent_user = message.reply_to_message.from_user
            if opponent_user.id == message.from_user.id:
                await message.answer("❌ نمی‌تونی با خودت دوئل کنی!")
                return
            opponent = await get_or_create_user(
                session,
                telegram_id=opponent_user.id,
                full_name=opponent_user.full_name,
                username=opponent_user.username
            )
        
        # روش ۲: تگ کردن
        elif message.entities:
            mentioned = None
            for entity in message.entities:
                if entity.type == "mention":
                    # @username
                    username = message.text[entity.offset+1:entity.offset+entity.length]
                    # فعلاً ساده پیاده‌سازی می‌کنیم (بعداً بهتر می‌شه)
                    await message.answer("فعلاً لطفاً روی پیام طرف مقابل ریپلای کن و /duel بزن.\n(پشتیبانی کامل تگ به زودی اضافه می‌شه)")
                    return
                elif entity.type == "text_mention":
                    opponent_user = entity.user
                    opponent = await get_or_create_user(
                        session,
                        telegram_id=opponent_user.id,
                        full_name=opponent_user.full_name,
                        username=opponent_user.username
                    )
                    break
            else:
                await message.answer("❌ لطفاً روی پیام طرف مقابل ریپلای کن یا تگش کن.")
                return
        else:
            await message.answer(
                "⚔️ برای شروع دوئل:\n"
                "۱. روی پیام طرف مقابل ریپلای کن و بزن /duel\n"
                "۲. یا بنویس: /duel @username"
            )
            return

        if opponent.is_banned or not opponent.is_active:
            await message.answer("❌ این کاربر در دسترس نیست.")
            return

        # ایجاد دوئل
        duel = await create_duel(session, challenger.id, opponent.id)

        await state.update_data(
            duel_id=duel.id,
            challenger_id=challenger.id,
            opponent_id=opponent.id
        )

        text = (
            f"⚔️ <b>درخواست دوئل!</b>\n\n"
            f"از: {challenger.full_name} ({challenger.rank})\n"
            f"به: {opponent.full_name} ({opponent.rank})\n\n"
            f"{opponent.full_name} برای قبول کردن بنویس: <b>قبول</b>\n"
            f"برای رد کردن بنویس: <b>رد</b>"
        )
        await message.answer(text)
        await state.set_state(DuelStates.waiting_accept)


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["قبول", "accept", "yes", "آره"]))
async def accept_duel(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data:
        await message.answer("درخواستی پیدا نشد.")
        await state.clear()
        return

    async with async_session() as session:
        opponent = await get_user_by_telegram_id(session, message.from_user.id)
        if not opponent or opponent.id != data.get("opponent_id"):
            await message.answer("❌ فقط طرف مقابل می‌تونه قبول کنه.")
            return

        challenger = await session.get(User, data["challenger_id"])
        
        # فعلاً نتیجه تصادفی برای تست (بعداً سیستم واقعی اضافه می‌شه)
        import random
        winner = challenger if random.random() > 0.5 else opponent
        loser = opponent if winner.id == challenger.id else challenger

        await update_user_stats(session, winner, won=True)
        await update_user_stats(session, loser, won=False)

        rank_result = process_duel_result(winner, loser, is_guardian=False)
        xp_messages = process_xp_for_duel(winner, loser, is_guardian=False)

        # امتیاز مشارکت فرقه (فقط اگر عضو فرقه باشه)
        from services.sects import add_contribution
        contrib_msg = ""
        new_points = await add_contribution(session, winner.id, 10)
        if new_points > 0:
            contrib_msg = f"\n🏛️ +۱۰ امتیاز مشارکت فرقه (مجموع: {new_points})"

        await session.commit()

        text = (
            f"🏁 <b>نتیجه دوئل</b>\n\n"
            f"برنده: <b>{winner.full_name}</b> 🏆\n"
            f"بازنده: {loser.full_name}\n\n"
        )
        if rank_result["messages"]:
            text += "\n".join(rank_result["messages"]) + "\n"
        if xp_messages:
            text += "\n".join(xp_messages)
        if contrib_msg:
            text += contrib_msg

        await message.answer(text)
        await state.clear()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["رد", "reject", "no", "نه"]))
async def reject_duel(message: Message, state: FSMContext):
    await message.answer("❌ دوئل رد شد.")
    await state.clear()
