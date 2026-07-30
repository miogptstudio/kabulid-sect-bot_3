from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from services.master import take_disciple, get_disciples, get_master

router = Router()


@router.message(Command("master", "استاد"))
async def cmd_master(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        
        as_master = await get_disciples(session, user.id)
        as_disciple = await get_master(session, user.id)
    
    text = "🎓 <b>سیستم استاد-شاگردی</b>\n\n"
    
    if as_disciple:
        text += "تو شاگرد هستی.\n"
    elif as_master:
        text += f"تو استاد هستی و {len(as_master)} شاگرد داری.\n"
    else:
        text += "هنوز نه استاد هستی نه شاگرد.\n"
    
    text += (
        "\nدستورات:\n"
        "/takedisciple (ریپلای روی پیام شخص)\n"
        "/mydisciples\n"
        "/mymaster"
    )
    await message.answer(text)


@router.message(Command("takedisciple"))
async def cmd_take_disciple(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام کسی که می‌خوای شاگردت بشه ریپلای کن و /takedisciple بزن.")
        return
    
    async with async_session() as session:
        master = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        disciple_user = message.reply_to_message.from_user
        disciple = await get_or_create_user(
            session, disciple_user.id,
            disciple_user.full_name, disciple_user.username
        )
        
        if master.id == disciple.id:
            await message.answer("نمی‌تونی خودت شاگرد خودت بشی!")
            return
        
        try:
            await take_disciple(session, master, disciple)
            await message.answer(
                f"✅ {disciple.full_name} شاگرد تو شد.\n"
                f"{master.full_name} حالا استادشه."
            )
        except ValueError as e:
            await message.answer(str(e))


@router.message(Command("mydisciples"))
async def cmd_my_disciples(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        disciples = await get_disciples(session, user.id)
    
    if not disciples:
        await message.answer("شاگردی نداری.")
        return
    
    text = f"🎓 شاگردهای تو ({len(disciples)} نفر):\n\n"
    for d in disciples:
        disc_user = await session.get(__import__("database.models", fromlist=["User"]).User, d.disciple_id)
        if disc_user:
            text += f"• {disc_user.full_name}\n"
    await message.answer(text)


@router.message(Command("mymaster"))
async def cmd_my_master(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        relation = await get_master(session, user.id)
        
        if not relation:
            await message.answer("استادی نداری.")
            return
        
        master = await session.get(__import__("database.models", fromlist=["User"]).User, relation.master_id)
        await message.answer(f"🎓 استاد تو: <b>{master.full_name if master else 'نامشخص'}</b>")
