import asyncio
import hashlib
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user
from services.xp import add_xp
from bot.config import XP_PER_GUARDIAN_WIN, GUARDIAN_TIMEOUT_SEC, GUARDIAN_COOLDOWN_SEC
from datetime import datetime, timedelta
from services.sects import add_contribution
from services.economy import get_or_create_wallet

router = Router()

# سوالاتی که هر کاربر دیده (تا ریست سرور)
_seen: dict[int, set[str]] = {}
# جلسه فعال نگهبان: user_id -> {qid, correct, task}
_active: dict[int, dict] = {}
_last_guardian: dict[int, datetime] = {}
# دوئل نگهبان دو نفره
_gduel: dict[str, dict] = {}

SAMPLE_QUESTIONS = [
    {"category": "منطق", "difficulty": 1, "question_text": "اگر همه گربه‌ها حیوان باشند و برخی حیوان‌ها سیاه، آیا همه گربه‌ها سیاه‌اند؟", "options": ["بله", "خیر", "نمی‌توان گفت", "بستگی دارد"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 1, "question_text": "حاصل ۲ + ۲ × ۲؟", "options": ["۶", "۸", "۴", "۲"], "correct_answer": 0},
    {"category": "عمومی", "difficulty": 1, "question_text": "پایتخت ایران؟", "options": ["اصفهان", "تبریز", "تهران", "شیراز"], "correct_answer": 2},
    {"category": "تاریخ", "difficulty": 1, "question_text": "کوروش بزرگ بنیان‌گذار کدام امپراتوری بود؟", "options": ["ساسانی", "هخامنشی", "اشکانی", "سلجوقی"], "correct_answer": 1},
    {"category": "جغرافیا", "difficulty": 1, "question_text": "بلندترین قله ایران؟", "options": ["سبلان", "دنا", "دماوند", "تفتان"], "correct_answer": 2},
    {"category": "ادبیات", "difficulty": 1, "question_text": "سراینده شاهنامه؟", "options": ["سعدی", "حافظ", "فردوسی", "مولوی"], "correct_answer": 2},
    {"category": "علوم", "difficulty": 1, "question_text": "آب در چند درجه سانتی‌گراد می‌جوشد (سطح دریا)؟", "options": ["۰", "۵۰", "۱۰۰", "۲۱۲"], "correct_answer": 2},
    {"category": "ریاضی", "difficulty": 2, "question_text": "جذر ۱۶؟", "options": ["۲", "۴", "۸", "۱۶"], "correct_answer": 1},
    {"category": "منطق", "difficulty": 2, "question_text": "کدام یکی با بقیه فرق دارد: سگ، گربه، سیب، اسب؟", "options": ["سگ", "گربه", "سیب", "اسب"], "correct_answer": 2},
    {"category": "عمومی", "difficulty": 1, "question_text": "واحد پول ایران؟", "options": ["افغانی", "ریال", "دینار", "لیر"], "correct_answer": 1},
    {"category": "تاریخ", "difficulty": 2, "question_text": "انقلاب مشروطه در چه قرنی رخ داد (شمسی تقریبی)؟", "options": ["۱۱", "۱۲", "۱۳", "۱۴"], "correct_answer": 2},
    {"category": "جغرافیا", "difficulty": 1, "question_text": "دریای شمال ایران؟", "options": ["عمان", "خزر", "سرخ", "سیاه"], "correct_answer": 1},
    {"category": "ادبیات", "difficulty": 2, "question_text": "گلستان اثر کیست؟", "options": ["حافظ", "سعدی", "خیام", "نظامی"], "correct_answer": 1},
    {"category": "علوم", "difficulty": 2, "question_text": "سیاره قرمز؟", "options": ["زهره", "مریخ", "مشتری", "عطارد"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 2, "question_text": "۱۵٪ از ۲۰۰؟", "options": ["۱۵", "۲۰", "۳۰", "۳۵"], "correct_answer": 2},
    {"category": "منطق", "difficulty": 1, "question_text": "اگر امروز سه‌شنبه باشد، فردا؟", "options": ["دوشنبه", "چهارشنبه", "پنجشنبه", "جمعه"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 2, "question_text": "زبان رسمی ایران؟", "options": ["عربی", "ترکی", "فارسی", "کردی"], "correct_answer": 2},
    {"category": "تاریخ", "difficulty": 1, "question_text": "تقویم رسمی ایران؟", "options": ["میلادی", "قمری", "هجری شمسی", "چینی"], "correct_answer": 2},
    {"category": "جغرافیا", "difficulty": 2, "question_text": "استان فارس مرکزش؟", "options": ["یزد", "شیراز", "کرمان", "بوشهر"], "correct_answer": 1},
    {"category": "ادبیات", "difficulty": 1, "question_text": "رباعیات معروف از؟", "options": ["خیام", "رودکی", "عنصری", "فرخی"], "correct_answer": 0},
    {"category": "علوم", "difficulty": 1, "question_text": "گاز لازم برای تنفس انسان؟", "options": ["نیتروژن", "اکسیژن", "هیدروژن", "هلیوم"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 1, "question_text": "۷ × ۸؟", "options": ["۵۴", "۵۶", "۶۳", "۴۸"], "correct_answer": 1},
    {"category": "معما", "difficulty": 2, "question_text": "چیزی که هر چه بیشتر از آن برداری بزرگ‌تر می‌شود؟", "options": ["چاله", "سایه", "باد", "ابر"], "correct_answer": 0},
    {"category": "برنامه", "difficulty": 2, "question_text": "زبان این ربات عمدتاً؟", "options": ["Java", "Python", "PHP", "C++"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 1, "question_text": "تعداد روزهای سال کبیسه؟", "options": ["۳۶۵", "۳۶۶", "۳۶۴", "۳۶۰"], "correct_answer": 1},
]


def _qid(q: dict) -> str:
    return hashlib.md5(q["question_text"].encode()).hexdigest()[:12]


def _pick_question(user_id: int) -> dict | None:
    seen = _seen.setdefault(user_id, set())
    available = [q for q in SAMPLE_QUESTIONS if _qid(q) not in seen]
    if not available:
        seen.clear()
        available = SAMPLE_QUESTIONS[:]
    q = random.choice(available)
    seen.add(_qid(q))
    return q


class GDuelStates(StatesGroup):
    waiting = State()


async def _timeout_solo(bot, chat_id: int, user_id: int, message_id: int):
    await asyncio.sleep(GUARDIAN_TIMEOUT_SEC)
    info = _active.pop(user_id, None)
    if not info:
        return
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="⏰ زمان تمام شد. سوال سوخت.",
        )
    except Exception:
        pass


@router.message(Command("guardian", "نگهبان"))
async def cmd_guardian(message: Message):
    uid = message.from_user.id
    if uid in _active:
        await message.answer("اول سوال فعلی را جواب بده یا صبر کن تا تمام شود.")
        return
    last = _last_guardian.get(uid)
    if last and (datetime.utcnow() - last).total_seconds() < GUARDIAN_COOLDOWN_SEC:
        left = int(GUARDIAN_COOLDOWN_SEC - (datetime.utcnow() - last).total_seconds())
        await message.answer(f"⏳ نگهبان هر ۵ دقیقه یک‌بار. {left} ثانیه صبر کن.")
        return
    _last_guardian[uid] = datetime.utcnow()

    q = _pick_question(uid)
    qid = _qid(q)
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(q["options"]):
        builder.button(
            text=option,
            callback_data=f"gans:{uid}:{qid}:{i}:{q['correct_answer']}",
        )
    builder.adjust(1)

    msg = await message.answer(
        f"🛡️ <b>نگهبان</b> — {GUARDIAN_TIMEOUT_SEC} ثانیه وقت داری!\n\n"
        f"دسته: {q['category']}\n"
        f"{q['question_text']}",
        reply_markup=builder.as_markup(),
    )
    task = asyncio.create_task(
        _timeout_solo(message.bot, message.chat.id, uid, msg.message_id)
    )
    _active[uid] = {"qid": qid, "correct": q["correct_answer"], "task": task}


@router.callback_query(F.data.startswith("gans:"))
async def process_guardian_answer(callback: CallbackQuery):
    parts = callback.data.split(":")
    # gans:uid:qid:selected:correct
    if len(parts) < 5:
        await callback.answer("نامعتبر", show_alert=True)
        return
    owner_id = int(parts[1])
    if callback.from_user.id != owner_id:
        await callback.answer()
        return

    selected = int(parts[3])
    correct = int(parts[4])
    info = _active.pop(owner_id, None)
    if info and info.get("task"):
        info["task"].cancel()

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            callback.from_user.id,
            callback.from_user.full_name,
            callback.from_user.username,
        )
        if selected == correct:
            res = add_xp(user, XP_PER_GUARDIAN_WIN)
            await add_contribution(session, user.id, 5)
            w = await get_or_create_wallet(session, user.id)
            w.coins += 10
            await session.commit()
            text = f"✅ درست!\n+{XP_PER_GUARDIAN_WIN} XP و +۱۰ سکه"
            if res.get("messages"):
                text += "\n" + "\n".join(res["messages"])
        else:
            text = f"❌ غلط. جواب درست گزینه {correct + 1} بود."
            await session.commit()

    try:
        await callback.message.edit_text(text)
    except Exception:
        await callback.message.answer(text)
    await callback.answer()


@router.message(Command("gduel", "نگهبان‌دو نفره"))
async def cmd_gduel(message: Message):
    """دوئل نگهبان دو نفره — ریپلای"""
    if not message.reply_to_message:
        await message.answer("روی پیام حریف ریپلای کن و /gduel بزن.\nهر کس زودتر جواب درست بدهد می‌برد.")
        return
    u2 = message.reply_to_message.from_user
    if u2.id == message.from_user.id:
        await message.answer("با خودت نه!")
        return

    q = random.choice(SAMPLE_QUESTIONS)
    qid = _qid(q)
    key = f"{min(message.from_user.id, u2.id)}_{max(message.from_user.id, u2.id)}_{qid}"
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(q["options"]):
        builder.button(text=option, callback_data=f"gdans:{key}:{i}:{q['correct_answer']}")
    builder.adjust(1)

    _gduel[key] = {
        "players": {message.from_user.id, u2.id},
        "done": False,
        "correct": q["correct_answer"],
    }
    await message.answer(
        f"🛡️⚔️ <b>دوئل نگهبان</b>\n"
        f"{message.from_user.full_name} vs {u2.full_name}\n"
        f"۲۰ ثانیه — هر کس زودتر درست بگوید می‌برد!\n\n"
        f"{q['question_text']}",
        reply_markup=builder.as_markup(),
    )
    asyncio.create_task(_timeout_gduel(message.bot, message.chat.id, key, GUARDIAN_TIMEOUT_SEC))


async def _timeout_gduel(bot, chat_id, key, sec):
    await asyncio.sleep(sec)
    g = _gduel.pop(key, None)
    if g and not g.get("done"):
        try:
            await bot.send_message(chat_id, "⏰ دوئل نگهبان بدون برنده تمام شد.")
        except Exception:
            pass


@router.callback_query(F.data.startswith("gdans:"))
async def gduel_ans(callback: CallbackQuery):
    parts = callback.data.split(":")
    # gdans:key:selected:correct  key may contain underscores
    if len(parts) < 4:
        await callback.answer("نامعتبر")
        return
    correct = int(parts[-1])
    selected = int(parts[-2])
    key = ":".join(parts[1:-2]) if False else parts[1]
    # callback_data was f"gdans:{key}:{i}:{correct}" and key has underscores
    key = parts[1]
    selected = int(parts[2])
    correct = int(parts[3])

    g = _gduel.get(key)
    if not g:
        await callback.answer("این دوئل تمام شده.", show_alert=True)
        return
    if callback.from_user.id not in g["players"]:
        await callback.answer()
        return
    if g["done"]:
        await callback.answer("تمام شده", show_alert=True)
        return

    if selected != correct:
        await callback.answer("غلط!", show_alert=True)
        return

    g["done"] = True
    _gduel.pop(key, None)
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        add_xp(user, XP_PER_GUARDIAN_WIN)
        w = await get_or_create_wallet(session, user.id)
        w.coins += 20
        await session.commit()

    await callback.message.edit_text(
        f"🏆 {callback.from_user.full_name} زودتر جواب درست داد و برد!"
    )
    await callback.answer("بردی!")
