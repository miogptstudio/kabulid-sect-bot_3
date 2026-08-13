from services.i18n import get_lang, t as _t, tr
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import ShopItem, Building
from services.shop import ensure_default_buildings_and_items

router = Router()

HOW_TO = {
    "pill": "داروخانه /buildings — خرید با سکه یا /use",
    "tea": "داروخانه — چای تذهیب +انرژی با کول‌داون",
    "weapon": "آهنگری — خرید؛ /equip برای تجهیز",
    "weapon_unique": "آهنگری — یکتا؛ فقط یک نفر",
    "armor": "آهنگری — زره در کیف قدرت می‌دهد",
    "material": "کیمیاگری / شکار / باغ — مواد ساخت",
    "herb_normal": "باغ گیاهان یا /garden",
    "herb_spiritual": "باغ / مأموریت نادر",
    "tech_book": "سالن تکنیک — یادگیری مستقیم",
    "talisman": "طلسم‌خانه — خرید یا /craft",
}


@router.message(Command("codex", "itemlist", "لیست‌آیتم", "codexitems", "دانشنامه‌آیتم", "انبارکل", "دانشنامه"))
async def cmd_item_codex(message: Message):
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        try:
            result = await session.execute(select(ShopItem).where(ShopItem.is_active == True))
            items = list(result.scalars().all())
        except Exception:
            result = await session.execute(select(ShopItem))
            items = list(result.scalars().all())
        try:
            buildings = {b.id: b for b in (await session.execute(select(Building))).scalars().all()}
        except Exception:
            buildings = {}

    if not items:
        await message.answer("آیتمی نیست. یک‌بار /buildings بزن تا فروشگاه ساخته شود.")
        return

    by_type = {}
    for it in items:
        by_type.setdefault(it.item_type or "other", []).append(it)

    lang = get_lang(message.from_user.id)
    chunks = [f"📚 <b>دانشنامه / Codex</b> — نسخه 4.1.2" + chr(10)          + f"تعداد آیتم: در حال بارگذاری…" + chr(10)]
    for itype, lst in sorted(by_type.items()):
        how = HOW_TO.get(itype, "فروشگاه /buildings یا مأموریت")
        line = f"{chr(10)}<b>▸ {itype}</b> — {how}" + chr(10)
        for it in lst[:20]:
            bname = ""
            if it.building_id and it.building_id in buildings:
                bname = buildings[it.building_id].name
            line += f"• {it.name} | {it.price} سکه | {bname}" + chr(10)
            if it.description:
                line += f"  {it.description[:60]}" + chr(10)
        chunks.append(line)

    text = ""
    for ch in chunks:
        if len(text) + len(ch) > 3500:
            await message.answer(text)
            text = ch
        else:
            text += ch
    if text:
        await message.answer(text)


@router.message(Command("buildingscodex", "ساختمان‌دانشنامه"))
async def cmd_building_codex(message: Message):
    await message.answer(
        f"<b>{_t('building_codex_title', get_lang(message.from_user.id))}</b>" + chr(10)
        + "/itemlist — همه آیتم‌ها و روش تهیه" + chr(10)
        + "/buildings — خرید از ساختمان‌ها" + chr(10)
        + "/craft — ساخت معجون و طلسم" + chr(10)
        + "/inventory — کیف تو"
    )



@router.message(Command("realms", "قلمروها", "قلمرو‌ها", "لیست‌قلمرو"))
async def cmd_realms(message: Message):
    from database.models_v2 import CULTIVATION_REALMS
    from bot.config import ENERGY_BASE, ENERGY_PER_LEVEL_ADD
    lines = ["🌀 <b>قلمروهای تذهیب</b>", ""]
    for i, r in enumerate(CULTIVATION_REALMS, 1):
        lines.append(f"{i}. {r}")
    lines += [
        "",
        f"مراحل در هر قلمرو: ۱۵",
        f"پایه انرژی مرحله ۱: {ENERGY_BASE:,}",
        f"افزایش هر مرحله: +{ENERGY_PER_LEVEL_ADD:,}",
        "",
        "قلمرو بدن: /bodyrealms",
        "قلمرو روح: /spiritrealms",
    ]
    text = chr(10).join(lines)
    # split if long
    if len(text) > 4000:
        await message.answer(chr(10).join(lines[:35]))
        await message.answer(chr(10).join(lines[35:]))
    else:
        await message.answer(text)



@router.message(Command("codexguide", "دانشنامه‌کامل", "مفاهیم"))
async def cmd_codex_guide(message: Message):
    text = (
        "📚 <b>دانشنامه مفاهیم — 4.1.2</b>" + chr(10) + chr(10)
        + "<b>تذهیب</b>: جمع انرژی تا ارتقای مرحله و قلمرو. /realms" + chr(10)
        + "<b>ریشه</b>: ضریب جذب چی؛ با بیداری شانسی." + chr(10)
        + "<b>بدن</b>: پرورش متعادل؛ /bodyrealms" + chr(10)
        + "<b>روح</b>: /spiritrealms و /trainspirit" + chr(10)
        + "<b>دوئل</b>: بر اساس قدرت کل (تذهیب+بدن+کاراکتر+سلاح)" + chr(10)
        + "<b>ارز</b>: سکه → روحی → بهشتی → آسمانی → خدا → هرج → پوچی → ازلی + کارما" + chr(10)
        + "<b>خانه</b>: /myhome بونوس تذهیب" + chr(10)
        + "<b>قفل ممنوعه</b>: بعد از تکنیک/چای ممنوعه دیگر مصرف نداری" + chr(10)
        + "<b>ذخیره</b>: داده‌ها در DB و persist می‌مانند" + chr(10) + chr(10)
        + "/codex — لیست آیتم‌ها | /buildings — فروشگاه | /help — راهنما"
    )
    await message.answer(text)
