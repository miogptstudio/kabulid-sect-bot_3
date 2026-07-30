from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.config import ADMIN_IDS
from database.engine import async_session
from database.crud import get_user_by_telegram_id, get_or_create_user
from database.models import (
    User, ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR, ROLE_MEMBER
)
from services.ranking import promote, demote, RANKS
from services.roles import can_restrict, can_promote_demote, can_set_deputy, can_ban, can_manage

router = Router()


def is_config_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

    if not (is_config_admin(message.from_user.id) or user.role in (ROLE_LEADER, ROLE_DEPUTY)):
        await message.answer("⛔️ دسترسی نداری.")
        return

    text = (
        "🛠 <b>پنل مدیریت</b>\n\n"
        "<b>دستورات نقش‌ها:</b>\n"
        "/setrole &lt;telegram_id&gt; &lt;نقش&gt;\n"
        "نقش‌ها: رهبر | معاون رهبر | ارجمند | ارشد | عضو\n\n"
        "<b>محدود کردن:</b>\n"
        "/restrict &lt;telegram_id&gt; &lt;دقیقه&gt; [دلیل]\n"
        "/unrestrict &lt;telegram_id&gt;\n\n"
        "<b>رتبه:</b>\n"
        "/promote &lt;telegram_id&gt;\n"
        "/demote &lt;telegram_id&gt;\n\n"
        "<b>دیگر:</b>\n"
        "/ban &lt;telegram_id&gt;\n"
        "/unban &lt;telegram_id&gt;"
    )
    await message.answer(text)


@router.message(Command("setrole"))
async def cmd_setrole(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not (is_config_admin(message.from_user.id) or actor.role == ROLE_LEADER):
            await message.answer("⛔️ فقط رهبر می‌تونه نقش تعیین کنه.")
            return

        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("فرمت: /setrole <telegram_id> <نقش>")
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer("آیدی باید عدد باشد.")
            return

        role_name = parts[2].strip()
        valid_roles = [ROLE_LEADER, ROLE_DEPUTY, ROLE_ARJOMAND, ROLE_SENIOR, ROLE_MEMBER]
        if role_name not in valid_roles:
            await message.answer(f"نقش معتبر نیست.\nنقش‌های مجاز:\n" + "\n".join(valid_roles))
            return

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer("کاربر پیدا نشد.")
            return

        target.role = role_name
        await session.commit()
        await message.answer(f"✅ نقش {target.full_name} به «{role_name}» تغییر کرد.")


@router.message(Command("restrict"))
async def cmd_restrict(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not can_restrict(actor) and not is_config_admin(message.from_user.id):
            await message.answer("⛔️ دسترسی نداری.")
            return

        parts = message.text.split()
        if len(parts) < 3:
            await message.answer("فرمت: /restrict <telegram_id> <دقیقه> [دلیل]")
            return

        try:
            tg_id = int(parts[1])
            minutes = int(parts[2])
        except ValueError:
            await message.answer("آیدی و دقیقه باید عدد باشند.")
            return

        reason = " ".join(parts[3:]) if len(parts) > 3 else "بدون دلیل"

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer("کاربر پیدا نشد.")
            return

        if not can_manage(actor, target) and not is_config_admin(message.from_user.id):
            await message.answer("⛔️ نمی‌تونی این کاربر رو محدود کنی.")
            return

        target.restricted_until = datetime.utcnow() + timedelta(minutes=minutes)
        target.restriction_reason = reason
        await session.commit()

        await message.answer(
            f"🔇 {target.full_name} به مدت {minutes} دقیقه محدود شد.\n"
            f"دلیل: {reason}"
        )


@router.message(Command("unrestrict"))
async def cmd_unrestrict(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not can_restrict(actor) and not is_config_admin(message.from_user.id):
            await message.answer("⛔️ دسترسی نداری.")
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("فرمت: /unrestrict <telegram_id>")
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer("آیدی باید عدد باشد.")
            return

        target = await get_user_by_telegram_id(session, tg_id)
        if not target:
            await message.answer("کاربر پیدا نشد.")
            return

        target.restricted_until = None
        target.restriction_reason = None
        await session.commit()
        await message.answer(f"✅ محدودیت {target.full_name} برداشته شد.")


@router.message(Command("promote"))
async def cmd_promote(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not can_promote_demote(actor) and not is_config_admin(message.from_user.id):
            await message.answer("⛔️ دسترسی نداری.")
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("فرمت: /promote <telegram_id>")
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer("آیدی باید عدد باشد.")
            return

        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            await message.answer("کاربر پیدا نشد.")
            return

        new_rank = promote(user)
        await session.commit()
        if new_rank:
            await message.answer(f"✅ {user.full_name} به «{new_rank}» ارتقا یافت.")
        else:
            await message.answer("کاربر در بالاترین رتبه است.")


@router.message(Command("demote"))
async def cmd_demote(message: Message):
    async with async_session() as session:
        actor = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )

        if not can_promote_demote(actor) and not is_config_admin(message.from_user.id):
            await message.answer("⛔️ دسترسی نداری.")
            return

        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("فرمت: /demote <telegram_id>")
            return

        try:
            tg_id = int(parts[1])
        except ValueError:
            await message.answer("آیدی باید عدد باشد.")
            return

        user = await get_user_by_telegram_id(session, tg_id)
        if not user:
            await message.answer("کاربر پیدا نشد.")
            return

        new_rank = demote(user)
        await session.commit()
        if new_rank:
            await message.answer(f"✅ {user.full_name} به «{new_rank}» تنزل یافت.")
        else:
            await message.answer("کاربر در پایین‌ترین رتبه است.")
