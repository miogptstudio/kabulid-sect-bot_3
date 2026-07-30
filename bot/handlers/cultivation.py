from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from database.models_v3 import CultivationTechnique, UserTechnique
from services.cultivation import (
    get_or_create_cultivation, add_energy,
    ensure_default_techniques, get_active_technique,
    learn_technique, set_active_technique
)

router = Router()

_last_gather: dict[int, datetime] = {}
COOLDOWN_SECONDS = 60

GATHER_PHRASES = [
    "جمع آوری چی", "جمع‌آوری چی", "جمع اوری چی",
    "تذهیب کردن", "مدیتیت", "مدیتیشن",
    "جمع چی", "جذب چی", "کشت چی",
]


class GatherQiFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        text = message.text.strip()
        return text in GATHER_PHRASES or text.lower() in [p.lower() for p in GATHER_PHRASES]


@router.message(Command("cultivation", "تذهیب", "cult"))
async def cmd_cultivation(message: Message):
    async with async_session() as session:
        await ensure_default_techniques(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        tech = await get_active_technique(session, user.id)
    
    text = (
        f"🧘 <b>وضعیت تذهیب</b>\n\n"
        f"ریشه معنوی: <b>{cult.spiritual_root or 'بدون ریشه'}</b>\n"
        f"قلمرو: <b>{cult.realm}</b>\n"
        f"سطح: {cult.stage} / ۳\n"
        f"انرژی: {cult.energy}\n"
    )
    if tech:
        text += f"تکنیک فعال: <b>{tech.name}</b> ({tech.grade})\n"
    else:
        text += "تکنیک فعال: ❌ نداره\n"
    
    text += (
        "\nدستورات:\n"
        "«جمع آوری چی» یا «تذهیب کردن» — جمع انرژی\n"
        "/techniques — تکنیک‌های من\n"
        "/learntech — یادگیری تکنیک پایه\n"
        "/givetech — انتقال تکنیک (ریپلای)"
    )
    await message.answer(text)


@router.message(Command("techniques", "تکنیک‌ها", "تکنیک"))
async def cmd_techniques(message: Message):
    async with async_session() as session:
        await ensure_default_techniques(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(UserTechnique, CultivationTechnique)
            .join(CultivationTechnique, UserTechnique.technique_id == CultivationTechnique.id)
            .where(UserTechnique.user_id == user.id)
        )
        rows = result.all()
    
    if not rows:
        await message.answer("هنوز تکنیکی بلد نیستی.\n/learntech بزن تا تکنیک پایه رو یاد بگیری.")
        return
    
    builder = InlineKeyboardBuilder()
    text = "📜 <b>تکنیک‌های تو</b>\n\n"
    for ut, tech in rows:
        active = " ✅ فعال" if ut.is_active else ""
        text += f"• {tech.name} ({tech.grade}){active}\n"
        if not ut.is_active:
            builder.button(text=f"فعال کردن {tech.name}", callback_data=f"activetech:{tech.id}")
    
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup() if rows else None)


@router.callback_query(F.data.startswith("activetech:"))
async def activate_tech(callback: CallbackQuery):
    tech_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        msg = await set_active_technique(session, user.id, tech_id)
    await callback.answer(msg, show_alert=True)


@router.message(Command("learntech"))
async def cmd_learn_starter(message: Message):
    async with async_session() as session:
        await ensure_default_techniques(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(CultivationTechnique).where(CultivationTechnique.is_starter == True)
        )
        tech = result.scalar_one_or_none()
        if not tech:
            await message.answer("تکنیک پایه‌ای پیدا نشد.")
            return
        msg = await learn_technique(session, user.id, tech)
    await message.answer(msg)


