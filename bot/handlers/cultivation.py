from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from database.models_v3 import CultivationTechnique, UserTechnique
from services.i18n import t_user, tr
from services.cultivation import (
    get_or_create_cultivation, add_energy,
    ensure_default_techniques, get_active_technique,
    learn_technique, set_active_technique
)

router = Router()

_last_gather: dict[int, datetime] = {}
COOLDOWN_SECONDS = 60

GATHER_PHRASES = [
    "تزکیه",

    'Cultivate', 'Gather Qi', 'Kültive et', 'Qi topla', 'Культивировать', 'Собрать Ци', 'تأمل', 'تذهیب کردن', 'جمع آوری چی', 'جمع الطاقة', 'جمع\u200cآوری چی', 'مدیتیت', '修炼', '聚气',
    "جمع چی", "جذب چی", "کشت چی",
]


class GatherQiFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        text = message.text.strip()
        return text in GATHER_PHRASES or text.lower() in [p.lower() for p in GATHER_PHRASES]


@router.message(Command("cultivation", "تذهیب", "cult", "tazhib"))
async def cmd_cultivation(message: Message):
    try:
        from services.cultivation import energy_needed_for_stage
        async with async_session() as session:
            await ensure_default_techniques(session)
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            cult = await get_or_create_cultivation(session, user.id)
            tech = await get_active_technique(session, user.id)
            need = energy_needed_for_stage(cult.stage or 1, cult.realm, cult.spiritual_root)
        text = (
            f"🧘 <b>وضعیت تذهیب</b>\n\n"
            f"ریشه: <b>{cult.spiritual_root or 'بدون ریشه'}</b>\n"
            f"قلمرو: <b>{cult.realm}</b> | مرحله: {cult.stage}/{10}\n"
            f"انرژی: {cult.energy} / {need}\n"
            f"جنسیت: {user.gender}\n"
        )
        if tech:
            text += f"تکنیک فعال: <b>{tech.name}</b> ({tech.grade})\n"
        else:
            text += "تکنیک فعال: ❌ — /learntech\n"
        text += (
            "\n⚡ جمع انرژی:\n"
            "• دکمه «تذهیب کردن» یا «جمع آوری چی»\n"
            "• /gather یا /meditate\n"
            "• اول /gender اگر جنسیت نزدی\n"
            "/techniques /learntech /afk /body"
        )
        await message.answer(text)
    except Exception as e:
        await message.answer(f"خطا در تذهیب: {type(e).__name__}: {e}")


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
        await message.answer(tr(message.from_user.id, "هنوز تکنیکی بلد نیستی.\n/learntech بزن تا تکنیک پایه رو یاد بگیری."))
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


@router.message(Command("learnforbidden", "پرورش‌ممنوعه", "ممنوعه"))
async def cmd_learn_forbidden(message: Message):
    """یادگیری تکنیک پرورش ممنوعه — غیرقابل برگشت"""
    async with async_session() as session:
        await ensure_default_techniques(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(CultivationTechnique).where(CultivationTechnique.name == "پرورش ممنوعه")
        )
        tech = result.scalar_one_or_none()
        if not tech:
            await message.answer(tr(message.from_user.id, "تکنیک پیدا نشد. بعداً تلاش کن."))
            return
        msg = await learn_technique(session, user.id, tech)
        await message.answer(msg)


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
            result = await session.execute(
                select(CultivationTechnique).where(CultivationTechnique.name == "تنفس پایه")
            )
            tech = result.scalar_one_or_none()
        if not tech:
            await message.answer(tr(message.from_user.id, "تکنیک پایه‌ای پیدا نشد. یک‌بار /cultivation بزن و دوباره /learntech"))
            return
        msg = await learn_technique(session, user.id, tech)
    await message.answer(msg)


