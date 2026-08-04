import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.cultivation import get_or_create_cultivation
from services.economy import get_or_create_wallet
from services.i18n import tr

router = Router()

REALM_CREATURES = {
    "پایه": ["موش روحی", "گنجشک چی", "مار کوچک"],
    "متوسط": ["گرگ باد", "روباه آتش", "لاک‌پشت سنگی"],
    "بالا": ["ببر سفید", "عقاب رعد", "خرس کوه"],
    "پیشرفته": ["اژدهای جوان", "ققنوس خرد", "شیر طلایی"],
    "نیمه‌خدا": ["اژدهای آسمانی", "ققنوس آتشین", "کرگدن آهنی"],
    "خدا": ["اژدهای باستانی", "فرشته نگهبان", "دیو بزرگ"],
    "آسمان": ["اژدهای نه آسمان", "عنقا", "کرم چاله"],
    "ای‌تری": ["موجود ای‌تری", "سایه اتر", "پرتو خالص"],
    "جاودان": ["روح جاودان", "نگهبان ابد", "اژدهای بی‌زمان"],
    "ابدی": ["هیولای ابدی", "خدای کهن", "نهنگ خلا"],
    "خلقت": ["آفریدگار خرد", "پرتو خلقت", "بذر جهان"],
    "پوچی": ["هیچ‌چیز", "سایه پوچ", "بلعنده‌ی وجود"],
}

PATHS = ["ارتدوکس", "بی‌طرف", "شیطانی", "بودایی", "شیطانی‌خون", "طبیعت", "شمشیر تنها"]

WORLDS_EXTRA = [f"جهان-{i}" for i in range(1, 101)] + [
    "جهان آیینه", "جهان سایه", "جهان خون", "جهان یخ", "جهان آتش ابدی",
    "جهان کتاب", "جهان خواب", "جهان مردگان", "جهان خدایان کوچک", "جهان فراموشی",
]


@router.message(Command("creatures", "موجودات"))
async def cmd_creatures(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        realm = cult.realm
    creeps = REALM_CREATURES.get(realm, ["موجود ناشناس"])
    text = f"🐉 موجودات قلمرو <b>{realm}</b>:\n"
    for c in creeps:
        text += f"• {c}\n"
    text += "\n/huntcreature — شکار موجود قلمرو"
    await message.answer(text)


@router.message(Command("huntcreature", "شکار‌موجود"))
async def cmd_hunt_creature(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cult = await get_or_create_cultivation(session, user.id)
        creeps = REALM_CREATURES.get(cult.realm, ["موجود"])
        c = random.choice(creeps)
        if random.random() < 0.4:
            w = await get_or_create_wallet(session, user.id)
            gain = random.randint(20, 80)
            w.coins += gain
            await session.commit()
            await message.answer(f"⚔️ {c} را شکست دادی! +{gain} سکه")
        elif random.random() < 0.15:
            user.is_dead = True
            await session.commit()
            await message.answer(f"💀 {c} تو را کشت. /afterdeath")
        else:
            await message.answer(f"🩸 {c} فرار کرد یا زخمی‌ات کرد.")


@router.message(Command("path", "مسیر"))
async def cmd_path(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if len(parts) < 2:
            await message.answer(
                "مسیرهای تذهیب:\n" + "\n".join(f"• {p}" for p in PATHS) +
                "\n\n/path نام‌مسیر"
            )
            return
        path = parts[1].strip()
        if path not in PATHS:
            await message.answer(tr(message.from_user.id, "مسیر نامعتبر."))
            return
        # store on user role field side - use a simple attribute if exists
        if hasattr(user, "path"):
            user.path = path
        else:
            # stash in rank note - use username path via cultivation talent
            cult = await get_or_create_cultivation(session, user.id)
            cult.talent = path
        await session.commit()
    await message.answer(f"مسیر تذهیب: <b>{path}</b>")


@router.message(Command("worldlist", "لیست‌جهان"))
async def cmd_worldlist(message: Message):
    sample = WORLDS_EXTRA[:15]
    await message.answer(
        "🌌 نمونه‌ای از جهان‌ها:\n" +
        "\n".join(f"• {w}" for w in sample) +
        f"\n… و {len(WORLDS_EXTRA)-15} جهان دیگر\n/goworld نام"
    )


@router.message(Command("attackdim", "حمله‌بعد"))
async def cmd_attack_dim(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.is_dead:
            await message.answer(tr(message.from_user.id, "مرده‌ای."))
            return
        w = await get_or_create_wallet(session, user.id)
        if random.random() < 0.5:
            gain = random.randint(30, 120)
            w.coins += gain
            await session.commit()
            await message.answer(f"🌀 حمله به بُعد دیگر موفق! +{gain} سکه غنیمت")
        else:
            if random.random() < 0.1:
                user.is_dead = True
                await session.commit()
                await message.answer(tr(message.from_user.id, "💀 در بُعد دیگر نابود شدی. /afterdeath"))
            else:
                await message.answer(tr(message.from_user.id, "حمله شکست خورد. بُعد مقاومت کرد."))
