"""انتخاب زبان"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.i18n import LANGS, set_lang, t, get_lang, t_user

router = Router()


@router.message(Command("lang", "language", "زبان", "dil", "语言"))
async def cmd_lang(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) >= 2:
        code = parts[1].strip()
        lang = set_lang(message.from_user.id, code)
        if lang not in LANGS:
            await message.answer(t("lang_invalid", get_lang(message.from_user.id)))
            return
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            user.language = lang
            await session.commit()
        await message.answer(t("lang_set", lang, name=LANGS[lang]))
        return

    builder = InlineKeyboardBuilder()
    for code, name in LANGS.items():
        builder.button(text=name, callback_data=f"setlang:{message.from_user.id}:{code}")
    builder.adjust(2)
    lang = get_lang(message.from_user.id)
    await message.answer(t("choose_lang", lang), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("setlang:"))
async def cb_set_lang(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, code = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    if code not in LANGS:
        await callback.answer()
        return
    set_lang(owner, code)
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        user.language = code
        await session.commit()
    await callback.message.edit_text(t("lang_set", code, name=LANGS[code]))
    await callback.answer()
