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
from services.i18n import tr

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
    {"category": "منطق", "difficulty": 2, "question_text": "اگر A>B و B>C آنگاه؟", "options": ["A<C", "A=C", "A>C", "نامشخص"], "correct_answer": 2},
    {"category": "ریاضی", "difficulty": 2, "question_text": "۱/۲ + ۱/۴؟", "options": ["۱/۶", "۳/۴", "۲/۶", "۱"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 1, "question_text": "رنگ پرچم ایران از بالا؟", "options": ["قرمز سفید سبز", "سبز سفید قرمز", "آبی سفید قرمز", "سفید سبز قرمز"], "correct_answer": 1},
    {"category": "تاریخ", "difficulty": 2, "question_text": "سلسله قبل از پهلوی؟", "options": ["صفوی", "قاجار", "افشار", "زند"], "correct_answer": 1},
    {"category": "علوم", "difficulty": 2, "question_text": "مرکز منظومه شمسی؟", "options": ["زمین", "ماه", "خورشید", "مشتری"], "correct_answer": 2},
    {"category": "ادبیات", "difficulty": 2, "question_text": "دیوان شرقی از؟", "options": ["گوته", "شکسپیر", "دانته", "هومر"], "correct_answer": 0},
    {"category": "جغرافیا", "difficulty": 1, "question_text": "کشور همسایه شرق ایران؟", "options": ["ترکیه", "عراق", "افغانستان", "ارمنستان"], "correct_answer": 2},
    {"category": "معما", "difficulty": 1, "question_text": "چه چیزی صبح چهار پا، ظهر دو پا، شب سه پا دارد؟", "options": ["سگ", "انسان", "میز", "اسب"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 3, "question_text": "۲ به توان ۵؟", "options": ["۱۰", "۲۵", "۳۲", "۶۴"], "correct_answer": 2},
    {"category": "علوم", "difficulty": 2, "question_text": "H2O چیست؟", "options": ["اکسیژن", "آب", "هیدروژن", "نمک"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 1, "question_text": "چند سیاره در منظومه شمسی؟", "options": ["۷", "۸", "۹", "۱۰"], "correct_answer": 1},
    {"category": "منطق", "difficulty": 3, "question_text": "همه کتاب‌ها کاغذ دارند. این مجله کاغذ دارد. پس؟", "options": ["مجله کتاب است", "نتیجه قطعی نیست", "مجله کتاب نیست", "همه مجلات کتاب‌اند"], "correct_answer": 1},
    {"category": "تاریخ", "difficulty": 1, "question_text": "جنگ جهانی دوم کی تمام شد تقریبی؟", "options": ["۱۹۱۸", "۱۹۳۹", "۱۹۴۵", "۱۹۵۰"], "correct_answer": 2},
    {"category": "جغرافیا", "difficulty": 2, "question_text": "قاره استرالیا در کدام نیمکره است بیشتر؟", "options": ["شمالی", "جنوبی", "فقط شرقی", "فقط غربی"], "correct_answer": 1},
    {"category": "ادبیات", "difficulty": 1, "question_text": "نویسنده بوف کور؟", "options": ["هدایت", "آل‌احمد", "دولت‌آبادی", "دانشور"], "correct_answer": 0},
    {"category": "برنامه", "difficulty": 1, "question_text": "HTML برای چیست؟", "options": ["دیتابیس", "ساختار صفحه وب", "سیستم‌عامل", "کامپایلر"], "correct_answer": 1},
    {"category": "معما", "difficulty": 2, "question_text": "چه کلیدی هیچ قفلی را باز نمی‌کند؟", "options": ["شاه‌کلید", "کلید پیانو", "کلید خانه", "کلید ماشین"], "correct_answer": 1},
    {"category": "علوم", "difficulty": 3, "question_text": "سرعت نور تقریبی؟", "options": ["۳۰۰ کیلومتر", "۳۰۰ هزار کیلومتر بر ثانیه", "۳۰ هزار", "۳ میلیون"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 2, "question_text": "المپیک هر چند سال؟", "options": ["۲", "۳", "۴", "۵"], "correct_answer": 2},
    {"category": "ریاضی", "difficulty": 1, "question_text": "۹ × ۹؟", "options": ["۷۲", "۸۱", "۹۹", "۹۰"], "correct_answer": 1},

    {"category": "منطق", "difficulty": 4, "question_text": "اگر A⇒B و B⇒C و ¬C، کدام درست است؟", "options": ["A حتماً درست", "A حتماً نادرست", "B درست", "هیچ‌کدام"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 4, "question_text": "حد (sin x)/x وقتی x→0؟", "options": ["0", "∞", "1", "وجود ندارد"], "correct_answer": 2},
    {"category": "ریاضی", "difficulty": 3, "question_text": "مشتق x³؟", "options": ["3x", "3x²", "x²", "3x³"], "correct_answer": 1},
    {"category": "فیزیک", "difficulty": 4, "question_text": "ثابت پلانک با چه واحدی؟", "options": ["ژول", "ژول‌ثانیه", "وات", "نیوتن"], "correct_answer": 1},
    {"category": "شیمی", "difficulty": 3, "question_text": "عدد اتمی کربن؟", "options": ["6", "8", "12", "14"], "correct_answer": 0},
    {"category": "شیمی", "difficulty": 4, "question_text": "pH آب خالص در ۲۵°C؟", "options": ["0", "7", "14", "1"], "correct_answer": 1},
    {"category": "تاریخ", "difficulty": 4, "question_text": "سلسله هخامنشی را چه کسی بنیان گذاشت؟", "options": ["داریوش", "کوروش", "خشایارشا", "کمبوجیه"], "correct_answer": 1},
    {"category": "تاریخ", "difficulty": 3, "question_text": "نبرد ملازگرد تقریبی؟", "options": ["۱۰۷۱", "۱۴۵۳", "۱۲۵۸", "۶۳۲"], "correct_answer": 0},
    {"category": "ادبیات", "difficulty": 3, "question_text": "مثنوی معنوی اثر کیست؟", "options": ["سعدی", "حافظ", "مولوی", "فردوسی"], "correct_answer": 2},
    {"category": "ادبیات", "difficulty": 4, "question_text": "وزن عروضی بر پایه چیست؟", "options": ["قافیه", "هجای بلند و کوتاه", "قافیه و ردیف فقط", "معنا"], "correct_answer": 1},
    {"category": "برنامه", "difficulty": 4, "question_text": "پیچیدگی جستجوی دودویی؟", "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"], "correct_answer": 1},
    {"category": "برنامه", "difficulty": 3, "question_text": "HTTP وضعیت 404 یعنی؟", "options": ["موفق", "یافت نشد", "خطای سرور", "هدایت"], "correct_answer": 1},
    {"category": "معما", "difficulty": 4, "question_text": "چه چیزی مال توست اما بیشتر دیگران استفاده می‌کنند؟", "options": ["پول", "اسمت", "خانه‌ات", "زمانت"], "correct_answer": 1},
    {"category": "منطق", "difficulty": 5, "question_text": "پارادوکس دروغگو: «این جمله نادرست است» چه وضعی دارد؟", "options": ["درست", "نادرست", "تناقض‌آمیز", "بی‌معنا نیست"], "correct_answer": 2},
    {"category": "جغرافیا", "difficulty": 3, "question_text": "بلندترین قله ایران؟", "options": ["سبلان", "دماوند", "تفتان", "الوند"], "correct_answer": 1},
    {"category": "جغرافیا", "difficulty": 4, "question_text": "رود نیل عمدتاً به کدام دریا می‌ریزد؟", "options": ["سرخ", "مدیترانه", "سیاه", "خزر"], "correct_answer": 1},
    {"category": "علوم", "difficulty": 4, "question_text": "DNA مخفف چیست تقریباً؟", "options": ["اسید ریبونوکلئیک", "دئوکسی‌ریبونوکلئیک اسید", "پروتئین", "آنزیم"], "correct_answer": 1},
    {"category": "عمومی", "difficulty": 3, "question_text": "واحد پول ژاپن؟", "options": ["یوان", "ین", "وون", "بات"], "correct_answer": 1},
    {"category": "فلسفه", "difficulty": 4, "question_text": "«می‌اندیشم پس هستم» از کیست؟", "options": ["افلاطون", "دکارت", "ارسطو", "کانت"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 5, "question_text": "مجموع زوایای داخلی چندضلعی n ضلعی؟", "options": ["(n-2)×180", "n×180", "(n-1)×180", "360"], "correct_answer": 0},
    {"category": "فیزیک", "difficulty": 3, "question_text": "نیروی گرانش با فاصله چه رابطه‌ای دارد؟", "options": ["مستقیم", "معکوس مربع", "ثابت", "نمایی"], "correct_answer": 1},
    {"category": "تاریخ ایران", "difficulty": 4, "question_text": "ضحاک در شاهنامه با چه معروف است؟", "options": ["دادگر", "مار بر دوش", "پیامبر", "وزیر"], "correct_answer": 1},
    {"category": "تاریخ ایران", "difficulty": 3, "question_text": "کاوه‌ی آهنگر علیه چه کسی شورید؟", "options": ["جمشید", "ضحاک", "افراسیاب", "رستم"], "correct_answer": 1},
    {"category": "منطق", "difficulty": 3, "question_text": "اگر بعضی Aها Bاند و همه Bها Cاند، آیا بعضی Aها Cاند؟", "options": ["حتماً بله", "حتماً خیر", "نتیجه قطعی نیست از این دو", "همه Aها Cاند"], "correct_answer": 0},
    {"category": "برنامه", "difficulty": 5, "question_text": "Deadlock در سیستم‌عامل یعنی؟", "options": ["سرعت بالا", "بن‌بست منابع", "حافظه آزاد", "صف خالی"], "correct_answer": 1},
    {"category": "معما", "difficulty": 3, "question_text": "چیزی که هرچه بیشتر برداری بزرگ‌تر می‌شود؟", "options": ["چاله", "کوه", "درخت", "ابر"], "correct_answer": 0},
    {"category": "شیمی", "difficulty": 5, "question_text": "عدد آووگادرو تقریبی؟", "options": ["۶٫۰۲×۱۰²³", "۳×۱۰⁸", "۹٫۸", "۱٫۶×۱۰⁻¹⁹"], "correct_answer": 0},
    {"category": "ادبیات", "difficulty": 5, "question_text": "سبک هندی بیشتر با کدام شاعر؟", "options": ["صائب", "فردوسی", "رودکی", "نظامی"], "correct_answer": 0},
    {"category": "فیزیک", "difficulty": 5, "question_text": "اصل عدم قطعیت هایزنبرگ درباره چیست؟", "options": ["انرژی فقط", "اندازه‌گیری همزمان مکان و تکانه", "نور فقط", "دما"], "correct_answer": 1},
    {"category": "ریاضی", "difficulty": 4, "question_text": "اگر log₁₀(x)=2 آنگاه x؟", "options": ["20", "100", "0.01", "2"], "correct_answer": 1},

]



def _qid(q: dict) -> str:
    return hashlib.md5(q["question_text"].encode()).hexdigest()[:12]


def _pick_question(user_id: int) -> dict | None:
    seen = _seen.setdefault(user_id, set())
    available = [q for q in SAMPLE_QUESTIONS if _qid(q) not in seen]
    # ترجیح سوال سخت‌تر
    hard = [q for q in available if int(q.get('difficulty') or 1) >= 3]
    if hard and random.random() < 0.65:
        available = hard
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


@router.message(Command("guardian", "نگهبان", "گاردین", "guard"))
async def cmd_guardian(message: Message):
    uid = message.from_user.id
    if uid in _active:
        await message.answer(tr(message.from_user.id, "اول سوال فعلی را جواب بده یا صبر کن تا تمام شود."))
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
        await callback.answer(tr(callback.from_user.id, "نامعتبر"), show_alert=True)
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
        try:
            from services.missions_progress import bump_mission
            await bump_mission(session, user.id, "guardian")
        except Exception:
            pass
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


@router.message(Command("gduel", "نگهبان‌دو نفره", "guardian2", "نگهبان2", "دوئل‌نگهبان"))
async def cmd_gduel(message: Message):
    """دوئل نگهبان دو نفره — ریپلای"""
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی پیام حریف ریپلای کن و /gduel بزن.\nهر کس زودتر جواب درست بدهد می‌برد."))
        return
    u2 = message.reply_to_message.from_user
    if u2.id == message.from_user.id:
        await message.answer(tr(message.from_user.id, "با خودت نه!"))
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
        await callback.answer(tr(callback.from_user.id, "این دوئل تمام شده."), show_alert=True)
        return
    if callback.from_user.id not in g["players"]:
        await callback.answer()
        return
    if g["done"]:
        await callback.answer(tr(callback.from_user.id, "تمام شده"), show_alert=True)
        return

    if selected != correct:
        await callback.answer(tr(callback.from_user.id, "غلط!"), show_alert=True)
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
