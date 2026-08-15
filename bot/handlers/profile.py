from aiogram import Router
from aiogram.types import Message, FSInputFile, FSInputFile, URLInputFile
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power
from services.cities import get_city
from services.economy import get_or_create_wallet
from services.cultivation import get_or_create_cultivation
from services.i18n import tr
from services.portraits import panel_url

router = Router()


@router.message(Command("profile", "me", "پروفایل"))
async def cmd_profile(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
        pw = await calc_power(session, user)
        city = get_city(getattr(user, "city", None) or "tehran")
        wallet = await get_or_create_wallet(session, user.id)
        cult = await get_or_create_cultivation(session, user.id)

        lifespan = getattr(user, "lifespan", None)
        if lifespan is None:
            lifespan = 100
        world = getattr(user, "world", None) or "فانی"

        win_rate = user.win_rate
        virgin = "باکره" if user.is_virgin else "غیر باکره"
        if user.is_dead:
            status = "💀 مرده — /afterdeath"
        elif getattr(user, "is_spirit_raiser", False):
            status = "👻 پرورشدهنده روح"
        else:
            status = "زنده"

        text = (
            f"👤 <b>پروفایل {user.full_name}</b>\n\n"
            f"🏆 رتبه: <b>{user.rank}</b>\n"
            f"⭐ نقش: <b>{user.role}</b>\n"
            f"⚧ جنسیت: {user.gender}\n"
            f"🏙️ شهر: {city['name']} ({city.get('country', '')})\n"
            f"🌌 دنیا: {world}\n"
            f"⚔️ قدرت مبارزه: <b>{pw['total']}</b>\n"
            f"💨 سرعت: <b>{pw.get('speed', 10)}</b> | 🛡️ دفاع: <b>{pw.get('defense', 10)}</b>\n"
            f"🌀 جاخالی: <b>{pw.get('dodge', 0):.1f}%</b> | 🧱 بلاک: <b>{pw.get('block', 0):.1f}%</b>\n"
            f"👻 روح رزمی: +{pw.get('spirit', 0)}\n"
            f"⏳ عمر باقیمانده: <b>{lifespan}</b>\n"
            f"🧬 باکرگی: {virgin}\n"
            f"وضعیت: {status}\n"
        )
        if user.gender == "مرد":
            text += f"☯️ یانگ: {user.yang}%\n"
        elif user.gender == "زن":
            text += f"☯️ یین: {user.yin}%\n"

        text += (
            f"\n🧘 تذهیب: {cult.realm} — مرحله {cult.stage}\n"
            f"ریشه: {cult.spiritual_root}\n"
            f"انرژی: {cult.energy}\n"
            f"\n💰 کیف پول:\n"
            f"├ 🪙 سکه: <b>{wallet.coins}</b>\n"
            f"├ 💎 روحی: <b>{wallet.spirit_stones}</b>\n"
            f"├ ✨ بهشتی: <b>{getattr(wallet, 'heavenly_stones', 0) or 0}</b>\n"
            f"├ 🌌 آسمانی: <b>{getattr(wallet, 'celestial_stones', 0) or 0}</b>\n"
            f"└ 👑 خدا: <b>{getattr(wallet, 'god_stones', 0) or 0}</b>\n"
            f"\nسطح: {user.level} | XP: {user.xp}\n\n"
            f"📊 آمار:\n"
            f"├ برد: {user.wins}\n"
            f"├ باخت: {user.losses}\n"
            f"├ دوئلها: {user.total_duels}\n"
            f"├ درصد برد: {win_rate}%\n"
            f"├ برد متوالی: {user.win_streak}\n"
            f"└ باخت متوالی: {user.loss_streak}\n"
        )
        await message.answer_photo(
            FSInputFile(panel_url("profile_female" if user.gender == "زن" else "profile_male", user.gender, str(user.id))),
            caption=text
        )