@router.message(Command("givetech", "انتقال‌تکنیک"))
async def cmd_give_tech(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی پیام کسی که می‌خوای تکنیک بدی ریپلای کن و /givetech بزن."))
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
            await message.answer(tr(message.from_user.id, "تکنیک فعالی نداری که انتقال بدی."))
            return
        
        msg = await learn_technique(session, student.id, tech, from_user_id=teacher.id)
        await message.answer(
            f"از طرف {teacher.full_name} به {student.full_name}:\n{msg}"
        )


@router.message(Command("meditate", "مدیتیت"))
async def cmd_meditate(message: Message):
    await do_gather(message, amount=5000)


@router.message(GatherQiFilter())
async def text_gather_qi(message: Message):
    try:
        from bot.config import GATHER_ENERGY_AMOUNT
        amt = GATHER_ENERGY_AMOUNT
    except Exception:
        amt = 1
    await do_gather(message, amount=amt)


async def do_gather(message: Message, amount: int = 5000):
    user_id = message.from_user.id
    now = datetime.utcnow()

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer(
                "⚧ قبل از تذهیب باید جنسیت را مشخص کنی.\n"
                "با /gender انتخاب کن.\n"
                "⚠️ بعد از انتخاب، قابل تغییر نیست."
            )
            return
        if user.is_dead:
            await message.answer(tr(message.from_user.id, "💀 مرده‌ای. /afterdeath"))
            return
        try:
            from services.prison import check_prison_block
            block = await check_prison_block(session, user)
            if block:
                await message.answer(block)
                return
        except Exception:
            pass

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
        try:
            from services.missions_progress import bump_mission
            for m in await bump_mission(session, user.id, "gather"):
                pass
        except Exception:
            pass
        try:
            need2 = energy_needed_for_stage(result.get("stage") or 1, result.get("realm"), result.get("root"))
        except Exception:
            need2 = result.get("need") or 0
        # refresh cult for accurate numbers
        cult2 = await get_or_create_cultivation(session, user.id)
        need2 = energy_needed_for_stage(cult2.stage or 1, cult2.realm, cult2.spiritual_root)
        cur2 = int(cult2.energy or 0)
        stage2 = cult2.stage or 1
        realm2 = cult2.realm or "?"
        root2 = cult2.spiritual_root or "بدون ریشه"
        tech2 = await get_active_technique(session, user.id)
        tech_n = tech2.name if tech2 else "—"
        absorbed = result.get("gained") or amount
        text = (
            f"🌀 <b>تزکیه / جمع چی</b>" + chr(10)
            + f"چی جذب‌شده این بار: <b>+{absorbed}</b>" + chr(10) + chr(10)
            + f"ریشه: <b>{root2}</b>" + chr(10)
            + f"قلمرو: <b>{realm2}</b> | مرحله: {stage2}" + chr(10)
            + f"انرژی: <b>{cur2}</b> / <b>{need2}</b>" + chr(10)
            + f"مانده تا ارتقا: <b>{max(0, int(need2) - int(cur2))}</b>" + chr(10)
            + f"تکنیک فعال: {tech_n}"
        )
        if result.get("messages"):
            text += chr(10) + chr(10) + chr(10).join(result["messages"])
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
            await message.answer(tr(message.from_user.id, "💀 تو مرده‌ای و نمی‌تونی تذهیب کنی."))
            return
        
        if user.gender == "نامشخص":
            await message.answer(tr(message.from_user.id, "اول با /gender جنسیت خودت رو مشخص کن."))
            return

        count_this_hour = len(times)
        times.append(now)

        # انرژی پایه
        result = await add_energy(session, user.id, 12)
        user.solo_count = (getattr(user, "solo_count", 0) or 0) + 1

        # ۳ بار اول در ساعت: بدون کاهش عمر | از بار چهارم عمر کم می‌شود
        if count_this_hour < 3:
            text = (
                "🔥 خودارضایی (+انرژی)" + chr(10)
                + f"در این ساعت: {count_this_hour + 1}/3 بدون کاهش عمر" + chr(10)
            )
            if hasattr(user, "lifespan"):
                text += f"⏳ عمر: {user.lifespan or 100}%" + chr(10)
        else:
            try:
                from bot.config import SOLO_LIFESPAN_COST
                cost = int(SOLO_LIFESPAN_COST)
            except Exception:
                cost = 5
            if hasattr(user, "lifespan"):
                user.lifespan = max(0, (user.lifespan or 100) - cost)
                if user.lifespan <= 0:
                    user.is_dead = True
            text = (
                "🔥 خودارضایی — زیاده‌روی (بیش از ۳ بار در ساعت)" + chr(10)
                + f"−{cost}% عمر" + chr(10)
            )
            if hasattr(user, "lifespan"):
                text += f"⏳ عمر باقی: {user.lifespan}%" + chr(10)
            if getattr(user, "is_dead", False):
                text += "💀 عمر تمام شد. /afterdeath" + chr(10)

        # بیش از ۳ بار در ساعت: یانگ/یین
        if count_this_hour >= 3:
            if user.gender == "مرد":
                user.yang = max(0, (user.yang or 100) - 1)
                text += f"⚠️ یانگ بدن: {user.yang}%" + chr(10)
                if user.yang <= 0:
                    user.is_dead = True
                    text += "💀 یانگ تمام شد. /afterdeath" + chr(10)
            elif user.gender == "زن":
                user.yin = min(100, (user.yin or 0) + 1)
                text += f"⚠️ یین بدن: {user.yin}%" + chr(10)
                if user.yin >= 100:
                    user.is_dead = True
                    text += "💀 یین به ۱۰۰٪ رسید. /afterdeath" + chr(10)

        # خودارضایی باکرگی را از بین نمی‌برد

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


from datetime import datetime, timedelta, timedelta
from bot.config import GATHER_ENERGY_AMOUNT

@router.message(Command("afk", "تذهیب‌خودکار", "AFK"))
async def cmd_afk(message: Message):
    """تذهیب خودکار نیم‌ساعته — از بیداری ریشه تا پایه"""
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer(tr(message.from_user.id, "اول /gender"))
            return
        cult = await get_or_create_cultivation(session, user.id)
        now = datetime.utcnow()
        if cult.afk_until and cult.afk_until > now:
            left = int((cult.afk_until - now).total_seconds() // 60)
            await message.answer(f"هنوز AFK هستی. حدود {left} دقیقه مانده. /afkclaim")
            return
        cult.afk_until = now + timedelta(minutes=30)
        await session.commit()
    await message.answer(
        "🧘 حالت AFK روشن شد (۳۰ دقیقه).\n"
        "بعد از نیم ساعت /afkclaim بزن تا پاداش تذهیب را بگیری.\n"
        "هدف: پیشرفت از بیداری ریشه تا قلمرو پایه."
    )


@router.message(Command("afkclaim", "دریافت‌افک"))
async def cmd_afk_claim(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        now = datetime.utcnow()
        if not cult.afk_until:
            await message.answer(tr(message.from_user.id, "AFK فعال نیست. /afk"))
            return
        if cult.afk_until > now:
            left = int((cult.afk_until - now).total_seconds())
            await message.answer(f"هنوز وقت تمام نشده ({left} ثانیه).")
            return
        # پاداش بزرگ برای رسیدن نزدیک پایه
        from services.cultivation import add_energy, energy_needed_for_stage, BODY_BONUS
        # انرژی کافی برای چند سطح
        gain = 80_000
        cult.afk_until = None
        result = await add_energy(session, user.id, gain)
        # اگر هنوز بیداری است و ریشه ندارد، کمک به باز شدن ریشه
        cult = await get_or_create_cultivation(session, user.id)
        msgs = result.get("messages") or []
        # تلاش برای رساندن به پایه
        if cult.realm in ("بیداری", "پایه") or cult.spiritual_root in (None, "بدون ریشه"):
            extra = await add_energy(session, user.id, 100_000)
            msgs.extend(extra.get("messages") or [])
            cult = await get_or_create_cultivation(session, user.id)
            if cult.realm == "بیداری" and cult.spiritual_root and cult.spiritual_root != "بدون ریشه":
                cult.realm = "پایه"
                cult.stage = 1
                await session.commit()
                msgs.append("🌟 به قلمرو «پایه» رسیدی!")
        await session.commit()
        text = "⏳ AFK تمام شد!\n" + "\n".join(msgs) if msgs else "⏳ AFK تمام شد و انرژی اضافه شد."
        await message.answer(text)


@router.message(Command("body", "بدن", "نوع‌بدن"))
async def cmd_body(message: Message):
    from services.cultivation import BODY_TYPES, BODY_BONUS, get_or_create_cultivation
    parts = (message.text or "").split(maxsplit=1)
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        if len(parts) < 2:
            cur = getattr(cult, "body_type", None) or "بدن معمولی"
            lines = [f"بدن فعلی: <b>{cur}</b>\n", "انواع:"]
            for b in BODY_TYPES:
                lines.append(f"• {b} (×{BODY_BONUS.get(b, 1)})")
            lines.append("\n/body نام‌بدن — انتخاب (یک‌بار رایگان بدن معمولی؛ بقیه با سنگ)")
            await message.answer("\n".join(lines))
            return
        name = parts[1].strip()
        if name not in BODY_TYPES:
            await message.answer(tr(message.from_user.id, "نام بدن نامعتبر."))
            return
        if name != "بدن معمولی":
            from services.economy import get_or_create_wallet
            w = await get_or_create_wallet(session, user.id)
            cost = {"بدن چوب زمینی": 50, "بدن بهشتی": 5, "بدن اژدهای اعظم": 20,
                    "بدن خدایان": 50, "بدن خدای غبطه‌انگیز": 1, "بدن نورانی": 10,
                    "بدن تاریک": 10, "بدن روحی": 15}.get(name, 10)
            # خدای غبطه با سنگ خدا، بقیه بهشتی یا روحی
            if name == "بدن خدای غبطه‌انگیز":
                if (w.god_stones or 0) < 1:
                    await message.answer(tr(message.from_user.id, "نیاز ۱ سنگ خدا"))
                    return
                w.god_stones -= 1
            elif name in ("بدن بهشتی", "بدن خدایان"):
                if (w.heavenly_stones or 0) < cost:
                    await message.answer(f"نیاز {cost} سنگ بهشتی")
                    return
                w.heavenly_stones -= cost
            else:
                if (w.spirit_stones or 0) < cost:
                    await message.answer(f"نیاز {cost} سنگ روحی")
                    return
                w.spirit_stones -= cost
        cult.body_type = name
        await session.commit()
        await message.answer(f"✅ بدن «{name}» فعال شد. (ضریب تذهیب ×{BODY_BONUS.get(name, 1)})")

# ——— پرورش بدن ———
@router.message(Command("bodytechs", "تکنیک‌بدن", "bodytechniques"))
async def cmd_body_techs(message: Message):
    from services import body_cult as bc
    await message.answer(bc.list_techs())


@router.message(Command("mybody", "بدن‌من", "وضعیت‌بدن"))
async def cmd_my_body(message: Message):
    from services import body_cult as bc
    await message.answer(bc.status(message.from_user.id))


@router.message(Command("bodycult", "پرورش‌بدن", "bodytrain"))
async def cmd_body_cult(message: Message):
    from services import body_cult as bc
    from services.cultivation import get_or_create_cultivation
    parts = (message.text or "").split(maxsplit=1)
    tech = None
    if len(parts) > 1:
        tech = parts[1].strip()
        if tech not in bc.BODY_TECHS:
            for k in bc.BODY_TECHS:
                if tech in k or k in tech:
                    tech = k
                    break
    ok, msg, cost = bc.train_body(message.from_user.id, tech)
    if not ok:
        await message.answer(msg)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        if (cult.energy or 0) < cost:
            await message.answer(f"انرژی کافی نیست (نیاز {cost}). /gather یا /afk")
            return
        cult.energy = (cult.energy or 0) - cost
        await session.commit()
    await message.answer(msg)


@router.message(F.text.in_({"پرورش بدن", "پرورش دادن بدن", "بدن پروری", "پرورش‌بدن"}))
async def text_body_train(message: Message):
    await cmd_body_cult(message)

