"""راهنما و فهرست دستورات"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADMIN_IDS, BOT_VERSION
from services.i18n import tr
from services.portraits import panel_url

router = Router()

SECTIONS = {
    "start": (
        "🚀 شروع و پایه",
        " /start — شروع ربات\n"
        " /help | /راهنما — راهنما\n"
        " /commands | /دستورات — فهرست دستورات\n"
        " /rules | /قوانین — قوانین\n"
        " /codex | /دانشنامه — دانشنامه\n"
        " /profile | /me — پروفایل\n"
        " /gender | /جنسیت — مرد یا زن\n"
        " /race | /نژاد — نژاد\n"
        " /lang | /زبان — زبان\n"
        " /version | /نسخه — نسخه\n"
        " /ping — تست\n"
        " /guide — راهنمای تازه‌کار\n"
        " /daily — ورود روزانه و استریک\n\n"
        "ترتیب: /start → جنسیت → /race → تذهیب کردن → /learntech → /buildings"
    ),
    "cult": (
        "🧘 تذهیب و قلمرو",
        "بنویس «تذهیب کردن» یا /gather\n"
        " /cultivation | /تذهیب — وضعیت\n"
        " /cultivationrules | /قوانین‌تذهیب — قوانین پایه تذهیب\n"
        " /realms | /قلمروها — قلمروها\n"
        " /learntech نام — یادگیری تکنیک\n"
        " /techniques — لیست و فعال‌سازی\n"
        " /cultpath — مسیر قدرت/سرعت/دفاع\n"
        " /daopath ارتدوکس|شیطانی|بی‌طرف — مسیر معنوی\n"
        " /afk | /afkclaim — تذهیب خودکار\n"
        " /trainstop — قطع تمرین\n"
        " /learnforbidden — پرورش ممنوعه\n"
        " /cultbuilding — ساختمان تذهیب\n"
        " /vein — رگ معنوی\n"
        "تکنیک ساخت جهان: قلمرو خدا مرحله ۹+"
    ),
    "combat": (
        "⚔️ نبرد و دوئل",
        " /duel — دوئل (ریپلای)\n"
        " /randomduel | /دوئل‌رندوم — صف رندوم\n"
        " /randomduelfight — دوئل رندوم فوری\n"
        " /cancelrandom — خروج از صف\n"
        " /arena — آرنا\n"
        " /guardian — نگهبان\n"
        " /ranking | /top — لیدربورد\n"
        " /richest | /پولدارترین — ثروتمندها"
    ),
    "eco": (
        "💰 اقتصاد و مغازه",
        " /wallet — کیف پول\n"
        " /dailycoin — سکه روزانه\n"
        " /buildings | /shop — مغازه\n"
        " /buyitem نام|شماره تعداد — خرید دسته‌ای\n"
        " /inventory | /کیف — موجودی\n"
        " /use شماره [تعداد] — مصرف دسته‌ای\n"
        " /exchangeup | /exchangedown — تبدیل ارز\n"
        " /pay — انتقال هر نوع ارز\n"
        " /payall — انتقال چند ارز با هم\n"
        " /market — بازار\n"
        " /marketoffer — پیشنهاد قیمت\n"
        " /repair — تعمیر (غرق سکه)"
    ),
    "social": (
        "👥 اجتماعی و فرقه",
        " /sects — فرقه‌ها\n"
        " /createsect — ساخت فرقه\n"
        " /warstatus — جنگ قلمرو زمان‌دار\n"
        " /marry | /divorce — ازدواج\n"
        " /master | /disciple — استاد/شاگرد\n"
        " /pets | /hunt — حیوانات و شکار\n"
        " /servants — خدمتکاران\n"
        " /event — رویداد هفتگی"
    ),
    "admin": (
        "🛡 ادمین (سازنده)",
        " /admin — پنل\n"
        " /helpforadmin — راهنمای ادمین\n"
        " /givepower آیدی مقدار [total|power|speed|defense|body] — اعطای قدرت\n"
        " /transfercult مبدأ مقصد — انتقال کامل تذهیب\n"
        " /setrealm | /givemoney — تنظیمات\n"
        "فقط سازنده ربات"
    ),
}


def _kb(uid: int = 0):
    b = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        b.button(text=title, callback_data=f"helpsec:{uid}:{key}")
    b.button(text="📋 همه دستورات", callback_data=f"helpsec:{uid}:all")
    b.adjust(2)
    return b.as_markup()


@router.message(Command("help", "راهنما", "منو", "menu"))
async def cmd_help(message: Message):
    uid = message.from_user.id
    text = (
        f"📖 <b>راهنمای ربات</b> — نسخه {BOT_VERSION}\n\n"
        "یک بخش را انتخاب کن:"
    )
    await message.answer_photo(URLInputFile(panel_url("help", name=str(uid))), caption=text, reply_markup=_kb(uid))


@router.callback_query(F.data.startswith("helpsec:"))
async def cb_help_section(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    try:
        owner = int(parts[1])
    except ValueError:
        owner = 0
    if owner and callback.from_user.id != owner:
        await callback.answer("این منو برای تو نیست.", show_alert=True)
        return
    key = parts[2]
    if key == "all":
        lines = [f"📋 <b>همه دستورات</b> — v{BOT_VERSION}", ""]
        for k, (title, body) in SECTIONS.items():
            lines.append(f"<b>{title}</b>")
            lines.append(body)
            lines.append("")
        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3900] + "\n…"
        await callback.message.edit_text(text, reply_markup=_kb(owner))
        await callback.answer()
        return
    if key not in SECTIONS:
        await callback.answer("بخش نامعتبر", show_alert=True)
        return
    title, body = SECTIONS[key]
    await callback.message.edit_text(
        f"<b>{title}</b>\n\n{body}",
        reply_markup=_kb(owner),
    )
    await callback.answer()


@router.message(Command("commands", "دستورات", "cmds"))
async def cmd_commands(message: Message):
    lines = [f"📋 <b>دستورات</b> v{BOT_VERSION}", ""]
    for key, (title, body) in SECTIONS.items():
        lines.append(f"<b>{title}</b>\n{body}\n")
    text = "\n".join(lines)
    if len(text) > 4000:
        for i in range(0, len(text), 3900):
            await message.answer(text[i:i+3900])
    else:
        await message.answer(text)


@router.message(Command("rules", "قوانین"))
async def cmd_rules(message: Message):
    await message.answer(
        "📜 <b>قوانین</b>\n"
        "• احترام به بازیکنان\n"
        "• سوءاستفاده از باگ = محرومیت\n"
        "• چندحسابه طبق قوانین ربات\n"
        "• تصمیم ادمین نهایی است\n"
        "• مرگ و مجازات‌های درون‌بازی بخشی از گیم‌پلی‌اند"
    )


@router.message(Command("helpforadmin", "ادمین‌راهنما"))
async def cmd_help_admin(message: Message):
    if message.from_user.id not in (ADMIN_IDS or []):
        await message.answer("فقط سازنده.")
        return
    await message.answer(
        "🛡 <b>ادمین</b>\n"
        "/admin — پنل\n"
        "/givepower telegram_id مقدار — قدرت نبرد/بدن\n"
        "/givemoney | /setrealm | /ban | /unban\n"
        "/rewardzahhak حذف شده\n"
        "نسخه: " + str(BOT_VERSION)
    )


@router.message(Command("version", "نسخه"))
async def cmd_version(message: Message):
    await message.answer(f"🤖 نسخه ربات: <b>{BOT_VERSION}</b>")


# سازگاری با start.py و فراخوانی‌های قدیمی
cmd_help_menu = cmd_help