@router.message(Command("givetech", "انتقال‌تکنیک"))
async def cmd_give_tech(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام کسی که می‌خوای تکنیک بدی ریپلای کن و /givetech بزن.")
        return
    
    async with async_session() as session:
        await ensure_default_techniques(session)
        teacher = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        student_tg = message.reply_to_message.from_user
        student = await get_or_create_user(
            session, student_tg.id, student_tg.full_name, student_tg.username
        )
        
        tech = await get_active_technique(session, teacher.id)
        if not tech:
            await message.answer("تکنیک فعالی نداری که انتقال بدی.")
            return
        
        msg = await learn_technique(session, student.id, tech, from_user_id=teacher.id)
        await message.answer(
            f"از طرف {teacher.full_name} به {student.full_name}:\n{msg}"
        )


@router.message(Command("meditate", "مدیتیت"))
async def cmd_meditate(message: Message):
    await do_gather(message, amount=25)


@router.message(GatherQiFilter())
async def text_gather_qi(message: Message):
    await do_gather(message, amount=20)


async def do_gather(message: Message, amount: int = 20):
    user_id = message.from_user.id
    now = datetime.utcnow()
    
    last = _last_gather.get(user_id)
    if last and (now - last).total_seconds() < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - last).total_seconds())
        await message.answer(f"⏳ {remaining} ثانیه دیگه صبر کن.")
        return
    
    _last_gather[user_id] = now
    
    async with async_session() as session:
        await ensure_default_techniques(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await add_energy(session, user.id, amount)
    
    text = f"🌀 (+{amount} انرژی)\n"
    if result.get("messages"):
        text += "\n".join(result["messages"])
    else:
        text += f"انرژی: {result['energy']} | {result.get('root', '')} | {result['realm']} سطح {result['stage']}"
    
    await message.answer(text)


# --- خودارضایی / تمرین انفرادی + یانگ/یین ---
from collections import defaultdict, deque

_solo_times: dict[int, deque] = defaultdict(deque)  # timestamps در یک ساعت اخیر
SOLO_PHRASES = [
    "خودارضایی", "جق", "جق زدن",
    "تمرین انفرادی", "تذهیب انفرادی", "خلوت تذهیب",
]


class SoloFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text.strip() in SOLO_PHRASES


@router.message(Command("solo", "خودارضایی", "انفرادی", "جق"))
@router.message(SoloFilter())
async def cmd_solo(message: Message):
    user_id = message.from_user.id
    now = datetime.utcnow()
    
    # پاک کردن زمان‌های قدیمی‌تر از ۱ ساعت
    times = _solo_times[user_id]
    while times and (now - times[0]).total_seconds() > 3600:
        times.popleft()
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        
        if user.is_dead:
            await message.answer("💀 تو مرده‌ای و نمی‌تونی تذهیب کنی.")
            return
        
        if user.gender == "نامشخص":
            await message.answer("اول با /gender جنسیت خودت رو مشخص کن.")
            return
        
        count_this_hour = len(times)
        times.append(now)
        
        # انرژی پایه
        result = await add_energy(session, user.id, 12)
        text = "🔥 خودارضایی انجام شد (+۱۲ انرژی تذهیب)\n"
        
        # بیش از ۳ بار در ساعت
        if count_this_hour >= 3:
            if user.gender == "مرد":
                user.yang = max(0, user.yang - 1)
                text += f"⚠️ زیاده‌روی! یانگ بدن: {user.yang}%\n"
                if user.yang <= 0:
                    user.is_dead = True
                    text += "💀 یانگ بدنت تمام شد... مردی.\nبا /afterdeath سرنوشتت را انتخاب کن."
            elif user.gender == "زن":
                user.yin = min(100, user.yin + 1)
                text += f"⚠️ زیاده‌روی! یین بدن: {user.yin}%\n"
                if user.yin >= 100:
                    user.is_dead = True
                    text += "💀 یین بدنت به ۱۰۰٪ رسید... مردی.\nبا /afterdeath سرنوشتت را انتخاب کن."
        
        # از دست دادن باکرگی در اولین بار
        if user.is_virgin:
            user.is_virgin = False
            text += "🌸 وضعیت باکرگی: از دست رفت.\n"
        
        await session.commit()
        
        if result.get("messages") and not user.is_dead:
            text += "\n".join(result["messages"])
        elif not user.is_dead:
            text += f"انرژی: {result.get('energy', 0)}"
        
        # نمایش وضعیت
        if user.gender == "مرد":
            text += f"\n☯️ یانگ: {user.yang}%"
        elif user.gender == "زن":
            text += f"\n☯️ یین: {user.yin}%"
    
    await message.answer(text)


@router.message(Command("virgin", "باکرگی", "وضعیت‌بدن"))
async def cmd_body_status(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
    
    virgin = "باکره ✅" if user.is_virgin else "غیر باکره"
    dead = "💀 مرده" if user.is_dead else "زنده"
    text = (
        f"🧬 <b>وضعیت بدن</b>\n\n"
        f"جنسیت: {user.gender}\n"
        f"باکرگی: {virgin}\n"
        f"وضعیت: {dead}\n"
    )
    if user.gender == "مرد":
        text += f"یانگ بدن: {user.yang}%\n"
    elif user.gender == "زن":
        text += f"یین بدن: {user.yin}%\n"
    
    await message.answer(text)
