from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user
from services.accounts import create_account, login_account, get_user_accounts

router = Router()


class AccountStates(StatesGroup):
    waiting_name = State()
    waiting_password = State()
    waiting_login_name = State()
    waiting_login_password = State()


@router.message(Command("accounts", "حساب‌ها", "اکانت"))
async def cmd_accounts(message: Message):
    async with async_session() as session:
        accounts = await get_user_accounts(session, message.from_user.id)
    
    text = "👤 <b>سیستم چندحسابه</b>\n\n"
    if accounts:
        text += "حساب‌های تو:\n"
        for acc in accounts:
            main = " (اصلی)" if acc.is_main else ""
            text += f"• {acc.account_name}{main}\n"
    else:
        text += "هنوز حساب اضافی نساختی.\n"
    
    text += (
        "\nدستورات:\n"
        "/createaccount — ساخت حساب جدید\n"
        "/login — ورود به حساب دیگر"
    )
    await message.answer(text)


@router.message(Command("createaccount"))
async def cmd_create_account(message: Message, state: FSMContext):
    await message.answer("نام حساب جدید را بنویس:")
    await state.set_state(AccountStates.waiting_name)


@router.message(AccountStates.waiting_name)
async def process_account_name(message: Message, state: FSMContext):
    await state.update_data(account_name=message.text.strip())
    await message.answer("رمز عبور حساب را بنویس:")
    await state.set_state(AccountStates.waiting_password)


@router.message(AccountStates.waiting_password)
async def process_account_password(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["account_name"]
    password = message.text.strip()
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        await create_account(
            session,
            owner_telegram_id=message.from_user.id,
            account_name=name,
            password=password,
            linked_user_id=user.id
        )
    
    await message.answer(f"✅ حساب «{name}» ساخته شد.")
    await state.clear()


@router.message(Command("login"))
async def cmd_login(message: Message, state: FSMContext):
    await message.answer("نام حساب را بنویس:")
    await state.set_state(AccountStates.waiting_login_name)


@router.message(AccountStates.waiting_login_name)
async def process_login_name(message: Message, state: FSMContext):
    await state.update_data(login_name=message.text.strip())
    await message.answer("رمز عبور را بنویس:")
    await state.set_state(AccountStates.waiting_login_password)


@router.message(AccountStates.waiting_login_password)
async def process_login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data["login_name"]
    password = message.text.strip()
    
    async with async_session() as session:
        acc = await login_account(session, message.from_user.id, name, password)
    
    if acc:
        await message.answer(f"✅ با موفقیت وارد حساب «{acc.account_name}» شدی.")
    else:
        await message.answer("❌ نام حساب یا رمز اشتباه است.")
    
    await state.clear()
