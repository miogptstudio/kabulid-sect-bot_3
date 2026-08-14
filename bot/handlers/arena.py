from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import User
from services.arena import (
    get_or_create_arena_profile,
    run_arena_fight,
    arena_leaderboard,
    ARENA_TIERS_FULL,
    ENTRY_COST,
    entry_cost_text,
    can_pay_entry,
    charge_entry,
    match_tier,
    create_open_room, join_open_room, list_open_rooms, start_open_arena,
)
from services.power import calc_power
from services.i18n import tr

router = Router()


@router.message(Command("arena", "آرنا"))
async def cmd_arena(message: Message):
    from aiogram.types import FSInputFile
    from services.portraits import panel_url
    await message.answer_photo(FSInputFile(panel_url("arena")), caption="🏟️ <b>آرنا</b>")
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        profile = await get_or_create_arena_profile(session, user.id)
        pw = await calc_power(session, user)

    costs = "\n".join(
        f"• {t}: {entry_cost_text(t)}" for t in ARENA_TIERS_FULL
    )
    text = (
        f"🏟️ <b>آرنا</b>\n\n"
        f"درجه تو: <b>{profile.tier}</b>\n"
        f"امتیاز: <b>{profile.points}</b>\n"
        f"برد/باخت: {profile.wins}/{profile.losses}\n"
        f"قدرت: {pw['total']}\n\n"
        f"<b>هزینه ورود هر درجه</b> (از هر دو نفر):\n{costs}\n\n"
        f"⚔️ /arenafight — چالش (ریپلای)\n"
        f"📊 /arenatop — لیدربورد\n"
        f"درجه مسابقه = بالاترین درجه دو نفر"
    )
    await message.answer(text)


