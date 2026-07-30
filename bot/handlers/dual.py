from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import DualCultivation
from services.dual import request_dual, accept_dual, reject_dual

router = Router()


class GenderStates(StatesGroup):
    waiting = State()


@router.message(Command("gender", "جنسیت"))
async def cmd_gender(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="مرد 👨", callback_data="setgender:مرد")
    builder.button(text="زن 👩", callback_data="setgender:زن")
    builder.button(text="نامشخص", callback_data="setgender:نامشخص")
    builder.adjust(2)
    
    await message.answer(
        "جنسیت خودت رو انتخاب کن:\n"
        "(برای تذهیب دوگانه و برخی قابلیت‌ها استفاده می‌شود)",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("setgender:"))
async def set_gender(callback: CallbackQuery):
    gender = callback.data.split(":")[1]
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        user.gender = gender
        await session.commit()
    
    await callback.message.edit_text(f"✅ جنسیت روی «{gender}» تنظیم شد.")
    await callback.answer()


@router.message(Command("dual", "تذهیب‌دوگانه", "دوگانه"))
async def cmd_dual(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "☯️ برای تذهیب دوگانه:\n"
            "روی پیام طرف مقابل ریپلای کن و بنویس /dual\n\n"
            "شرایط:\n"
            "• یکی مرد و یکی زن باشن\n"
            "• هر دو ریشه معنوی داشته باشن\n"
            "• هر دو تکنیک تذهیب فعال داشته باشن"
        )
        return
    
    async with async_session() as session:
        user1 = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        u2 = message.reply_to_message.from_user
        user2 = await get_or_create_user(
            session, u2.id, u2.full_name, u2.username
        )
        
        result = await request_dual(session, user1, user2)
        
        if isinstance(result, str):
            await message.answer(result)
            return
        
        dual = result
        builder = InlineKeyboardBuilder()
        builder.button(text="قبول ✅", callback_data=f"dualaccept:{dual.id}")
        builder.button(text="رد ❌", callback_data=f"dualreject:{dual.id}")
        builder.adjust(2)
        
        await message.answer(
            f"☯️ <b>درخواست تذهیب دوگانه</b>\n\n"
            f"از: {user1.full_name} ({user1.gender})\n"
            f"به: {user2.full_name} ({user2.gender})\n\n"
            f"{user2.full_name} باید قبول یا رد کنه.",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("dualaccept:"))
async def dual_accept(callback: CallbackQuery):
    dual_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        dual = await session.get(DualCultivation, dual_id)
        if not dual:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        
        msg = await accept_dual(session, dual, callback.from_user.id)
    
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("dualreject:"))
async def dual_reject(callback: CallbackQuery):
    dual_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        dual = await session.get(DualCultivation, dual_id)
        if not dual:
            await callback.answer("درخواست پیدا نشد.", show_alert=True)
            return
        
        msg = await reject_dual(session, dual, callback.from_user.id)
    
    await callback.message.edit_text(msg)
    await callback.answer()
