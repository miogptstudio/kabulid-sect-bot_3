from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user, get_random_question
from database.models import Question
from services.ranking import process_duel_result, promote, can_promote
from services.xp import add_xp
from bot.config import XP_PER_GUARDIAN_WIN

router = Router()


# سوالات نمونه (بعداً از دیتابیس لود می‌شن)
SAMPLE_QUESTIONS = [
    {
        "category": "منطق",
        "difficulty": 1,
        "question_text": "اگر همه گربه‌ها حیوان باشند و برخی حیوان‌ها سیاه باشند، آیا همه گربه‌ها سیاه هستند؟",
        "options": ["بله", "خیر", "نمی‌توان گفت", "بستگی دارد"],
        "correct_answer": 1
    },
    {
        "category": "ریاضی",
        "difficulty": 1,
        "question_text": "حاصل ۲ + ۲ × ۲ چند است؟",
        "options": ["۶", "۸", "۴", "۲"],
        "correct_answer": 0
    },
    {
        "category": "اطلاعات عمومی",
        "difficulty": 2,
        "question_text": "پایتخت ایران کدام شهر است؟",
        "options": ["اصفهان", "تبریز", "تهران", "شیراز"],
        "correct_answer": 2
    },
]


@router.message(Command("guardian"))
async def cmd_guardian(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

    # انتخاب سوال بر اساس سطح (فعلاً نمونه)
    import random
    q = random.choice(SAMPLE_QUESTIONS)

    builder = InlineKeyboardBuilder()
    for i, option in enumerate(q["options"]):
        builder.button(text=option, callback_data=f"guardian_ans:{i}:{q['correct_answer']}")
    builder.adjust(1)

    text = (
        f"🛡️ <b>حالت نگهبان</b>\n\n"
        f"دسته: {q['category']}\n"
        f"سوال:\n{q['question_text']}"
    )
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("guardian_ans:"))
async def process_guardian_answer(callback: CallbackQuery):
    parts = callback.data.split(":")
    selected = int(parts[1])
    correct = int(parts[2])

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username
        )

        if selected == correct:
            # برد
            messages = []
            if can_promote(user):
                new_rank = promote(user)
                messages.append(f"🎉 به رتبه «{new_rank}» ارتقا یافتی!")
            
            xp_res = add_xp(user, XP_PER_GUARDIAN_WIN)
            messages.extend(xp_res["messages"])
            
            await session.commit()

            text = "✅ <b>درست بود!</b>\n\n" + "\n".join(messages) if messages else "✅ درست بود! آفرین."
            await callback.message.edit_text(text)
        else:
            # باخت - فعلاً فقط پیام (تنزل کامل بعداً)
            text = "❌ اشتباه بود.\n\nدر حالت نگهبان باخت تأثیر بیشتری داره. مراقب باش!"
            await callback.message.edit_text(text)

    await callback.answer()