@router.message(Command("arenafight", "مبارزه‌آرنا", "آرنافایت"))
async def cmd_arena_fight(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی حریف ریپلای کن و /arenafight بزن."))
        return

    async with async_session() as session:
        challenger = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        ou = message.reply_to_message.from_user
        if ou.id == message.from_user.id:
            await message.answer(tr(message.from_user.id, "با خودت نه."))
            return
        opponent = await get_or_create_user(
            session, ou.id, ou.full_name, ou.username
        )
        if challenger.is_dead or opponent.is_dead:
            await message.answer(tr(message.from_user.id, "یکی مرده است."))
            return

        cp = await get_or_create_arena_profile(session, challenger.id)
        op = await get_or_create_arena_profile(session, opponent.id)
        tier = match_tier(cp.tier, op.tier)
        cost = entry_cost_text(tier)

        ok1, err1 = await can_pay_entry(session, challenger.id, tier)
        ok2, err2 = await can_pay_entry(session, opponent.id, tier)
        if not ok1:
            await message.answer(f"تو هزینه ورود آرنا {tier} را نداری.\n{err1}")
            return
        if not ok2:
            await message.answer(f"حریف هزینه ورود آرنا {tier} را ندارد.\n{err2}")
            return

        p1 = await calc_power(session, challenger)
        p2 = await calc_power(session, opponent)

    builder = InlineKeyboardBuilder()
    builder.button(
        text="قبول و پرداخت ✅",
        callback_data=f"arenaacc:{challenger.id}:{opponent.id}:{tier}",
    )
    builder.button(
        text="رد ❌",
        callback_data=f"arenarej:{challenger.id}:{opponent.id}",
    )
    builder.adjust(1)
    await message.answer(
        f"🏟️ <b>چالش آرنا — درجه {tier}</b>\n\n"
        f"از: {challenger.full_name} ({cp.tier} | {p1['total']})\n"
        f"به: {opponent.full_name} ({op.tier} | {p2['total']})\n\n"
        f"💰 هزینه ورود هر نفر: <b>{cost}</b>\n"
        f"با قبول، از هر دو کم می‌شود.\n\n"
        f"فقط <b>{opponent.full_name}</b> دکمه بزند.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("arenaacc:"))
async def cb_arena_accept(callback: CallbackQuery):
    parts = callback.data.split(":")
    c_id, o_id = int(parts[1]), int(parts[2])
    tier = parts[3] if len(parts) > 3 else "برنز"
    if tier not in ARENA_TIERS_FULL:
        tier = "برنز"

    async with async_session() as session:
        me = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if me.id != o_id:
            await callback.answer()
            return
        challenger = await session.get(User, c_id)
        opponent = me
        if not challenger:
            await callback.answer()
            return

        ok1, err1 = await can_pay_entry(session, challenger.id, tier)
        ok2, err2 = await can_pay_entry(session, opponent.id, tier)
        if not ok1 or not ok2:
            await callback.message.edit_text(
                f"❌ هزینه ورود کافی نیست.\n{err1}\n{err2}"
            )
            await callback.answer()
            return

        try:
            fee1 = await charge_entry(session, challenger.id, tier)
            fee2 = await charge_entry(session, opponent.id, tier)
            await session.commit()
        except ValueError as e:
            await callback.message.edit_text(f"❌ {e}")
            await callback.answer()
            return

        text = await run_arena_fight(session, challenger, opponent)
        text = f"💳 ورود: {fee1} / {fee2}\n\n" + text
        await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("arenarej:"))
async def cb_arena_reject(callback: CallbackQuery):
    parts = callback.data.split(":")
    o_id = int(parts[2])
    async with async_session() as session:
        me = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if me.id != o_id:
            await callback.answer()
            return
    await callback.message.edit_text(tr(callback.from_user.id, "❌ چالش آرنا رد شد. هزینه‌ای کم نشد."))
    await callback.answer()


@router.message(Command("arenatop", "آرنا‌برتر", "لیدرآرنا"))
async def cmd_arena_top(message: Message):
    async with async_session() as session:
        text = await arena_leaderboard(session)
    await message.answer(text)


@router.message(Command("arenaopen", "آرنا‌باز"))
async def cmd_arena_open(message: Message):
    """ساخت اتاق چندنفره — حداقل ۳ حداکثر ۱۰"""
    parts = (message.text or "").split()
    tier = parts[1] if len(parts) > 1 else "برنز"
    if tier not in ARENA_TIERS_FULL:
        await message.answer("درجه نامعتبر. " + " | ".join(ARENA_TIERS_FULL))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        ok, err = await can_pay_entry(session, user.id, tier)
        if not ok:
            await message.answer(f"برای میزبانی باید بتوانی ورود بپردازی:\n{err}")
            return
        rid = create_open_room(user.id, user.full_name, tier)
    await message.answer(
        f"🏟️ اتاق آرنا #{rid} ساخته شد.\n"
        f"درجه: {tier}\nهزینه ورود هر نفر: {entry_cost_text(tier)}\n"
        f"حداقل ۳ — حداکثر ۱۰ نفر\n"
        f"دیگران: /arenajoin {rid}\n"
        f"شروع (میزبان): /arenastart"
    )


@router.message(Command("arenajoin", "ورود‌آرنا"))
async def cmd_arena_join(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/arenajoin شماره‌اتاق\nلیست: /arenarooms"))
        return
    try:
        rid = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.arena import _open_rooms
        room = _open_rooms.get(rid)
        if room:
            ok, err = await can_pay_entry(session, user.id, room["tier"])
            if not ok:
                await message.answer(f"هزینه ورود نداری:\n{err}")
                return
        msg = join_open_room(rid, user.id, user.full_name)
    await message.answer(msg)


@router.message(Command("arenarooms", "اتاق‌آرنا"))
async def cmd_arena_rooms(message: Message):
    await message.answer(list_open_rooms())


@router.message(Command("arenastart", "شروع‌آرنا"))
async def cmd_arena_start(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        text = await start_open_arena(session, user.id, user.id)
    await message.answer(text)
