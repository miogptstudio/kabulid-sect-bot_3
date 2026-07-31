from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

SECTIONS = {
    "duel": ("⚔️ دوئل و نگهبان",
             "/duel ریپلای — دوئل با دکمه قبول/رد\n/guardian — سوال ۲۰ثانیه‌ای\n/gduel ریپلای — دوئل نگهبان دو نفره\n/power — قدرت رزمی"),
    "sect": ("🏛️ فرقه",
             "/sects — لیست\n/newsect نام — ساخت با دکمه نوع\n/joinsect نام — عضو شدن\n/mysect\n/transferleader ریپلای — واگذاری رهبری\n/challengeleader — هر ۱ ساعت\n/betray"),
    "cult": ("🧘 تذهیب",
             "/cultivation\nجمع آوری چی\n/techniques /learntech\n/dual\n/worlds\n/afterdeath\n/releasespirit روح انتقام"),
    "family": ("💍 خانواده",
               "/gender\n/marry نامزدی\n/divorce\n/wives\n/mate راهنمای جفت‌گیری"),
    "shop": ("🛒 مغازه و حیوان",
             "/buildings مغازه (با برگشت)\n/inventory\n/pets /hunt\n/sellpet شماره\n/giftpet شماره (ریپلای)\n/wallet /dailycoin"),
    "world": ("🏙️ جهان",
              "/cities شهرهای ایران\n/travel نام\n/worlds /goworld\n/power\n/dimension بُعد گروه\n/setdimension (ادمین)"),
    "master": ("🎓 استاد",
               "/master\n/takedisciple ریپلای\n/leavemaster لغو رابطه\n/mydisciples /mymaster"),
}


@router.message(Command("help", "راهنما", "منو"))
async def cmd_help_menu(message: Message):
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{message.from_user.id}:{key}")
    builder.adjust(1)
    await message.answer(
        "📖 <b>راهنما</b>\nبخش مورد نظر را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("helpsec:"))
async def help_section(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, key = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer("این منو مال تو نیست!", show_alert=True)
        return
    title, body = SECTIONS.get(key, ("؟", "نامشخص"))
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ بازگشت به منو", callback_data=f"helpback:{owner}")
    await callback.message.edit_text(
        f"<b>{title}</b>\n\n{body}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("helpback:"))
async def help_back(callback: CallbackQuery):
    owner = int(callback.data.split(":")[1])
    if callback.from_user.id != owner:
        await callback.answer("مال تو نیست!", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for key, (title, _) in SECTIONS.items():
        builder.button(text=title, callback_data=f"helpsec:{owner}:{key}")
    builder.adjust(1)
    await callback.message.edit_text(
        "📖 <b>راهنما</b>\nبخش مورد نظر را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
